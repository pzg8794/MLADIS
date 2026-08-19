"""CLEAN and PREPARE sidecar for protected MLADIS historical data.

The module is intentionally free of Django model imports and performs no I/O
at import time. JSON and JSONL are storage representations for the domain
objects below; they are not authoritative Guest or Reservation models.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence


HISTORY_SCHEMA_VERSION = "1.0"
DEFAULT_COLD_YEARS = frozenset(range(2021, 2026))


class HistoricalDataError(Exception):
    """Base error for the historical-data sidecar."""


class PrivateWorkingSegmentRequired(HistoricalDataError):
    """Raised when protected input/output handling was not acknowledged."""


class InvalidHistoricalRecord(HistoricalDataError):
    """Raised when COLLECT evidence cannot be parsed without guessing."""


class ArchiveIntegrityError(HistoricalDataError):
    """Raised when a referenced archive is missing or fails integrity checks."""


class HistoryNotFoundError(HistoricalDataError):
    """Raised when the index has no exact guest/year archive reference."""


@dataclass(frozen=True)
class SourceCollection:
    key: str
    relative_path: str
    entity_kind: str


# This explicit inventory is also the no-startup-scan contract. Adding a new
# source requires a reviewed code change; ordinary lookup never walks the lake.
SOURCE_COLLECTIONS: tuple[SourceCollection, ...] = (
    SourceCollection("customer_profiles", "CUSTOMERS/customer_profiles.jsonl", "guest"),
    SourceCollection("airbnb_guest_records", "CUSTOMERS/airbnb_guest_records.jsonl", "guest_record"),
    SourceCollection("booking_requests", "BOOKINGS/booking_requests.jsonl", "reservation"),
    SourceCollection("reservations", "BOOKINGS/reservations.jsonl", "reservation"),
    SourceCollection(
        "airbnb_reservation_snapshots",
        "BOOKINGS/airbnb_reservation_snapshots.jsonl",
        "reservation",
    ),
    SourceCollection("inventory", "STAYS/inventory.jsonl", "property"),
    SourceCollection("payments", "TRANSACTIONS/payments.jsonl", "payment"),
    SourceCollection(
        "reservation_payment_holds",
        "TRANSACTIONS/reservation_payment_holds.jsonl",
        "payment",
    ),
    SourceCollection("damage_deposits", "TRANSACTIONS/damage_deposits.jsonl", "deposit_hold"),
    SourceCollection("invoices", "TRANSACTIONS/invoices.jsonl", "invoice"),
    SourceCollection("messages", "BOOKINGS/messages.jsonl", "message"),
    SourceCollection("agent_conversations", "BOOKINGAGENTS/agent_conversations.jsonl", "message"),
    SourceCollection(
        "anonymous_interactions",
        "INTERACTIONS/anonymous_interactions.jsonl",
        "anonymous_interaction",
    ),
    SourceCollection("work_orders", "OPERATIONS/work_orders.jsonl", "work_order"),
    SourceCollection("maintenance_events", "MAINTENANCE/maintenance_events.jsonl", "work_order"),
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collapse_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", normalized).strip()


def _nested_get(mapping: Mapping[str, Any], *paths: Sequence[str]) -> Any:
    for path in paths:
        current: Any = mapping
        for part in path:
            if not isinstance(current, Mapping) or part not in current:
                current = None
                break
            current = current[part]
        if current not in (None, "", [], {}):
            return current
    return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _collapse_text(value)
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    for pattern in ("%m/%d/%Y", "%Y/%m/%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, datetime.min.time())
    else:
        text = _collapse_text(value)
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            parsed_date = _parse_date(text)
            return datetime.combine(parsed_date, datetime.min.time(), tzinfo=timezone.utc) if parsed_date else None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _normalize_timestamp(value: Any) -> str:
    parsed = _parse_datetime(value)
    return parsed.isoformat() if parsed else _collapse_text(value)


def _activity_sort_key(value: str) -> tuple[int, str]:
    return (1, value) if _parse_datetime(value) else (0, value or "")


class HotPartitionPolicy(ABC):
    """Selects hot/cold placement without changing guest or reservation logic."""

    def __init__(self, *, as_of: date, cold_years: Iterable[int] = DEFAULT_COLD_YEARS):
        self.as_of = as_of
        self.cold_years = frozenset(int(year) for year in cold_years)

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_hot(self, activity_date: date) -> bool:
        raise NotImplementedError

    def classify(self, activity_at: str) -> tuple[str, int | None]:
        activity_date = _parse_date(activity_at)
        if not activity_date:
            return "unassigned", None
        if self.is_hot(activity_date):
            return "hot", activity_date.year
        if activity_date.year in self.cold_years:
            return "cold", activity_date.year
        return "unassigned", activity_date.year

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "as_of": self.as_of.isoformat(),
            "cold_years": sorted(self.cold_years),
        }


class CurrentOperationalYearPolicy(HotPartitionPolicy):
    @property
    def name(self) -> str:
        return "current-operational-year"

    def is_hot(self, activity_date: date) -> bool:
        return activity_date.year == self.as_of.year


class RollingTwelveMonthPolicy(HotPartitionPolicy):
    @property
    def name(self) -> str:
        return "rolling-12-months"

    def is_hot(self, activity_date: date) -> bool:
        return self.as_of - timedelta(days=365) <= activity_date <= self.as_of


def build_partition_policy(name: str, *, as_of: date) -> HotPartitionPolicy:
    normalized = _collapse_text(name).lower().replace("_", "-")
    if normalized in {"year", "current-year", "current-operational-year"}:
        return CurrentOperationalYearPolicy(as_of=as_of)
    if normalized in {"rolling", "rolling-12", "rolling-12-months"}:
        return RollingTwelveMonthPolicy(as_of=as_of)
    raise ValueError(f"Unsupported hot policy: {name}")


class HistoricalStoragePolicy(ABC):
    """Archive storage port used by preparation and targeted rehydration."""

    @abstractmethod
    def write_json(self, relative_path: str, payload: Mapping[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def write_jsonl(self, relative_path: str, records: Iterable[Mapping[str, Any]]) -> int:
        raise NotImplementedError

    @abstractmethod
    def read_json(self, relative_path: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def read_jsonl(self, relative_path: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def file_metadata(self, relative_path: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def verify_file(self, relative_path: str, *, sha256: str, size_bytes: int | None = None) -> None:
        raise NotImplementedError


class FilesystemHistoryStorage(HistoricalStoragePolicy):
    """Filesystem adapter for a protected local or mounted Drive segment."""

    def __init__(self, root: str | os.PathLike[str], *, private_working_segment: bool):
        if not private_working_segment:
            raise PrivateWorkingSegmentRequired(
                "Historical input/output requires an explicitly acknowledged private working segment."
            )
        self.root = Path(root).expanduser().resolve()

    def _resolve(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute():
            raise HistoricalDataError("Archive references must be relative paths.")
        resolved = (self.root / candidate).resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise HistoricalDataError("Archive reference escapes the configured history root.")
        return resolved

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(path)

    def write_json(self, relative_path: str, payload: Mapping[str, Any]) -> None:
        self._atomic_write(
            self._resolve(relative_path),
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        )

    def write_jsonl(self, relative_path: str, records: Iterable[Mapping[str, Any]]) -> int:
        lines: list[str] = []
        for record in records:
            lines.append(_canonical_json(record))
        self._atomic_write(self._resolve(relative_path), "".join(f"{line}\n" for line in lines))
        return len(lines)

    def read_json(self, relative_path: str) -> dict[str, Any]:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise ArchiveIntegrityError(f"Historical archive is missing: {relative_path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ArchiveIntegrityError(f"Historical archive is unreadable: {relative_path}") from error
        if not isinstance(payload, dict):
            raise ArchiveIntegrityError(f"Historical archive must contain an object: {relative_path}")
        return payload

    def read_jsonl(self, relative_path: str) -> list[dict[str, Any]]:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise ArchiveIntegrityError(f"Historical archive is missing: {relative_path}")
        records: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as source:
                for line_number, line in enumerate(source, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError(f"line {line_number} is not an object")
                    records.append(record)
        except (OSError, ValueError) as error:
            raise ArchiveIntegrityError(f"Historical archive is unreadable: {relative_path}") from error
        return records

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).is_file()

    def file_metadata(self, relative_path: str) -> dict[str, Any]:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise ArchiveIntegrityError(f"Historical archive is missing: {relative_path}")
        return {
            "path": relative_path,
            "sha256": _sha256_file(path),
            "size_bytes": path.stat().st_size,
        }

    def verify_file(self, relative_path: str, *, sha256: str, size_bytes: int | None = None) -> None:
        path = self._resolve(relative_path)
        if not path.is_file():
            raise ArchiveIntegrityError(f"Historical archive is missing: {relative_path}")
        if size_bytes is not None and path.stat().st_size != int(size_bytes):
            raise ArchiveIntegrityError(f"Historical archive size mismatch: {relative_path}")
        if not sha256 or _sha256_file(path) != sha256:
            raise ArchiveIntegrityError(f"Historical archive hash mismatch: {relative_path}")


@dataclass(frozen=True)
class SourceFileEvidence:
    collection: SourceCollection
    path: Path
    sha256: str
    size_bytes: int

    def manifest_record(self) -> dict[str, Any]:
        return {
            "collection": self.collection.key,
            "path": self.collection.relative_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class CollectedRecord:
    collection: SourceCollection
    source_path: str
    line_number: int
    record: dict[str, Any]


class CollectRepository:
    """Read-only adapter over the existing, explicit Object Lake snapshots."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root).expanduser().resolve()

    def inventory(self) -> list[SourceFileEvidence]:
        evidence: list[SourceFileEvidence] = []
        for collection in SOURCE_COLLECTIONS:
            path = (self.root / collection.relative_path).resolve()
            if path.is_file():
                evidence.append(
                    SourceFileEvidence(
                        collection=collection,
                        path=path,
                        sha256=_sha256_file(path),
                        size_bytes=path.stat().st_size,
                    )
                )
        return evidence

    def records(self, evidence: Sequence[SourceFileEvidence]) -> Iterable[CollectedRecord]:
        for source in evidence:
            try:
                with source.path.open("r", encoding="utf-8") as stream:
                    for line_number, line in enumerate(stream, start=1):
                        if not line.strip():
                            continue
                        payload = json.loads(line)
                        if not isinstance(payload, dict):
                            raise ValueError("row is not an object")
                        declared_collection = payload.get("collection")
                        if declared_collection and declared_collection != source.collection.key:
                            raise ValueError(
                                f"declares collection {declared_collection!r}, expected {source.collection.key!r}"
                            )
                        yield CollectedRecord(
                            collection=source.collection,
                            source_path=source.collection.relative_path,
                            line_number=line_number,
                            record=payload,
                        )
            except (OSError, ValueError) as error:
                raise InvalidHistoricalRecord(
                    f"Could not read {source.collection.relative_path} without guessing: {error}"
                ) from error


