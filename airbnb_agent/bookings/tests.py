import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import BookingInquiryForm
from .models import (
    AdminAccess,
    AgentConversation,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CancellationPolicy,
    ClientSegment,
    Coupon,
    CustomerProfile,
    Donation,
    DonationStatus,
    DamageDeposit,
    DepositStatus,
    Invoice,
    InvoiceLineItem,
    PageVisit,
)


class BookingInquiryFormTests(TestCase):
    def test_rejects_checkout_before_checkin(self):
        today = timezone.localdate()
        form = BookingInquiryForm(
            data={
                "guest_name": "Alex",
                "email": "alex@example.com",
                "phone": "555-0100",
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
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
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
                "phone": "555-0101",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BookingInquiry.objects.count(), 1)
        inquiry = BookingInquiry.objects.get()
        self.assertEqual(inquiry.email_delivery_status, "sent")
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_inquiry_records_coupon_and_blacklist_flag(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        CustomerProfile.objects.create(
            name="Blocked Guest",
            email="blocked@example.com",
            segment=ClientSegment.BLACKLISTED,
        )
        coupon = Coupon.objects.get(code="WELCOME25")
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Blocked Guest",
                "email": "blocked@example.com",
                "phone": "555-0102",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
                "coupon_code": "welcome25",
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = BookingInquiry.objects.get()
        coupon.refresh_from_db()
        self.assertEqual(inquiry.coupon_code, "WELCOME25")
        self.assertTrue(inquiry.is_blacklist_flagged)
        self.assertEqual(coupon.redemption_count, 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_staff_can_submit_admin_test_reservation(self):
        user = get_user_model().objects.create_user("staff", "staff@example.com", "secret", is_staff=True)
        self.client.force_login(user)
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
                "guest_name": "Staff Test",
                "email": "staff@example.com",
                "phone": "555-0103",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
                "is_admin_test": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = BookingInquiry.objects.get()
        self.assertTrue(inquiry.is_admin_test)
        self.assertEqual(inquiry.total_cents, 0)
        self.assertEqual(inquiry.deposit_cents, 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_redirects_to_deposit_hold_step(self):
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
                "guest_name": "Morgan",
                "email": "morgan@example.com",
                "phone": "555-0104",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
            },
        )

        inquiry = BookingInquiry.objects.get()
        self.assertRedirects(
            response,
            f"{reverse('bookings:home')}?submitted=1&deposit_for={inquiry.id}#deposit",
            fetch_redirect_response=False,
        )


class MarketingPageTests(TestCase):
    def test_home_displays_airbnb_images_and_review_proof(self):
        response = self.client.get(reverse("bookings:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stay close to Santo Domingo")
        self.assertContains(response, "https://a0.muscache.com/im/pictures/")
        self.assertContains(response, "Guest proof")

    def test_stay_detail_displays_gallery_and_booking_form(self):
        stay = BookableItem.objects.get(slug="mladis-santo-domingo-guest-home")

        response = self.client.get(stay.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gallery")
        self.assertContains(response, "Airbnb review snapshot")
        self.assertContains(response, "3 Bedrooms Vacation Home &amp; Pool G-101")
        self.assertContains(response, "Top guest highlights")
        self.assertContains(response, "Apartment rules")
        self.assertContains(response, "rules-book")
        self.assertContains(response, "Make secure deposit hold")

    def test_spanish_language_switches_public_copy(self):
        response = self.client.get(reverse("bookings:home"), HTTP_ACCEPT_LANGUAGE="es")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quédate cerca de Santo Domingo")
        self.assertContains(response, "Explorar alojamientos")


class AccountReservationTests(TestCase):
    def test_seeded_admin_email_gets_staff_access_after_signup(self):
        response = self.client.post(
            reverse("bookings:signup"),
            data={
                "username": "piter-owner",
                "email": "garciapiterz@gmail.com",
                "first_name": "Piter",
                "last_name": "Garcia",
                "phone": "631-575-4841",
                "password1": "A-strong-pass-2026!",
                "password2": "A-strong-pass-2026!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="piter-owner")
        self.assertTrue(AdminAccess.objects.filter(email="garciapiterz@gmail.com", is_active=True).exists())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_login_page_renders_social_account_options(self):
        response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google")
        self.assertContains(response, "Facebook")
        self.assertContains(response, "Microsoft")
        self.assertContains(response, "GitHub")
        self.assertContains(response, "setup needed")
        self.assertNotContains(response, 'action="/oauth/google/login/"')

    def test_unconfigured_google_login_redirects_instead_of_erroring(self):
        response = self.client.post(reverse("google_login"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("bookings:login"))

    def test_account_dashboard_and_cancel_reservation(self):
        user = get_user_model().objects.create_user(
            username="guest",
            email="guest@example.com",
            password="secret",
        )
        policy = CancellationPolicy.objects.get(slug="standard-24-hour")
        item = BookableItem.objects.get(slug="mladis-santo-domingo-guest-home")
        reservation = BookingInquiry.objects.create(
            user=user,
            item=item,
            guest_name="Guest User",
            email="guest@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
            cancellation_policy=policy,
        )
        self.client.force_login(user)

        dashboard = self.client.get(reverse("bookings:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Guest User")

        response = self.client.post(
            reverse("bookings:reservation-cancel", kwargs={"pk": reservation.pk}),
            data={"reason": "Plans changed"},
        )

        self.assertEqual(response.status_code, 302)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, BookingStatus.CANCELED)


class InvoicePageTests(TestCase):
    def test_invoice_print_page_renders_logo_ready_invoice(self):
        invoice = Invoice.objects.create(
            recipient_name="Guest User",
            recipient_email="guest@example.com",
            subtotal_cents=50000,
            total_cents=50000,
        )
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Test reservation",
            quantity=1,
            amount_cents=50000,
        )

        response = self.client.get(reverse("bookings:invoice-print", kwargs={"token": invoice.public_token}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invoice.invoice_number)
        self.assertContains(response, "$500.00 USD")


class OpsDashboardTests(TestCase):
    def test_ops_dashboard_shows_metrics_for_staff(self):
        staff = get_user_model().objects.create_user("ops", "ops@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        PageVisit.objects.create(path="/")
        AgentConversation.objects.create(
            session_id="abc",
            last_user_message="What is the price?",
            last_agent_reply="Setup mode.",
            question_topic="pricing",
        )

        response = self.client.get(reverse("bookings:ops-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner dashboard")
        self.assertContains(response, "Pricing")


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


class DonationTests(TestCase):
    def test_donation_checkout_without_stripe_key_records_configuration_status(self):
        response = self.client.post(
            reverse("bookings:donation-checkout"),
            data={
                "amount": "25.00",
                "donor_name": "Riley",
                "email": "riley@example.com",
                "cause": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        donation = Donation.objects.get()
        self.assertEqual(donation.amount_cents, 2500)
        self.assertEqual(donation.status, DonationStatus.REQUIRES_CONFIGURATION)


class CalendarOpsTests(TestCase):
    def test_calendar_ops_requires_staff_login(self):
        response = self.client.get(reverse("bookings:calendar-ops"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_calendar_ops_loads_for_staff(self):
        user = get_user_model().objects.create_user(
            username="ops",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("bookings:calendar-ops"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manual Airbnb iCal first")
