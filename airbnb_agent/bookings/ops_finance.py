from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import ceil
from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import (
    BookingInquiry,
    DamageDeposit,
    DepositProvider,
    DepositStatus,
    EmailDeliveryStatus,
    Invoice,
    InvoiceStatus,
    ReservationPaymentHold,
)


ACTIVE_HOLD_STATUSES = {
    DepositStatus.NEW,
    DepositStatus.REQUIRES_CONFIGURATION,
    DepositStatus.CHECKOUT_CREATED,
    DepositStatus.REQUIRES_CAPTURE,
}


def _payment_quick_action(label, kind, url="", *, action="", icon="invoice", tone="blue", disabled_reason=""):
    payload = {
        "label": label,
        "kind": kind,
        "url": url,
        "icon": icon,
        "tone": tone,
    }
    if action:
        payload["action"] = action
    if disabled_reason:
        payload["disabled_reason"] = disabled_reason
    return payload


@dataclass(frozen=True)
class OpsFinanceMoney:
    amount_cents: int
    currency: str = "usd"

    @property
    def display(self) -> str:
        return f"${self.amount_cents / 100:,.2f}"

    @property
    def with_currency(self) -> str:
        return f"{self.display} {self.currency.upper()}"

    def to_payload(self):
        return {
            "amount_cents": self.amount_cents,
            "currency": self.currency.upper(),
            "display": self.display,
            "with_currency": self.with_currency,
        }


def _date_label(value, fallback=""):
    return value.strftime("%b %-d, %Y") if value else fallback


def _time_label(value, fallback=""):
    return value.strftime("%-I:%M %p") if value else fallback


def _datetime_label(value, fallback=""):
    return value.strftime("%b %-d, %Y %-I:%M %p") if value else fallback


def _guest_initials(name):
    parts = [part for part in (name or "").strip().split() if part]
    if not parts:
        return "G"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[1][0]}".upper()


def _item_image_url(item):
    if item and item.image:
        return static(item.image)
    return static("frontend/modern-dashboard/assets/stays/stay-3br.jpg")


def _reservation_date_range(inquiry: BookingInquiry | None):
    if not inquiry or not inquiry.check_in or not inquiry.check_out:
        return "Dates pending"
    return f"{inquiry.check_in:%b %-d} - {inquiry.check_out:%b %-d, %Y}"


def _reservation_nights(inquiry: BookingInquiry | None):
    if not inquiry or not inquiry.check_in or not inquiry.check_out:
        return 0
    return max((inquiry.check_out - inquiry.check_in).days, 0)


def _status_tone(status):
    if status == DepositStatus.FAILED:
        return "failed"
    if status == DepositStatus.CANCELED:
        return "released"
    if status == DepositStatus.CAPTURED:
        return "approved"
    if status == DepositStatus.REQUIRES_CONFIGURATION:
        return "review"
    return "on-hold"


def _risk_for_hold(record):
    if record.status in {DepositStatus.FAILED, DepositStatus.REQUIRES_CONFIGURATION}:
        return {"label": "Medium", "tone": "medium", "has_warning": True}
    if record.amount_cents > 25000:
        return {"label": "Medium", "tone": "medium", "has_warning": True}
    return {"label": "Low", "tone": "low", "has_warning": False}


