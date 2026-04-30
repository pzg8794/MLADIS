from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from .reports import OpsReportsView
from .views import (
    AgentAPIView,
    AboutPageView,
    BookingInquiryCreateView,
    CalendarOpsView,
    CustomerDashboardView,
    DamageDepositCheckoutView,
    DamageDepositSuccessView,
    DonationCheckoutView,
    DonationSuccessView,
    HomePageView,
    InvoicePrintView,
    OpsDashboardView,
    ReservationCancelView,
    ReservationDetailView,
    ReservationUpdateView,
    SignUpView,
    StayDetailView,
    StripeWebhookView,
)


app_name = "bookings"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
    path("accounts/login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/", CustomerDashboardView.as_view(), name="dashboard"),
    path("accounts/reservations/<int:pk>/", ReservationDetailView.as_view(), name="reservation-detail"),
    path("accounts/reservations/<int:pk>/edit/", ReservationUpdateView.as_view(), name="reservation-edit"),
    path("accounts/reservations/<int:pk>/cancel/", ReservationCancelView.as_view(), name="reservation-cancel"),
    path("stays/<slug:slug>/", StayDetailView.as_view(), name="stay-detail"),
    path("inquiries/", BookingInquiryCreateView.as_view(), name="inquiry-create"),
    path("invoices/<uuid:token>/", InvoicePrintView.as_view(), name="invoice-print"),
    path("deposits/checkout/", DamageDepositCheckoutView.as_view(), name="deposit-checkout"),
    path("deposits/success/", DamageDepositSuccessView.as_view(), name="deposit-success"),
    path("donations/checkout/", DonationCheckoutView.as_view(), name="donation-checkout"),
    path("donations/success/", DonationSuccessView.as_view(), name="donation-success"),
    path("ops/dashboard/", OpsDashboardView.as_view(), name="ops-dashboard"),
    path("ops/reports/", OpsReportsView.as_view(), name="ops-reports"),
    path("ops/calendar/", CalendarOpsView.as_view(), name="calendar-ops"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("api/agent/", AgentAPIView.as_view(), name="agent-api"),
]
