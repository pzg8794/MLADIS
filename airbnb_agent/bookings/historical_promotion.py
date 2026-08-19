"""Reconcile verified PREPARE history into MLADIS transactional objects.

This module is the explicit PREPARE -> PROMOTE boundary. It reads only files
listed in the historical manifest, verifies every selected file, resolves
identity before writing, and records stable source markers so reruns are
idempotent. Ambiguous evidence is reported and never guessed.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from django.db import transaction
from django.utils.dateparse import parse_datetime

from .historical_data import (
    ArchiveIntegrityError,
    FilesystemHistoryStorage,
    HistoricalDataPreparationService,
)
from .models import (
    AirbnbGuestRecord,
    BookableItem,
    BookingInquiry,
    BookingStatus,
    ClientSegment,
    ContactSource,
    CustomerFeedback,
    CustomerProfile,
    MarketingConsentStatus,
)


HOT_OBSERVATIONS_RE = re.compile(r"^partitions/hot/\d{4}/clean_observations\.jsonl$")
PROFILE_MARKER_PREFIX = "historical-guest"
RESERVATION_MARKER_PREFIX = "historical-reservation"
AIRBNB_RECORD_MARKER_PREFIX = "historical-airbnb-record"


class HistoricalPromotionError(RuntimeError):
    """Raised when verified history cannot be promoted without guessing."""


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _email(value: Any) -> str:
    return _clean(value).lower()


def _phone(value: Any) -> str:
    return "".join(character for character in _clean(value) if character.isdigit())


def _usable(value: Any) -> bool:
    return value not in (None, "", [], {}, "[redacted]")


def _source_marker(prefix: str, reference: str) -> str:
    return f"[{prefix}:{reference}]"


def _append_marker(value: str, marker: str, note: str = "") -> str:
    current = str(value or "").strip()
    if marker in current:
        return current
    additions = [marker]
    if note:
        additions.append(note)
    return "\n".join(part for part in (current, *additions) if part)


def _date(value: Any) -> date | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _latest(observations: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    return max(
        observations,
        key=lambda row: (
            str((row.get("facts") or {}).get("updated_at") or ""),
            str(row.get("activity_at") or ""),
            str(row.get("observation_id") or ""),
        ),
    )


class PreparedHistoryRepository:
    """Verified, manifest-bounded reader for hot CLEAN/PREPARE evidence."""

    def __init__(self, root: str | Path, *, private_working_segment: bool):
        self.storage = FilesystemHistoryStorage(
            root,
            private_working_segment=private_working_segment,
        )
        self._manifest: dict[str, Any] | None = None

    def manifest(self) -> dict[str, Any]:
        if self._manifest is None:
            manifest = self.storage.read_json(HistoricalDataPreparationService.MANIFEST_PATH)
            if manifest.get("sidecar") != "airbnb-historical-data":
                raise ArchiveIntegrityError("The history manifest has an unsupported sidecar identity.")
            if not {"clean", "prepare"}.issubset(set(manifest.get("stages") or [])):
                raise ArchiveIntegrityError("The history manifest does not contain CLEAN and PREPARE stages.")
            if not isinstance(manifest.get("files"), Mapping):
                raise ArchiveIntegrityError("The history manifest has no verified file inventory.")
            self._manifest = manifest
        return self._manifest

    def hot_observations(self) -> list[dict[str, Any]]:
        manifest = self.manifest()
        records: list[dict[str, Any]] = []
        selected = [
            (str(path), metadata)
            for path, metadata in manifest["files"].items()
            if HOT_OBSERVATIONS_RE.match(str(path))
        ]
        for relative_path, metadata in sorted(selected):
            if not isinstance(metadata, Mapping):
                raise ArchiveIntegrityError(f"Invalid manifest metadata for {relative_path}.")
            self.storage.verify_file(
                relative_path,
                sha256=str(metadata.get("sha256") or ""),
                size_bytes=metadata.get("size_bytes"),
            )
            for record in self.storage.read_jsonl(relative_path):
                partition = record.get("partition") or {}
                if record.get("stage") != "clean" or partition.get("tier") != "hot":
                    raise ArchiveIntegrityError(
                        f"Hot promotion input contains an invalid CLEAN record: {relative_path}."
                    )
                records.append(record)
        if not selected:
            raise HistoricalPromotionError("The prepared history manifest contains no hot partitions.")
        return records

    def conflict_map(self) -> dict[str, dict[str, Any]]:
        relative_path = HistoricalDataPreparationService.CONFLICTS_PATH
        metadata = self.manifest()["files"].get(relative_path)
        if not isinstance(metadata, Mapping):
            return {}
        self.storage.verify_file(
            relative_path,
            sha256=str(metadata.get("sha256") or ""),
            size_bytes=metadata.get("size_bytes"),
        )
        return {
            str(record.get("conflict_id")): record
            for record in self.storage.read_jsonl(relative_path)
            if record.get("conflict_id")
        }


@dataclass(frozen=True)
class GuestResolution:
    status: str
    reason: str
    profile: CustomerProfile | None = None
    created: bool = False


@dataclass(frozen=True)
class PromotionSummary:
    source_observations: int = 0
    guest_candidates: int = 0
    guests_created: int = 0
    guests_matched: int = 0
    guests_would_create: int = 0
    guests_unresolved: int = 0
    reservations_created: int = 0
    reservations_matched: int = 0
    reservations_would_create: int = 0
    reservations_unresolved: int = 0
    guest_records_created: int = 0
    guest_records_matched: int = 0
    guest_records_would_create: int = 0
    guest_records_unresolved: int = 0
    apply: bool = False

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


class GuestIdentityResolver:
    """Resolve a prepared guest identity before creating transactional state."""

    BLOCKING_CONFLICT_FIELDS = {"guest.name", "guest.email", "guest.phone"}

    def resolve(
        self,
        guest_identity: str,
        observations: Sequence[Mapping[str, Any]],
        *,
        conflict_map: Mapping[str, Mapping[str, Any]],
        apply: bool,
    ) -> GuestResolution:
        conflict_fields = {
            str(conflict_map[reference].get("field") or "")
            for observation in observations
            for reference in observation.get("conflict_refs") or []
            if reference in conflict_map
        }
        blocking = sorted(conflict_fields & self.BLOCKING_CONFLICT_FIELDS)
        if blocking:
            return GuestResolution("unresolved", f"identity_conflict:{','.join(blocking)}")

        facts_rows = [
            observation.get("facts") or {}
            for observation in observations
            if observation.get("entity_kind") in {"guest", "guest_record", "reservation"}
        ]
        profile_rows = [
            observation
            for observation in observations
            if observation.get("entity_kind") == "guest"
        ]
        preferred = (_latest(profile_rows).get("facts") or {}) if profile_rows else {}
        emails = sorted({_email(row.get("email")) for row in facts_rows if _usable(row.get("email"))})
        phones = sorted({_phone(row.get("phone")) for row in facts_rows if _usable(row.get("phone"))})
        names = sorted({_clean(row.get("name") or row.get("guest_name")) for row in facts_rows if _usable(row.get("name") or row.get("guest_name"))})
        if len(emails) > 1 or len(phones) > 1:
            return GuestResolution("unresolved", "multiple_durable_contact_values")

        marker = _source_marker(PROFILE_MARKER_PREFIX, guest_identity)
        candidates: dict[int, CustomerProfile] = {
            profile.pk: profile
            for profile in CustomerProfile.objects.filter(notes__contains=marker)
        }
        if emails:
            for profile in CustomerProfile.objects.filter(email__iexact=emails[0]):
                candidates[profile.pk] = profile
        if phones:
            for profile in CustomerProfile.objects.exclude(phone=""):
                if _phone(profile.phone) == phones[0]:
                    candidates[profile.pk] = profile
        if len(candidates) > 1:
            return GuestResolution("unresolved", "durable_identity_matches_multiple_profiles")
        if candidates:
            profile = next(iter(candidates.values()))
            if apply:
                self._fill_missing(profile, preferred, emails, phones, names, marker)
            return GuestResolution("matched", "existing_profile", profile=profile)

        if not guest_identity.startswith("customer_profile:"):
            return GuestResolution("unresolved", "missing_stable_mladis_guest_identity")
        if not names and not emails and not phones:
            return GuestResolution("unresolved", "insufficient_identity_evidence")

        values = self._new_profile_values(preferred, emails, phones, names, marker)
        if not apply:
            return GuestResolution(
                "would_create",
                "stable_source_identity",
                profile=CustomerProfile(**values),
                created=True,
            )
        profile = CustomerProfile.objects.create(**values)
        return GuestResolution("created", "stable_source_identity", profile=profile, created=True)

    def _new_profile_values(self, preferred, emails, phones, names, marker):
        segment = _clean(preferred.get("segment"))
        source = _clean(preferred.get("source"))
        consent = _clean(preferred.get("marketing_consent_status"))
        return {
            "name": _clean(preferred.get("name")) or (names[0] if names else ""),
            "email": emails[0] if emails else "",
            "phone": _clean(preferred.get("phone")) or (phones[0] if phones else ""),
            "segment": segment if segment in ClientSegment.values else ClientSegment.AVERAGE,
            "source": source if source in ContactSource.values else ContactSource.AIRBNB,
            "marketing_consent_status": (
                consent if consent in MarketingConsentStatus.values else MarketingConsentStatus.UNKNOWN
            ),
            "preferred_language": _clean(preferred.get("preferred_language"))[:8] or "en",
            "notes": _append_marker(
                "",
                marker,
                "Promoted from verified MLADIS historical PREPARE evidence.",
            ),
        }

    def _fill_missing(self, profile, preferred, emails, phones, names, marker):
        changed: list[str] = []
        missing_values = {
            "name": _clean(preferred.get("name")) or (names[0] if names else ""),
            "email": emails[0] if emails else "",
            "phone": _clean(preferred.get("phone")) or (phones[0] if phones else ""),
            "preferred_language": _clean(preferred.get("preferred_language"))[:8],
        }
        for field_name, value in missing_values.items():
            if value and not getattr(profile, field_name):
                setattr(profile, field_name, value)
                changed.append(field_name)
        consent = _clean(preferred.get("marketing_consent_status"))
        if (
            profile.marketing_consent_status == MarketingConsentStatus.UNKNOWN
            and consent in MarketingConsentStatus.values
            and consent != MarketingConsentStatus.UNKNOWN
        ):
            profile.marketing_consent_status = consent
            changed.append("marketing_consent_status")
        notes = _append_marker(
            profile.notes,
            marker,
            "Matched to verified MLADIS historical PREPARE evidence.",
        )
        if notes != profile.notes:
            profile.notes = notes
            changed.append("notes")
        if changed:
            profile.save(update_fields=[*changed, "updated_at"])


class ReservationReconciliationService:
    """Idempotently create or match BookingInquiry records from hot evidence."""

    BLOCKING_CONFLICT_FIELDS = {
        "reservation.check_in",
        "reservation.check_out",
        "reservation.guest_count",
        "reservation.property",
        "reservation.total",
        "reservation.currency",
    }

    def promote(
        self,
        observations: Sequence[Mapping[str, Any]],
        *,
        profile: CustomerProfile,
        conflict_map: Mapping[str, Mapping[str, Any]],
        apply: bool,
    ) -> list[str]:
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for observation in observations:
            if observation.get("entity_kind") != "reservation":
                continue
            reference = str((observation.get("identities") or {}).get("reservation") or "")
            if reference:
                grouped[reference].append(observation)
        return [
            self._promote_one(reference, rows, profile=profile, conflict_map=conflict_map, apply=apply)
            for reference, rows in sorted(grouped.items())
        ]

    def _promote_one(self, reference, rows, *, profile, conflict_map, apply):
        conflict_fields = {
            str(conflict_map[conflict_ref].get("field") or "")
            for row in rows
            for conflict_ref in row.get("conflict_refs") or []
            if conflict_ref in conflict_map
        }
        if conflict_fields & self.BLOCKING_CONFLICT_FIELDS:
            return "unresolved"
        facts = _latest(rows).get("facts") or {}
        check_in = _date(facts.get("check_in"))
        check_out = _date(facts.get("check_out"))
        email = _email(facts.get("email") or getattr(profile, "email", ""))
        item = self._resolve_item(facts)
        if not check_in or not check_out or check_out <= check_in or not email or item is None:
            return "unresolved"

        marker = _source_marker(RESERVATION_MARKER_PREFIX, reference)
        matches = list(BookingInquiry.objects.filter(admin_notes__contains=marker))
        if not matches:
            matches = list(
                BookingInquiry.objects.filter(
                    email__iexact=email,
                    check_in=check_in,
                    check_out=check_out,
                    item=item,
                )
            )
        if len(matches) > 1:
            return "unresolved"
        if matches:
            inquiry = matches[0]
            if apply:
                changed = []
                if not inquiry.customer_profile_id and profile.pk:
                    inquiry.customer_profile = profile
                    changed.append("customer_profile")
                notes = _append_marker(
                    inquiry.admin_notes,
                    marker,
                    "Matched to verified MLADIS historical PREPARE evidence.",
                )
                if notes != inquiry.admin_notes:
                    inquiry.admin_notes = notes
                    changed.append("admin_notes")
                if changed:
                    inquiry.save(update_fields=[*changed, "updated_at"])
            return "matched"

        if not apply:
            return "would_create"
        BookingInquiry.objects.create(
            customer_profile=profile,
            item=item,
            guest_name=_clean(facts.get("guest_name")) or profile.name or email,
            email=email,
            phone=_clean(facts.get("phone")) or profile.phone,
            check_in=check_in,
            check_out=check_out,
            guests=max(_int(facts.get("guests"), 1), 1),
            status=self._status(facts.get("status")),
            subtotal_cents=max(_int(facts.get("subtotal_cents")), 0),
            discount_cents=max(_int(facts.get("discount_cents")), 0),
            deposit_cents=max(_int(facts.get("deposit_cents")), 0),
            total_cents=max(_int(facts.get("total_cents")), 0),
            currency=_clean(facts.get("currency")).lower()[:3] or "usd",
            is_admin_test=bool(facts.get("is_admin_test")),
            is_blacklist_flagged=bool(facts.get("is_blacklist_flagged")),
            admin_notes=_append_marker(
                "",
                marker,
                "Promoted from verified MLADIS historical PREPARE evidence; no email was sent.",
            ),
        )
        return "created"

    @staticmethod
    def _resolve_item(facts):
        item_id = _int(facts.get("item_id"))
        if item_id:
            item = BookableItem.objects.filter(pk=item_id).first()
            if item:
                return item
        item_name = _clean(facts.get("item_name"))
        if item_name:
            matches = list(BookableItem.objects.filter(name__iexact=item_name))
            if len(matches) == 1:
                return matches[0]
        return None

    @staticmethod
    def _status(value):
        normalized = _clean(value).lower()
        aliases = {
            "accepted": BookingStatus.CONFIRMED,
            "completed": BookingStatus.CONFIRMED,
            "cancelled": BookingStatus.CANCELED,
            "declined": BookingStatus.DECLINED,
            "pending": BookingStatus.REVIEWING,
        }
        if normalized in BookingStatus.values:
            return normalized
        return aliases.get(normalized, BookingStatus.NEW)


class AirbnbGuestRecordPromotionService:
    """Promote linked Airbnb stay evidence without duplicating records."""

    def promote(
        self,
        observations: Sequence[Mapping[str, Any]],
        *,
        profile: CustomerProfile,
        apply: bool,
    ) -> list[str]:
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for observation in observations:
            if observation.get("entity_kind") != "guest_record":
                continue
            reference = str((observation.get("identities") or {}).get("subject") or "")
            if reference:
                grouped[reference].append(observation)
        return [
            self._promote_one(reference, rows, profile=profile, apply=apply)
            for reference, rows in sorted(grouped.items())
        ]

    def _promote_one(self, reference, rows, *, profile, apply):
        facts = _latest(rows).get("facts") or {}
        guest_name = _clean(facts.get("guest_name")) or profile.name
        if not guest_name:
            return "unresolved"
        marker = _source_marker(AIRBNB_RECORD_MARKER_PREFIX, reference)
        matches = list(AirbnbGuestRecord.objects.filter(permission_notes__contains=marker))
        source_message_id = _clean(facts.get("source_message_id"))
        if not matches and source_message_id:
            matches = list(AirbnbGuestRecord.objects.filter(source_message_id=source_message_id))
        item = ReservationReconciliationService._resolve_item(facts)
        if not matches:
            matches = list(
                AirbnbGuestRecord.objects.filter(
                    customer_profile=profile if profile.pk else None,
                    item=item,
                    guest_name__iexact=guest_name,
                    check_in=_date(facts.get("check_in")),
                    check_out=_date(facts.get("check_out")),
                )
            )
        if len(matches) > 1:
            return "unresolved"
        if matches:
            record = matches[0]
            if apply:
                changed = []
                if not record.customer_profile_id and profile.pk:
                    record.customer_profile = profile
                    changed.append("customer_profile")
                notes = _append_marker(record.permission_notes, marker)
                if notes != record.permission_notes:
                    record.permission_notes = notes
                    changed.append("permission_notes")
                if changed:
                    record.save(update_fields=[*changed, "updated_at"])
            return "matched"
        if not apply:
            return "would_create"

        timestamp = parse_datetime(_clean(facts.get("source_email_timestamp")))
        rating = facts.get("rating") if _usable(facts.get("rating")) else None
        record = AirbnbGuestRecord.objects.create(
            customer_profile=profile,
            item=item,
            guest_name=guest_name,
            email=_email(facts.get("email")) or profile.email,
            phone=_clean(facts.get("phone")) or profile.phone,
            listing_title=_clean(facts.get("listing_title")),
            airbnb_listing_id=_clean(facts.get("airbnb_listing_id")),
            source_message_id=source_message_id or None,
            source_email_subject=_clean(facts.get("source_email_subject")),
            source_email_timestamp=timestamp,
            check_in=_date(facts.get("check_in")),
            check_out=_date(facts.get("check_out")),
            guests=max(_int(facts.get("guests")), 0) or None,
            feedback_summary=_clean(facts.get("feedback_summary")),
            rating=rating,
            permission_notes=marker,
        )
        CustomerFeedback.sync_from_airbnb_record(record)
        return "created"


class HistoricalPromotionService:
    """Coordinate verified hot-history promotion into current MLADIS state."""

    def __init__(
        self,
        repository: PreparedHistoryRepository,
        *,
        identity_resolver: GuestIdentityResolver | None = None,
        reservation_service: ReservationReconciliationService | None = None,
        guest_record_service: AirbnbGuestRecordPromotionService | None = None,
    ):
        self.repository = repository
        self.identity_resolver = identity_resolver or GuestIdentityResolver()
        self.reservation_service = reservation_service or ReservationReconciliationService()
        self.guest_record_service = guest_record_service or AirbnbGuestRecordPromotionService()

    def promote(self, *, apply: bool = False, limit_guests: int | None = None) -> PromotionSummary:
        observations = self.repository.hot_observations()
        conflict_map = self.repository.conflict_map()
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in observations:
            guest_identity = str((observation.get("identities") or {}).get("guest") or "")
            if guest_identity:
                grouped[guest_identity].append(observation)

        counters = defaultdict(int)
        candidates = sorted(grouped.items())
        if limit_guests is not None:
            candidates = candidates[: max(int(limit_guests), 0)]
        for guest_identity, rows in candidates:
            with transaction.atomic():
                resolution = self.identity_resolver.resolve(
                    guest_identity,
                    rows,
                    conflict_map=conflict_map,
                    apply=apply,
                )
                counters[f"guests_{resolution.status}"] += 1
                if resolution.profile is None:
                    continue
                for action in self.reservation_service.promote(
                    rows,
                    profile=resolution.profile,
                    conflict_map=conflict_map,
                    apply=apply,
                ):
                    counters[f"reservations_{action}"] += 1
                for action in self.guest_record_service.promote(
                    rows,
                    profile=resolution.profile,
                    apply=apply,
                ):
                    counters[f"guest_records_{action}"] += 1
                if not apply:
                    transaction.set_rollback(True)

        return PromotionSummary(
            source_observations=len(observations),
            guest_candidates=len(candidates),
            guests_created=counters["guests_created"],
            guests_matched=counters["guests_matched"],
            guests_would_create=counters["guests_would_create"],
            guests_unresolved=counters["guests_unresolved"],
            reservations_created=counters["reservations_created"],
            reservations_matched=counters["reservations_matched"],
            reservations_would_create=counters["reservations_would_create"],
            reservations_unresolved=counters["reservations_unresolved"],
            guest_records_created=counters["guest_records_created"],
            guest_records_matched=counters["guest_records_matched"],
            guest_records_would_create=counters["guest_records_would_create"],
            guest_records_unresolved=counters["guest_records_unresolved"],
            apply=apply,
        )
