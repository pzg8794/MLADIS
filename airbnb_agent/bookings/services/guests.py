from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from bookings.data_lake import DataLakeObjectEventWriter
from bookings.models import (
    AirbnbGuestRecord,
    BookingInquiry,
    BookingStatus,
    ClientSegment,
    ContactSource,
    CustomerFeedback,
    CustomerProfile,
    DamageDeposit,
    Invoice,
    MarketingConsentStatus,
    ReservationPaymentHold,
)


def _money_payload(cents: int | Decimal | None, currency: str = "USD") -> dict[str, Any]:
    amount_cents = int(cents or 0)
    currency_code = (currency or "USD").upper()
    display = f"${amount_cents / 100:,.0f}"
    return {
        "amount_cents": amount_cents,
        "currency": currency_code,
        "display": display,
        "with_currency": f"{display} {currency_code}",
    }


def _date_label(value) -> str:
    if not value:
        return ""
    if hasattr(value, "date") and not isinstance(value, date):
        value = value.date()
    return value.strftime("%b %-d, %Y")


def _datetime_label(value) -> str:
    if not value:
        return ""
    return timezone.localtime(value).strftime("%b %-d, %Y %-I:%M %p")


def _status_payload(value: str, label: str = "", tone: str = "") -> dict[str, str]:
    normalized = value or "active"
    return {
        "value": normalized,
        "label": label or normalized.replace("_", " ").title(),
        "tone": tone or {
            "vip": "warning",
            "favorite": "info",
            "repeat": "success",
            "average": "neutral",
            "new": "info",
            "blacklisted": "danger",
            "blocked": "danger",
            "active": "success",
            "inactive": "neutral",
            "archived": "neutral",
        }.get(normalized, "neutral"),
    }


def _normalized_email(value: str | None) -> str:
    return (value or "").strip().lower()


def _normalized_phone(value: str | None) -> str:
    digits = re.sub(r"\D+", "", value or "")
    return digits if len(digits) >= 7 else ""


@dataclass(frozen=True)
class GuestTagProjection:
    label: str
    slug: str
    tone: str = "neutral"

    def to_payload(self) -> dict[str, str]:
        return {"label": self.label, "slug": self.slug, "tone": self.tone}