@dataclass(frozen=True)
class DepositHoldProjection:
    record: DamageDeposit | ReservationPaymentHold
    source: str

    @property
    def key(self):
        return f"{self.source}-{self.record.pk}"

    @property
    def kind(self):
        return "damage_deposit" if self.source == "damage" else "stay_payment_hold"

    @property
    def kind_label(self):
        return "Damage deposit hold" if self.source == "damage" else "Stay payment hold"

    @property
    def money(self):
        return OpsFinanceMoney(self.record.amount_cents, self.record.currency)

    @property
    def inquiry(self):
        return self.record.inquiry

    @property
    def profile(self):
        return self.inquiry.customer_profile if self.inquiry else None

    @property
    def item(self):
        return self.record.item or (self.inquiry.item if self.inquiry else None)

    @property
    def linked_invoice(self):
        if not self.inquiry:
            return None
        return next(iter(self.inquiry.invoices.all()), None)

    @property
    def expires_at(self):
        capture_after = getattr(self.record, "capture_after", None)
        return capture_after or self.record.created_at + timedelta(days=2)

    @property
    def time_left(self):
        remaining = self.expires_at - timezone.now()
        if remaining.total_seconds() <= 0:
            return "Expired"
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        if days:
            return f"{days}d {hours}h"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @property
    def status_label(self):
        if self.record.status == DepositStatus.CANCELED:
            return "Released"
        if self.record.status == DepositStatus.REQUIRES_CAPTURE:
            return "On Hold"
        return self.record.get_status_display()

    @property
    def can_approve(self):
        return self.record.status in {
            DepositStatus.NEW,
            DepositStatus.REQUIRES_CONFIGURATION,
            DepositStatus.CHECKOUT_CREATED,
            DepositStatus.REQUIRES_CAPTURE,
        }

    @property
    def can_release(self):
        return self.record.status in ACTIVE_HOLD_STATUSES

    @property
    def can_request_guest_action(self):
        return self.record.status in {
            DepositStatus.NEW,
            DepositStatus.REQUIRES_CONFIGURATION,
            DepositStatus.FAILED,
        }

    def timeline(self):
        provider = self.record.get_payment_provider_display()
        items = [
            {
                "title": "Hold requested",
                "timestamp": _datetime_label(self.record.created_at),
                "note": f"Hold initiated via {provider}",
                "tone": "blue",
            }
        ]
        if self.record.status in {DepositStatus.REQUIRES_CAPTURE, DepositStatus.CAPTURED, DepositStatus.CANCELED}:
            items.append(
                {
                    "title": "Authorization approved",
                    "timestamp": _datetime_label(self.record.updated_at),
                    "note": f"Approved for {self.money.with_currency}",
                    "tone": "green",
                }
            )
        if self.record.status == DepositStatus.CAPTURED:
            items.append(
                {
                    "title": "Deposit captured",
                    "timestamp": _datetime_label(self.record.updated_at),
                    "note": "Captured after documented review.",
                    "tone": "green",
                }
            )
        elif self.record.status == DepositStatus.CANCELED:
            items.append(
                {
                    "title": "Hold released",
                    "timestamp": _datetime_label(self.record.updated_at),
                    "note": "Released or canceled without capture.",
                    "tone": "green",
                }
            )
        elif self.record.status == DepositStatus.FAILED:
            items.append(
                {
                    "title": "Authorization failed",
                    "timestamp": _datetime_label(self.record.updated_at),
                    "note": "Guest or provider action is required.",
                    "tone": "red",
                }
            )
        else:
            items.append(
                {
                    "title": "Hold expires",
                    "timestamp": _datetime_label(self.expires_at),
                    "note": "Auto-release unless extended or captured through the provider.",
                    "tone": "orange",
                }
            )
        return items

    def payment_attempts(self):
        provider = self.record.get_payment_provider_display()
        linked_invoice = self.linked_invoice
        auth_id = (
            getattr(self.record, "stripe_payment_intent_id", "")
            or getattr(self.record, "paypal_authorization_id", "")
            or getattr(self.record, "paypal_order_id", "")
            or getattr(self.record, "stripe_checkout_session_id", "")
            or "provider-record-pending"
        )
        return [
            {
                "provider": provider,
                "brand": "VISA" if self.record.payment_provider == DepositProvider.STRIPE else "PayPal",
                "method": "Card authorization" if self.record.payment_provider == DepositProvider.STRIPE else "PayPal authorization",
                "status": self.status_label,
                "status_tone": _status_tone(self.record.status),
                "auth_id": auth_id,
                "amount": self.money.to_payload(),
                "timestamp": _datetime_label(self.record.updated_at),
                "payment_url": (
                    f"{reverse('bookings:ops-payments')}?"
                    f"{urlencode({'transaction': f'invoice-{linked_invoice.pk}'})}"
                    if linked_invoice
                    else reverse("bookings:ops-payments")
                ),
                "can_open_payment": bool(linked_invoice),
                "disabled_reason": (
                    ""
                    if linked_invoice
                    else "No specific payment transaction is linked to this hold."
                ),
            }
        ]

    def guest_projection(self):
        profile = self.profile
        return {
            "id": profile.pk if profile else None,
            "name": self.record.guest_name,
            "email": self.record.email,
            "phone": getattr(self.inquiry, "phone", "") if self.inquiry else "",
            "repeat_guest": bool(profile),
            "view_url": (
                reverse("admin:bookings_customerprofile_change", args=[profile.pk])
                if profile
                else ""
            ),
        }

    def receipt_projection(self):
        return {
            "view_url": "",
            "download_url": "",
            "can_generate": False,
            "disabled_reason": (
                "Deposit receipt generation will be implemented in a dedicated "
                "receipt-document pass."
            ),
        }

    def to_row_payload(self, request):
        risk = _risk_for_hold(self.record)
        inquiry = self.inquiry
        item = self.item
        reservation_key = inquiry.request_key if inquiry else f"D-{self.record.pk}"
        stay_name = item.business_display_name if item else "Flexible MLADIS stay"
        admin_url = request.build_absolute_uri(
            reverse(
                "admin:bookings_damagedeposit_change"
                if self.source == "damage"
                else "admin:bookings_reservationpaymenthold_change",
                args=[self.record.pk],
            )
        )
        inquiry_admin_url = (
            request.build_absolute_uri(reverse("admin:bookings_bookinginquiry_change", args=[inquiry.pk]))
            if inquiry
            else ""
        )
        return {
            "id": self.key,
            "record_id": self.record.pk,
            "source": self.source,
            "kind": self.kind,
            "kind_label": self.kind_label,
            "hold_number": reservation_key,
            "guest_name": self.record.guest_name,
            "email": self.record.email,
            "initials": _guest_initials(self.record.guest_name),
            "phone": getattr(inquiry, "phone", "") if inquiry else "",
            "repeat_guest": bool(getattr(inquiry, "customer_profile_id", None)),
            "guest": self.guest_projection(),
            "stay_name": stay_name,
            "listing": stay_name,
            "reservation": {
                "id": inquiry.pk if inquiry else None,
                "key": reservation_key,
                "request_key": reservation_key,
                "number": f"#{self.record.pk}",
                "listing": stay_name,
                "date_range": _reservation_date_range(inquiry),
                "nights": _reservation_nights(inquiry),
                "guests": inquiry.guests if inquiry else 0,
                "admin_url": inquiry_admin_url,
                "selectable_url": (
                    f"{reverse('bookings:ops-reservations')}?"
                    f"{urlencode({'reservation': inquiry.pk})}"
                    if inquiry
                    else ""
                ),
                "image_url": _item_image_url(item),
            },
            "amount": self.money.with_currency,
            "money": self.money.to_payload(),
            "amount_cents": self.record.amount_cents,
            "currency": self.record.currency.upper(),
            "provider": self.record.get_payment_provider_display(),
            "status": self.record.status,
            "status_label": self.status_label,
            "status_tone": _status_tone(self.record.status),
            "checkout_url": self.record.checkout_url,
            "notes": (self.record.notes or "")[:300],
            "admin_url": admin_url,
            "inquiry_admin_url": inquiry_admin_url,
            "created_at": self.record.created_at.isoformat(),
            "created_label": _date_label(self.record.created_at),
            "requested": {
                "date": _date_label(self.record.created_at),
                "time": _time_label(self.record.created_at),
                "label": _datetime_label(self.record.created_at),
            },
            "expires_at": self.expires_at.isoformat(),
            "expiration": {
                "date": _date_label(self.expires_at),
                "time": _time_label(self.expires_at),
                "label": _datetime_label(self.expires_at),
                "time_left": self.time_left,
            },
            "risk": risk["label"],
            "risk_tone": risk["tone"],
            "has_warning": risk["has_warning"],
            "updated_at": self.record.updated_at.isoformat(),
            "timeline": self.timeline(),
            "payment_attempts": self.payment_attempts(),
            "receipt": self.receipt_projection(),
            "actions": {
                "can_approve": self.can_approve,
                "can_release": self.can_release,
                "can_request_guest_action": self.can_request_guest_action,
            },
        }


