import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import BookingInquiryForm
from .models import (
    AgentConversation,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    DamageDeposit,
    DepositStatus,
)


class BookingInquiryFormTests(TestCase):
    def test_rejects_checkout_before_checkin(self):
        today = timezone.localdate()
        form = BookingInquiryForm(
            data={
                "guest_name": "Alex",
                "email": "alex@example.com",
                "check_in": today + timedelta(days=2),
                "check_out": today + timedelta(days=1),
                "guests": 2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("check_out", form.errors)


class AgentAPITests(TestCase):
    def setUp(self):
        self.item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )

    def test_agent_api_persists_conversation(self):
        response = self.client.post(
            reverse("bookings:agent-api"),
            data=json.dumps({"message": "Can I book this?", "item_id": self.item.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.json())
        self.assertEqual(AgentConversation.objects.count(), 1)


class BookingInquiryViewTests(TestCase):
    def test_booking_inquiry_creates_record(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Casey",
                "email": "casey@example.com",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BookingInquiry.objects.count(), 1)


class DamageDepositTests(TestCase):
    def test_deposit_checkout_without_stripe_key_records_configuration_status(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Jordan",
                "email": "jordan@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.amount_cents, 20000)
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CONFIGURATION)
