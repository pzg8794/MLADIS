# Backend Code Stubs

These are implementation stubs, not final production code. They show the intended object shape and service boundaries for the Guest object.

## Current model alignment

Current persistence model: `CustomerProfile`.

Preferred domain vocabulary: `Guest`.

Short-term implementation should wrap `CustomerProfile` with Guest services and serializers instead of forcing a risky model rename immediately.

## Domain enums

```python
class GuestSegment(models.TextChoices):
    NEW = "new", "New"
    AVERAGE = "average", "Average"
    REPEAT = "repeat", "Repeat"
    VIP = "vip", "VIP"
    BLACKLISTED = "blacklisted", "Blacklisted"


class GuestStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLOCKED = "blocked", "Blocked"
    ARCHIVED = "archived", "Archived"


class GuestSource(models.TextChoices):
    DIRECT_WEBSITE = "direct_website", "Direct Website"
    AIRBNB = "airbnb", "Airbnb"
    BOOKING_COM = "booking_com", "Booking.com"
    VRBO = "vrbo", "Vrbo"
    CORPORATE_BOOKING = "corporate_booking", "Corporate Booking"
    MANUAL = "manual", "Manual"
    SOCIAL = "social", "Social"
    AGENT = "agent", "Agent"
```

## Guest aggregate wrapper

```python
class Guest:
    def __init__(self, customer_profile):
        self.profile = customer_profile

    @property
    def id(self):
        return self.profile.pk

    @property
    def display_name(self):
        return self.profile.name or self.profile.email or f"Guest {self.profile.pk}"

    @property
    def email(self):
        return self.profile.email

    @property
    def phone(self):
        return self.profile.phone

    @property
    def segment(self):
        return self.profile.segment

    @property
    def preferred_language(self):
        return self.profile.preferred_language

    @property
    def is_blocked(self):
        return self.profile.is_blacklisted

    @property
    def can_receive_promotions(self):
        return self.profile.can_receive_promotions

    def initials(self):
        parts = [part for part in self.display_name.split() if part]
        if not parts:
            return "G"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return f"{parts[0][0]}{parts[1][0]}".upper()

    def to_row_payload(self):
        return {
            "id": self.id,
            "display_name": self.display_name,
            "initials": self.initials(),
            "email": self.email,
            "phone": self.phone,
            "country": self._country_label(),
            "source": self.profile.source,
            "segment": self.segment,
            "marketing_consent_status": self.profile.marketing_consent_status,
            "preferred_language": self.preferred_language,
            "past_stays": self._past_stay_count(),
            "total_spend": self._total_spend_payload(),
            "last_contact_at": self._last_contact_at(),
        }

    def to_detail_payload(self):
        payload = self.to_row_payload()
        payload.update({
            "notes": self.profile.notes,
            "tags": self._tag_payload(),
            "preferences": self._preference_payload(),
            "messages": self._message_payload(),
            "stays": self._stay_payload(),
            "payments": self._payment_payload(),
            "deposits": self._deposit_payload(),
            "documents": self._document_payload(),
            "timeline": self._timeline_payload(),
            "admin": {
                "record_url": self._record_admin_url(),
            },
        })
        return payload
```

## Guest service boundary

```python
from django.db import transaction
from django.core.exceptions import ValidationError


class GuestService:
    @transaction.atomic
    def create_guest(self, payload, actor):
        normalized_email = (payload.get("email") or "").strip().lower()
        if not normalized_email and not payload.get("phone"):
            raise ValidationError("Guest requires at least email or phone.")
        profile = CustomerProfile.objects.create(
            name=payload.get("name", ""),
            email=normalized_email,
            phone=payload.get("phone", ""),
            segment=payload.get("segment", ClientSegment.AVERAGE),
            source=payload.get("source", ContactSource.DIRECT),
            preferred_language=payload.get("preferred_language", "en"),
            notes=payload.get("notes", ""),
        )
        self.emit_event("guest_created", profile, actor, {})
        return Guest(profile)

    @transaction.atomic
    def sync_from_reservation(self, inquiry, actor=None):
        profile = CustomerProfile.find_or_create_for_email(
            inquiry.email,
            defaults={
                "name": inquiry.guest_name,
                "phone": inquiry.phone,
                "source": ContactSource.DIRECT,
            },
        )
        if profile and inquiry.customer_profile_id != profile.pk:
            inquiry.customer_profile = profile
            inquiry.save(update_fields=["customer_profile", "updated_at"])
        self.emit_event("guest_synced_from_reservation", profile, actor, {"reservation_id": inquiry.pk})
        return Guest(profile)

    @transaction.atomic
    def merge_guests(self, primary_profile, duplicate_profile, actor):
        if primary_profile.pk == duplicate_profile.pk:
            raise ValidationError("Cannot merge a guest into itself.")
        BookingInquiry.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        CustomerFeedback.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        AirbnbGuestRecord.objects.filter(customer_profile=duplicate_profile).update(customer_profile=primary_profile)
        duplicate_profile.notes = f"Merged into guest #{primary_profile.pk}.\n\n" + duplicate_profile.notes
        duplicate_profile.save(update_fields=["notes", "updated_at"])
        self.emit_event("guest_merged", primary_profile, actor, {"duplicate_guest_id": duplicate_profile.pk})
        return Guest(primary_profile)

    def emit_event(self, event_type, profile, actor, metadata):
        # Delegate to GuestDataLakeService / GuestTimelineService.
        pass
```

## Long-term model target

When migration risk is low, `CustomerProfile` can be promoted to a formal `Guest` or `GuestProfile` model.

Do not rename casually. The transition must include:

- migration review
- admin compatibility
- URL compatibility
- old data verification
- reservation compatibility
- payment/deposit compatibility
- import compatibility
- data-lake compatibility