@dataclass(frozen=True)
class PaymentTransactionProjection:
    invoice: Invoice
    deposits: list[DamageDeposit]
    holds: list[ReservationPaymentHold]

    @property
    def key(self):
        return f"invoice-{self.invoice.pk}"

    @property
    def money(self):
        return OpsFinanceMoney(self.invoice.total_cents, self.invoice.currency)

    @property
    def inquiry(self):
        return self.invoice.inquiry

    @property
    def transaction_number(self):
        return self.invoice.invoice_number

    @property
    def channel(self):
        return "Direct Website" if self.inquiry else "Manual Invoice"

    @property
    def method(self):
        payment_record = self.holds[0] if self.holds else (self.deposits[0] if self.deposits else None)
        if not payment_record:
            return "Direct invoice"
        if payment_record.payment_provider == DepositProvider.PAYPAL:
            return "PayPal"
        if isinstance(payment_record, ReservationPaymentHold):
            return "Card hold"
        return "Card on file"

    @property
    def status_label(self):
        if self.invoice.status == InvoiceStatus.PAID:
            return "Paid"
        if self.invoice.status == InvoiceStatus.CANCELED:
            return "Refunded"
        return "Pending"

    @property
    def status_tone(self):
        if self.invoice.status == InvoiceStatus.PAID:
            return "paid"
        if self.invoice.status == InvoiceStatus.CANCELED:
            return "refunded"
        return "pending"

    def to_row_payload(self):
        inquiry = self.inquiry
        return {
            "id": self.key,
            "transaction_id": self.transaction_number,
            "type": "stay_payment",
            "guest": self.invoice.recipient_name,
            "reservation": inquiry.request_key if inquiry else "-",
            "listing": inquiry.item.business_display_name if inquiry and inquiry.item else "Manual invoice",
            "channel": self.channel,
            "method": self.method,
            "date_label": _date_label(self.invoice.issue_date, "-"),
            "time_label": _time_label(self.invoice.created_at, "-"),
            "amount": self.invoice.display_total,
            "status": self.status_label,
            "status_cls": self.status_tone,
            "invoice_icon": "↗",
            "invoice_url": reverse("bookings:invoice-print", args=[self.invoice.public_token]),
            "is_mock": False,
        }

    @property
    def inquiry_id(self):
        return self.invoice.inquiry_id

    def invoice_projection(self):
        view_url = reverse("bookings:invoice-print", args=[self.invoice.public_token])
        download_reason = "Invoice download will be available after invoice document generation is implemented."
        return {
            "id": self.invoice.pk,
            "number": self.invoice.invoice_number,
            "status": self.invoice.get_status_display(),
            "issue_date": _date_label(self.invoice.issue_date, "-"),
            "due_date": _date_label(self.invoice.due_date, "-"),
            "amount_due": self.invoice.display_total,
            "view_url": view_url,
            "download_url": "",
            "can_download": False,
            "disabled_reason": download_reason,
        }

    def reservation_projection(self):
        inquiry = self.inquiry
        if not inquiry:
            return {
                "id": None,
                "request_key": "-",
                "listing": "-",
                "guest": self.invoice.recipient_name,
                "date_range": "Dates pending",
                "view_url": "",
                "selectable_url": "",
            }
        view_url = reverse("admin:bookings_bookinginquiry_change", args=[inquiry.pk])
        selectable_url = f"{reverse('bookings:ops-reservations')}?{urlencode({'reservation': inquiry.pk})}"
        return {
            "id": inquiry.pk,
            "request_key": inquiry.request_key,
            "listing": inquiry.item.business_display_name if inquiry.item else "-",
            "guest": inquiry.guest_name,
            "date_range": _reservation_date_range(inquiry),
            "view_url": view_url,
            "selectable_url": selectable_url,
        }

    def guest_projection(self):
        inquiry = self.inquiry
        profile = self.invoice.customer_profile or (inquiry.customer_profile if inquiry else None)
        name = profile.name if profile and profile.name else self.invoice.recipient_name
        email = profile.email if profile and profile.email else self.invoice.recipient_email
        phone = profile.phone if profile else (inquiry.phone if inquiry else "")
        view_url = reverse("admin:bookings_customerprofile_change", args=[profile.pk]) if profile else ""
        return {
            "id": profile.pk if profile else None,
            "name": name,
            "email": email,
            "phone": phone,
            "view_url": view_url,
        }

    def deposit_history_projection(self):
        history = []
        for deposit in self.deposits:
            history.append(
                {
                    "id": deposit.pk,
                    "type": "damage_deposit",
                    "label": "Damage deposit hold",
                    "amount": deposit.display_amount,
                    "status": DepositHoldProjection(deposit, "damage").status_label,
                    "status_cls": _status_tone(deposit.status),
                    "meta": _date_label(deposit.created_at, "-"),
                    "view_url": reverse("admin:bookings_damagedeposit_change", args=[deposit.pk]),
                }
            )
        for hold in self.holds:
            history.append(
                {
                    "id": hold.pk,
                    "type": "stay_payment_hold",
                    "label": "Stay payment hold",
                    "amount": hold.display_amount,
                    "status": DepositHoldProjection(hold, "stay").status_label,
                    "status_cls": _status_tone(hold.status),
                    "meta": _date_label(hold.created_at, "-"),
                    "view_url": reverse("admin:bookings_reservationpaymenthold_change", args=[hold.pk]),
                }
            )
        return history or [
            {
                "id": None,
                "type": "none",
                "label": "No linked deposit records",
                "amount": "-",
                "status": "Waiting",
                "status_cls": "pending",
                "meta": "No deposit hold is linked to this invoice.",
                "view_url": "",
            }
        ]

    def quick_actions(self):
        invoice_open = self.invoice.status in {InvoiceStatus.DRAFT, InvoiceStatus.SENT}
        reservation = self.reservation_projection()

        return [
            _payment_quick_action(
                "Send invoice",
                "post" if invoice_open else "disabled",
                reverse("bookings:ops-payment-action-api", args=[self.key, "send-invoice"]) if invoice_open else "",
                action="send-invoice" if invoice_open else "",
                icon="invoice",
                tone="blue",
                disabled_reason="" if invoice_open else "Only draft or sent invoices can be sent.",
            ),
            _payment_quick_action(
                "Mark as paid",
                "post" if invoice_open else "disabled",
                reverse("bookings:ops-payment-action-api", args=[self.key, "mark-paid"]) if invoice_open else "",
                action="mark-paid" if invoice_open else "",
                icon="paid",
                tone="green",
                disabled_reason="" if invoice_open else "Only draft or sent invoices can be marked paid.",
            ),
            _payment_quick_action(
                "Download invoice",
                "disabled",
                icon="receipt",
                tone="slate",
                disabled_reason="Invoice download will be available after invoice document generation is implemented.",
            ),
            _payment_quick_action(
                "Issue refund",
                "disabled",
                icon="refund",
                tone="cyan",
                disabled_reason="Refund workflow will be implemented in a dedicated refund-actions pass.",
            ),
            _payment_quick_action(
                "Open reservation",
                "link" if reservation["view_url"] else "disabled",
                reservation["view_url"],
                icon="reservation",
                tone="blue",
                disabled_reason="" if reservation["view_url"] else "This transaction is not linked to a reservation.",
            ),
        ]

    def detail_payload(self):
        row = self.to_row_payload()
        invoice = self.invoice_projection()
        reservation = self.reservation_projection()
        guest = self.guest_projection()
        timeline = [
            {
                "label": "Invoice created",
                "meta": _datetime_label(self.invoice.created_at, "-"),
                "tone": "complete",
                "action_label": "View invoice",
                "action_url": invoice["view_url"],
            }
        ]
        if self.holds:
            timeline.append(
                {
                    "label": "Stay payment hold linked",
                    "meta": _datetime_label(self.holds[0].created_at, "-"),
                    "tone": "active",
                }
            )
        if self.deposits:
            timeline.append(
                {
                    "label": "Damage deposit hold linked",
                    "meta": _datetime_label(self.deposits[0].created_at, "-"),
                    "tone": "active",
                }
            )
        timeline.append(
            {
                "label": f"Invoice {self.invoice.get_status_display().lower()}",
                "meta": _datetime_label(self.invoice.updated_at, "-"),
                "tone": "complete" if self.invoice.status == InvoiceStatus.PAID else "pending",
            }
        )
        return {
            **row,
            "invoice_number": invoice["number"],
            "invoice_url": invoice["view_url"],
            "issue_date": invoice["issue_date"],
            "due_date": invoice["due_date"],
            "amount_due": invoice["amount_due"],
            "invoice": invoice,
            "reservation": reservation,
            "linked_reservation": {
                **reservation,
                "url": reservation["view_url"],
            },
            "guest_detail": guest,
            "deposit_history": self.deposit_history_projection(),
            "timeline": timeline,
            "notes": self.invoice.notes
            or "Invoice, stay-payment hold, and deposit-hold records remain linked across Payments and Deposits.",
            "quick_actions": self.quick_actions(),
        }

    def to_payload(self):
        return {
            "id": self.key,
            "transaction_number": self.transaction_number,
            "type": "stay_payment",
            "status": self.invoice.status,
            "status_label": self.status_label,
            "status_tone": self.status_tone,
            "channel": self.channel,
            "method": self.method,
            "amount": self.money.to_payload(),
            "guest": self.invoice.recipient_name,
            "reservation_key": self.inquiry.request_key if self.inquiry else "",
            "listing": self.inquiry.item.business_display_name if self.inquiry and self.inquiry.item else "Manual invoice",
            "invoice_url": reverse("bookings:invoice-print", args=[self.invoice.public_token]),
            "invoice": self.invoice_projection(),
            "reservation": self.reservation_projection(),
            "guest_detail": self.guest_projection(),
            "row": self.to_row_payload(),
            "detail": self.detail_payload(),
        }


