# Backend Code Stubs

These are implementation stubs, not final production code. They show the intended object shape and service boundaries for the Reservation object.

## Current model alignment

Current persistence model: `BookingInquiry`.

Preferred domain vocabulary: `Reservation`.

Short-term implementation should wrap `BookingInquiry` with Reservation services and serializers instead of forcing a risky model rename immediately.

## Domain enums

```python
class ReservationStatus(models.TextChoices):
    NEW = "new", "New"
    REVIEWING = "reviewing", "Reviewing"
    QUOTED = "quoted", "Quoted"
    CONFIRMED = "confirmed", "Confirmed"
    HOLD = "hold", "Hold"
    COMPLETED = "completed", "Completed"
    CANCELED = "canceled", "Canceled"
    DECLINED = "declined", "Declined"


class ReservationChannel(models.TextChoices):
    DIRECT_WEBSITE = "direct_website", "Direct Website"
    AIRBNB = "airbnb", "Airbnb"
    MANUAL = "manual", "Manual"
    SOCIAL = "social", "Social"
    AGENT = "agent", "Agent"


class ReservationRiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
```

## Reservation aggregate wrapper

```python
class Reservation:
    def __init__(self, inquiry):
        self.inquiry = inquiry

    @property
    def id(self):
        return self.inquiry.pk

    @property
    def request_key(self):
        return self.inquiry.request_key

    @property
    def guest_name(self):
        return self.inquiry.guest_name

    @property
    def nights(self):
        return self.inquiry.nights

    @property
    def required_documents_accepted(self):
        return self.inquiry.required_documents_accepted

    @property
    def display_total(self):
        return self.inquiry.display_total

    @property
    def display_deposit(self):
        return self.inquiry.display_deposit

    @property
    def display_stay_payment(self):
        return self.inquiry.display_reservation_payment

    def can_cancel(self):
        return self.inquiry.can_customer_cancel

    def to_row_payload(self):
        return {
            "id": self.id,
            "request_key": self.request_key,
            "guest": self._guest_payload(),
            "stay": self._stay_payload(),
            "dates": self._date_payload(),
            "status": self._status_payload(),
            "deposit": self._deposit_payload(),
            "payment": self._payment_payload(),
            "risk": self._risk_payload(),
        }

    def to_detail_payload(self):
        payload = self.to_row_payload()
        payload.update({
            "messages": self._message_payload(),
            "documents": self._document_payload(),
            "timeline": self._timeline_payload(),
            "agent": self._agent_payload(),
            "admin": {
                "record_url": self._record_admin_url(),
                "notes": self.inquiry.admin_notes,
            },
        })
        return payload
```

## Reservation service boundary

```python
from django.db import transaction
from django.core.exceptions import ValidationError


class ReservationService:
    @transaction.atomic
    def transition_status(self, inquiry, next_status, actor, note=""):
        if next_status not in {"reviewing", "confirmed", "canceled", "declined"}:
            raise ValidationError({"status": "Unsupported reservation status."})
        previous = inquiry.status
        inquiry.status = next_status
        if next_status == "canceled":
            inquiry.cancel(reason=note, by_user=actor)
        else:
            inquiry.save(update_fields=["status", "updated_at"])
        self.emit_event("reservation_status_changed", inquiry, actor, {
            "old_status": previous,
            "new_status": next_status,
            "note": note,
        })
        return Reservation(inquiry)

    @transaction.atomic
    def record_document_acceptance(self, inquiry, document_type, version, actor=None):
        if document_type == "property_rules":
            inquiry.accepted_property_rules_version = version
            inquiry.property_rules_accepted_at = timezone.now()
            fields = ["accepted_property_rules_version", "property_rules_accepted_at", "updated_at"]
        elif document_type == "damage_terms":
            inquiry.accepted_damage_terms_version = version
            inquiry.damage_terms_accepted_at = timezone.now()
            fields = ["accepted_damage_terms_version", "damage_terms_accepted_at", "updated_at"]
        else:
            raise ValidationError({"document_type": "Unknown reservation document."})
        inquiry.save(update_fields=fields)
        self.emit_event("reservation_document_accepted", inquiry, actor, {
            "document_type": document_type,
            "version": version,
        })
        return Reservation(inquiry)

    def emit_event(self, event_type, inquiry, actor, metadata):
        # Delegate to ReservationDataLakeService / ReservationTimelineService.
        pass
```

## Long-term model target

When migration risk is low, `BookingInquiry` can be promoted to a formal `Reservation` model or replaced with a new aggregate model that preserves legacy references.

Do not rename casually. The transition must include:

- migration review
- admin compatibility
- URL compatibility
- old data verification
- reports compatibility
- payment/deposit compatibility