class HistoricalRedactionNormalizer:
    """Normalize useful facts while enforcing existing lake privacy boundaries."""

    SECRET_FRAGMENTS = (
        "password",
        "secret",
        "api_key",
        "apikey",
        "private_key",
        "webhook",
        "access_token",
        "refresh_token",
        "session_key",
        "public_token",
    )
    PROVIDER_REFERENCE_KEYS = {
        "checkout_url",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "paypal_order_id",
        "paypal_authorization_id",
    }
    SOURCE_URL_KEYS = {"airbnb_thread_url", "thread_url", "profile_url", "source_url"}
    DIRECT_IDENTITY_KEYS = {
        "name",
        "guest_name",
        "recipient_name",
        "donor_name",
        "vendor_name",
        "vendor_contact",
        "email",
        "phone",
        "phone_number",
        "guest_email",
        "recipient_email",
    }
    PRIVATE_FREE_TEXT_KEYS = {
        "message",
        "message_excerpt",
        "feedback_text",
        "review_text",
        "raw_body",
        "body",
        "admin_notes",
        "permission_notes",
    }
    DATE_KEYS = {
        "booking_date",
        "check_in",
        "check_out",
        "issue_date",
        "due_date",
        "start_date",
        "end_date",
    }

    def normalize(self, value: Any, *, pii_classification: str) -> tuple[Any, list[dict[str, str]]]:
        issues: list[dict[str, str]] = []
        normalized = self._normalize_value(value, (), pii_classification.lower(), issues)
        return normalized, issues

    def _normalize_value(
        self,
        value: Any,
        path: tuple[str, ...],
        pii_classification: str,
        issues: list[dict[str, str]],
    ) -> Any:
        if isinstance(value, Mapping):
            result: dict[str, Any] = {}
            for raw_key, item in value.items():
                key = str(raw_key)
                lowered = key.lower()
                current_path = (*path, key)
                if any(fragment in lowered for fragment in self.SECRET_FRAGMENTS):
                    result[key] = "[redacted]" if item not in (None, "") else ""
                    continue
                if lowered in self.PROVIDER_REFERENCE_KEYS or lowered in self.SOURCE_URL_KEYS:
                    result[key] = "" if item in (None, "") else "[redacted]"
                    continue
                if pii_classification in {"redacted", "anonymized"} and lowered in self.DIRECT_IDENTITY_KEYS:
                    result[key] = ""
                    continue
                if pii_classification == "private" and lowered in self.PRIVATE_FREE_TEXT_KEYS:
                    result[key] = "" if item in (None, "") else "[redacted]"
                    continue
                result[key] = self._normalize_scalar_or_nested(
                    item,
                    current_path,
                    pii_classification,
                    issues,
                )
            return result
        if isinstance(value, list):
            return [
                self._normalize_value(item, (*path, str(index)), pii_classification, issues)
                for index, item in enumerate(value)
            ]
        return value

    def _normalize_scalar_or_nested(
        self,
        value: Any,
        path: tuple[str, ...],
        pii_classification: str,
        issues: list[dict[str, str]],
    ) -> Any:
        if isinstance(value, (Mapping, list)):
            return self._normalize_value(value, path, pii_classification, issues)
        key = path[-1].lower()
        if value in (None, ""):
            return value
        if key in self.DIRECT_IDENTITY_KEYS or key.endswith("_name"):
            if key in {"email", "guest_email", "recipient_email"}:
                return _collapse_text(value).lower()
            return _collapse_text(value)
        if key == "currency":
            return _collapse_text(value).upper()
        if key in self.DATE_KEYS:
            parsed = _parse_date(value)
            if parsed:
                return parsed.isoformat()
            self._issue(issues, path, "unparseable_date", value)
            return _collapse_text(value)
        if key.endswith("_at") or key in {"occurred_at", "extracted_at", "captured_at"}:
            parsed = _parse_datetime(value)
            if parsed:
                return parsed.isoformat()
            self._issue(issues, path, "unparseable_timestamp", value)
            return _collapse_text(value)
        if key.endswith("_cents"):
            try:
                return int(Decimal(str(value)))
            except (InvalidOperation, TypeError, ValueError):
                self._issue(issues, path, "unparseable_cents", value)
                return value
        if self._is_amount_key(key):
            try:
                return str(Decimal(str(value).replace(",", "")).quantize(Decimal("0.01")))
            except (InvalidOperation, TypeError, ValueError):
                self._issue(issues, path, "unparseable_amount", value)
                return value
        if isinstance(value, str):
            return _collapse_text(value)
        return value

    @staticmethod
    def _is_amount_key(key: str) -> bool:
        return any(
            marker in key
            for marker in ("amount", "price", "earnings", "payout", "fees", "cost")
        ) and not key.endswith("_id")

    @staticmethod
    def _issue(issues: list[dict[str, str]], path: tuple[str, ...], reason: str, value: Any) -> None:
        issues.append(
            {
                "field": ".".join(path),
                "reason": reason,
                "value_fingerprint": hashlib.sha256(str(value).encode("utf-8")).hexdigest(),
            }
        )