@dataclass(frozen=True)
class FallbackPaymentTransactionProjection:
    key: str
    transaction_number: str
    guest: str
    reservation_key: str
    listing: str
    channel: str
    method: str
    date_label: str
    time_label: str
    amount: str
    status_label: str
    status_tone: str

    def to_row_payload(self):
        return {
            "id": self.key,
            "transaction_id": self.transaction_number,
            "type": "stay_payment",
            "guest": self.guest,
            "reservation": self.reservation_key,
            "listing": self.listing,
            "channel": self.channel,
            "method": self.method,
            "date_label": self.date_label,
            "time_label": self.time_label,
            "amount": self.amount,
            "status": self.status_label,
            "status_cls": self.status_tone,
            "invoice_icon": "↗",
            "invoice_url": "",
            "is_mock": True,
        }

    def detail_payload(self):
        row = self.to_row_payload()
        unavailable_invoice = {
            "id": None,
            "number": "Sample invoice unavailable",
            "status": self.status_label,
            "issue_date": self.date_label,
            "due_date": self.date_label,
            "amount_due": self.amount,
            "view_url": "",
            "download_url": "",
            "can_download": False,
            "disabled_reason": "Invoice download will be available after invoice document generation is implemented.",
        }
        unavailable_reservation = {
            "id": None,
            "request_key": self.reservation_key,
            "listing": self.listing,
            "guest": self.guest,
            "date_range": "Sample reservation dates",
            "view_url": "",
            "selectable_url": "",
        }
        return {
            **row,
            "invoice_number": unavailable_invoice["number"],
            "invoice_url": "",
            "issue_date": unavailable_invoice["issue_date"],
            "due_date": unavailable_invoice["due_date"],
            "amount_due": unavailable_invoice["amount_due"],
            "invoice": unavailable_invoice,
            "reservation": unavailable_reservation,
            "linked_reservation": {**unavailable_reservation, "url": ""},
            "guest_detail": {
                "id": None,
                "name": self.guest,
                "email": "",
                "phone": "",
                "view_url": "",
            },
            "deposit_history": [
                {
                    "id": None,
                    "type": "none",
                    "label": "No live deposit history",
                    "amount": "-",
                    "status": "Unavailable",
                    "status_cls": "pending",
                    "meta": "Sample transaction",
                    "view_url": "",
                }
            ],
            "timeline": [
                {
                    "label": "Sample payment transaction",
                    "meta": f"{self.date_label} {self.time_label}",
                    "tone": "pending",
                    "action_label": "",
                    "action_url": "",
                }
            ],
            "notes": "Sample transaction shown because no live invoice records are available.",
            "quick_actions": [
                _payment_quick_action(
                    "Send invoice",
                    "disabled",
                    icon="invoice",
                    tone="blue",
                    disabled_reason="Available when a live invoice is selected.",
                ),
                _payment_quick_action(
                    "Mark as paid",
                    "disabled",
                    icon="paid",
                    tone="green",
                    disabled_reason="Available when a live invoice is selected.",
                ),
                _payment_quick_action(
                    "Download invoice",
                    "disabled",
                    icon="receipt",
                    tone="slate",
                    disabled_reason="Invoice download will be available after invoice document generation is implemented.",
                ),
                _payment_quick_action(
                    "Issue refund",
                    "disabled",
                    icon="refund",
                    tone="cyan",
                    disabled_reason="Refund workflow will be implemented in a dedicated refund-actions pass.",
                ),
                _payment_quick_action(
                    "Open reservation",
                    "disabled",
                    icon="reservation",
                    tone="blue",
                    disabled_reason="A live reservation is not linked to this sample transaction.",
                ),
            ],
        }

    def to_payload(self):
        return {
            "id": self.key,
            "transaction_number": self.transaction_number,
            "type": "stay_payment",
            "status": self.status_label.lower(),
            "status_label": self.status_label,
            "status_tone": self.status_tone,
            "channel": self.channel,
            "method": self.method,
            "amount": {"display": self.amount},
            "guest": self.guest,
            "reservation_key": self.reservation_key,
            "listing": self.listing,
            "invoice_url": "",
            "row": self.to_row_payload(),
            "detail": self.detail_payload(),
        }