class Guest:
    """Guest aggregate wrapper around the existing CustomerProfile model."""

    COUNTRY_POOL = (
        ("Dominican Republic", "DO"),
        ("United States", "US"),
        ("Canada", "CA"),
        ("France", "FR"),
        ("Spain", "ES"),
        ("Mexico", "MX"),
        ("Colombia", "CO"),
    )

    def __init__(self, profile: CustomerProfile, request=None, aliases: list[CustomerProfile] | None = None):
        self.profile = profile
        self.request = request
        by_id: dict[int, CustomerProfile] = {}
        for candidate in [profile, *(aliases or [])]:
            if candidate and candidate.pk:
                by_id[candidate.pk] = candidate
        self._profiles = tuple(by_id.values()) or (profile,)

    @property
    def profiles(self) -> tuple[CustomerProfile, ...]:
        return self._profiles

    @property
    def profile_ids(self) -> list[int]:
        return [profile.pk for profile in self.profiles if profile.pk]

    @property
    def id(self) -> str:
        return str(self.profile.pk)

    @property
    def key(self) -> str:
        return f"guest-{self.profile.pk}"

    @property
    def display_name(self) -> str:
        for profile in self.profiles:
            if profile.name:
                return profile.name
        for profile in self.profiles:
            if profile.email:
                return profile.email
        return f"Guest {self.profile.pk}"

    def initials(self) -> str:
        parts = [part for part in self.display_name.replace("@", " ").replace(".", " ").split() if part]
        if not parts:
            return "G"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return f"{parts[0][0]}{parts[1][0]}".upper()

    def country(self) -> tuple[str, str]:
        return "Not captured", ""

    def past_stay_count(self) -> int:
        direct = getattr(self.profile, "direct_reservations", None)
        airbnb = getattr(self.profile, "airbnb_reservations", None)
        if len(self.profiles) == 1 and (direct is not None or airbnb is not None):
            return int(direct or 0) + int(airbnb or 0)
        return (
            BookingInquiry.objects.filter(customer_profile__in=self.profiles).count()
            + AirbnbGuestRecord.objects.filter(customer_profile__in=self.profiles).count()
        )

    def total_spend_cents(self) -> int:
        annotated = getattr(self.profile, "total_spend_cents", None)
        if len(self.profiles) == 1 and annotated:
            return int(annotated)
        invoice_total = Invoice.objects.filter(customer_profile__in=self.profiles).aggregate(total=Coalesce(Sum("total_cents"), 0))["total"] or 0
        booking_total = BookingInquiry.objects.filter(customer_profile__in=self.profiles).aggregate(total=Coalesce(Sum("total_cents"), 0))["total"] or 0
        return int(invoice_total or booking_total or 0)

    def last_contact_at(self):
        timestamps = [profile.updated_at for profile in self.profiles if profile.updated_at]
        latest_booking = BookingInquiry.objects.filter(customer_profile__in=self.profiles).order_by("-updated_at").first()
        latest_airbnb = AirbnbGuestRecord.objects.filter(customer_profile__in=self.profiles).order_by("-updated_at").first()
        latest_feedback = CustomerFeedback.objects.filter(customer_profile__in=self.profiles).order_by("-updated_at").first()
        latest_invoice = Invoice.objects.filter(customer_profile__in=self.profiles).order_by("-updated_at").first()
        for item in (latest_booking, latest_airbnb, latest_feedback, latest_invoice):
            if item and getattr(item, "updated_at", None):
                timestamps.append(item.updated_at)
        return max(timestamps) if timestamps else self.profile.updated_at

    def segment_value(self) -> str:
        if any(profile.segment == ClientSegment.BLACKLISTED for profile in self.profiles):
            return "blacklisted"
        if any(profile.segment == ClientSegment.VIP for profile in self.profiles):
            return "vip"
        if self.past_stay_count() >= 2:
            return "repeat"
        if self.past_stay_count() == 0:
            return "new"
        return self.profile.segment or ClientSegment.AVERAGE

    def segment_label(self) -> str:
        value = self.segment_value()
        if value == "repeat":
            return "Repeat"
        if value == "new":
            return "New"
        if value == "blacklisted":
            return "Blocked"
        return self.profile.get_segment_display()

    def status_value(self) -> str:
        return "blocked" if any(profile.is_blacklisted for profile in self.profiles) else "active"

    def tags(self) -> list[GuestTagProjection]:
        tags = [
            GuestTagProjection(self.segment_label(), slugify(self.segment_label()), self._tag_tone(self.segment_value())),
            GuestTagProjection(self.profile.get_source_display(), slugify(self.profile.get_source_display()), "info"),
        ]
        if self.past_stay_count() >= 2:
            tags.append(GuestTagProjection("Repeat", "repeat", "success"))
        if self.profile.can_receive_promotions:
            tags.append(GuestTagProjection("Marketing OK", "marketing-ok", "success"))
        if len(self.profiles) > 1:
            tags.append(GuestTagProjection(f"{len(self.profiles)} source records", "source-records", "neutral"))
        return tags

    def preferences(self) -> list[dict[str, str]]:
        return [
            {"key": "preferred_language", "label": "Preferred language", "value": (self.profile.preferred_language or "en").upper(), "source": "profile"},
            {"key": "source", "label": "Source", "value": self.profile.get_source_display(), "source": "profile"},
            {"key": "travel_style", "label": "Travel style", "value": self._travel_style(), "source": "derived"},
        ]

    def row_projection(self) -> dict[str, Any]:
        country, country_code = self.country()
        return {
            "id": self.id,
            "key": self.key,
            "initials": self.initials(),
            "name": self.display_name,
            "email": self._contact_email(),
            "phone": self._contact_phone(),
            "country": country,
            "country_code": country_code,
            "source": self.profile.get_source_display(),
            "source_value": self.profile.source,
            "past_stays": self.past_stay_count(),
            "total_spend": _money_payload(self.total_spend_cents()),
            "status": _status_payload(self.status_value(), "Blocked" if self.status_value() == "blocked" else "Active"),
            "segment": _status_payload(self.segment_value(), self.segment_label()),
            "marketing_consent": self.profile.get_marketing_consent_status_display(),
            "last_contact_at": self.last_contact_at().isoformat() if self.last_contact_at() else "",
            "last_contact_label": _date_label(self.last_contact_at()),
            "source_profile_count": len(self.profiles),
            "source_profile_ids": self.profile_ids,
        }

    def profile_projection(self) -> dict[str, Any]:
        return {
            "birthday": self._birthday(),
            "travel_style": self._travel_style(),
            "guest_since": _date_label(min(profile.created_at for profile in self.profiles if profile.created_at)),
            "notes": self._profile_notes(),
            "admin_url": self._absolute_admin_url(),
            "full_profile_url": f"/ops/guests/?guest={self.profile.pk}",
        }

    def message_projection(self) -> dict[str, Any]:
        feedback = list(CustomerFeedback.objects.filter(customer_profile__in=self.profiles).order_by("-created_at")[:2])
        messages: list[dict[str, Any]] = []
        for item in feedback:
            messages.append(
                {
                    "id": f"feedback-{item.pk}",
                    "sender_label": item.guest_name or self.display_name,
                    "body": item.feedback_text[:320],
                    "status": "received",
                    "timestamp": _datetime_label(item.created_at),
                    "from_staff": False,
                }
            )
        latest_booking = BookingInquiry.objects.filter(customer_profile__in=self.profiles).order_by("-created_at").first()
        if latest_booking and latest_booking.message:
            messages.append(
                {
                    "id": f"reservation-message-{latest_booking.pk}",
                    "sender_label": self.display_name,
                    "body": latest_booking.message[:320],
                    "status": "received",
                    "timestamp": _datetime_label(latest_booking.created_at),
                    "from_staff": False,
                }
            )
        return {"draft": "", "items": sorted(messages, key=lambda item: item["timestamp"], reverse=True)}

    def documents_projection(self) -> list[dict[str, Any]]:
        documents = [
            {
                "id": f"profile-{self.profile.pk}",
                "title": "Guest profile record",
                "type": "profile",
                "status": "available",
                "url": self._absolute_admin_url(),
                "created_at": _date_label(self.profile.created_at),
            },
            {
                "id": f"marketing-{self.profile.pk}",
                "title": "Marketing consent",
                "type": "consent",
                "status": self.profile.get_marketing_consent_status_display(),
                "url": self._absolute_admin_url(),
                "created_at": _date_label(self.profile.marketing_consent_at or self.profile.marketing_consent_requested_at),
            },
        ]
        for alias in self.profiles:
            if alias.pk == self.profile.pk:
                continue
            documents.append(
                {
                    "id": f"profile-{alias.pk}",
                    "title": f"Linked guest profile #{alias.pk}",
                    "type": "profile_alias",
                    "status": "linked",
                    "url": self._absolute_url(reverse("admin:bookings_customerprofile_change", args=[alias.pk])),
                    "created_at": _date_label(alias.created_at),
                }
            )
        for record in AirbnbGuestRecord.objects.filter(customer_profile__in=self.profiles).order_by("-created_at")[:3]:
            documents.append(
                {
                    "id": f"airbnb-{record.pk}",
                    "title": record.source_email_subject or "Airbnb guest record",
                    "type": "airbnb_record",
                    "status": "imported",
                    "url": record.airbnb_thread_url,
                    "created_at": _date_label(record.created_at),
                }
            )
        return documents

    def stays_projection(self) -> list[dict[str, Any]]:
        stays = []
        for booking in BookingInquiry.objects.filter(customer_profile__in=self.profiles).select_related("item").order_by("-check_in", "-updated_at")[:8]:
            listing = booking.item.business_display_name if booking.item else "Flexible MLADIS stay"
            stays.append(
                {
                    "id": f"reservation-{booking.pk}",
                    "reservation_key": booking.request_key,
                    "listing_name": listing,
                    "date_range": self._booking_date_range(booking),
                    "total": _money_payload(booking.total_cents, booking.currency),
                    "status": booking.get_status_display(),
                    "status_value": booking.status,
                    "reservation_url": self._absolute_url(reverse("admin:bookings_bookinginquiry_change", args=[booking.pk])),
                    "guests": booking.guests,
                }
            )
        for record in AirbnbGuestRecord.objects.filter(customer_profile__in=self.profiles).select_related("item").order_by("-check_in", "-updated_at")[:4]:
            listing = record.listing_title or (record.item.business_display_name if record.item else "Airbnb stay")
            stays.append(
                {
                    "id": f"airbnb-{record.pk}",
                    "reservation_key": record.source_message_id or f"AIRBNB-{record.pk}",
                    "listing_name": listing,
                    "date_range": record.stay_dates,
                    "total": _money_payload(0),
                    "status": "Imported",
                    "status_value": "imported",
                    "reservation_url": record.airbnb_thread_url,
                    "guests": record.guests or 0,
                }
            )
        return sorted(stays, key=lambda stay: stay["date_range"], reverse=True)

    def payments_projection(self) -> dict[str, Any]:
        invoices = list(Invoice.objects.filter(customer_profile__in=self.profiles).order_by("-issue_date", "-created_at")[:8])
        items = [
            {
                "id": f"invoice-{invoice.pk}",
                "label": invoice.invoice_number,
                "amount": _money_payload(invoice.total_cents, invoice.currency),
                "status": invoice.get_status_display(),
                "status_value": invoice.status,
                "date": _date_label(invoice.issue_date),
                "url": self._absolute_url(reverse("admin:bookings_invoice_change", args=[invoice.pk])),
            }
            for invoice in invoices
        ]
        hold_query = Q(inquiry__customer_profile__in=self.profiles)
        for email in self._contact_emails():
            hold_query |= Q(email__iexact=email)
        holds = ReservationPaymentHold.objects.filter(hold_query).select_related("inquiry").distinct().order_by("-created_at")[:4]
        for hold in holds:
            items.append(
                {
                    "id": f"payment-hold-{hold.pk}",
                    "label": "Stay payment hold",
                    "amount": _money_payload(hold.amount_cents, hold.currency),
                    "status": hold.get_status_display(),
                    "status_value": hold.status,
                    "date": _date_label(hold.created_at),
                    "url": self._absolute_url(reverse("admin:bookings_reservationpaymenthold_change", args=[hold.pk])),
                }
            )
        return {
            "total_spend": _money_payload(self.total_spend_cents()),
            "payment_count": len(items),
            "last_payment_at": items[0]["date"] if items else "",
            "items": items,
        }

    def deposits_projection(self) -> dict[str, Any]:
        deposit_query = Q(inquiry__customer_profile__in=self.profiles)
        for email in self._contact_emails():
            deposit_query |= Q(email__iexact=email)
        deposits = list(
            DamageDeposit.objects.filter(deposit_query)
            .select_related("inquiry", "item")
            .distinct()
            .order_by("-created_at")[:8]
        )
        active_values = {"new", "checkout_created", "requires_capture", "requires_configuration"}
        released_values = {"canceled"}
        items = [
            {
                "id": f"deposit-{deposit.pk}",
                "label": deposit.item.business_display_name if deposit.item else "Damage deposit hold",
                "amount": _money_payload(deposit.amount_cents, deposit.currency),
                "status": deposit.get_status_display(),
                "status_value": deposit.status,
                "date": _date_label(deposit.created_at),
                "url": self._absolute_url(reverse("admin:bookings_damagedeposit_change", args=[deposit.pk])),
            }
            for deposit in deposits
        ]
        return {
            "active_holds": sum(1 for deposit in deposits if deposit.status in active_values),
            "released_holds": sum(1 for deposit in deposits if deposit.status in released_values),
            "dispute_count": sum(1 for deposit in deposits if deposit.status == "failed"),
            "items": items,
        }

    def activity_projection(self) -> list[dict[str, Any]]:
        events = [
            {
                "type": "guest_created",
                "label": "Guest profile created",
                "actor": "MLADIS",
                "timestamp": _datetime_label(self.profile.created_at),
                "note": self.profile.get_source_display(),
            }
        ]
        for alias in self.profiles:
            if alias.pk == self.profile.pk:
                continue
            events.append(
                {
                    "type": "guest_profile_linked",
                    "label": f"Linked source profile #{alias.pk}",
                    "actor": "MLADIS",
                    "timestamp": _datetime_label(alias.updated_at),
                    "note": alias.name or alias.email or "Additional real guest record",
                }
            )
        for booking in BookingInquiry.objects.filter(customer_profile__in=self.profiles).order_by("-created_at")[:4]:
            events.append(
                {
                    "type": "reservation_linked",
                    "label": f"Reservation {booking.request_key}",
                    "actor": booking.guest_name or self.display_name,
                    "timestamp": _datetime_label(booking.created_at),
                    "note": booking.get_status_display(),
                }
            )
        for feedback in CustomerFeedback.objects.filter(customer_profile__in=self.profiles).order_by("-created_at")[:3]:
            events.append(
                {
                    "type": "feedback_recorded",
                    "label": "Feedback recorded",
                    "actor": feedback.guest_name or self.display_name,
                    "timestamp": _datetime_label(feedback.created_at),
                    "note": feedback.feedback_summary or feedback.feedback_text[:120],
                }
            )
        return sorted(events, key=lambda item: item["timestamp"], reverse=True)

    def to_payload(self) -> dict[str, Any]:
        country, country_code = self.country()
        return {
            "id": self.id,
            "key": self.key,
            "identity": {
                "name": self.display_name,
                "initials": self.initials(),
                "country": country,
                "country_code": country_code,
                "preferred_language": self.profile.preferred_language or "en",
                "source": self.profile.source,
                "source_label": self.profile.get_source_display(),
            },
            "contact": {
                "email": self._contact_email(),
                "phone": self._contact_phone(),
                "last_contact_at": self.last_contact_at().isoformat() if self.last_contact_at() else "",
                "last_contact_label": _date_label(self.last_contact_at()),
                "profile_admin_url": self._absolute_admin_url(),
                "full_profile_url": f"/ops/guests/?guest={self.profile.pk}",
            },
            "profile": self.profile_projection(),
            "status": _status_payload(self.status_value(), "Blocked" if self.status_value() == "blocked" else "Active"),
            "segment": _status_payload(self.segment_value(), self.segment_label()),
            "marketing": {
                "consent_status": self.profile.marketing_consent_status,
                "consent_label": self.profile.get_marketing_consent_status_display(),
                "requested_at": self.profile.marketing_consent_requested_at.isoformat() if self.profile.marketing_consent_requested_at else "",
                "consent_at": self.profile.marketing_consent_at.isoformat() if self.profile.marketing_consent_at else "",
                "can_receive_promotions": self.profile.can_receive_promotions,
            },
            "tags": [tag.to_payload() for tag in self.tags()],
            "preferences": self.preferences(),
            "messages": self.message_projection(),
            "documents": self.documents_projection(),
            "stays": self.stays_projection(),
            "payments": self.payments_projection(),
            "deposits": self.deposits_projection(),
            "timeline": self.activity_projection(),
            "row": self.row_projection(),
            "source": "api",
            "source_profile_count": len(self.profiles),
            "source_profile_ids": self.profile_ids,
            "missing_fields": self._missing_fields(),
            "is_complete": not self._missing_fields(),
        }

    def _absolute_url(self, path: str) -> str:
        if not path:
            return ""
        return self.request.build_absolute_uri(path) if self.request else path

    def _absolute_admin_url(self) -> str:
        return self._absolute_url(reverse("admin:bookings_customerprofile_change", args=[self.profile.pk]))

    @staticmethod
    def _tag_tone(value: str) -> str:
        return {
            "vip": "warning",
            "repeat": "success",
            "new": "info",
            "blacklisted": "danger",
            "favorite": "info",
        }.get(value, "neutral")

    @staticmethod
    def _booking_date_range(booking: BookingInquiry) -> str:
        if booking.check_in and booking.check_out:
            return f"{booking.check_in:%b %-d} - {booking.check_out:%b %-d, %Y}"
        return "Dates pending"

    def _birthday(self) -> str:
        return ""

    def _travel_style(self) -> str:
        return "Not captured"

    def _contact_email(self) -> str:
        return next((profile.email for profile in self.profiles if profile.email), "")

    def _contact_emails(self) -> list[str]:
        emails: list[str] = []
        seen: set[str] = set()
        for profile in self.profiles:
            normalized = _normalized_email(profile.email)
            if normalized and normalized not in seen:
                emails.append(normalized)
                seen.add(normalized)
        return emails

    def _contact_phone(self) -> str:
        return next((profile.phone for profile in self.profiles if profile.phone), "")

    def _profile_notes(self) -> str:
        for profile in self.profiles:
            if profile.notes:
                return profile.notes
        return "No notes captured yet."

    def _search_terms(self) -> list[str]:
        terms: list[str] = []
        for profile in self.profiles:
            terms.extend(
                [
                    profile.name,
                    profile.email,
                    profile.phone,
                ]
            )
        for booking in BookingInquiry.objects.filter(customer_profile__in=self.profiles).select_related("item")[:20]:
            terms.extend(
                [
                    booking.guest_name,
                    booking.email,
                    booking.phone,
                    booking.request_key,
                    booking.item.business_display_name if booking.item else "",
                ]
            )
        for record in AirbnbGuestRecord.objects.filter(customer_profile__in=self.profiles).select_related("item")[:20]:
            terms.extend(
                [
                    record.guest_name,
                    record.email,
                    record.phone,
                    record.listing_title,
                    record.source_email_subject,
                    record.item.business_display_name if record.item else "",
                ]
            )
        return [term for term in terms if term]

    def _missing_fields(self) -> list[str]:
        fields = []
        if not self._contact_email():
            fields.append("contact.email")
        if not self._contact_phone():
            fields.append("contact.phone")
        if self.profile.marketing_consent_status == MarketingConsentStatus.UNKNOWN:
            fields.append("marketing.consent_status")
        return fields