@dataclass
class CleanObservation:
    observation_id: str
    fingerprint: str
    source_identity_key: str
    entity_kind: str
    source_identity: dict[str, Any]
    provenance: dict[str, Any]
    pii_classification: str
    occurred_at: str
    captured_at: str
    activity_at: str
    facts: dict[str, Any]
    guest_identity: str
    reservation_identity: str
    property_identity: str
    subject_key: str
    duplicate_count: int = 1
    uncertainty: list[dict[str, Any]] = field(default_factory=list)
    conflict_refs: list[str] = field(default_factory=list)
    partition_tier: str = "unassigned"
    partition_year: int | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "stage": "clean",
            "observation_id": self.observation_id,
            "observation_fingerprint": self.fingerprint,
            "source_identity_key": self.source_identity_key,
            "entity_kind": self.entity_kind,
            "source_identity": self.source_identity,
            "provenance": self.provenance,
            "pii_classification": self.pii_classification,
            "occurred_at": self.occurred_at,
            "captured_at": self.captured_at,
            "activity_at": self.activity_at,
            "partition": {"tier": self.partition_tier, "year": self.partition_year},
            "identities": {
                "guest": self.guest_identity,
                "reservation": self.reservation_identity,
                "property": self.property_identity,
                "subject": self.subject_key,
            },
            "duplicate_count": self.duplicate_count,
            "uncertainty": self.uncertainty,
            "conflict_refs": sorted(self.conflict_refs),
            "facts": self.facts,
        }


@dataclass(frozen=True)
class ConflictSet:
    conflict_id: str
    subject_key: str
    field: str
    observation_refs: tuple[str, ...]
    value_fingerprints: tuple[str, ...]

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "stage": "clean",
            "conflict_id": self.conflict_id,
            "subject_key": self.subject_key,
            "field": self.field,
            "observation_refs": list(self.observation_refs),
            "value_fingerprints": list(self.value_fingerprints),
            "resolution_state": "unresolved",
        }


@dataclass(frozen=True)
class CleanResult:
    observations: tuple[CleanObservation, ...]
    conflicts: tuple[ConflictSet, ...]
    source_record_count: int
    duplicate_observation_count: int


