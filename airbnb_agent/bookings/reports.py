from datetime import timedelta

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from .models import (
    AgentConversation,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CalendarFeed,
    ClientSegment,
    ContactSource,
    Coupon,
    CustomerFeedback,
    CustomerProfile,
    DamageDeposit,
    Donation,
    Invoice,
    PageVisit,
    Promotion,
)


ops_staff_required = user_passes_test(
    lambda user: user.is_active and user.is_staff,
    login_url=reverse_lazy("bookings:login"),
)


@method_decorator(ops_staff_required, name="dispatch")
class OpsReportsView(TemplateView):
    template_name = "bookings/ops_reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        since = now - timedelta(days=30)
        reservations = BookingInquiry.objects.all()
        recent_reservations = reservations.filter(created_at__gte=since)
        invoices = Invoice.objects.all()
        donations = Donation.objects.all()
        deposits = DamageDeposit.objects.all()
        visits = PageVisit.objects.filter(created_at__gte=since)
        conversations = AgentConversation.objects.filter(created_at__gte=since)
        clients = CustomerProfile.objects.all()
        feedback = CustomerFeedback.objects.all()
        listings = BookableItem.objects.all()
        coupons = Coupon.objects.all()
        promotions = Promotion.objects.all()

        context.update(
            {
                "report_since": since,
                "report_until": now,
                "summary_cards": [
                    self._card("Reservations", reservations.count(), "All booking requests captured."),
                    self._card("30-day inquiries", recent_reservations.count(), "New demand in the last 30 days."),
                    self._card("Visits", visits.count(), "Tracked page visits in the last 30 days."),
                    self._card("Agent chats", conversations.count(), "Guest questions answered by the booking agent."),
                    self._card("Clients", clients.count(), "Customer profiles and segments."),
                    self._card("Feedback entries", feedback.count(), "Guest feedback linked to profiles, stays, and reservation records."),
                    self._card("Active listings", listings.filter(is_active=True).count(), "Bookable stays, services, experiences, and transport."),
                    self._card("Coupons + promos", coupons.count() + promotions.count(), "Discount codes and campaigns managed together."),
                    self._card("Invoices", invoices.count(), "Draft, sent, paid, and canceled invoices."),
                    self._card("Invoice value", self._money(invoices.aggregate(total=Sum("total_cents"))["total"]), "Total invoice value tracked."),
                    self._card("Deposits", deposits.count(), "Damage deposit checkout records."),
                    self._card("Donations", self._money(donations.aggregate(total=Sum("amount_cents"))["total"]), "Mission donations tracked."),
                ],
                "reservation_status_chart": self._choice_chart(
                    reservations,
                    "status",
                    BookingStatus.choices,
                    "Reservations by status",
                ),
                "booking_category_chart": self._choice_chart(
                    listings,
                    "category",
                    BookingCategory.choices,
                    "Bookable inventory by category",
                ),
                "item_chart": self._query_chart(
                    reservations.values("item__name").annotate(total=Count("id")).order_by("-total", "item__name")[:10],
                    "item__name",
                    "Reservations by listing/service",
                    empty_label="Flexible / unassigned",
                ),
                "visit_chart": self._query_chart(
                    visits.values("path").annotate(total=Count("id")).order_by("-total", "path")[:10],
                    "path",
                    "Most visited pages",
                ),
                "agent_topic_chart": self._query_chart(
                    conversations.values("question_topic").annotate(total=Count("id")).order_by("-total", "question_topic")[:10],
                    "question_topic",
                    "Agent question topics",
                    transform=str.title,
                ),
                "client_segment_chart": self._choice_chart(
                    clients,
                    "segment",
                    ClientSegment.choices,
                    "Clients by segment",
                ),
                "feedback_source_chart": self._choice_chart(
                    feedback,
                    "source",
                    ContactSource.choices,
                    "Feedback by source",
                ),
                "feedback_listing_chart": self._query_chart(
                    feedback.values("item__name").annotate(total=Count("id")).order_by("-total", "item__name")[:10],
                    "item__name",
                    "Feedback by listing",
                ),
                "booking_timeline": self._daily_timeline(recent_reservations, "created_at", "Reservation requests by day"),
                "visit_timeline": self._daily_timeline(visits, "created_at", "Visits by day"),
                "invoice_status_chart": self._query_chart(
                    invoices.values("status").annotate(total=Count("id")).order_by("-total", "status"),
                    "status",
                    "Invoices by status",
                    transform=str.title,
                ),
                "deposit_status_chart": self._query_chart(
                    deposits.values("status").annotate(total=Count("id")).order_by("-total", "status"),
                    "status",
                    "Deposits by status",
                    transform=lambda value: str(value).replace("_", " ").title(),
                ),
                "donation_status_chart": self._query_chart(
                    donations.values("status").annotate(total=Count("id")).order_by("-total", "status"),
                    "status",
                    "Donations by status",
                    transform=lambda value: str(value).replace("_", " ").title(),
                ),
                "campaign_status_chart": self._campaign_status_chart(coupons, promotions),
                "calendar_chart": self._calendar_chart(),
            }
        )
        return context

    @staticmethod
    def _card(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    @staticmethod
    def _money(cents):
        cents = cents or 0
        return f"${cents / 100:,.2f}"

    def _choice_chart(self, queryset, field_name, choices, title):
        rows = []
        for value, label in choices:
            rows.append({"label": label, "total": queryset.filter(**{field_name: value}).count()})
        return self._with_widths(title, rows)

    def _boolean_chart(self, queryset, field_name, title, true_label, false_label):
        rows = [
            {"label": true_label, "total": queryset.filter(**{field_name: True}).count()},
            {"label": false_label, "total": queryset.filter(**{field_name: False}).count()},
        ]
        return self._with_widths(title, rows)

    def _query_chart(self, queryset, label_field, title, empty_label="Unassigned", transform=None):
        rows = []
        for row in queryset:
            label = row.get(label_field) or empty_label
            if transform:
                label = transform(label)
            rows.append({"label": label, "total": row.get("total", 0)})
        return self._with_widths(title, rows)

    def _daily_timeline(self, queryset, date_field, title):
        start = timezone.localdate() - timedelta(days=29)
        totals = {
            row["day"]: row["total"]
            for row in queryset.annotate(day=TruncDate(date_field)).values("day").annotate(total=Count("id"))
        }
        rows = []
        for offset in range(30):
            day = start + timedelta(days=offset)
            rows.append({"label": day.strftime("%b %d"), "total": totals.get(day, 0)})
        return self._with_widths(title, rows)

    def _calendar_chart(self):
        total_stays = BookableItem.objects.filter(category=BookingCategory.STAY, is_active=True).count()
        configured = CalendarFeed.objects.filter(is_active=True).exclude(airbnb_ical_url="").count()
        rows = [
            {"label": "Active stays", "total": total_stays},
            {"label": "Configured calendar feeds", "total": configured},
            {"label": "Needs setup", "total": max(total_stays - configured, 0)},
        ]
        return self._with_widths("Calendar setup coverage", rows)

    def _campaign_status_chart(self, coupons, promotions):
        rows = [
            {"label": "Active coupons", "total": coupons.filter(is_active=True).count()},
            {"label": "Inactive coupons", "total": coupons.filter(is_active=False).count()},
        ]
        for row in promotions.values("status").annotate(total=Count("id")).order_by("-total", "status"):
            label = str(row.get("status") or "unassigned").replace("_", " ").title()
            rows.append({"label": f"{label} promotions", "total": row.get("total", 0)})
        return self._with_widths("Coupons and promotions", rows)

    @staticmethod
    def _with_widths(title, rows):
        max_total = max([row["total"] for row in rows] or [0])
        normalized = []
        for row in rows:
            width = int((row["total"] / max_total) * 100) if max_total else 0
            normalized.append({**row, "width": max(width, 3) if row["total"] else 0})
        return {"title": title, "rows": normalized, "max_total": max_total}


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsReportsView(TemplateView):
    template_name = "bookings/modern_dashboard.html"


@method_decorator(ops_staff_required, name="dispatch")
class OpsReportsAPIView(View):
    def get(self, request):
        view = OpsReportsView()
        view.setup(request)
        context = view.get_context_data()
        chart_keys = [
            "reservation_status_chart",
            "booking_category_chart",
            "item_chart",
            "visit_chart",
            "agent_topic_chart",
            "client_segment_chart",
            "feedback_source_chart",
            "feedback_listing_chart",
            "booking_timeline",
            "visit_timeline",
            "invoice_status_chart",
            "deposit_status_chart",
            "donation_status_chart",
            "campaign_status_chart",
            "calendar_chart",
        ]
        return JsonResponse(
            {
                "summary_cards": context["summary_cards"],
                "charts": [
                    {**context[key], "id": key, "category": self._category_for(key)}
                    for key in chart_keys
                ],
                "report_since": context["report_since"].isoformat(),
                "report_until": context["report_until"].isoformat(),
                "legacy_url": reverse("bookings:ops-reports"),
                "calendar_url": reverse("bookings:calendar-ops"),
            }
        )

    @staticmethod
    def _category_for(key):
        if "agent" in key:
            return "agent"
        if "deposit" in key or "invoice" in key or "donation" in key or "campaign" in key:
            return "money"
        if "client" in key or "feedback" in key:
            return "customers"
        if "visit" in key:
            return "traffic"
        if "calendar" in key:
            return "calendar"
        return "booking"
