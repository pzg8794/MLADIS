import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from django.utils import timezone

from .models import AirbnbGuestRecord, BookableItem, ContactSource, CustomerProfile, MarketingConsentStatus


@dataclass(frozen=True)
class AirbnbGuestPayload:
    source_message_id: str = ""
    source_email_subject: str = ""
    source_email_timestamp: datetime | None = None
    guest_name: str = ""
    email: str = ""
    phone: str = ""
    listing_title: str = ""
    airbnb_listing_id: str = ""
    airbnb_thread_url: str = ""
    check_in: date | None = None
    check_out: date | None = None
    guests: int | None = None
    message_excerpt: str = ""
    feedback_summary: str = ""


@dataclass(frozen=True)
class AirbnbGuestImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


class AirbnbGuestEmailParser:
    ROOM_RE = re.compile(r"airbnb\.com/rooms/(\d+)")
    THREAD_RE = re.compile(r"https://www\.airbnb\.com/hosting/thread/\d+[^\s)\]]*")
    GUESTS_RE = re.compile(r"\bGuests\s+(\d+)\s+guests?\b", re.IGNORECASE)
    RESPOND_TO_RE = re.compile(r"Respond to\s+(.+?)\s+by replying", re.IGNORECASE)
    SUBJECT_RE = re.compile(r"at\s+(.+?)\s+for\s+(.+?)\s+-\s+(.+)$", re.IGNORECASE)
    CHECK_IN_RE = re.compile(r"Check-In\s+\w+\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE)
    CHECK_OUT_RE = re.compile(r"Check-out\s+\w+\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE)

    def parse_many(self, messages):
        for message in messages:
            payload = self.parse_message(message)
            if payload.guest_name or payload.airbnb_listing_id or payload.listing_title:
                yield payload

    def parse_message(self, message):
        body = self._clean_text(message.get("body", ""))
        subject = self._clean_text(message.get("subject", ""))
        listing_title, subject_check_in, subject_check_out = self._parse_subject(subject)
        check_in = self._parse_date_match(self.CHECK_IN_RE.search(body)) or subject_check_in
        check_out = self._parse_date_match(self.CHECK_OUT_RE.search(body)) or subject_check_out
        guest_name = self._parse_guest_name(body)
        message_excerpt = self._parse_message_excerpt(body, guest_name)
        listing_id = self._first_match(self.ROOM_RE, body)
        guests = self._parse_guests(body)

        return AirbnbGuestPayload(
            source_message_id=message.get("id", "") or message.get("message_id", ""),
            source_email_subject=subject,
            source_email_timestamp=self._parse_timestamp(message.get("email_ts")),
            guest_name=guest_name,
            email=(message.get("guest_email") or message.get("email") or "").strip().lower(),
            phone=(message.get("guest_phone") or message.get("phone") or "").strip(),
            listing_title=listing_title or self._parse_listing_title(body),
            airbnb_listing_id=listing_id,
            airbnb_thread_url=self._first_match(self.THREAD_RE, body),
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            message_excerpt=message_excerpt,
            feedback_summary=(message.get("feedback_summary") or "").strip(),
        )

    def _clean_text(self, value):
        return re.sub(r"\n{3,}", "\n\n", str(value or "").replace("\r\n", "\n")).strip()

    def _parse_subject(self, subject):
        match = self.SUBJECT_RE.search(subject)
        if not match:
            return "", None, None
        listing_title = match.group(1).strip()
        return listing_title, self._parse_date(match.group(2)), self._parse_date(match.group(3))

    def _parse_guest_name(self, body):
        match = self.RESPOND_TO_RE.search(body)
        if match:
            return self._compact_name(match.group(1))
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if line.startswith("Remember: Airbnb will never ask you"):
                for candidate in lines[index + 1 : index + 4]:
                    if self._looks_like_name(candidate):
                        return self._compact_name(candidate)
        return ""

    def _parse_listing_title(self, body):
        lines = [line.strip("[] ") for line in body.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if line == "Reservation details" and index + 1 < len(lines):
                return lines[index + 1]
        for line in lines:
            if "airbnb.com/rooms/" not in line and ("Vacation Home" in line or "Apartment" in line):
                return line
        return ""

    def _parse_message_excerpt(self, body, guest_name):
        if not guest_name:
            return ""
        marker = f"\n{guest_name}\n"
        _, separator, after_name = body.partition(marker)
        if not separator:
            return ""
        for stop in ("\n[Pre-approve", "\n[Reply", "\nRespond to ", "\nReservation details"):
            if stop in after_name:
                after_name = after_name.split(stop, 1)[0]
        return after_name.strip()[:1200]

    def _parse_guests(self, body):
        match = self.GUESTS_RE.search(body)
        return int(match.group(1)) if match else None

    def _parse_date_match(self, match):
        if not match:
            return None
        return self._parse_date(match.group(1))

    def _parse_date(self, value):
        value = (value or "").strip()
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _parse_timestamp(self, value):
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    def _first_match(self, regex, text):
        match = regex.search(text)
        return match.group(1) if match and match.groups() else match.group(0) if match else ""

    def _looks_like_name(self, value):
        if len(value) > 80 or any(character.isdigit() for character in value):
            return False
        rejected = {"Airbnb", "Hi", "Hello", "Automatically translated. Original message follows:"}
        return value not in rejected

    def _compact_name(self, value):
        return re.sub(r"\s+", " ", value).strip(" :.,")


class AirbnbGuestImportService:
    def __init__(self, parser=None):
        self.parser = parser or AirbnbGuestEmailParser()

    def import_file(self, path, dry_run=False):
        messages = self._load_messages(Path(path))
        return self.import_messages(messages, dry_run=dry_run)

    def import_messages(self, messages, dry_run=False):
        result = {"created": 0, "updated": 0, "skipped": 0}
        for payload in self.parser.parse_many(messages):
            if not payload.guest_name and not payload.airbnb_listing_id:
                result["skipped"] += 1
                continue
            action = self._upsert(payload, dry_run=dry_run)
            result[action] += 1
        return AirbnbGuestImportResult(**result)

    def _upsert(self, payload, dry_run=False):
        lookup = {}
        if payload.source_message_id:
            lookup["source_message_id"] = payload.source_message_id
        else:
            lookup = {
                "guest_name": payload.guest_name,
                "airbnb_listing_id": payload.airbnb_listing_id,
                "check_in": payload.check_in,
                "check_out": payload.check_out,
            }
        existing = AirbnbGuestRecord.objects.filter(**lookup).first()
        action = "updated" if existing else "created"
        if dry_run:
            return action

        profile = self._profile_for(payload)
        item = self._item_for(payload)
        values = {
            "customer_profile": profile,
            "item": item,
            "guest_name": payload.guest_name or (profile.name if profile else "Airbnb guest"),
            "email": payload.email,
            "phone": payload.phone,
            "listing_title": payload.listing_title,
            "airbnb_listing_id": payload.airbnb_listing_id,
            "airbnb_thread_url": payload.airbnb_thread_url,
            "source_message_id": payload.source_message_id or None,
            "source_email_subject": payload.source_email_subject,
            "source_email_timestamp": payload.source_email_timestamp,
            "check_in": payload.check_in,
            "check_out": payload.check_out,
            "guests": payload.guests,
            "message_excerpt": payload.message_excerpt,
            "feedback_summary": payload.feedback_summary,
        }
        if existing:
            for field, value in values.items():
                setattr(existing, field, value)
            existing.save()
        else:
            AirbnbGuestRecord.objects.create(**values)
        return action

    def _profile_for(self, payload):
        defaults = {
            "name": payload.guest_name,
            "phone": payload.phone,
            "source": ContactSource.AIRBNB,
            "marketing_consent_status": MarketingConsentStatus.UNKNOWN,
            "notes": "Imported from Airbnb message history. Request permission before sending promotions.",
        }
        if payload.email:
            return CustomerProfile.find_or_create_for_email(payload.email, defaults=defaults)
        if not payload.guest_name:
            return None
        profile = CustomerProfile.objects.filter(
            name__iexact=payload.guest_name,
            source=ContactSource.AIRBNB,
            email="",
        ).first()
        if profile:
            return profile
        return CustomerProfile.objects.create(**defaults)

    def _item_for(self, payload):
        if not payload.airbnb_listing_id:
            return None
        return BookableItem.objects.filter(airbnb_listing_id=payload.airbnb_listing_id).first()

    def _load_messages(self, path):
        suffix = path.suffix.lower()
        if suffix == ".json":
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                return data.get("responses") or data.get("messages") or []
            return data
        if suffix == ".csv":
            with path.open(newline="") as handle:
                return list(csv.DictReader(handle))
        raise ValueError("Airbnb import expects a .json or .csv file.")