class HistoricalCleaner:
    def __init__(self, *, normalizer: HistoricalRedactionNormalizer | None = None):
        self.normalizer = normalizer or HistoricalRedactionNormalizer()

    def clean(self, records: Iterable[CollectedRecord]) -> CleanResult:
        deduplicated: dict[tuple[str, str], CleanObservation] = {}
        source_record_count = 0
        duplicate_count = 0
        for collected in records:
            source_record_count += 1
            observation = self._clean_record(collected)
            key = (observation.source_identity_key, observation.fingerprint)
            existing = deduplicated.get(key)
            if existing:
                existing.duplicate_count += 1
                duplicate_count += 1
                locations = {
                    (str(item.get("path") or ""), int(item.get("line") or 0))
                    for item in (
                        *existing.provenance.get("source_locations", []),
                        *observation.provenance.get("source_locations", []),
                    )
                }
                existing.provenance["source_locations"] = [
                    {"path": path, "line": line}
                    for path, line in sorted(locations)
                ]
                captures = {
                    value
                    for value in (
                        *existing.provenance.get("capture_timestamps", []),
                        *observation.provenance.get("capture_timestamps", []),
                    )
                    if value
                }
                existing.provenance["capture_timestamps"] = sorted(captures)
                continue
            deduplicated[key] = observation

        observations = sorted(deduplicated.values(), key=lambda item: item.observation_id)
        conflicts = self._detect_conflicts(observations)
        observation_map = {item.observation_id: item for item in observations}
        for conflict in conflicts:
            for observation_ref in conflict.observation_refs:
                observation = observation_map.get(observation_ref)
                if observation and conflict.conflict_id not in observation.conflict_refs:
                    observation.conflict_refs.append(conflict.conflict_id)
        return CleanResult(
            observations=tuple(observations),
            conflicts=tuple(conflicts),
            source_record_count=source_record_count,
            duplicate_observation_count=duplicate_count,
        )

    def _clean_record(self, collected: CollectedRecord) -> CleanObservation:
        record = collected.record
        facts_value = record.get("data", record)
        if not isinstance(facts_value, Mapping):
            raise InvalidHistoricalRecord(
                f"{collected.source_path}:{collected.line_number} has no object data payload."
            )
        pii_classification = _collapse_text(record.get("pii_classification") or "private").lower()
        facts, issues = self.normalizer.normalize(facts_value, pii_classification=pii_classification)
        if not isinstance(facts, dict):
            raise InvalidHistoricalRecord(
                f"{collected.source_path}:{collected.line_number} could not be normalized as an object."
            )
        source_identity = self._source_identity(collected, record, pii_classification)
        source_identity_key = self._source_identity_key(source_identity)
        occurred_at = _normalize_timestamp(record.get("occurred_at"))
        captured_at = self._captured_at(record, facts)
        activity_at = self._activity_at(collected.collection.entity_kind, facts, occurred_at, captured_at)
        guest_identity = self._guest_identity(facts, collected.collection)
        reservation_identity = self._reservation_identity(facts, record, collected.collection)
        property_identity = self._property_identity(facts, collected.collection)
        subject_key = self._subject_key(
            collected.collection,
            facts,
            source_identity_key,
            guest_identity,
            reservation_identity,
            property_identity,
        )
        uncertainty = list(issues)
        if bool(_nested_get(facts, ("source", "needs_reconciliation"))):
            uncertainty.append(
                {
                    "field": "source.needs_reconciliation",
                    "reason": "source_requires_reconciliation",
                }
            )
        confidence = _nested_get(facts, ("source", "confidence"), ("confidence",))
        if confidence:
            uncertainty.append({"field": "source.confidence", "reason": _collapse_text(confidence)})
        fingerprint_payload = {
            "source_identity_key": source_identity_key,
            "occurred_at": occurred_at,
            "facts": facts,
        }
        fingerprint = _sha256_value(fingerprint_payload)
        observation_id = f"observation:{fingerprint}"
        upstream_fingerprint = _nested_get(facts, ("source_observation_fingerprint",))
        provenance = {
            "source_locations": [{"path": collected.source_path, "line": collected.line_number}],
            "capture_timestamps": [captured_at] if captured_at else [],
            "upstream_observation_fingerprint": _collapse_text(upstream_fingerprint),
        }
        return CleanObservation(
            observation_id=observation_id,
            fingerprint=fingerprint,
            source_identity_key=source_identity_key,
            entity_kind=collected.collection.entity_kind,
            source_identity=source_identity,
            provenance=provenance,
            pii_classification=pii_classification,
            occurred_at=occurred_at,
            captured_at=captured_at,
            activity_at=activity_at,
            facts=facts,
            guest_identity=guest_identity,
            reservation_identity=reservation_identity,
            property_identity=property_identity,
            subject_key=subject_key,
            uncertainty=uncertainty,
        )

    def _source_identity(
        self,
        collected: CollectedRecord,
        record: Mapping[str, Any],
        pii_classification: str,
    ) -> dict[str, Any]:
        natural_keys = record.get("natural_keys") if isinstance(record.get("natural_keys"), Mapping) else {}
        normalized_keys, _ = self.normalizer.normalize(
            natural_keys,
            pii_classification=pii_classification,
        )
        return {
            "collection": collected.collection.key,
            "record_key": _collapse_text(record.get("record_key")),
            "source_system": _collapse_text(record.get("source_system") or "unknown"),
            "source_model": _collapse_text(record.get("source_model")),
            "source_pk": _collapse_text(record.get("source_pk")),
            "natural_keys": normalized_keys,
        }

    @staticmethod
    def _source_identity_key(source_identity: Mapping[str, Any]) -> str:
        collection = source_identity.get("collection") or "unknown"
        for value in (
            source_identity.get("record_key"),
            source_identity.get("source_pk"),
        ):
            if value:
                return f"{collection}:{value}"
        natural_keys = source_identity.get("natural_keys") or {}
        if natural_keys:
            return f"{collection}:natural:{_sha256_value(natural_keys)}"
        return f"{collection}:content:{_sha256_value(source_identity)}"

    @staticmethod
    def _captured_at(record: Mapping[str, Any], facts: Mapping[str, Any]) -> str:
        value = _nested_get(
            facts,
            ("captured_at",),
            ("source", "captured_at"),
            ("communication", "last_message_at"),
        ) or record.get("extracted_at") or record.get("occurred_at")
        return _normalize_timestamp(value)

    @staticmethod
    def _activity_at(entity_kind: str, facts: Mapping[str, Any], occurred_at: str, captured_at: str) -> str:
        common_paths: list[tuple[str, ...]] = []
        if entity_kind in {"reservation", "guest_record"}:
            common_paths.extend(
                [
                    ("lifecycle", "check_in"),
                    ("check_in",),
                    ("lifecycle", "booking_date"),
                    ("booking_date",),
                ]
            )
        elif entity_kind in {"payment", "deposit_hold", "invoice"}:
            common_paths.extend([("created_at",), ("issue_date",), ("updated_at",)])
        elif entity_kind == "message":
            common_paths.extend([("last_message_at",), ("created_at",)])
        elif entity_kind == "work_order":
            common_paths.extend([("reported_at",), ("started_at",), ("created_at",)])
        else:
            common_paths.extend([("created_at",), ("updated_at",)])
        value = _nested_get(facts, *common_paths) or occurred_at or captured_at
        parsed = _parse_datetime(value)
        return parsed.isoformat() if parsed else _collapse_text(value)

    @staticmethod
    def _guest_identity(facts: Mapping[str, Any], collection: SourceCollection) -> str:
        value = _nested_get(
            facts,
            ("customer_profile_id",),
            ("guest", "customer_profile_id"),
            ("reservation", "customer_profile_id"),
        )
        if value not in (None, ""):
            return f"customer_profile:{value}"
        if collection.key == "customer_profiles":
            profile_id = _nested_get(facts, ("profile_id",))
            if profile_id not in (None, ""):
                return f"customer_profile:{profile_id}"
        return ""

    @staticmethod
    def _reservation_identity(
        facts: Mapping[str, Any],
        record: Mapping[str, Any],
        collection: SourceCollection,
    ) -> str:
        inquiry_id = _nested_get(facts, ("booking_inquiry_id",), ("reservation", "booking_inquiry_id"))
        if inquiry_id not in (None, ""):
            return f"booking_inquiry:{inquiry_id}"
        reservation_key = _nested_get(facts, ("mladis_reservation_key",), ("reservation_id",))
        if reservation_key not in (None, ""):
            return f"reservation:{reservation_key}"
        if collection.entity_kind == "reservation" and record.get("record_key"):
            return f"source_reservation:{record['record_key']}"
        return ""

    @staticmethod
    def _property_identity(facts: Mapping[str, Any], collection: SourceCollection) -> str:
        item_id = _nested_get(
            facts,
            ("item_id",),
            ("bookable_item_id",),
            ("property", "item_id"),
        )
        if item_id not in (None, ""):
            return f"bookable_item:{item_id}"
        listing_id = _nested_get(
            facts,
            ("airbnb_listing_id",),
            ("property", "listing_id"),
        )
        if listing_id not in (None, ""):
            return f"airbnb_listing:{listing_id}"
        if collection.entity_kind == "property":
            slug = _nested_get(facts, ("slug",))
            if slug:
                return f"property_slug:{slug}"
        return ""

    @staticmethod
    def _subject_key(
        collection: SourceCollection,
        facts: Mapping[str, Any],
        source_identity_key: str,
        guest_identity: str,
        reservation_identity: str,
        property_identity: str,
    ) -> str:
        if collection.entity_kind == "guest":
            return guest_identity or source_identity_key
        if collection.entity_kind == "guest_record":
            record_id = _nested_get(facts, ("airbnb_guest_record_id",))
            return f"airbnb_guest_record:{record_id}" if record_id not in (None, "") else source_identity_key
        if collection.entity_kind == "reservation":
            return reservation_identity or source_identity_key
        if collection.entity_kind == "property":
            return property_identity or source_identity_key
        identifier_fields = {
            "payment": ("payment_id", "reservation_payment_hold_id"),
            "deposit_hold": ("deposit_hold_id", "damage_deposit_id"),
            "invoice": ("invoice_id",),
            "message": ("message_id",),
            "work_order": ("work_order_id", "maintenance_event_id"),
        }
        for identifier in identifier_fields.get(
            collection.entity_kind,
            (f"{collection.entity_kind}_id",),
        ):
            value = _nested_get(facts, (identifier,))
            if value not in (None, ""):
                return f"{collection.entity_kind}:{value}"
        return source_identity_key

    def _detect_conflicts(self, observations: Sequence[CleanObservation]) -> list[ConflictSet]:
        conflicts: list[ConflictSet] = []
        by_source: dict[str, list[CleanObservation]] = defaultdict(list)
        for observation in observations:
            by_source[observation.source_identity_key].append(observation)
        for source_key, group in sorted(by_source.items()):
            fingerprints = {item.fingerprint for item in group}
            if len(fingerprints) > 1:
                conflicts.append(self._conflict(source_key, "$source_observation", group, fingerprints))

        claims: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for observation in observations:
            for subject_key, field_name, value in self._claims(observation):
                claims[(subject_key, field_name)][_canonical_json(value)].add(observation.observation_id)
        for (subject_key, field_name), values in sorted(claims.items()):
            if len(values) <= 1:
                continue
            observation_refs = sorted({ref for refs in values.values() for ref in refs})
            value_fingerprints = sorted(hashlib.sha256(value.encode("utf-8")).hexdigest() for value in values)
            conflicts.append(
                self._conflict_from_parts(subject_key, field_name, observation_refs, value_fingerprints)
            )
        unique = {conflict.conflict_id: conflict for conflict in conflicts}
        return sorted(unique.values(), key=lambda item: item.conflict_id)

    def _claims(self, observation: CleanObservation) -> Iterable[tuple[str, str, Any]]:
        if observation.guest_identity:
            for field_name, paths in {
                "name": (("name",), ("guest_name",), ("guest", "name")),
                "email": (("email",), ("guest", "email")),
                "phone": (("phone",), ("phone_number",), ("guest", "phone")),
            }.items():
                value = _nested_get(observation.facts, *paths)
                if value not in (None, "", "[redacted]"):
                    yield observation.guest_identity, f"guest.{field_name}", value
        if observation.reservation_identity:
            fields: dict[str, tuple[tuple[str, ...], ...]] = {
                "check_in": (("check_in",), ("lifecycle", "check_in")),
                "check_out": (("check_out",), ("lifecycle", "check_out")),
                "status": (("status",), ("reservation_state",), ("lifecycle", "status")),
                "guest_count": (("guests",), ("occupancy", "guests")),
                "property": (("item_id",), ("property", "listing_id"), ("airbnb_listing_id",)),
                "total": (("total_cents",), ("financials", "total_amount")),
                "currency": (("currency",), ("financials", "currency")),
            }
            for field_name, paths in fields.items():
                value = _nested_get(observation.facts, *paths)
                if value not in (None, "", "[redacted]"):
                    yield observation.reservation_identity, f"reservation.{field_name}", value

    def _conflict(
        self,
        subject_key: str,
        field_name: str,
        observations: Sequence[CleanObservation],
        values: Iterable[str],
    ) -> ConflictSet:
        return self._conflict_from_parts(
            subject_key,
            field_name,
            sorted(item.observation_id for item in observations),
            sorted(hashlib.sha256(value.encode("utf-8")).hexdigest() for value in values),
        )

    @staticmethod
    def _conflict_from_parts(
        subject_key: str,
        field_name: str,
        observation_refs: Sequence[str],
        value_fingerprints: Sequence[str],
    ) -> ConflictSet:
        identity = {
            "subject_key": subject_key,
            "field": field_name,
            "observation_refs": sorted(observation_refs),
            "value_fingerprints": sorted(value_fingerprints),
        }
        return ConflictSet(
            conflict_id=f"conflict:{_sha256_value(identity)}",
            subject_key=subject_key,
            field=field_name,
            observation_refs=tuple(sorted(observation_refs)),
            value_fingerprints=tuple(sorted(value_fingerprints)),
        )


