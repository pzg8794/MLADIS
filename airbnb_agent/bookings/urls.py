from django.urls import path

from .views import (
    AgentAPIView,
    BookingInquiryCreateView,
    DamageDepositCheckoutView,
    DamageDepositSuccessView,
    HomePageView,
    StripeWebhookView,
)


app_name = "bookings"

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("inquiries/", BookingInquiryCreateView.as_view(), name="inquiry-create"),
    path("deposits/checkout/", DamageDepositCheckoutView.as_view(), name="deposit-checkout"),
    path("deposits/success/", DamageDepositSuccessView.as_view(), name="deposit-success"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
    path("api/agent/", AgentAPIView.as_view(), name="agent-api"),
]