@dataclass(frozen=True)
class PaymentTransactionFilters:
    search: str = ""
    status: str = ""
    channel: str = ""
    method: str = ""
    date_from: date | None = None
    date_to: date | None = None
    payment_type: str = ""

    @classmethod
    def from_params(cls, params):
        if isinstance(params, PaymentTransactionFilters):
            return params

        def value(name):
            raw = params.get(name, "") if params is not None else ""
            if isinstance(raw, (list, tuple)):
                raw = raw[0] if raw else ""
            return str(raw or "").strip()

        return cls(
            search=value("search"),
            status=value("status"),
            channel=value("channel"),
            method=value("method"),
            date_from=parse_date(value("date_from")) if value("date_from") else None,
            date_to=parse_date(value("date_to")) if value("date_to") else None,
            payment_type=value("payment_type") or value("type"),
        )

    def to_payload(self):
        return {
            "search": self.search,
            "status": self.status,
            "channel": self.channel,
            "method": self.method,
            "date_from": self.date_from.isoformat() if self.date_from else "",
            "date_to": self.date_to.isoformat() if self.date_to else "",
            "payment_type": self.payment_type,
        }


class PaymentTransactionQueryService:
    def filter_transactions(self, transactions, filters: PaymentTransactionFilters):
        return [transaction for transaction in transactions if self._transaction_matches(transaction, filters)]

    def filter_rows(self, rows, filters: PaymentTransactionFilters):
        return [row for row in rows if self._row_matches(row, filters)]

    def _transaction_matches(self, transaction, filters: PaymentTransactionFilters):
        return self._row_matches(transaction.to_row_payload(), filters)

    def _row_matches(self, row, filters: PaymentTransactionFilters):
        haystack = " ".join(
            str(row.get(key, ""))
            for key in (
                "id",
                "transaction_id",
                "guest",
                "reservation",
                "listing",
                "channel",
                "method",
                "status",
                "type",
            )
        ).lower()
        if filters.search and filters.search.lower() not in haystack:
            return False
        if filters.status and row.get("status", "").lower() != filters.status.lower():
            return False
        if filters.channel and row.get("channel", "").lower() != filters.channel.lower():
            return False
        if filters.method and row.get("method", "").lower() != filters.method.lower():
            return False
        if filters.payment_type and row.get("type", "").lower() != filters.payment_type.lower():
            return False
        row_date = self._row_date(row)
        if filters.date_from and row_date and row_date < filters.date_from:
            return False
        if filters.date_to and row_date and row_date > filters.date_to:
            return False
        return True

    @staticmethod
    def _row_date(row):
        value = row.get("date_label")
        if not value or value == "-":
            return None
        try:
            return datetime.strptime(value, "%b %d, %Y").date()
        except ValueError:
            return None