class GuestAnalyticsService:
    def compute_segment(self, guest: Guest) -> dict[str, str]:
        if guest.status_value() == "blocked":
            return _status_payload("blacklisted", "Blocked", "danger")
        return _status_payload(guest.segment_value(), guest.segment_label())

    def workspace_metrics(self, guests: list[Guest]) -> list[dict[str, Any]]:
        total = len(guests)
        repeat = sum(1 for guest in guests if guest.past_stay_count() >= 2)
        vip = sum(1 for guest in guests if guest.segment_value() == "vip")
        blocked = sum(1 for guest in guests if guest.status_value() == "blocked")
        promo = sum(1 for guest in guests if guest.profile.can_receive_promotions)
        spend = sum(guest.total_spend_cents() for guest in guests)
        return [
            {"label": "Guests", "value": total, "caption": "Relationship profiles", "tone": "blue"},
            {"label": "Repeat Guests", "value": repeat, "caption": "Two or more stays", "tone": "green"},
            {"label": "VIP", "value": vip, "caption": "High-touch profiles", "tone": "orange"},
            {"label": "Promo-ready", "value": promo, "caption": "Email consent verified", "tone": "teal"},
            {"label": "Total Spend", "value": _money_payload(spend)["display"], "caption": "Linked invoices/reservations", "tone": "violet"},
            {"label": "Blocked", "value": blocked, "caption": "Requires review", "tone": "red"},
        ]

    def segment_tabs(self, guests: list[Guest]) -> list[dict[str, Any]]:
        return [
            {"value": "all", "label": "All", "count": len(guests)},
            {"value": "repeat", "label": "Repeat Guests", "count": sum(1 for guest in guests if guest.past_stay_count() >= 2)},
            {"value": "vip", "label": "VIP", "count": sum(1 for guest in guests if guest.segment_value() == "vip")},
            {"value": "new", "label": "New", "count": sum(1 for guest in guests if guest.segment_value() == "new")},
            {"value": "blocked", "label": "Blocked", "count": sum(1 for guest in guests if guest.status_value() == "blocked")},
        ]


