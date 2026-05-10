import csv
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from django.db.models import Q
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
    marketing_consent_status: str = MarketingConsentStatus.UNKNOWN
    permission_notes: str = ""


@dataclass(frozen=True)
class AirbnbGuestImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


class AirbnbGuestEmailParser:
    ROOM_RE = re.compile(r"airbnb\.com/rooms/(\d+)")
    THREAD_RE = re.compile(r"airbnb\.com/hosting/(?:thread|messages)/(\d+)")
    GUESTS_RE = re.compile(r"\bGuests\s+(\d+)\s+guests?\b", re.IGNORECASE)
    TRAVELERS_RE = re.compile(
        r"\b(?:Guests|Viajeros)\s+(\d+)\s+(?:adultos?|adults?)\b"
        r"(?:,\s*(\d+)\s+(?:children|kids|infants?|bab(?:y|ies)|ni[nñ]os?|beb[eé]s?)\b)?",
        re.IGNORECASE,
    )
    ADULTS_RE = re.compile(r"\b(?:Guests|Viajeros)\s+(\d+)\s+(?:adults?|adultos?|guests?|hu[eé]spedes|viajeros?)\b", re.IGNORECASE)
    INITIAL_INQUIRY_RE = re.compile(r"Respond to\s+(.+?)['’]s inquiry", re.IGNORECASE)
    INITIAL_INQUIRY_ES_RE = re.compile(r"Responde a la solicitud de\s+(.+)", re.IGNORECASE)
    RESPOND_TO_RE = re.compile(r"Respond to\s+(.+?)\s+by replying", re.IGNORECASE)
    SUBJECT_RE = re.compile(r"at\s+(.+?)\s+for\s+(.+?)\s+-\s+(.+)$", re.IGNORECASE)
    CHECK_IN_RE = re.compile(r"Check-In\s+\w+\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE)
    CHECK_OUT_RE = re.compile(r"Check-out\s+\w+\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE)
    CHECK_IN_ES_RE = re.compile(r"Check-in\s+\w+\s+(\d{1,2}\s+de\s+[A-Za-záéíóúñ]+\s+de\s+\d{4})", re.IGNORECASE)
    CHECK_OUT_ES_RE = re.compile(r"Check-out\s+\w+\s+(\d{1,2}\s+de\s+[A-Za-záéíóúñ]+\s+de\s+\d{4})", re.IGNORECASE)
    RESPONSIBLE_RE = re.compile(r"\n([^\n]{2,80})\n\nResponsable de reservaci[oó]n\b", re.IGNORECASE)
    SPANISH_MONTHS = {
        "ene": 1,
        "enero": 1,
        "feb": 2,
        "febrero": 2,
        "mar": 3,
        "marzo": 3,
        "abr": 4,
        "abril": 4,
        "may": 5,
        "mayo": 5,
        "jun": 6,
        "junio": 6,
        "jul": 7,
        "julio": 7,
        "ago": 8,
        "agosto": 8,
        "sep": 9,
        "sept": 9,
        "septiembre": 9,
        "setiembre": 9,
        "oct": 10,
        "octubre": 10,
        "nov": 11,
        "noviembre": 11,
        "dic": 12,
        "diciembre": 12,
    }
    LISTING_IDS_BY_TITLE = {
        "6 Bedrooms Vacation Home & Pool (Apartment G-102)": "588632365342578374",
        "3 Bedrooms Vacation Home & Pool (Apartment G-102)": "587194328968598250",
        "3 Bedrooms Vacation Home & Pool (Apartment G-101)": "582161420407543691",
    }

    def parse_many(self, messages):
        for message in messages:
            payload = self.parse_message(message)
            if payload.guest_name or payload.airbnb_listing_id or payload.listing_title:
                yield payload

    def parse_message(self, message):
        if self._is_structured_contact_export(message):
            return self._parse_structured_contact_export(message)

        body = self._clean_text(message.get("body", ""))
        subject = self._clean_text(message.get("subject", ""))
        listing_title, subject_check_in, subject_check_out = self._parse_subject(subject)
        check_in = (
            self._parse_date_match(self.CHECK_IN_RE.search(body))
            or self._parse_date_match(self.CHECK_IN_ES_RE.search(body))
            or subject_check_in
        )
        check_out = (
            self._parse_date_match(self.CHECK_OUT_RE.search(body))
            or self._parse_date_match(self.CHECK_OUT_ES_RE.search(body))
            or subject_check_out
        )
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
            airbnb_thread_url=self._parse_thread_url(body),
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            message_excerpt=message_excerpt,
            feedback_summary=(message.get("feedback_summary") or "").strip(),
        )

    def _is_structured_contact_export(self, message):
        return any(
            key in message
            for key in (
                "guest_name",
                "listing_apartment",
                "check_in_date",
                "check_out_date",
                "airbnb_profile_name_or_id",
            )
        )

    def _parse_structured_contact_export(self, row):
        listing_title = self._clean_text(row.get("listing_title") or row.get("listing_apartment"))
        check_in = self._parse_date(row.get("check_in") or row.get("check_in_date"), default_year=timezone.localdate().year)
        check_out_default_year = check_in.year if check_in else timezone.localdate().year
        check_out = self._parse_date(row.get("check_out") or row.get("check_out_date"), default_year=check_out_default_year)
        if check_in and check_out and check_out < check_in:
            check_out = date(check_out.year + 1, check_out.month, check_out.day)
        message_excerpt = self._clean_text(row.get("message_excerpt") or row.get("message_summary"))
        feedback_summary = self._clean_text(row.get("feedback_summary") or row.get("feedback_or_review_summary"))
        return AirbnbGuestPayload(
            source_message_id=self._clean_text(row.get("source_message_id") or row.get("id")),
            source_email_subject=self._clean_text(row.get("source_email_subject") or "Structured Airbnb contact export"),
            source_email_timestamp=self._parse_timestamp(row.get("source_email_timestamp") or row.get("email_ts")),
            guest_name=self._compact_name(row.get("guest_name") or ""),
            email=(row.get("email") or "").strip().lower(),
            phone=(row.get("phone") or row.get("phone_number") or "").strip(),
            listing_title=listing_title,
            airbnb_listing_id=(row.get("airbnb_listing_id") or self.LISTING_IDS_BY_TITLE.get(listing_title, "")).strip(),
            airbnb_thread_url=self._parse_thread_url(row.get("airbnb_thread_url") or ""),
            check_in=check_in,
            check_out=check_out,
            guests=self._parse_guest_count(row.get("guests") or row.get("number_of_guests")),
            message_excerpt=message_excerpt,
            feedback_summary=feedback_summary,
            marketing_consent_status=self._normalize_marketing_consent(row.get("marketing_consent_status") or row.get("consent_status")),
            permission_notes=self._structured_permission_notes(row),
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
        match = self.INITIAL_INQUIRY_RE.search(body)
        if match:
            return self._compact_name(match.group(1))
        match = self.INITIAL_INQUIRY_ES_RE.search(body)
        if match:
            return self._compact_name(match.group(1))
        match = self.RESPOND_TO_RE.search(body)
        if match:
            return self._compact_name(match.group(1))
        match = self.RESPONSIBLE_RE.search(f"\n{body}")
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
        for stop in (
            "\n[Pre-approve",
            "\n[Preaprobar",
            "\n[Reply",
            "\n[Revisar",
            "\n[Responder",
            "\nRespond to ",
            "\nTambién puedes",
            "\nDiana\n",
            "\nReservation details",
        ):
            if stop in after_name:
                after_name = after_name.split(stop, 1)[0]
        return after_name.strip()[:1200]

    def _parse_guests(self, body):
        travelers_match = self.TRAVELERS_RE.search(body)
        if travelers_match:
            adults = int(travelers_match.group(1))
            children = int(travelers_match.group(2) or 0)
            return adults + children
        match = self.GUESTS_RE.search(body) or self.ADULTS_RE.search(body)
        return int(match.group(1)) if match else None

    def _parse_date_match(self, match):
        if not match:
            return None
        return self._parse_date(match.group(1))

    def _parse_date(self, value, default_year=None):
        value = (value or "").strip()
        value = value.replace("\u2009", " ").replace("\xa0", " ")
        spanish_match = re.match(
            r"(\d{1,2})\s+de\s+([A-Za-záéíóúñ]+)\s+de\s+(\d{4})",
            value,
            re.IGNORECASE,
        )
        if spanish_match:
            day = int(spanish_match.group(1))
            month = self.SPANISH_MONTHS.get(spanish_match.group(2).lower())
            year = int(spanish_match.group(3))
            if month:
                return date(year, month, day)
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        if default_year:
            for fmt in ("%B %d", "%b %d"):
                try:
                    return datetime.strptime(f"{value} {default_year}", f"{fmt} %Y").date()
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

    def _parse_thread_url(self, body):
        thread_id = self._first_match(self.THREAD_RE, body)
        return f"https://www.airbnb.com/hosting/thread/{thread_id}" if thread_id else ""

    def _parse_guest_count(self, value):
        if value in ("", None):
            return None
        if isinstance(value, int):
            return value
        match = re.search(r"\d+", str(value))
        return int(match.group(0)) if match else None

    def _normalize_marketing_consent(self, value):
        normalized = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
        return (
            normalized
            if normalized in MarketingConsentStatus.values
            else MarketingConsentStatus.UNKNOWN
        )

    def _structured_permission_notes(self, row):
        notes = []
        promotion_notes = self._clean_text(row.get("permission_notes") or row.get("promotion_permission_notes"))
        permission = self._clean_text(row.get("permission_to_contact_outside_airbnb"))
        profile_id = self._clean_text(row.get("airbnb_profile_name_or_id"))
        if promotion_notes:
            notes.append(promotion_notes)
        if permission:
            notes.append(f"Airbnb outside-contact permission: {permission}")
        if profile_id:
            notes.append(f"Airbnb profile name/id: {profile_id}")
        return "\n".join(notes)

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
        existing = self._find_existing(payload)
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
            "permission_notes": payload.permission_notes,
        }
        if existing:
            if (
                existing.guest_name
                and payload.guest_name
                and existing.guest_name != payload.guest_name
                and not self._is_initial_inquiry(payload)
            ):
                values["guest_name"] = existing.guest_name
                values["customer_profile"] = existing.customer_profile
            if (
                existing.airbnb_thread_url
                and payload.airbnb_thread_url
                and existing.airbnb_thread_url != payload.airbnb_thread_url
            ):
                values["airbnb_thread_url"] = existing.airbnb_thread_url
            for field, value in values.items():
                if value in ("", None) and getattr(existing, field):
                    continue
                setattr(existing, field, value)
            existing.save()
        else:
            AirbnbGuestRecord.objects.create(**values)
        return action

    def _is_initial_inquiry(self, payload):
        return payload.source_email_subject.lower().startswith("inquiry for")

    def _find_existing(self, payload):
        signature = Q()
        if payload.guest_name and payload.airbnb_listing_id and payload.check_in and payload.check_out:
            signature = Q(
                guest_name__iexact=payload.guest_name,
                airbnb_listing_id=payload.airbnb_listing_id,
                check_in=payload.check_in,
                check_out=payload.check_out,
            )
        if payload.airbnb_thread_url and signature:
            return AirbnbGuestRecord.objects.filter(Q(airbnb_thread_url=payload.airbnb_thread_url) | signature).first()
        if payload.airbnb_thread_url:
            return AirbnbGuestRecord.objects.filter(airbnb_thread_url=payload.airbnb_thread_url).first()
        if signature:
            return AirbnbGuestRecord.objects.filter(signature).first()
        if payload.source_message_id:
            return AirbnbGuestRecord.objects.filter(source_message_id=payload.source_message_id).first()
        return AirbnbGuestRecord.objects.filter(
            guest_name__iexact=payload.guest_name,
            airbnb_listing_id=payload.airbnb_listing_id,
        ).first()

    def _profile_for(self, payload):
        defaults = {
            "name": payload.guest_name,
            "phone": payload.phone,
            "source": ContactSource.AIRBNB,
            "marketing_consent_status": payload.marketing_consent_status or MarketingConsentStatus.UNKNOWN,
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
                return data.get("guest_contact_list") or data.get("responses") or data.get("messages") or []
            return data
        if suffix == ".csv":
            with path.open(newline="") as handle:
                return list(csv.DictReader(handle))
        raise ValueError("Airbnb import expects a .json or .csv file.")