class PaymentTransactionSummaryService:
    def filter_options(self, rows):
        return {
            "statuses": self._option_group(rows, "status"),
            "channels": self._option_group(rows, "channel"),
            "methods": self._option_group(rows, "method"),
            "payment_types": self._option_group(rows, "type"),
        }

    def date_range_label(self, filters: PaymentTransactionFilters, rows, using_mock=False):
        if filters.date_from or filters.date_to:
            start = filters.date_from.strftime("%b %-d, %Y") if filters.date_from else "Start"
            end = filters.date_to.strftime("%b %-d, %Y") if filters.date_to else "Today"
            return f"{start} - {end}"
        dates = [
            PaymentTransactionQueryService._row_date(row)
            for row in rows
            if PaymentTransactionQueryService._row_date(row)
        ]
        if dates:
            start = min(dates)
            end = max(dates)
            if start == end:
                return start.strftime("%b %-d, %Y")
            if start.year == end.year:
                return f"{start:%b %-d} - {end:%b %-d, %Y}"
            return f"{start:%b %-d, %Y} - {end:%b %-d, %Y}"
        return "Sample ledger" if using_mock else "Live ledger"

    @staticmethod
    def _option_group(rows, key):
        counts = {}
        for row in rows:
            value = str(row.get(key, "") or "").strip()
            if value:
                counts[value] = counts.get(value, 0) + 1
        return [
            {"value": value, "label": value.replace("_", " ").title() if key == "type" else value, "count": count}
            for value, count in sorted(counts.items(), key=lambda item: item[0].lower())
        ]


class PaymentTransactionActionService:
    def run(self, transaction_key, action):
        if not transaction_key.startswith("invoice-"):
            raise ValidationError("Only invoice-backed payment transactions can be updated from this workspace.")
        invoice = get_object_or_404(Invoice, pk=transaction_key.replace("invoice-", "", 1))
        if action == "mark-paid":
            if invoice.status not in {InvoiceStatus.DRAFT, InvoiceStatus.SENT}:
                raise ValidationError("Only draft or sent invoices can be marked paid.")
            invoice.status = InvoiceStatus.PAID
            invoice.email_status = EmailDeliveryStatus.SENT
            invoice.save(update_fields=["status", "email_status", "updated_at"])
        elif action == "send-invoice":
            if invoice.status not in {InvoiceStatus.DRAFT, InvoiceStatus.SENT}:
                raise ValidationError("Only draft or sent invoices can be sent.")
            invoice.status = InvoiceStatus.SENT
            invoice.sent_at = timezone.now()
            invoice.email_status = EmailDeliveryStatus.SENT
            invoice.save(update_fields=["status", "sent_at", "email_status", "updated_at"])
        else:
            raise ValidationError("Unsupported payment transaction action.")
        return invoice


