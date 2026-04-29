from django.urls import path

from .views import (
    AgentAPIView,
    AboutPageView,
    BookingInquiryCreateView,
    CalendarOpsView,
    DamageDepositCheckoutView,
    DamageDepositSuccessView,
    DonationCheckoutView,
    DonationSuccessView,
    HomePageView,
    StayDetailView,
    StripeWebhookView,
)


app_name = "bookings"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("about/", AboutPageView.as_view(), name="about"),
    path("stays/<slug:slug>/", StayDetailView.as_view(), name="stay-detail"),
    path("inquiries/", BookingInquiryCreateView.as_view(), name="inquiry-create"),
    path("deposits/checkout/", DamageDepositCheckoutView.as_view(), name="deposit-checkout"),
    path("deposits/success/", DamageDepositSuccessView.as_view(), name="deposit-success"),
    path("donations/checkout/", DonationCheckoutView.as_view(), name="donation-checkout"),
    path("donations/success/", DonationSuccessView.as_view(), name="donation-success"),
    path("ops/calendar/", CalendarOpsView.as_view(), name="calendar-ops"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("api/agent/", AgentAPIView.as_view(), name="agent-api"),
]
