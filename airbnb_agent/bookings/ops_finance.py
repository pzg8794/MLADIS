from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone

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
    def item(self):
        return self.record.item or (self.inquiry.item if self.inquiry else None)

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
            }
        ]

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
            "stay_name": stay_name,
            "listing": stay_name,
            "reservation": {
                "key": reservation_key,
                "number": f"#{self.record.pk}",
                "listing": stay_name,
                "date_range": _reservation_date_range(inquiry),
                "nights": _reservation_nights(inquiry),
                "guests": inquiry.guests if inquiry else 0,
                "admin_url": inquiry_admin_url,
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

    def detail_payload(self):
        row = self.to_row_payload()
        inquiry = self.inquiry
        deposit_history = []
        for deposit in self.deposits:
            deposit_history.append(
                {
                    "label": "Damage deposit hold",
                    "amount": deposit.display_amount,
                    "status": DepositHoldProjection(deposit, "damage").status_label,
                    "status_cls": _status_tone(deposit.status),
                    "meta": _date_label(deposit.created_at, "-"),
                }
            )
        for hold in self.holds:
            deposit_history.append(
                {
                    "label": "Stay payment hold",
                    "amount": hold.display_amount,
                    "status": DepositHoldProjection(hold, "stay").status_label,
                    "status_cls": _status_tone(hold.status),
                    "meta": _date_label(hold.created_at, "-"),
                }
            )
        timeline = [
            {
                "label": "Invoice created",
                "meta": _datetime_label(self.invoice.created_at, "-"),
                "tone": "complete",
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
            "invoice_number": self.invoice.invoice_number,
            "issue_date": _date_label(self.invoice.issue_date, "-"),
            "due_date": _date_label(self.invoice.due_date, "-"),
            "amount_due": self.invoice.display_total,
            "linked_reservation": {
                "request_key": inquiry.request_key if inquiry else "-",
                "listing": inquiry.item.business_display_name if inquiry and inquiry.item else "-",
                "date_range": _reservation_date_range(inquiry),
                "guest": inquiry.guest_name if inquiry else row["guest"],
                "url": reverse("bookings:ops-reservations"),
            },
            "deposit_history": deposit_history
            or [
                {
                    "label": "No linked deposit records",
                    "amount": "-",
                    "status": "Waiting",
                    "status_cls": "pending",
                    "meta": "Create one from Deposits",
                }
            ],
            "timeline": timeline,
            "notes": self.invoice.notes
            or "Invoice, stay-payment hold, and deposit-hold records remain linked across Payments and Deposits.",
            "quick_actions": [
                {"label": "Send invoice", "kind": "post", "action": "send-invoice", "url": reverse("bookings:ops-payment-action-api", args=[self.key, "send-invoice"])},
                {"label": "Mark as paid", "kind": "post", "action": "mark-paid", "url": reverse("bookings:ops-payment-action-api", args=[self.key, "mark-paid"])},
                {"label": "Download receipt", "kind": "link", "url": row["invoice_url"]},
                {"label": "Issue refund", "kind": "link", "url": reverse("bookings:ops-deposits")},
                {"label": "Open reservation", "kind": "link", "url": reverse("bookings:ops-reservations")},
            ],
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
            "row": self.to_row_payload(),
            "detail": self.detail_payload(),
        }


class PaymentsTransactionsService:
    """PaymentTransaction aggregate service for the operations payments page."""

    def page_payload(self, selected_id=""):
        transactions = self.live_transactions()
        using_mock = not transactions
        if using_mock:
            rows = self.mock_rows()
            selected = next((row for row in rows if row["id"] == selected_id), rows[0] if rows else None)
            detail = self._mock_detail_payload(selected) if selected else None
            selected_key = selected["id"] if selected else ""
        else:
            rows = [transaction.to_row_payload() for transaction in transactions]
            selected = next((item for item in transactions if item.key == selected_id), transactions[0] if transactions else None)
            detail = selected.detail_payload() if selected else None
            selected_key = selected.key if selected else ""

        return {
            "summary_cards": self.summary_cards(using_mock=using_mock),
            "rows": rows,
            "detail": detail,
            "selected_transaction_id": selected_key,
            "total_results": len(rows),
            "total_results_display": "126" if using_mock else f"{len(rows):,}",
            "generated_at": timezone.now(),
            "date_range_label": "Jun 6 - Jun 12, 2026" if using_mock else "Live ledger",
            "payment_transactions": [transaction.to_payload() for transaction in transactions],
        }

    def live_transactions(self):
        invoices = list(
            Invoice.objects.select_related("inquiry__item", "customer_profile")
            .order_by("-issue_date", "-created_at")[:25]
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
        if not transaction_key.startswith("invoice-"):
            raise ValidationError("Only invoice-backed payment transactions can be updated from this workspace.")
        invoice = get_object_or_404(Invoice, pk=transaction_key.replace("invoice-", "", 1))
        if action == "mark-paid":
            invoice.status = InvoiceStatus.PAID
            invoice.email_status = EmailDeliveryStatus.SENT
            invoice.save(update_fields=["status", "email_status", "updated_at"])
        elif action == "send-invoice":
            invoice.status = InvoiceStatus.SENT if invoice.status == InvoiceStatus.DRAFT else invoice.status
            invoice.sent_at = timezone.now()
            invoice.email_status = EmailDeliveryStatus.SENT
            invoice.save(update_fields=["status", "sent_at", "email_status", "updated_at"])
        else:
            raise ValidationError("Unsupported payment transaction action.")
        return next((item for item in self.live_transactions() if item.key == transaction_key), None)

    @staticmethod
    def _money(cents):
        return f"${(cents or 0) / 100:,.2f}"

    @staticmethod
    def mock_rows():
        def row(row_id, transaction_id, guest, reservation, listing, channel, method, date_label, time_label, amount, status, status_cls):
            return {
                "id": row_id,
                "transaction_id": transaction_id,
                "guest": guest,
                "reservation": reservation,
                "listing": listing,
                "channel": channel,
                "method": method,
                "date_label": date_label,
                "time_label": time_label,
                "amount": amount,
                "status": status,
                "status_cls": status_cls,
                "invoice_icon": "↗",
                "invoice_url": "#",
                "is_mock": True,
            }

        return [
            row("mock-txn-10541", "TXN-2026-10541", "Maria Rodriguez", "R-1042", "3 Beds Apt, G-101", "Direct Website", "VISA .... 4242", "Jun 12, 2026", "9:30 AM", "$1,250.00", "Paid", "paid"),
            row("mock-txn-10540", "TXN-2026-10540", "John Smith", "R-1040", "2 Beds Apt, Pool", "Airbnb", "MC .... 5655", "Jun 11, 2026", "4:15 PM", "$550.00", "Paid", "paid"),
            row("mock-txn-10539", "TXN-2026-10539", "Ana Lopez", "R-1039", "Meeting Room 1", "Corporate Booking", "ACH Transfer", "Jun 10, 2026", "11:20 AM", "$250.00", "Paid", "paid"),
            row("mock-txn-10538", "TXN-2026-10538", "David Brown", "R-1038", "6 Beds Apt, G-101", "Vrbo", "VISA .... 1111", "Jun 9, 2026", "2:45 PM", "$2,100.00", "Settled", "settled"),
            row("mock-txn-10537", "TXN-2026-10537", "Sophie Martin", "R-1037", "3 Beds Apt, G-101", "Booking.com", "MC .... 8888", "Jun 9, 2026", "10:05 AM", "$500.00", "Pending", "pending"),
            row("mock-txn-10536", "TXN-2026-10536", "Carlos Mendez", "R-1036", "2 Beds Apt, Pool", "Direct Website", "Amex .... 1005", "Jun 8, 2026", "8:20 PM", "$1,320.00", "Paid", "paid"),
            row("mock-txn-10535", "TXN-2026-10535", "Emily Johnson", "R-1035", "Conference Room A", "Direct Website", "VISA .... 4242", "Jun 8, 2026", "1:10 PM", "$180.00", "Refunded", "refunded"),
            row("mock-txn-10534", "TXN-2026-10534", "Michael Lee", "R-1034", "6 Beds Apt, Pool", "Airbnb", "MC .... 2222", "Jun 7, 2026", "6:40 PM", "$2,350.00", "Paid", "paid"),
            row("mock-txn-10533", "TXN-2026-10533", "Laura Garcia", "R-1033", "3 Beds Apt, G-101", "Corporate Booking", "ACH Transfer", "Jun 7, 2026", "9:00 AM", "$300.00", "Pending", "pending"),
            row("mock-txn-10532", "TXN-2026-10532", "Robert Wilson", "R-1032", "2 Beds Apt, Pool", "Vrbo", "VISA .... 9009", "Jun 6, 2026", "3:15 PM", "$720.00", "Paid", "paid"),
        ]

    def _mock_detail_payload(self, row):
        return {
            "transaction_id": row["transaction_id"],
            "status": row["status"],
            "status_cls": row["status_cls"],
            "amount": row["amount"],
            "date_label": row["date_label"],
            "time_label": row["time_label"],
            "invoice_number": "INV-2026-3314",
            "invoice_url": "#",
            "issue_date": "Jun 12, 2026",
            "due_date": "Jun 12, 2026",
            "amount_due": row["amount"],
            "linked_reservation": {
                "request_key": row["reservation"],
                "listing": "3 Beds Apt, Vacation Home & Pool, G-101",
                "date_range": "Jun 8 - Jun 14, 2026",
                "guest": row["guest"],
                "url": "/ops/reservations/",
            },
            "deposit_history": [
                {"label": "Deposit required (50%)", "amount": "$625.00", "status": "Paid", "status_cls": "paid", "meta": "Due: May 25, 2026"},
                {"label": "Remaining balance", "amount": "$625.00", "status": "Paid", "status_cls": "paid", "meta": "Due: Jun 12, 2026"},
            ],
            "timeline": [
                {"label": "Payment received", "meta": "$1,250.00 - Visa .... 4242 - Jun 12, 2026 9:30 AM", "tone": "complete", "action_label": "Download receipt", "action_url": "#"},
                {"label": "Invoice sent", "meta": "INV-2026-3314 - Jun 12, 2026 9:28 AM", "tone": "active", "action_label": "", "action_url": ""},
                {"label": "Booking confirmed", "meta": "R-1042 - Jun 6, 2026 9:12 AM", "tone": "pending", "action_label": "Open reservation", "action_url": "/ops/reservations/"},
            ],
            "notes": "Direct booking via mladis.com.",
            "quick_actions": [
                {"label": "Send invoice", "kind": "link", "url": "#"},
                {"label": "Mark as paid", "kind": "link", "url": "#"},
                {"label": "Download receipt", "kind": "link", "url": "#"},
                {"label": "Issue refund", "kind": "link", "url": "#"},
                {"label": "Open reservation", "kind": "link", "url": "/ops/reservations/"},
            ],
        }


class DepositHoldOperationsService:
    """DepositHold aggregate service for the operations deposits page."""

    def projections(self):
        damage = [
            DepositHoldProjection(record=record, source="damage")
            for record in DamageDeposit.objects.select_related("item", "inquiry__item", "inquiry__customer_profile").order_by("-created_at")
        ]
        stay = [
            DepositHoldProjection(record=record, source="stay")
            for record in ReservationPaymentHold.objects.select_related("item", "inquiry__item", "inquiry__customer_profile").order_by("-created_at")
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
                    DamageDeposit.objects.select_related("item", "inquiry__item", "inquiry__customer_profile"),
                    pk=raw_id,
                ),
                source="damage",
            )
        if source == "stay":
            return DepositHoldProjection(
                record=get_object_or_404(
                    ReservationPaymentHold.objects.select_related("item", "inquiry__item", "inquiry__customer_profile"),
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