class PreparedRelationshipProjector:
    """Build bounded relationship context without creating Django records."""

    RELATION_KEYS = {
        "reservation": "reservations",
        "property": "properties",
        "payment": "payments",
        "deposit_hold": "deposit_holds",
        "invoice": "invoices",
        "message": "messages",
        "work_order": "work_orders",
        "guest_record": "guest_records",
    }
    DEPENDENT_KINDS = {"payment", "deposit_hold", "invoice", "message", "work_order"}

    def __init__(self, partition_policy: HotPartitionPolicy):
        self.partition_policy = partition_policy

    def prepare(
        self,
        observations: Sequence[CleanObservation],
        conflicts: Sequence[ConflictSet],
    ) -> list[dict[str, Any]]:
        reservation_parents: dict[str, list[CleanObservation]] = defaultdict(list)
        property_evidence: dict[str, list[CleanObservation]] = defaultdict(list)
        guest_evidence: dict[str, list[CleanObservation]] = defaultdict(list)
        for observation in observations:
            tier, year = self.partition_policy.classify(observation.activity_at)
            observation.partition_tier = tier
            observation.partition_year = year
            if observation.entity_kind == "reservation" and observation.reservation_identity:
                reservation_parents[observation.reservation_identity].append(observation)
            if observation.entity_kind == "property" and observation.property_identity:
                property_evidence[observation.property_identity].append(observation)
            if observation.guest_identity and observation.entity_kind in {"guest", "guest_record"}:
                guest_evidence[observation.guest_identity].append(observation)

        memberships: dict[tuple[str, int, str], list[CleanObservation]] = defaultdict(list)
        for observation in observations:
            membership = self._membership(observation, reservation_parents)
            if membership:
                guest_identity, year, tier = membership
                memberships[(guest_identity, year, tier)].append(observation)
                if observation.entity_kind in self.DEPENDENT_KINDS:
                    observation.partition_year = year
                    observation.partition_tier = tier

        conflict_map = {conflict.conflict_id: conflict for conflict in conflicts}
        contexts: list[dict[str, Any]] = []
        for (guest_identity, year, tier), members in sorted(memberships.items()):
            contexts.append(
                self._context(
                    guest_identity=guest_identity,
                    year=year,
                    tier=tier,
                    members=members,
                    guest_evidence=guest_evidence.get(guest_identity, []),
                    property_evidence=property_evidence,
                    conflict_map=conflict_map,
                )
            )
        return contexts

    def _membership(
        self,
        observation: CleanObservation,
        reservation_parents: Mapping[str, Sequence[CleanObservation]],
    ) -> tuple[str, int, str] | None:
        if observation.entity_kind in self.DEPENDENT_KINDS and observation.reservation_identity:
            parents = reservation_parents.get(observation.reservation_identity, ())
            candidates = {
                (parent.guest_identity, parent.partition_year, parent.partition_tier)
                for parent in parents
                if parent.guest_identity and parent.partition_year and parent.partition_tier != "unassigned"
            }
            if len(candidates) == 1:
                guest_identity, year, tier = next(iter(candidates))
                return guest_identity, int(year), tier
            if len(candidates) > 1:
                observation.uncertainty.append(
                    {
                        "field": "reservation",
                        "reason": "ambiguous_parent_partition",
                    }
                )
                return None
        if (
            observation.guest_identity
            and observation.partition_year
            and observation.partition_tier in {"hot", "cold"}
        ):
            return observation.guest_identity, observation.partition_year, observation.partition_tier
        return None

    def _context(
        self,
        *,
        guest_identity: str,
        year: int,
        tier: str,
        members: Sequence[CleanObservation],
        guest_evidence: Sequence[CleanObservation],
        property_evidence: Mapping[str, Sequence[CleanObservation]],
        conflict_map: Mapping[str, ConflictSet],
    ) -> dict[str, Any]:
        relationships: dict[str, list[dict[str, Any]]] = {
            key: [] for key in self.RELATION_KEYS.values()
        }
        grouped: dict[tuple[str, str], list[CleanObservation]] = defaultdict(list)
        for observation in members:
            relation_key = self.RELATION_KEYS.get(observation.entity_kind)
            if relation_key:
                grouped[(relation_key, observation.subject_key)].append(observation)

        for (relation_key, reference), grouped_observations in sorted(grouped.items()):
            relationships[relation_key].append(
                self._relation(reference, relation_key, grouped_observations)
            )

        property_refs = {
            observation.property_identity
            for observation in members
            if observation.property_identity
        }
        existing_property_refs = {item["reference"] for item in relationships["properties"]}
        for property_ref in sorted(property_refs - existing_property_refs):
            evidence = property_evidence.get(property_ref, ())
            relationships["properties"].append(self._relation(property_ref, "properties", evidence))

        dependents_by_reservation: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for relation_key in ("payments", "deposit_holds", "invoices", "messages", "work_orders"):
            for relation in relationships[relation_key]:
                reservation_ref = relation.get("reservation_ref")
                if reservation_ref:
                    dependents_by_reservation[reservation_ref][relation_key].append(relation["reference"])
        for reservation in relationships["reservations"]:
            links = dependents_by_reservation.get(reservation["reference"], {})
            reservation["relationship_refs"] = {
                "properties": sorted(reservation.get("property_refs", [])),
                "payments": sorted(links.get("payments", [])),
                "deposit_holds": sorted(links.get("deposit_holds", [])),
                "invoices": sorted(links.get("invoices", [])),
                "messages": sorted(links.get("messages", [])),
                "work_orders": sorted(links.get("work_orders", [])),
            }

        observation_refs = sorted({item.observation_id for item in members})
        supporting_refs = sorted(
            {
                item.observation_id
                for item in guest_evidence
                if item.observation_id not in observation_refs
            }
            | {
                item.observation_id
                for property_ref in property_refs
                for item in property_evidence.get(property_ref, ())
                if item.observation_id not in observation_refs
            }
        )
        conflict_refs = sorted(
            {
                conflict_ref
                for item in (*members, *guest_evidence)
                for conflict_ref in item.conflict_refs
            }
        )
        latest_activity_at = max(
            (item.activity_at for item in members if item.activity_at),
            key=_activity_sort_key,
            default="",
        )
        projection_identity = {
            "guest_identity": guest_identity,
            "year": year,
            "tier": tier,
            "observation_refs": observation_refs,
        }
        return {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "stage": "prepare",
            "projection_type": "guest_history_context",
            "projection_id": f"guest_history:{_sha256_value(projection_identity)}",
            "guest_identity": {
                "key": guest_identity,
                "kind": "CustomerProfile",
                "resolution": {
                    "boundary": "AirbnbGuestRecord -> GuestIdentityResolver -> Guest/CustomerProfile",
                    "status": "confirmed",
                    "authoritative_write": False,
                },
            },
            "partition": {
                "tier": tier,
                "year": year,
                "policy": self.partition_policy.name,
            },
            "latest_activity_at": latest_activity_at,
            "observation_refs": observation_refs,
            "supporting_observation_refs": supporting_refs,
            "conflict_refs": conflict_refs,
            "conflicts": [
                conflict_map[conflict_ref].to_record()
                for conflict_ref in conflict_refs
                if conflict_ref in conflict_map
            ],
            "relationships": relationships,
            "reconciliation": {
                "reservation_boundary": (
                    "AirbnbReservationSnapshot -> ReservationReconciliation -> Reservation/BookingInquiry"
                ),
                "contains_unresolved_conflicts": bool(conflict_refs),
                "authoritative_writes_performed": False,
            },
        }

    def _relation(
        self,
        reference: str,
        relation_key: str,
        observations: Sequence[CleanObservation],
    ) -> dict[str, Any]:
        source_models = sorted(
            {
                str(item.source_identity.get("source_model") or "")
                for item in observations
                if item.source_identity.get("source_model")
            }
        )
        conflict_refs = sorted({ref for item in observations for ref in item.conflict_refs})
        relation = {
            "reference": reference,
            "observation_refs": sorted(item.observation_id for item in observations),
            "source_models": source_models,
            "conflict_refs": conflict_refs,
            "observations": [
                {
                    "observation_ref": item.observation_id,
                    "summary": self._summary(relation_key, item.facts),
                }
                for item in sorted(observations, key=lambda value: value.observation_id)
            ],
        }
        reservation_ref = next(
            (item.reservation_identity for item in observations if item.reservation_identity),
            "",
        )
        if reservation_ref and relation_key != "reservations":
            relation["reservation_ref"] = reservation_ref
        if relation_key == "reservations":
            relation["property_refs"] = sorted(
                {item.property_identity for item in observations if item.property_identity}
            )
            relation["reconciliation"] = self._reservation_reconciliation(observations, conflict_refs)
        return relation

    @staticmethod
    def _reservation_reconciliation(
        observations: Sequence[CleanObservation],
        conflict_refs: Sequence[str],
    ) -> dict[str, Any]:
        models = {
            str(item.source_identity.get("source_model") or "")
            for item in observations
        }
        if conflict_refs:
            status = "conflict"
        elif "bookings.BookingInquiry" in models:
            status = "confirmed_match"
        elif any("AirbnbReservationSnapshot" in model for model in models):
            status = "candidate_match" if any(item.guest_identity for item in observations) else "unmatched"
        else:
            status = "candidate_match"
        return {
            "boundary": "AirbnbReservationSnapshot -> ReservationReconciliation -> Reservation/BookingInquiry",
            "status": status,
            "authoritative_write": False,
        }

    @staticmethod
    def _summary(relation_key: str, facts: Mapping[str, Any]) -> dict[str, Any]:
        fields: dict[str, tuple[tuple[str, ...], ...]] = {
            "guest_records": {
                "check_in": (("check_in",),),
                "check_out": (("check_out",),),
                "guests": (("guests",),),
                "rating": (("rating",),),
            },
            "reservations": {
                "check_in": (("check_in",), ("lifecycle", "check_in")),
                "check_out": (("check_out",), ("lifecycle", "check_out")),
                "status": (("status",), ("reservation_state",), ("lifecycle", "status")),
                "guests": (("guests",), ("occupancy", "guests")),
                "currency": (("currency",), ("financials", "currency")),
                "total_cents": (("total_cents",),),
                "total_amount": (("financials", "total_amount"),),
            },
            "properties": {
                "item_id": (("item_id",), ("bookable_item_id",)),
                "listing_id": (("airbnb_listing_id",), ("property", "listing_id")),
                "listing_title": (("listing_title",), ("property", "listing_title")),
            },
            "payments": {
                "amount_cents": (("amount_cents",),),
                "status": (("status",),),
                "currency": (("currency",),),
                "payment_provider": (("payment_provider",),),
            },
            "deposit_holds": {
                "amount_cents": (("amount_cents",),),
                "status": (("status",),),
                "currency": (("currency",),),
                "payment_provider": (("payment_provider",),),
            },
            "invoices": {
                "invoice_number": (("invoice_number",),),
                "status": (("status",),),
                "total_cents": (("total_cents",),),
                "currency": (("currency",),),
            },
            "messages": {
                "message_count": (("message_count",), ("turn_count",)),
                "last_message_at": (("last_message_at",),),
                "outcome": (("outcome",),),
            },
            "work_orders": {
                "title": (("title",),),
                "work_type": (("work_type",),),
                "status": (("status",),),
                "cost_amount": (("cost_amount",),),
                "cost_currency": (("cost_currency",),),
            },
        }
        result: dict[str, Any] = {}
        for output_name, paths in fields.get(relation_key, {}).items():
            value = _nested_get(facts, *paths)
            if value not in (None, "", [], {}):
                result[output_name] = value
        return result