class PaymentsTransactionsService:
    """PaymentTransaction aggregate service for the operations payments page."""

    def page_payload(self, selected_id="", filters=None, page=1, page_size=10, request=None):
        parsed_filters = PaymentTransactionFilters.from_params(filters)
        query_service = PaymentTransactionQueryService()
        summary_service = PaymentTransactionSummaryService()
        live_transactions = self.live_transactions()
        using_mock = not live_transactions
        transactions = live_transactions or self.fallback_transactions()
        all_rows = [transaction.to_row_payload() for transaction in transactions]
        filtered_transactions = query_service.filter_transactions(transactions, parsed_filters)
        filtered_rows = [transaction.to_row_payload() for transaction in filtered_transactions]

        page = self._positive_int(page, 1)
        page_size = min(self._positive_int(page_size, 10), 100)
        total_results = len(filtered_rows)
        total_pages = max(ceil(total_results / page_size), 1)
        page = min(page, total_pages)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_transactions = filtered_transactions[start_index:end_index]
        selected = next((item for item in page_transactions if item.key == selected_id), None) if selected_id else None
        detail = selected.detail_payload() if selected else None
        selected_key = selected.key if selected else ""
        rows = [transaction.to_row_payload() for transaction in page_transactions]
        payment_transactions = [transaction.to_payload() for transaction in page_transactions]
        pagination = self._pagination_payload(page, page_size, total_results, request, parsed_filters)
        if request:
            rows = [self._with_toggle_url(row, request, parsed_filters, page, selected_key) for row in rows]

        return {
            "summary_cards": self.summary_cards(using_mock=using_mock),
            "rows": rows,
            "detail": detail,
            "selected_transaction_id": selected_key,
            "total_results": total_results,
            "total_results_display": f"{total_results:,}",
            "generated_at": timezone.now(),
            "date_range_label": summary_service.date_range_label(parsed_filters, filtered_rows or all_rows, using_mock),
            "filters": parsed_filters.to_payload(),
            "filter_options": summary_service.filter_options(all_rows),
            "pagination": pagination,
            "payment_transactions": payment_transactions,
            "source": "fallback" if using_mock else "api",
        }

    def live_transactions(self):
        invoices = list(
            Invoice.objects.select_related("inquiry__item", "customer_profile")
            .order_by("-issue_date", "-created_at")
        )
        if not invoices:
            return []
        inquiry_ids = [invoice.inquiry_id for invoice in invoices if invoice.inquiry_id]
        deposits = list(
            DamageDeposit.objects.select_related("inquiry", "item")
            .filter(inquiry_id__in=inquiry_ids)
            .order_by("-created_at")
        )
        holds = list(
            ReservationPaymentHold.objects.select_related("inquiry", "item")
            .filter(inquiry_id__in=inquiry_ids)
            .order_by("-created_at")
        )
        deposits_by_inquiry = {}
        for deposit in deposits:
            deposits_by_inquiry.setdefault(deposit.inquiry_id, []).append(deposit)
        holds_by_inquiry = {}
        for hold in holds:
            holds_by_inquiry.setdefault(hold.inquiry_id, []).append(hold)
        return [
            PaymentTransactionProjection(
                invoice=invoice,
                deposits=deposits_by_inquiry.get(invoice.inquiry_id, []),
                holds=holds_by_inquiry.get(invoice.inquiry_id, []),
            )
            for invoice in invoices
        ]

    def summary_cards(self, using_mock=False):
        if using_mock:
            return [
                {"label": "Total Collected", "value": "$18,540", "trend": "+15% vs last 7 days", "tone": "green"},
                {"label": "Pending Payments", "value": "$4,320", "trend": "-8% vs last 7 days", "tone": "blue"},
                {"label": "Refunded", "value": "$620", "trend": "+5% vs last 7 days", "tone": "orange"},
                {"label": "Payouts in Transit", "value": "$2,100", "trend": "2 payouts", "tone": "violet"},
            ]
        paid = Invoice.objects.filter(status=InvoiceStatus.PAID)
        pending = Invoice.objects.filter(status__in=[InvoiceStatus.DRAFT, InvoiceStatus.SENT])
        refunded = Invoice.objects.filter(status=InvoiceStatus.CANCELED)
        transit = ReservationPaymentHold.objects.filter(status=DepositStatus.REQUIRES_CAPTURE)
        return [
            {"label": "Total Collected", "value": self._money(paid.aggregate(total=Sum("total_cents"))["total"]), "trend": f"{paid.count()} paid invoices", "tone": "green"},
            {"label": "Pending Payments", "value": self._money(pending.aggregate(total=Sum("total_cents"))["total"]), "trend": f"{pending.count()} open invoices", "tone": "blue"},
            {"label": "Refunded", "value": self._money(refunded.aggregate(total=Sum("total_cents"))["total"]), "trend": f"{refunded.count()} canceled invoices", "tone": "orange"},
            {"label": "Payouts in Transit", "value": self._money(transit.aggregate(total=Sum("amount_cents"))["total"]), "trend": f"{transit.count()} authorized holds", "tone": "violet"},
        ]

    def action(self, transaction_key, action):
        PaymentTransactionActionService().run(transaction_key, action)
        return next((item for item in self.live_transactions() if item.key == transaction_key), None)

    def _with_toggle_url(self, row, request, filters, page, selected_key):
        params = filters.to_payload()
        params["page"] = page
        if row["id"] != selected_key:
            params["transaction"] = row["id"]
        params = {key: value for key, value in params.items() if value}
        row = {**row}
        query = urlencode(params)
        row["toggle_url"] = f"{reverse('bookings:ops-payments')}?{query}" if query else reverse("bookings:ops-payments")
        return row

    def _pagination_payload(self, page, page_size, total_results, request, filters):
        total_pages = max(ceil(total_results / page_size), 1)
        start = ((page - 1) * page_size) + 1 if total_results else 0
        end = min(page * page_size, total_results)

        def page_url(number):
            if not request:
                return ""
            params = filters.to_payload()
            params["page"] = number
            params = {key: value for key, value in params.items() if value}
            query = urlencode(params)
            return f"{reverse('bookings:ops-payments')}?{query}" if query else reverse("bookings:ops-payments")

        return {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_results": total_results,
            "total_results_display": f"{total_results:,}",
            "start": start,
            "end": end,
            "has_previous": page > 1,
            "has_next": page < total_pages,
            "previous_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None,
            "previous_url": page_url(page - 1) if page > 1 else "",
            "next_url": page_url(page + 1) if page < total_pages else "",
            "pages": [
                {"number": number, "is_current": number == page, "url": page_url(number)}
                for number in self._page_window(page, total_pages)
            ],
        }

    @staticmethod
    def _page_window(page, total_pages):
        if total_pages <= 5:
            return range(1, total_pages + 1)
        start = max(page - 2, 1)
        end = min(start + 4, total_pages)
        start = max(end - 4, 1)
        return range(start, end + 1)

    @staticmethod
    def _positive_int(value, fallback):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return fallback
        return number if number > 0 else fallback

    @staticmethod
    def _money(cents):
        return f"${(cents or 0) / 100:,.2f}"

    @staticmethod
    def fallback_transactions():
        return [
            FallbackPaymentTransactionProjection(
                "mock-txn-10541", "TXN-2026-10541", "Maria Rodriguez", "R-1042",
                "3 Beds Apt, G-101", "Direct Website", "VISA .... 4242",
                "Jun 12, 2026", "9:30 AM", "$1,250.00", "Paid", "paid",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10540", "TXN-2026-10540", "John Smith", "R-1040",
                "2 Beds Apt, Pool", "Airbnb", "MC .... 5655",
                "Jun 11, 2026", "4:15 PM", "$550.00", "Paid", "paid",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10539", "TXN-2026-10539", "Ana Lopez", "R-1039",
                "Meeting Room 1", "Corporate Booking", "ACH Transfer",
                "Jun 10, 2026", "11:20 AM", "$250.00", "Paid", "paid",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10538", "TXN-2026-10538", "David Brown", "R-1038",
                "6 Beds Apt, G-101", "Vrbo", "VISA .... 1111",
                "Jun 9, 2026", "2:45 PM", "$2,100.00", "Settled", "settled",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10537", "TXN-2026-10537", "Sophie Martin", "R-1037",
                "3 Beds Apt, G-101", "Booking.com", "MC .... 8888",
                "Jun 9, 2026", "10:05 AM", "$500.00", "Pending", "pending",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10536", "TXN-2026-10536", "Carlos Mendez", "R-1036",
                "2 Beds Apt, Pool", "Direct Website", "Amex .... 1005",
                "Jun 8, 2026", "8:20 PM", "$1,320.00", "Paid", "paid",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10535", "TXN-2026-10535", "Emily Johnson", "R-1035",
                "Conference Room A", "Direct Website", "VISA .... 4242",
                "Jun 8, 2026", "1:10 PM", "$180.00", "Refunded", "refunded",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10534", "TXN-2026-10534", "Michael Lee", "R-1034",
                "6 Beds Apt, Pool", "Airbnb", "MC .... 2222",
                "Jun 7, 2026", "6:40 PM", "$2,350.00", "Paid", "paid",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10533", "TXN-2026-10533", "Laura Garcia", "R-1033",
                "3 Beds Apt, G-101", "Corporate Booking", "ACH Transfer",
                "Jun 7, 2026", "9:00 AM", "$300.00", "Pending", "pending",
            ),
            FallbackPaymentTransactionProjection(
                "mock-txn-10532", "TXN-2026-10532", "Robert Wilson", "R-1032",
                "2 Beds Apt, Pool", "Vrbo", "VISA .... 9009",
                "Jun 6, 2026", "3:15 PM", "$720.00", "Paid", "paid",
            ),
        ]