class GuestTimelineService:
    def events_for_guest(self, guest: Guest) -> list[dict[str, Any]]:
        return guest.activity_projection()


class GuestDataLakeService:
    def emit_event(self, event_type: str, profile: CustomerProfile, actor=None, metadata: dict[str, Any] | None = None, request=None) -> None:
        data = {"event_type": event_type, **(metadata or {})}
        if actor and getattr(actor, "is_authenticated", False):
            data["actor_id"] = actor.pk
        try:
            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_type,
                instance=profile,
                request=request,
                data=data,
            )
        except Exception:
            # Data-lake emission should not block staff operations.
            return


class GuestQueryService:
    """Loads and filters CustomerProfile records for the Guest aggregate."""

    def queryset(self):
        return (
            CustomerProfile.objects.annotate(
                direct_reservations=Count("booking_inquiries", distinct=True),
                airbnb_reservations=Count("airbnb_guest_records", distinct=True),
                feedback_total=Count("feedback_entries", distinct=True),
                invoice_total=Count("invoices", distinct=True),
                total_spend_cents=Coalesce(Sum("invoices__total_cents"), 0),
            )
            .prefetch_related("booking_inquiries__item", "airbnb_guest_records__item", "feedback_entries", "invoices")
            .order_by("-updated_at", "name", "email")
        )

    def filtered_queryset(self, filters: dict[str, str] | None = None):
        filters = filters or {}
        qs = self.queryset()
        query = (filters.get("search") or filters.get("query") or "").strip()
        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
                | Q(booking_inquiries__guest_name__icontains=query)
                | Q(booking_inquiries__email__icontains=query)
                | Q(booking_inquiries__item__name__icontains=query)
                | Q(airbnb_guest_records__guest_name__icontains=query)
                | Q(airbnb_guest_records__listing_title__icontains=query)
            ).distinct()
        source = (filters.get("source") or "").strip()
        if source:
            qs = qs.filter(source=source)
        status = (filters.get("status") or "").strip()
        if status == "blocked":
            qs = qs.filter(segment=ClientSegment.BLACKLISTED)
        elif status == "active":
            qs = qs.exclude(segment=ClientSegment.BLACKLISTED)
        return qs

    def guests(self, request=None, filters: dict[str, str] | None = None) -> list[Guest]:
        guests = self.unique_guests(request=request)
        return [guest for guest in guests if self._matches_filters(guest, filters or {})]

    def unique_guests(self, request=None) -> list[Guest]:
        return self._profiles_to_guests(list(self.queryset()), request=request)

    def _profiles_to_guests(self, profiles: list[CustomerProfile], request=None) -> list[Guest]:
        grouped: dict[str, list[CustomerProfile]] = defaultdict(list)
        parent: dict[str, str] = {}
        profile_roots: dict[int, str] = {}

        def find(key: str) -> str:
            parent.setdefault(key, key)
            while parent[key] != key:
                parent[key] = parent[parent[key]]
                key = parent[key]
            return key

        def union(left: str, right: str) -> None:
            parent[find(right)] = find(left)

        for profile in profiles:
            keys = self._identity_keys(profile)
            for key in keys:
                parent.setdefault(key, key)
            for key in keys[1:]:
                union(keys[0], key)
            profile_roots[profile.pk] = keys[0]

        for profile in profiles:
            grouped[find(profile_roots[profile.pk])].append(profile)

        guests: list[Guest] = []
        for profile_group in grouped.values():
            canonical = self._canonical_profile(profile_group)
            aliases = [profile for profile in profile_group if profile.pk != canonical.pk]
            guests.append(Guest(canonical, request=request, aliases=aliases))
        return sorted(guests, key=lambda guest: (guest.last_contact_at() or timezone.now(), guest.display_name.lower()), reverse=True)

    @staticmethod
    def _identity_keys(profile: CustomerProfile) -> list[str]:
        keys = []
        email = _normalized_email(profile.email)
        phone = _normalized_phone(profile.phone)
        if email:
            keys.append(f"email:{email}")
        if phone:
            keys.append(f"phone:{phone}")
        return keys or [f"profile:{profile.pk}"]

    @staticmethod
    def _canonical_profile(profiles: list[CustomerProfile]) -> CustomerProfile:
        def score(profile: CustomerProfile):
            relationship_total = (
                int(getattr(profile, "direct_reservations", 0) or 0)
                + int(getattr(profile, "airbnb_reservations", 0) or 0)
                + int(getattr(profile, "feedback_total", 0) or 0)
                + int(getattr(profile, "invoice_total", 0) or 0)
            )
            return (
                profile.is_blacklisted,
                profile.segment == ClientSegment.VIP,
                relationship_total,
                bool(profile.email),
                bool(profile.phone),
                profile.updated_at or timezone.now(),
                -(profile.pk or 0),
            )

        return max(profiles, key=score)

    @staticmethod
    def _matches_filters(guest: Guest, filters: dict[str, str]) -> bool:
        query = (filters.get("search") or filters.get("query") or "").strip().lower()
        if query and query not in " ".join(guest._search_terms()).lower():
            return False
        source = (filters.get("source") or "").strip()
        if source and not any(profile.source == source for profile in guest.profiles):
            return False
        status = (filters.get("status") or "").strip()
        if status == "blocked" and guest.status_value() != "blocked":
            return False
        if status == "active" and guest.status_value() == "blocked":
            return False
        return True