@dataclass(frozen=True)
class PreparationResult:
    input_digest: str
    source_file_count: int
    source_record_count: int
    clean_observation_count: int
    duplicate_observation_count: int
    conflict_count: int
    prepared_context_count: int
    guest_index_count: int
    resumed: bool


class HistoricalDataPreparationService:
    """Orchestrates deterministic CLEAN and PREPARE over COLLECT evidence."""

    MANIFEST_PATH = "manifest.json"
    INDEX_PATH = "guest_history_index.jsonl"
    CONFLICTS_PATH = "conflicts.jsonl"

    def __init__(
        self,
        *,
        collect_repository: CollectRepository,
        storage: HistoricalStoragePolicy,
        partition_policy: HotPartitionPolicy,
    ):
        self.collect_repository = collect_repository
        self.storage = storage
        self.partition_policy = partition_policy
        if isinstance(storage, FilesystemHistoryStorage):
            collect_root = collect_repository.root
            output_root = storage.root
            if collect_root == output_root or collect_root in output_root.parents or output_root in collect_root.parents:
                raise HistoricalDataError("COLLECT and historical output roots must be disjoint.")

    def prepare(self, *, resume: bool = False) -> PreparationResult:
        sources = self.collect_repository.inventory()
        if not sources:
            raise InvalidHistoricalRecord("No supported Object Lake COLLECT files were found.")
        input_digest = _sha256_value([source.manifest_record() for source in sources])
        if resume:
            resumed = self._resume_result(input_digest)
            if resumed:
                return resumed

        cleaner = HistoricalCleaner()
        clean_result = cleaner.clean(self.collect_repository.records(sources))
        projector = PreparedRelationshipProjector(self.partition_policy)
        contexts = projector.prepare(clean_result.observations, clean_result.conflicts)

        generated_files: dict[str, dict[str, Any]] = {}
        observations_by_partition: dict[tuple[str, int | None], list[CleanObservation]] = defaultdict(list)
        for observation in clean_result.observations:
            observations_by_partition[(observation.partition_tier, observation.partition_year)].append(observation)
        for (tier, year), observations in sorted(
            observations_by_partition.items(),
            key=lambda item: (item[0][0], item[0][1] or 0),
        ):
            relative_path = self._observations_path(tier, year)
            self.storage.write_jsonl(
                relative_path,
                (item.to_record() for item in sorted(observations, key=lambda value: value.observation_id)),
            )
            generated_files[relative_path] = self.storage.file_metadata(relative_path)

        self.storage.write_jsonl(
            self.CONFLICTS_PATH,
            (conflict.to_record() for conflict in clean_result.conflicts),
        )
        generated_files[self.CONFLICTS_PATH] = self.storage.file_metadata(self.CONFLICTS_PATH)

        context_archive: dict[str, dict[str, Any]] = {}
        for context in contexts:
            guest_key = context["guest_identity"]["key"]
            tier = context["partition"]["tier"]
            year = int(context["partition"]["year"])
            relative_path = self._guest_context_path(guest_key, tier, year)
            self.storage.write_json(relative_path, context)
            metadata = self.storage.file_metadata(relative_path)
            generated_files[relative_path] = metadata
            context_archive[context["projection_id"]] = metadata

        index_records = self._index_records(contexts, context_archive)
        self.storage.write_jsonl(self.INDEX_PATH, index_records)
        generated_files[self.INDEX_PATH] = self.storage.file_metadata(self.INDEX_PATH)

        manifest = {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "sidecar": "airbnb-historical-data",
            "stages": ["clean", "prepare"],
            "as_of": self.partition_policy.as_of.isoformat(),
            "visibility": "private-protected",
            "storage_representation": "json-jsonl",
            "transactional_source_of_truth": "MLADIS Django transactional store",
            "durable_archive": "MLADIS Drive/Object Lake protected segment",
            "private_git_dataset_used": False,
            "input_digest": input_digest,
            "source_files": [source.manifest_record() for source in sources],
            "partition_policy": self.partition_policy.descriptor(),
            "files": {path: generated_files[path] for path in sorted(generated_files)},
            "counts": {
                "source_files": len(sources),
                "source_records": clean_result.source_record_count,
                "clean_observations": len(clean_result.observations),
                "duplicate_observations": clean_result.duplicate_observation_count,
                "conflicts": len(clean_result.conflicts),
                "prepared_guest_contexts": len(contexts),
                "guest_index_entries": len(index_records),
            },
            "boundaries": {
                "guest": "AirbnbGuestRecord -> GuestIdentityResolver -> Guest/CustomerProfile",
                "reservation": (
                    "AirbnbReservationSnapshot -> ReservationReconciliation -> Reservation/BookingInquiry"
                ),
                "authoritative_writes_performed": False,
            },
        }
        self.storage.write_json(self.MANIFEST_PATH, manifest)
        return self._result_from_manifest(manifest, resumed=False)

    def _resume_result(self, input_digest: str) -> PreparationResult | None:
        if not self.storage.exists(self.MANIFEST_PATH):
            return None
        try:
            manifest = self.storage.read_json(self.MANIFEST_PATH)
            if manifest.get("input_digest") != input_digest:
                return None
            if manifest.get("partition_policy") != self.partition_policy.descriptor():
                return None
            files = manifest.get("files")
            if not isinstance(files, Mapping):
                return None
            for relative_path, metadata in files.items():
                if not isinstance(metadata, Mapping):
                    return None
                self.storage.verify_file(
                    str(relative_path),
                    sha256=str(metadata.get("sha256") or ""),
                    size_bytes=metadata.get("size_bytes"),
                )
        except ArchiveIntegrityError:
            return None
        return self._result_from_manifest(manifest, resumed=True)

    @staticmethod
    def _observations_path(tier: str, year: int | None) -> str:
        if tier in {"hot", "cold"} and year:
            return f"partitions/{tier}/{year}/clean_observations.jsonl"
        return "partitions/unassigned/clean_observations.jsonl"

    @staticmethod
    def _guest_context_path(guest_key: str, tier: str, year: int) -> str:
        guest_segment = hashlib.sha256(guest_key.encode("utf-8")).hexdigest()[:24]
        return f"partitions/{tier}/{year}/guests/{guest_segment}.json"

    def _index_records(
        self,
        contexts: Sequence[dict[str, Any]],
        context_archive: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        by_guest: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for context in contexts:
            by_guest[context["guest_identity"]["key"]].append(context)
        index_records: list[dict[str, Any]] = []
        for guest_key, guest_contexts in sorted(by_guest.items()):
            partitions: list[dict[str, Any]] = []
            aggregate_refs: dict[str, set[str]] = {
                relation_key: set()
                for relation_key in PreparedRelationshipProjector.RELATION_KEYS.values()
            }
            latest_activity_at = ""
            for context in sorted(
                guest_contexts,
                key=lambda value: (
                    value["partition"]["year"],
                    value["partition"]["tier"],
                ),
            ):
                relationships = context["relationships"]
                references: dict[str, list[str]] = {}
                counts: dict[str, int] = {}
                for relation_key, relation_rows in relationships.items():
                    refs = sorted(row["reference"] for row in relation_rows)
                    references[relation_key] = refs
                    counts[relation_key] = len(refs)
                    aggregate_refs.setdefault(relation_key, set()).update(refs)
                latest_activity_at = max(
                    (latest_activity_at, context.get("latest_activity_at") or ""),
                    key=_activity_sort_key,
                )
                archive = dict(context_archive[context["projection_id"]])
                partitions.append(
                    {
                        "tier": context["partition"]["tier"],
                        "year": context["partition"]["year"],
                        "latest_activity_at": context.get("latest_activity_at") or "",
                        "counts": counts,
                        "references": references,
                        "archive": archive,
                        "rehydration_state": "available",
                    }
                )
            index_records.append(
                {
                    "schema_version": HISTORY_SCHEMA_VERSION,
                    "index_type": "GuestHistoryIndex",
                    "guest_identity": guest_key,
                    "latest_activity_at": latest_activity_at,
                    "partitions_present": [
                        f"{partition['tier']}:{partition['year']}" for partition in partitions
                    ],
                    "counts": {
                        key: len(values) for key, values in sorted(aggregate_refs.items())
                    },
                    "references": {
                        key: sorted(values) for key, values in sorted(aggregate_refs.items())
                    },
                    "archive_locations": partitions,
                    "rehydration_state": "available",
                    "full_historical_records_duplicated": False,
                }
            )
        return index_records

    @staticmethod
    def _result_from_manifest(manifest: Mapping[str, Any], *, resumed: bool) -> PreparationResult:
        counts = manifest.get("counts") if isinstance(manifest.get("counts"), Mapping) else {}
        return PreparationResult(
            input_digest=str(manifest.get("input_digest") or ""),
            source_file_count=int(counts.get("source_files") or 0),
            source_record_count=int(counts.get("source_records") or 0),
            clean_observation_count=int(counts.get("clean_observations") or 0),
            duplicate_observation_count=int(counts.get("duplicate_observations") or 0),
            conflict_count=int(counts.get("conflicts") or 0),
            prepared_context_count=int(counts.get("prepared_guest_contexts") or 0),
            guest_index_count=int(counts.get("guest_index_entries") or 0),
            resumed=resumed,
        )


class ActiveHistorySource(Protocol):
    """Read-only port for the MLADIS transactional source of current truth."""

    def lookup(self, guest_identity: str, year: int) -> dict[str, Any] | None:
        ...


class NullActiveHistorySource:
    def lookup(self, guest_identity: str, year: int) -> dict[str, Any] | None:
        del guest_identity, year
        return None


class GuestHistoryIndexRepository:
    """Lazy index reader. Construction and module import perform no I/O."""

    def __init__(self, storage: HistoricalStoragePolicy):
        self.storage = storage
        self._entries: dict[str, dict[str, Any]] | None = None

    def get(self, guest_identity: str) -> dict[str, Any] | None:
        if self._entries is None:
            self._entries = self._load_entries()
        return self._entries.get(guest_identity)

    def _load_entries(self) -> dict[str, dict[str, Any]]:
        manifest = self.storage.read_json(HistoricalDataPreparationService.MANIFEST_PATH)
        files = manifest.get("files") if isinstance(manifest.get("files"), Mapping) else {}
        metadata = files.get(HistoricalDataPreparationService.INDEX_PATH)
        if not isinstance(metadata, Mapping):
            raise ArchiveIntegrityError("History manifest does not contain a verified guest index.")
        self.storage.verify_file(
            HistoricalDataPreparationService.INDEX_PATH,
            sha256=str(metadata.get("sha256") or ""),
            size_bytes=metadata.get("size_bytes"),
        )
        entries: dict[str, dict[str, Any]] = {}
        for record in self.storage.read_jsonl(HistoricalDataPreparationService.INDEX_PATH):
            if record.get("index_type") != "GuestHistoryIndex" or not record.get("guest_identity"):
                raise ArchiveIntegrityError("Guest history index contains an invalid record.")
            entries[str(record["guest_identity"])] = record
        return entries


class ReservationReconciler:
    """Annotate temporary archive context; never write authoritative records."""

    def reconcile(self, context: dict[str, Any]) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        for reservation in context.get("relationships", {}).get("reservations", []):
            reconciliation = reservation.get("reconciliation") or {}
            if reconciliation.get("status") != "confirmed_match" or reservation.get("conflict_refs"):
                continue
            identity = {
                "guest_identity": context["guest_identity"]["key"],
                "reservation_ref": reservation.get("reference"),
                "observation_refs": reservation.get("observation_refs", []),
            }
            candidates.append(
                {
                    "promotion_key": f"history_promotion:{_sha256_value(identity)}",
                    "object_type": "reservation_context",
                    "reference": reservation.get("reference"),
                    "observation_refs": sorted(reservation.get("observation_refs", [])),
                    "reconciliation_status": "confirmed_match",
                    "requires_explicit_approval": True,
                }
            )
        context["rehydration"] = {
            "state": "temporary_prepared_context",
            "integrity_verified": True,
            "validation": "passed",
            "authoritative_writes_performed": False,
            "promotion_candidates": candidates,
        }
        return context


class HistoryLookupService:
    """Active-first lookup followed by exact, verified archive rehydration."""

    def __init__(
        self,
        *,
        active_source: ActiveHistorySource,
        index_repository: GuestHistoryIndexRepository,
        storage: HistoricalStoragePolicy,
        reconciler: ReservationReconciler | None = None,
    ):
        self.active_source = active_source
        self.index_repository = index_repository
        self.storage = storage
        self.reconciler = reconciler or ReservationReconciler()

    def lookup(self, guest_identity: str, year: int) -> dict[str, Any]:
        year = int(year)
        active = self.active_source.lookup(guest_identity, year)
        if active is not None:
            result = dict(active)
            result.setdefault("lookup", {})
            result["lookup"].update(
                {
                    "source": "active-transactional-store",
                    "guest_identity": guest_identity,
                    "year": year,
                    "archive_accessed": False,
                }
            )
            return result

        index = self.index_repository.get(guest_identity)
        if not index:
            raise HistoryNotFoundError("No history index entry exists for the requested guest.")
        exact_partitions = [
            partition
            for partition in index.get("archive_locations", [])
            if int(partition.get("year") or 0) == year
        ]
        if not exact_partitions:
            raise HistoryNotFoundError("No exact historical partition exists for the requested guest/year.")

        contexts: list[dict[str, Any]] = []
        for partition in sorted(exact_partitions, key=lambda item: item.get("tier") or ""):
            archive = partition.get("archive")
            if not isinstance(archive, Mapping):
                raise ArchiveIntegrityError("Guest index contains an invalid archive reference.")
            relative_path = str(archive.get("path") or "")
            self.storage.verify_file(
                relative_path,
                sha256=str(archive.get("sha256") or ""),
                size_bytes=archive.get("size_bytes"),
            )
            context = self.storage.read_json(relative_path)
            self._validate_context(context, guest_identity=guest_identity, year=year)
            contexts.append(context)
        merged = self._merge_contexts(contexts)
        merged["lookup"] = {
            "source": "verified-history-archive",
            "guest_identity": guest_identity,
            "year": year,
            "archive_accessed": True,
            "exact_partition_count": len(contexts),
        }
        return self.reconciler.reconcile(merged)

    @staticmethod
    def _validate_context(context: Mapping[str, Any], *, guest_identity: str, year: int) -> None:
        if context.get("stage") != "prepare" or context.get("projection_type") != "guest_history_context":
            raise ArchiveIntegrityError("Historical guest archive has an invalid projection type.")
        identity = context.get("guest_identity")
        partition = context.get("partition")
        if not isinstance(identity, Mapping) or identity.get("key") != guest_identity:
            raise ArchiveIntegrityError("Historical guest archive identity mismatch.")
        if not isinstance(partition, Mapping) or int(partition.get("year") or 0) != year:
            raise ArchiveIntegrityError("Historical guest archive partition mismatch.")

    @staticmethod
    def _merge_contexts(contexts: Sequence[dict[str, Any]]) -> dict[str, Any]:
        if not contexts:
            raise HistoryNotFoundError("No historical context was selected.")
        if len(contexts) == 1:
            return dict(contexts[0])
        first = contexts[0]
        relationships: dict[str, list[dict[str, Any]]] = {}
        for relation_key in first.get("relationships", {}):
            by_reference: dict[str, dict[str, Any]] = {}
            for context in contexts:
                for relation in context.get("relationships", {}).get(relation_key, []):
                    by_reference[str(relation.get("reference"))] = relation
            relationships[relation_key] = [by_reference[key] for key in sorted(by_reference)]
        latest_activity_at = max(
            (context.get("latest_activity_at") or "" for context in contexts),
            key=_activity_sort_key,
        )
        merged = {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "stage": "prepare",
            "projection_type": "guest_history_context",
            "projection_id": f"rehydrated:{_sha256_value([item.get('projection_id') for item in contexts])}",
            "guest_identity": first["guest_identity"],
            "partition": {
                "tier": "mixed",
                "year": first["partition"]["year"],
                "policy": first["partition"]["policy"],
            },
            "latest_activity_at": latest_activity_at,
            "observation_refs": sorted(
                {ref for context in contexts for ref in context.get("observation_refs", [])}
            ),
            "supporting_observation_refs": sorted(
                {
                    ref
                    for context in contexts
                    for ref in context.get("supporting_observation_refs", [])
                }
            ),
            "conflict_refs": sorted(
                {ref for context in contexts for ref in context.get("conflict_refs", [])}
            ),
            "conflicts": [
                conflict
                for _, conflict in sorted(
                    {
                        conflict.get("conflict_id"): conflict
                        for context in contexts
                        for conflict in context.get("conflicts", [])
                    }.items()
                )
            ],
            "relationships": relationships,
            "reconciliation": first.get("reconciliation", {}),
        }
        return merged


class PromotionTarget(ABC):
    """Port for a future authorized reconciliation-backed active-store adapter."""

    @abstractmethod
    def contains(self, promotion_key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def promote(self, candidate: Mapping[str, Any]) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class PromotionResult:
    promoted: int
    already_present: int
    skipped: int


class IdempotentHistoryPromotionService:
    """Promote only explicitly approved, reconciled references through a port."""

    def promote(
        self,
        context: Mapping[str, Any],
        *,
        target: PromotionTarget,
        approved_keys: Iterable[str],
    ) -> PromotionResult:
        approved = set(approved_keys)
        promoted = 0
        already_present = 0
        skipped = 0
        rehydration = context.get("rehydration") if isinstance(context.get("rehydration"), Mapping) else {}
        candidates = rehydration.get("promotion_candidates") if isinstance(rehydration, Mapping) else []
        for candidate in candidates or []:
            if not isinstance(candidate, Mapping):
                skipped += 1
                continue
            promotion_key = str(candidate.get("promotion_key") or "")
            if (
                not promotion_key
                or promotion_key not in approved
                or candidate.get("reconciliation_status") != "confirmed_match"
            ):
                skipped += 1
                continue
            if target.contains(promotion_key):
                already_present += 1
                continue
            target.promote(candidate)
            promoted += 1
        return PromotionResult(promoted=promoted, already_present=already_present, skipped=skipped)


def write_private_json(path: str | os.PathLike[str], payload: Mapping[str, Any]) -> Path:
    """Write an explicitly requested temporary prepared context with mode 0600."""

    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(destination)
    return destination