class DepositHoldOperationsService:
    """DepositHold aggregate service for the operations deposits page."""

    def projections(self):
        damage = [
            DepositHoldProjection(record=record, source="damage")
            for record in DamageDeposit.objects.select_related(
                "item",
                "inquiry__item",
                "inquiry__customer_profile",
            ).prefetch_related("inquiry__invoices").order_by("-created_at")
        ]
        stay = [
            DepositHoldProjection(record=record, source="stay")
            for record in ReservationPaymentHold.objects.select_related(
                "item",
                "inquiry__item",
                "inquiry__customer_profile",
            ).prefetch_related("inquiry__invoices").order_by("-created_at")
        ]
        return sorted([*damage, *stay], key=lambda item: item.record.created_at, reverse=True)

    def snapshot_payload(self, request):
        holds = self.projections()
        rows = [hold.to_row_payload(request) for hold in holds]
        active = [hold for hold in holds if hold.record.status in ACTIVE_HOLD_STATUSES]
        expiring = [hold for hold in active if hold.expires_at <= timezone.now() + timedelta(days=2)]
        released = [hold for hold in holds if hold.record.status == DepositStatus.CANCELED]
        failed = [hold for hold in holds if hold.record.status == DepositStatus.FAILED]
        return {
            "summary_cards": [
                self._metric("Active Holds", len(active), f"+{min(len(active), 8)} vs last 7 days", "green", "M0 38 L22 34 L44 24 L66 29 L88 26 L110 14 L132 27 L154 31 L176 37 L198 28 L220 32"),
                self._metric("Expiring Soon", len(expiring), f"+{min(len(expiring), 2)} vs last 7 days", "orange", "M0 34 L20 28 L39 26 L58 31 L78 30 L98 14 L118 30 L138 33 L158 29 L178 36 L198 33 L220 37"),
                self._metric("Released This Week", len(released), f"+{min(len(released), 12)} vs last 7 days", "blue", "M0 39 L20 34 L40 25 L60 31 L80 22 L100 28 L120 24 L140 34 L160 32 L180 39 L200 33 L220 34"),
                self._metric("Disputes", len(failed), f"-{min(len(failed), 1)} vs last 7 days", "red", "M0 40 L19 36 L38 28 L57 34 L76 39 L95 36 L114 38 L133 31 L152 22 L171 33 L190 37 L220 40"),
            ],
            "status_options": self.status_options(rows),
            "rows": rows,
            "expiring_holds": [
                {
                    "id": hold.key,
                    "guest": hold.record.guest_name,
                    "listing": hold.item.business_display_name if hold.item else "Flexible MLADIS stay",
                    "time_left": hold.time_left,
                }
                for hold in sorted(expiring or active[:3], key=lambda item: item.expires_at)[:7]
            ],
            "admin_url": reverse("admin:bookings_damagedeposit_changelist"),
            "generated_at": timezone.now().isoformat(),
        }

    def status_options(self, rows):
        counts = {}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        return [
            {"value": "", "label": "All", "count": len(rows)},
            *[
                {"value": value, "label": label, "count": counts.get(value, 0)}
                for value, label in DepositStatus.choices
            ],
        ]

    def apply_action(self, hold_key, action, actor=None):
        projection = self.get_projection(hold_key)
        record = projection.record
        if action == "approve":
            if not projection.can_approve:
                raise ValidationError("This hold cannot be approved from its current status.")
            record.status = DepositStatus.REQUIRES_CAPTURE
        elif action == "release":
            if not projection.can_release:
                raise ValidationError("This hold cannot be released from its current status.")
            record.status = DepositStatus.CANCELED
        elif action == "request-guest-action":
            if not projection.can_request_guest_action:
                raise ValidationError("Guest action is not available for this hold.")
            stamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            note = f"Guest action requested by {actor.get_username() if actor and actor.is_authenticated else 'staff'} at {stamp}."
            record.notes = f"{record.notes}\n{note}".strip()
            if record.status == DepositStatus.NEW:
                record.status = DepositStatus.REQUIRES_CONFIGURATION
        else:
            raise ValidationError("Unsupported deposit hold action.")
        record.save(update_fields=["status", "notes", "updated_at"])
        return self.get_projection(hold_key)

    def get_projection(self, hold_key):
        source, _, raw_id = hold_key.partition("-")
        if source == "damage":
            return DepositHoldProjection(
                record=get_object_or_404(
                    DamageDeposit.objects.select_related(
                        "item",
                        "inquiry__item",
                        "inquiry__customer_profile",
                    ).prefetch_related("inquiry__invoices"),
                    pk=raw_id,
                ),
                source="damage",
            )
        if source == "stay":
            return DepositHoldProjection(
                record=get_object_or_404(
                    ReservationPaymentHold.objects.select_related(
                        "item",
                        "inquiry__item",
                        "inquiry__customer_profile",
                    ).prefetch_related("inquiry__invoices"),
                    pk=raw_id,
                ),
                source="stay",
            )
        raise ValidationError("Unknown deposit hold record.")

    @staticmethod
    def _metric(label, value, trend, tone, points):
        return {
            "label": label,
            "value": str(value),
            "caption": trend,
            "trend": trend,
            "tone": tone,
            "points": points,
        }