class GuestProjectionService:
    """Converts Guest objects into stable Guests workspace API payloads."""

    def __init__(self, analytics_service: GuestAnalyticsService | None = None):
        self.analytics_service = analytics_service or GuestAnalyticsService()

    def workspace_payload(
        self,
        guests: list[Guest],
        all_guests: list[Guest],
        request=None,
        filters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        filters = filters or {}
        segment = filters.get("segment") or filters.get("tab") or "all"
        rows = [guest.to_payload() for guest in guests]
        return {
            "metrics": self.analytics_service.workspace_metrics(all_guests),
            "summary_cards": self.analytics_service.workspace_metrics(all_guests),
            "segment_options": self.analytics_service.segment_tabs(all_guests),
            "filter_options": self.filter_options(all_guests),
            "filters": {
                "search": (filters.get("search") or filters.get("query") or "").strip(),
                "segment": segment,
                "source": filters.get("source", ""),
                "country": filters.get("country", ""),
                "tags": filters.get("tags", ""),
                "status": filters.get("status", ""),
            },
            "rows": rows,
            "admin_url": reverse("admin:bookings_customerprofile_changelist"),
            "legacy_url": reverse("bookings:ops-customers"),
            "generated_at": timezone.now().isoformat(),
            "source": "api",
            "missing_fields": sorted({field for row in rows for field in row["missing_fields"]}),
            "is_complete": all(row["is_complete"] for row in rows),
        }

    def filter_options(self, guests: list[Guest]) -> dict[str, list[dict[str, Any]]]:
        sources: dict[str, dict[str, Any]] = {}
        statuses = {
            "active": {"value": "active", "label": "Active", "count": 0},
            "blocked": {"value": "blocked", "label": "Blocked", "count": 0},
        }
        for guest in guests:
            sources.setdefault(
                guest.profile.source,
                {"value": guest.profile.source, "label": guest.profile.get_source_display(), "count": 0},
            )
            sources[guest.profile.source]["count"] += 1
            statuses[guest.status_value()]["count"] += 1
        return {
            "sources": sorted(sources.values(), key=lambda item: item["label"]),
            "statuses": list(statuses.values()),
        }

    def filter_by_segment(self, guests: list[Guest], segment: str = "all") -> list[Guest]:
        if segment in {"", "all"}:
            return guests
        if segment == "repeat":
            return [guest for guest in guests if guest.past_stay_count() >= 2]
        if segment == "blocked":
            return [guest for guest in guests if guest.status_value() == "blocked"]
        return [guest for guest in guests if guest.segment_value() == segment]


class GuestMessageService:
    def __init__(self, timeline_service: GuestTimelineService | None = None, data_lake_service: GuestDataLakeService | None = None):
        self.timeline_service = timeline_service or GuestTimelineService()
        self.data_lake_service = data_lake_service or GuestDataLakeService()

    def send_message(self, profile: CustomerProfile, payload: dict[str, Any], actor=None, request=None) -> dict[str, Any]:
        body = (payload.get("body") or payload.get("message") or "").strip()
        if not body:
            raise ValidationError("Message body is required.")
        confirmed = bool(payload.get("confirmed"))
        event_name = "guest_message_sent" if confirmed else "guest_message_drafted"
        self.data_lake_service.emit_event(
            event_name,
            profile,
            actor=actor,
            request=request,
            metadata={"channel": payload.get("channel") or "email", "confirmed": confirmed},
        )
        return {
            "id": f"{event_name}-{timezone.now().timestamp()}",
            "sender_label": getattr(actor, "get_full_name", lambda: "")() or getattr(actor, "username", "") or "Staff",
            "body": body,
            "status": "sent" if confirmed else "drafted",
            "timestamp": _datetime_label(timezone.now()),
            "from_staff": True,
            "requires_confirmation": not confirmed,
        }


class GuestService:
    def __init__(
        self,
        query_service: GuestQueryService | None = None,
        projection_service: GuestProjectionService | None = None,
        analytics_service: GuestAnalyticsService | None = None,
        message_service: GuestMessageService | None = None,
        timeline_service: GuestTimelineService | None = None,
        data_lake_service: GuestDataLakeService | None = None,
    ):
        self.analytics_service = analytics_service or GuestAnalyticsService()
        self.query_service = query_service or GuestQueryService()
        self.projection_service = projection_service or GuestProjectionService(self.analytics_service)
        self.timeline_service = timeline_service or GuestTimelineService()
        self.data_lake_service = data_lake_service or GuestDataLakeService()
        self.message_service = message_service or GuestMessageService(self.timeline_service, self.data_lake_service)

    def queryset(self):
        return self.query_service.queryset()

    def workspace_payload(self, request=None, filters: dict[str, str] | None = None) -> dict[str, Any]:
        filters = filters or {}
        all_guests = self.query_service.unique_guests(request=request)
        guests = self.query_service.guests(request=request, filters=filters)
        segment = filters.get("segment") or filters.get("tab") or "all"
        filtered = self.projection_service.filter_by_segment(guests, segment=segment)
        return self.projection_service.workspace_payload(filtered, all_guests, request=request, filters=filters)

    @staticmethod
    def filtered_guests(guests: list[Guest], segment: str = "all") -> list[Guest]:
        return GuestProjectionService().filter_by_segment(guests, segment=segment)

    def get_guest(self, guest_id: int, request=None) -> Guest:
        profile = CustomerProfile.objects.get(pk=guest_id)
        for guest in self.query_service.unique_guests(request=request):
            if profile.pk in guest.profile_ids:
                return guest
        return Guest(profile, request=request)

    @transaction.atomic
    def create_guest(self, payload: dict[str, Any], actor=None, request=None) -> Guest:
        email = self.normalize_email(payload.get("email"))
        phone = self.normalize_phone(payload.get("phone"))
        allow_anonymous = bool(payload.get("allow_anonymous") or payload.get("is_manual_anonymous"))
        if not email and not phone and not allow_anonymous:
            raise ValidationError("Guest requires at least email or phone.")
        if email and CustomerProfile.objects.filter(email__iexact=email).exists():
            raise ValidationError("A guest with that email already exists.")
        profile = CustomerProfile.objects.create(
            name=(payload.get("name") or "").strip(),
            email=email,
            phone=phone,
            segment=payload.get("segment") or ClientSegment.AVERAGE,
            source=payload.get("source") or ContactSource.MANUAL,
            preferred_language=payload.get("preferred_language") or "en",
            notes=payload.get("notes") or "",
            marketing_consent_status=MarketingConsentStatus.UNKNOWN,
        )
        self.data_lake_service.emit_event("guest_created", profile, actor=actor, request=request, metadata={"source": profile.source})
        return Guest(profile, request=request)

    @transaction.atomic
    def update_guest(self, profile: CustomerProfile, payload: dict[str, Any], actor=None, request=None) -> Guest:
        allowed = {"name", "phone", "segment", "source", "preferred_language", "notes"}
        update_fields = []
        if "email" in payload:
            email = self.normalize_email(payload.get("email"))
            if email and CustomerProfile.objects.filter(email__iexact=email).exclude(pk=profile.pk).exists():
                raise ValidationError("A guest with that email already exists.")
            profile.email = email
            update_fields.append("email")
        for field in allowed:
            if field in payload:
                setattr(profile, field, (payload.get(field) or "").strip() if isinstance(payload.get(field), str) else payload.get(field))
                update_fields.append(field)
        if update_fields:
            profile.save(update_fields=sorted(set(update_fields + ["updated_at"])))
            self.data_lake_service.emit_event("guest_updated", profile, actor=actor, request=request, metadata={"fields": sorted(set(update_fields))})
        return Guest(profile, request=request)

    @transaction.atomic
    def sync_from_reservation(self, inquiry: BookingInquiry, actor=None, request=None) -> Guest | None:
        profile = CustomerProfile.find_or_create_for_email(
            inquiry.email,
            defaults={"name": inquiry.guest_name, "phone": inquiry.phone, "source": ContactSource.DIRECT},
        )
        if not profile:
            return None
        changed = []
        if inquiry.customer_profile_id != profile.pk:
            inquiry.customer_profile = profile
            changed.append("customer_profile")
        profile_updates = []
        if inquiry.guest_name and not profile.name:
            profile.name = inquiry.guest_name
            profile_updates.append("name")
        if inquiry.phone and not profile.phone:
            profile.phone = self.normalize_phone(inquiry.phone)
            profile_updates.append("phone")
        if profile.source == ContactSource.MANUAL:
            profile.source = ContactSource.DIRECT
            profile_updates.append("source")
        if profile_updates:
            profile.save(update_fields=sorted(set(profile_updates + ["updated_at"])))
        if changed:
            inquiry.save(update_fields=changed + ["updated_at"])
        self.data_lake_service.emit_event(
            "guest_synced_from_reservation",
            profile,
            actor=actor,
            request=request,
            metadata={"reservation_id": inquiry.pk},
        )
        return Guest(profile, request=request)

    @transaction.atomic
    def merge_guests(self, primary_profile: CustomerProfile, duplicate_profile: CustomerProfile, actor=None, request=None) -> Guest:
        if primary_profile.pk == duplicate_profile.pk:
            raise ValidationError("Cannot merge a guest into itself.")
        BookingInquiry.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        CustomerFeedback.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        AirbnbGuestRecord.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        Invoice.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        duplicate_profile.notes = (
            f"Merged into guest #{primary_profile.pk} on {timezone.now():%Y-%m-%d %H:%M}."
            f"\n\nPreserved duplicate evidence:\n{duplicate_profile.notes}"
        ).strip()
        duplicate_profile.save(update_fields=["notes", "updated_at"])
        self.data_lake_service.emit_event(
            "guest_merged",
            primary_profile,
            actor=actor,
            request=request,
            metadata={"duplicate_guest_id": duplicate_profile.pk},
        )
        return Guest(primary_profile, request=request)

    def add_tag(self, profile: CustomerProfile, tag: str, actor=None, request=None) -> Guest:
        self.data_lake_service.emit_event("guest_tag_added", profile, actor=actor, request=request, metadata={"tag": tag})
        return Guest(profile, request=request)

    def remove_tag(self, profile: CustomerProfile, tag_slug: str, actor=None, request=None) -> Guest:
        self.data_lake_service.emit_event("guest_tag_removed", profile, actor=actor, request=request, metadata={"tag_slug": tag_slug})
        return Guest(profile, request=request)

    def record_preference(self, profile: CustomerProfile, payload: dict[str, Any], actor=None, request=None) -> dict[str, str]:
        key = slugify(payload.get("key") or payload.get("label") or "preference")
        value = str(payload.get("value") or "").strip()
        if not value:
            raise ValidationError("Preference value is required.")
        self.data_lake_service.emit_event("guest_preference_recorded", profile, actor=actor, request=request, metadata={"key": key, "value": value})
        return {"key": key, "label": key.replace("-", " ").title(), "value": value, "source": "staff"}

    def request_marketing_consent(self, profile: CustomerProfile, actor=None, request=None) -> Guest:
        profile.marketing_consent_status = MarketingConsentStatus.REQUESTED
        profile.marketing_consent_requested_at = timezone.now()
        profile.save(update_fields=["marketing_consent_status", "marketing_consent_requested_at", "updated_at"])
        self.data_lake_service.emit_event("guest_marketing_consent_requested", profile, actor=actor, request=request)
        return Guest(profile, request=request)

    def update_marketing_consent(self, profile: CustomerProfile, status: str, source: str = "", actor=None, request=None) -> Guest:
        if status not in dict(MarketingConsentStatus.choices):
            raise ValidationError("Unknown marketing consent status.")
        profile.marketing_consent_status = status
        profile.marketing_consent_source = source or "staff"
        if status in {MarketingConsentStatus.OPTED_IN, MarketingConsentStatus.OPTED_OUT}:
            profile.marketing_consent_at = timezone.now()
        profile.save(update_fields=["marketing_consent_status", "marketing_consent_source", "marketing_consent_at", "updated_at"])
        self.data_lake_service.emit_event("guest_marketing_consent_updated", profile, actor=actor, request=request, metadata={"status": status})
        return Guest(profile, request=request)

    @staticmethod
    def normalize_email(email: str | None) -> str:
        return (email or "").strip().lower()

    @staticmethod
    def normalize_phone(phone: str | None) -> str:
        return (phone or "").strip()
