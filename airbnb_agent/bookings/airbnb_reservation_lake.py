"""Private, idempotent Airbnb reservation snapshots for MLADIS reconciliation.

These snapshots are deliberately separate from the anonymized interaction lake.
Conversation learning removes identity and source references; reservation records
retain the structured identifiers needed to reconcile a stay with MLADIS objects.
They are not BookingInquiry rows and must be reviewed before operational import.
"""

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .data_lake import (
    DataLakeCollection,
    DataLakeDriveMirror,
    DataLakeJsonEncoder,
    SimpleObjectLakeLayout,
)


AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION = DataLakeCollection(
    key="airbnb_reservation_snapshots",
    folder="BOOKINGS",
    entity_type="airbnb_reservation_snapshot",
    description="Structured private reservation records captured from an Airbnb host reservation panel.",
    pii_classification="private",
)


class AirbnbReservationSnapshotWriter:
    """Upsert structured reservation snapshots by a deterministic MLADIS key."""

    def __init__(self, root):
        self.layout = SimpleObjectLakeLayout(root)

    @classmethod
    def from_settings(cls):
        configured_root = (getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        root = configured_root or Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"
        return cls(root)

    def write_snapshot(self, snapshot):
        self.layout.initialize()
        record = self.build_record(snapshot)
        path = self.layout.collection_path(AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION)
        records = self._read_records(path)
        replaced = False
        for index, existing in enumerate(records):
            if existing.get("record_key") == record["record_key"]:
                records[index] = record
                replaced = True
                break
        if not replaced:
            records.append(record)
        self._write_records(path, records)
        DataLakeDriveMirror.from_settings(self.layout.root).copy_path(path)
        return path, "updated" if replaced else "created"

    def write_snapshots(self, snapshots):
        results = {"created": 0, "updated": 0}
        for snapshot in snapshots:
            _, action = self.write_snapshot(snapshot)
            results[action] += 1
        return results

    def build_record(self, snapshot):
        if not isinstance(snapshot, dict):
            raise ValueError("Each Airbnb reservation snapshot must be an object.")

        normalized = self._normalize_snapshot(snapshot)
        reservation_key = self.reservation_key(normalized)
        captured_at = normalized.pop("captured_at")
        return {
            "schema_version": "1.0",
            "collection": AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION.key,
            "entity_type": AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION.entity_type,
            "record_key": f"reservation_snapshot:{reservation_key}",
            "source_system": "airbnb",
            "source_model": "AirbnbReservationSnapshot",
            "source_pk": reservation_key,
            "pii_classification": "private",
            "occurred_at": normalized.get("lifecycle", {}).get("booking_date") or captured_at,
            "extracted_at": timezone.now().isoformat(),
            "natural_keys": {
                "mladis_reservation_key": reservation_key,
                "airbnb_confirmation_code": normalized["source"].get("confirmation_code", ""),
                "airbnb_thread_id": normalized["source"].get("thread_id", ""),
            },
            "data": {
                "mladis_reservation_key": reservation_key,
                **normalized,
            },
        }

    @staticmethod
    def reservation_key(snapshot):
        source = snapshot.get("source", {})
        identity_parts = [
            source.get("confirmation_code"),
            source.get("thread_id"),
            snapshot.get("property", {}).get("listing_id"),
            snapshot.get("lifecycle", {}).get("check_in"),
            snapshot.get("lifecycle", {}).get("check_out"),
            snapshot.get("guest", {}).get("email"),
            snapshot.get("guest", {}).get("name"),
        ]
        identity = "|".join(str(value or "").strip().lower() for value in identity_parts)
        if not identity.strip("|"):
            raise ValueError("Reservation snapshots need a confirmation code, thread, guest, or stay identity.")
        return f"AIRBNB-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20].upper()}"

    def _normalize_snapshot(self, snapshot):
        source = snapshot.get("source") or {}
        guest = snapshot.get("guest") or {}
        property_data = snapshot.get("property") or snapshot.get("listing") or {}
        lifecycle = snapshot.get("lifecycle") or {}
        occupancy = snapshot.get("occupancy") or {}
        financials = snapshot.get("financials") or {}
        communication = snapshot.get("communication") or {}
        marketing = snapshot.get("marketing_consent") or {}
        consent_status = self._consent_status(
            marketing.get("status")
            or snapshot.get("marketing_consent_status")
            or snapshot.get("consent_status")
        )
        no_response = bool(
            marketing.get("no_response")
            or snapshot.get("no_response_to_consent")
            or (consent_status == "requested" and marketing.get("response_received") is False)
        )
        if consent_status == "no_response":
            no_response = True
        hash_contact = consent_status == "opted_out" or no_response
        guest_email = self._email(guest.get("email") or snapshot.get("email"))
        guest_phone = self._text(guest.get("phone") or snapshot.get("phone"))
        return {
            "captured_at": self._timestamp(snapshot.get("captured_at")),
            "source": {
                "system": "airbnb",
                "scope": self._text(source.get("scope") or snapshot.get("scope") or "unknown"),
                "thread_id": self._text(source.get("thread_id") or snapshot.get("thread_id")),
                "thread_url": self._url(source.get("thread_url") or snapshot.get("thread_url")),
                "confirmation_code": self._text(
                    source.get("confirmation_code") or snapshot.get("confirmation_code")
                ),
                "captured_from": self._text(source.get("captured_from") or "reservation_panel"),
                "confidence": "conversation_reservation_panel",
                "needs_reconciliation": True,
            },
            "guest": {
                "name": self._text(guest.get("name") or snapshot.get("guest_name")),
                "email": "" if hash_contact else guest_email,
                "phone": "" if hash_contact else guest_phone,
                "email_hash": self._identity_hash(guest_email) if hash_contact else "",
                "phone_hash": self._identity_hash(guest_phone) if hash_contact else "",
                "profile_url": self._url(guest.get("profile_url")),
            },
            "marketing_consent": {
                "status": "no_response" if no_response else consent_status,
                "response_received": False if no_response else marketing.get("response_received"),
                "contact_policy": "hash_contact_for_promotions" if hash_contact else "retain_for_permission_request",
            },
            "property": {
                "listing_id": self._text(property_data.get("listing_id") or property_data.get("airbnb_listing_id")),
                "listing_title": self._text(
                    property_data.get("listing_title") or property_data.get("title") or snapshot.get("listing_title")
                ),
                "address": self._text(property_data.get("address")),
            },
            "lifecycle": {
                "booking_date": self._date_or_empty(lifecycle.get("booking_date") or snapshot.get("booking_date")),
                "check_in": self._date_or_empty(lifecycle.get("check_in") or snapshot.get("check_in")),
                "check_out": self._date_or_empty(lifecycle.get("check_out") or snapshot.get("check_out")),
                "status": self._text(lifecycle.get("status") or snapshot.get("status")),
                "cancellation_policy": self._text(lifecycle.get("cancellation_policy")),
                "cancellation_status": self._text(lifecycle.get("cancellation_status")),
                "last_modified": self._timestamp(lifecycle.get("last_modified")),
            },
            "occupancy": {
                "guests": self._integer(occupancy.get("guests") or snapshot.get("guests") or snapshot.get("guest_count")),
                "adults": self._integer(occupancy.get("adults") or snapshot.get("adults")),
                "children": self._integer(occupancy.get("children") or snapshot.get("children")),
                "infants": self._integer(occupancy.get("infants") or snapshot.get("infants")),
                "pets": self._integer(occupancy.get("pets") or snapshot.get("pets")),
                "nights": self._integer(occupancy.get("nights") or snapshot.get("nights")),
            },
            "financials": {
                "total_amount": self._money(financials.get("total_amount") or snapshot.get("total_amount")),
                "potential_earnings": self._money(
                    financials.get("potential_earnings") or snapshot.get("potential_earnings")
                ),
                "payout_amount": self._money(financials.get("payout_amount")),
                "currency": self._text(financials.get("currency") or snapshot.get("currency") or "usd").upper(),
                "payment_status": self._text(financials.get("payment_status")),
                "deposit_amount": self._money(financials.get("deposit_amount")),
                "fees": self._money(financials.get("fees")),
            },
            "communication": {
                "message_count": self._integer(communication.get("message_count")),
                "last_message_at": self._timestamp(communication.get("last_message_at")),
                "has_raw_messages": False,
            },
            "review": {
                "rating": self._rating(snapshot.get("rating") or snapshot.get("guest_rating")),
                "count": self._integer(snapshot.get("review_count")),
                "text": self._text(snapshot.get("review") or snapshot.get("review_text")),
                "submitted_at": self._timestamp(snapshot.get("review_submitted_at"))
                if snapshot.get("review_submitted_at")
                else "",
            },
            "notes": self._text(snapshot.get("notes")),
        }

    def _read_records(self, path):
        if not path.exists():
            return []
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    def _write_records(self, path, records):
        temporary = path.with_suffix(".jsonl.tmp")
        temporary.write_text(
            "".join(json.dumps(record, cls=DataLakeJsonEncoder, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _text(value):
        return re.sub(r"\s+", " ", str(value or "")).strip()

    @staticmethod
    def _email(value):
        value = str(value or "").strip().lower()
        return value if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) else ""

    @staticmethod
    def _identity_hash(value):
        value = str(value or "").strip().lower()
        if not value:
            return ""
        return hashlib.sha256(f"{settings.SECRET_KEY}:{value}".encode("utf-8")).hexdigest()

    @staticmethod
    def _consent_status(value):
        normalized = str(value or "unknown").strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"yes", "opt_in", "opted_in", "approved", "consented"}:
            return "opted_in"
        if normalized in {"no", "opt_out", "opted_out", "declined", "denied"}:
            return "opted_out"
        if normalized in {"no_response", "no_reply", "unanswered", "no_answer"}:
            return "no_response"
        if normalized in {"requested", "pending"}:
            return "requested"
        return "unknown"

    @staticmethod
    def _url(value):
        value = str(value or "").strip()
        return value if value.startswith(("https://", "http://")) else ""

    @staticmethod
    def _integer(value):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _money(value):
        if value in (None, ""):
            return None
        try:
            return str(Decimal(str(value)).quantize(Decimal("0.01")))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    def _rating(value):
        if value in (None, ""):
            return None
        try:
            rating = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None
        return str(rating.quantize(Decimal("0.01")))

    @staticmethod
    def _date_or_empty(value):
        if not value:
            return ""
        if isinstance(value, date):
            return value.isoformat()
        try:
            return date.fromisoformat(str(value)[:10]).isoformat()
        except ValueError:
            return ""

    @staticmethod
    def _timestamp(value):
        if not value:
            return timezone.now().isoformat()
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return str(value)
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed.isoformat()


def load_reservation_documents(path):
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(source.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else [payload]
