import json
import os
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.internal.flows.signup import process_auto_signup
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .adapters import MLADISAccountAdapter, MLADISSocialAccountAdapter
from .admin import DamageDepositAdmin
from .airbnb_import import AirbnbGuestEmailParser, AirbnbGuestImportService
from .forms import BookingInquiryForm
from .models import (
    AdminAccess,
    AgentConversation,
    AirbnbGuestRecord,
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CancellationPolicy,
    ClientSegment,
    ContactSource,
    Coupon,
    CustomerFeedback,
    CustomerProfile,
    DailyPriceOverride,
    Donation,
    DonationStatus,
    DamageDeposit,
    DepositProvider,
    DepositStatus,
    Invoice,
    InvoiceLineItem,
    MarketingConsentStatus,
    PageVisit,
    Promotion,
    PromotionRecipient,
    SiteSettings,
)
from .services import AgentRequest, BookingAgentService, BookingCalendarService, PromotionEmailService


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


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

    @override_settings(OPENAI_AGENT_MODEL="gpt-5-mini")
    def test_agent_service_uses_openai_when_key_is_configured(self):
        class FakeResponses:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(output_text="Yes, I can help with those dates.", id="resp_test")

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)

        response = BookingAgentService(api_key="sk-test", client=fake_client).reply(
            AgentRequest(
                message="Is there room for four guests?",
                session_id="session-123",
                item_id=self.item.id,
            )
        )

        conversation = AgentConversation.objects.get()
        self.assertEqual(response.reply, "Yes, I can help with those dates.")
        self.assertEqual(fake_responses.kwargs["model"], "gpt-5-mini")
        self.assertIn("admin-confirmed", fake_responses.kwargs["instructions"])
        self.assertIn("secure deposit-hold step", fake_responses.kwargs["instructions"])
        self.assertIn("Do not promise discounts", fake_responses.kwargs["instructions"])
        self.assertIn("Is there room for four guests?", fake_responses.kwargs["input"])
        self.assertIn("Booking workflow", fake_responses.kwargs["input"])
        self.assertEqual(conversation.metadata["agent_mode"], "openai")
        self.assertEqual(conversation.metadata["openai_response_id"], "resp_test")

    def test_agent_panel_includes_panel_scoped_csrf_token(self):
        response = self.client.get(reverse("bookings:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')


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
        self.assertEqual(DamageDeposit.objects.count(), 0)


class BookingCalendarServiceTests(TestCase):
    def test_build_month_merges_bookings_blocks_and_daily_prices(self):
        item = BookableItem.objects.create(
            name="Calendar Stay",
            slug="calendar-stay",
            category=BookingCategory.STAY,
            short_description="A test calendar stay.",
            starting_price=Decimal("120.00"),
            is_active=True,
        )
        BookingInquiry.objects.create(
            item=item,
            guest_name="Booked Guest",
            email="guest@example.com",
            check_in=date(2026, 6, 10),
            check_out=date(2026, 6, 13),
            guests=2,
            status=BookingStatus.CONFIRMED,
        )
        BookingInquiry.objects.create(
            item=item,
            guest_name="Canceled Guest",
            email="canceled@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 17),
            guests=2,
            status=BookingStatus.CANCELED,
        )
        AvailabilityBlock.objects.create(
            item=item,
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 19),
            reason="Owner stay",
        )
        DailyPriceOverride.objects.create(
            item=item,
            start_date=date(2026, 6, 20),
            end_date=date(2026, 6, 21),
            nightly_price=Decimal("175.00"),
            label="Weekend premium",
        )

        result = BookingCalendarService().build_month(item, month_start=date(2026, 6, 1))

        booked_day = self._calendar_cell(result["weeks"], date(2026, 6, 11))
        blocked_day = self._calendar_cell(result["weeks"], date(2026, 6, 18))
        priced_day = self._calendar_cell(result["weeks"], date(2026, 6, 20))
        available_day = self._calendar_cell(result["weeks"], date(2026, 6, 15))

        self.assertEqual(booked_day["status"], "booked")
        self.assertEqual(len(booked_day["reservations"]), 1)
        self.assertEqual(booked_day["price_display"], "$120.00")

        self.assertEqual(blocked_day["status"], "blocked")
        self.assertEqual(blocked_day["blocks"][0].reason, "Owner stay")

        self.assertEqual(priced_day["status"], "available")
        self.assertEqual(priced_day["price_display"], "$175.00")
        self.assertEqual(priced_day["price_source"], "override")

        self.assertEqual(available_day["status"], "available")
        self.assertEqual(available_day["price_display"], "$120.00")
        self.assertEqual(len(result["reservations"]), 1)

    def _calendar_cell(self, weeks, target_day):
        for week in weeks:
            for cell in week:
                if cell["date"] == target_day:
                    return cell
        self.fail(f"Could not find calendar cell for {target_day}.")


@override_settings(STORAGES=TEST_STORAGES)
class BookableItemCalendarAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="calendar-admin",
            email="calendar-admin@example.com",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)
        self.item = BookableItem.objects.create(
            name="Calendar Admin Stay",
            slug="calendar-admin-stay",
            category=BookingCategory.STAY,
            short_description="A stay used for admin calendar tests.",
            starting_price=Decimal("120.00"),
            is_active=True,
        )

    def test_admin_home_surfaces_business_calendar(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business calendar")
        self.assertContains(response, reverse("admin:bookings_bookableitem_calendar"))
        self.assertContains(response, "Owner dashboard")
        self.assertContains(response, "Reports")

    def test_bookable_item_changelist_surfaces_business_calendar(self):
        response = self.client.get(reverse("admin:bookings_bookableitem_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business calendar")
        self.assertContains(response, reverse("admin:bookings_bookableitem_calendar"))

    def test_calendar_view_renders_booked_blocked_and_priced_days(self):
        reservation = BookingInquiry.objects.create(
            item=self.item,
            guest_name="Booked Guest",
            email="guest@example.com",
            check_in=date(2026, 6, 10),
            check_out=date(2026, 6, 13),
            guests=2,
            status=BookingStatus.CONFIRMED,
        )
        block = AvailabilityBlock.objects.create(
            item=self.item,
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 19),
            reason="Owner stay",
        )
        override = DailyPriceOverride.objects.create(
            item=self.item,
            start_date=date(2026, 6, 20),
            end_date=date(2026, 6, 21),
            nightly_price=Decimal("175.00"),
            label="Weekend premium",
        )

        response = self.client.get(
            reverse("admin:bookings_bookableitem_calendar"),
            data={"item": self.item.pk, "month": "2026-06"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business calendar")
        self.assertContains(response, "Booked Guest")
        self.assertContains(response, "Owner stay")
        self.assertContains(response, "$175.00")
        self.assertContains(response, "Default nightly price")
        self.assertContains(response, "Click one day to start a range")
        self.assertContains(response, 'data-calendar-quick-action="block"', html=False)
        self.assertContains(response, 'data-calendar-quick-action="price"', html=False)
        self.assertContains(response, reverse("admin:bookings_bookinginquiry_change", args=[reservation.pk]))
        self.assertContains(response, reverse("admin:bookings_availabilityblock_change", args=[block.pk]))
        self.assertContains(response, reverse("admin:bookings_dailypriceoverride_change", args=[override.pk]))
        self.assertContains(response, 'data-calendar-date="2026-06-10"', html=False)

    def test_calendar_view_post_add_block_creates_manual_block(self):
        response = self.client.post(
            reverse("admin:bookings_bookableitem_calendar"),
            data={
                "calendar_action": "add_block",
                "month": "2026-06",
                "item": self.item.pk,
                "block-start_date": "2026-06-22",
                "block-end_date": "2026-06-24",
                "block-reason": "Maintenance",
                "block-notes": "Paint work",
            },
        )

        self.assertEqual(response.status_code, 302)
        block = AvailabilityBlock.objects.get()
        self.assertEqual(block.reason, "Maintenance")
        self.assertEqual(block.start_date, date(2026, 6, 22))
        self.assertEqual(block.end_date, date(2026, 6, 24))

    def test_calendar_view_post_add_price_override_creates_override(self):
        response = self.client.post(
            reverse("admin:bookings_bookableitem_calendar"),
            data={
                "calendar_action": "add_price",
                "month": "2026-06",
                "item": self.item.pk,
                "price-start_date": "2026-06-27",
                "price-end_date": "2026-06-28",
                "price-nightly_price": "210.00",
                "price-label": "Holiday weekend",
                "price-notes": "High demand dates",
            },
        )

        self.assertEqual(response.status_code, 302)
        override = DailyPriceOverride.objects.get()
        self.assertEqual(override.label, "Holiday weekend")
        self.assertEqual(override.nightly_price, Decimal("210.00"))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        STRIPE_SECRET_KEY="sk_test_123",
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    def test_booking_still_redirects_to_deposit_choice_when_payment_providers_are_configured(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay-direct-checkout",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Jamie",
                "email": "jamie@example.com",
                "phone": "555-0106",
                "check_in": today + timedelta(days=4),
                "check_out": today + timedelta(days=7),
                "guests": 2,
            },
        )

        inquiry = BookingInquiry.objects.get()
        self.assertRedirects(
            response,
            f"{reverse('bookings:home')}?submitted=1&deposit_for={inquiry.id}#deposit",
            fetch_redirect_response=False,
        )
        self.assertEqual(DamageDeposit.objects.count(), 0)


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


class LegalPageTests(TestCase):
    def setUp(self):
        site_settings = SiteSettings.current()
        site_settings.contact_email = "privacy@example.com"
        site_settings.save(update_fields=["contact_email", "updated_at"])

    def test_business_page_renders_public_business_details(self):
        site_settings = SiteSettings.current()

        response = self.client.get(reverse("bookings:business"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business profile")
        self.assertContains(response, site_settings.site_name)
        self.assertContains(response, site_settings.public_address_label)
        self.assertContains(response, "privacy@example.com")
        self.assertContains(response, reverse("bookings:privacy-policy"))

    def test_privacy_policy_page_renders_contact_details(self):
        response = self.client.get(reverse("bookings:privacy-policy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Privacy policy")
        self.assertContains(response, "privacy@example.com")
        self.assertContains(response, "Social login details")

    def test_terms_page_renders_booking_rules_summary(self):
        response = self.client.get(reverse("bookings:terms"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Terms of service")
        self.assertContains(response, "Payments are processed through Stripe")

    def test_data_deletion_page_renders_request_instructions(self):
        response = self.client.get(reverse("bookings:data-deletion"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Data deletion instructions")
        self.assertContains(response, "Data deletion request")
        self.assertContains(response, "privacy@example.com")

    def test_data_deletion_callback_returns_meta_confirmation_payload(self):
        response = self.client.post(
            reverse("bookings:data-deletion-callback"),
            data={"signed_request": "test"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["url"], f"http://testserver{reverse('bookings:data-deletion')}")
        self.assertEqual(len(payload["confirmation_code"]), 32)

    def test_data_deletion_callback_gets_instruction_metadata(self):
        response = self.client.get(reverse("bookings:data-deletion-callback"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload["instructions_url"],
            f"http://testserver{reverse('bookings:data-deletion')}",
        )


class AccountReservationTests(TestCase):
    def test_agent_admin_command_provisions_dedicated_superuser(self):
        output = StringIO()

        call_command(
            "provision_agent_admin",
            email="agent@mladis.com",
            name="MLADIS Agent",
            phone="631-575-4841",
            username="mladis-agent",
            stdout=output,
        )

        user = get_user_model().objects.get(email="agent@mladis.com")
        access = AdminAccess.objects.get(email="agent@mladis.com")
        profile = CustomerProfile.objects.get(email="agent@mladis.com")
        self.assertEqual(user.username, "mladis-agent")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(access.name, "MLADIS Agent")
        self.assertEqual(access.phone, "631-575-4841")
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.segment, ClientSegment.VIP)
        self.assertIn("Provisioned agent admin", output.getvalue())

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

    def test_seeded_diana_admin_email_gets_staff_access_after_signup(self):
        response = self.client.post(
            reverse("bookings:signup"),
            data={
                "username": "diana-owner",
                "email": "GarciaBDianaS@gmail.com",
                "first_name": "Diana",
                "last_name": "Garcia",
                "phone": "555-0105",
                "password1": "A-strong-pass-2026!",
                "password2": "A-strong-pass-2026!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="diana-owner")
        self.assertTrue(AdminAccess.objects.filter(email="garciabdianas@gmail.com", is_active=True).exists())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    @override_settings(SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=[])
    def test_login_page_renders_social_account_options(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "",
                "GOOGLE_OAUTH_CLIENT_SECRET": "",
                "FACEBOOK_OAUTH_CLIENT_ID": "",
                "FACEBOOK_OAUTH_CLIENT_SECRET": "",
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "GITHUB_OAUTH_CLIENT_ID": "",
                "GITHUB_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
                "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": "",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, "Continue with Facebook")
        self.assertContains(response, "Continue with Microsoft")
        self.assertContains(response, "Continue with GitHub")
        self.assertContains(response, "setup needed")
        self.assertNotContains(response, 'action="/oauth/google/login/"')

    @override_settings(SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=["microsoft"])
    def test_unconfigured_microsoft_is_hidden_from_social_options(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "",
                "GOOGLE_OAUTH_CLIENT_SECRET": "",
                "FACEBOOK_OAUTH_CLIENT_ID": "",
                "FACEBOOK_OAUTH_CLIENT_SECRET": "",
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "GITHUB_OAUTH_CLIENT_ID": "",
                "GITHUB_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
                "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": "microsoft",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Continue with Microsoft")

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="http://127.0.0.1:8000",
        ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"],
    )
    def test_social_auth_canonical_origin_redirects_login_host(self):
        response = self.client.get(reverse("bookings:login"), HTTP_HOST="localhost:8000")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"http://127.0.0.1:8000{reverse('bookings:login')}")

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="http://127.0.0.1:8000",
        ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"],
    )
    def test_social_auth_canonical_origin_keeps_matching_host(self):
        response = self.client.get(reverse("bookings:login"), HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, 200)

    def test_login_page_auto_configures_google_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "google-client-id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "google-client-secret",
                "SITE_DOMAIN": "127.0.0.1:8000",
                "SITE_NAME": "MLADIS Local",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("google_login")}"')
        self.assertContains(response, "Choose a social provider for a faster sign-in")
        app = SocialApp.objects.get(provider="google")
        self.assertEqual(app.client_id, "google-client-id")
        self.assertEqual(app.secret, "google-client-secret")
        self.assertTrue(app.sites.filter(id=1).exists())
        site = Site.objects.get(id=1)
        self.assertEqual(site.domain, "127.0.0.1:8000")
        self.assertEqual(site.name, "MLADIS Local")

    @override_settings(SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=[])
    def test_stale_microsoft_social_app_is_ignored_when_env_is_empty(self):
        stale_app = SocialApp.objects.create(
            provider="microsoft",
            name="Microsoft OAuth",
            client_id="demo-microsoft-client",
            secret="demo-microsoft-secret",
        )
        stale_app.sites.add(Site.objects.get(id=1))

        with patch.dict(
            os.environ,
            {
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))
            launch_response = self.client.post(reverse("microsoft_login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Microsoft")
        self.assertContains(response, "setup needed")
        self.assertNotContains(response, f'action="{reverse("microsoft_login")}"')
        self.assertEqual(launch_response.status_code, 302)
        self.assertEqual(launch_response["Location"], reverse("bookings:login"))

    def test_stale_microsoft_social_app_stays_hidden_by_default(self):
        stale_app = SocialApp.objects.create(
            provider="microsoft",
            name="Microsoft OAuth",
            client_id="demo-microsoft-client",
            secret="demo-microsoft-secret",
        )
        stale_app.sites.add(Site.objects.get(id=1))

        with patch.dict(
            os.environ,
            {
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
                "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": "microsoft",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Continue with Microsoft")

    def test_login_page_auto_configures_microsoft_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "MICROSOFT_OAUTH_CLIENT_ID": "microsoft-client-id",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "microsoft-client-secret",
                "MICROSOFT_OAUTH_TENANT": "organizations",
                "MICROSOFT_OAUTH_LOGIN_URL": "https://login.microsoftonline.com",
                "MICROSOFT_GRAPH_URL": "https://graph.microsoft.com",
                "SITE_DOMAIN": "127.0.0.1:8000",
                "SITE_NAME": "MLADIS Local",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("microsoft_login")}"')
        app = SocialApp.objects.get(provider="microsoft")
        self.assertEqual(app.client_id, "microsoft-client-id")
        self.assertEqual(app.secret, "microsoft-client-secret")
        self.assertEqual(app.settings["tenant"], "organizations")
        self.assertEqual(app.settings["login_url"], "https://login.microsoftonline.com")
        self.assertEqual(app.settings["graph_url"], "https://graph.microsoft.com")

    def test_unconfigured_google_login_redirects_instead_of_erroring(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "",
                "GOOGLE_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
            },
            clear=False,
        ):
            response = self.client.post(reverse("google_login"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("bookings:login"))


class SocialAccountAdapterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_facebook_without_email_auto_signs_up_using_generated_email(self):
        request = self.factory.get("/accounts/login/")
        sociallogin = SocialLogin(
            user=get_user_model()(),
            account=SocialAccount(
                provider="facebook",
                uid="123456789",
                extra_data={"id": "123456789", "name": "Peter Zac"},
            ),
        )

        adapter = MLADISSocialAccountAdapter()
        adapter.populate_user(request, sociallogin, {"name": "Peter Zac"})
        auto_signup, response = process_auto_signup(request, sociallogin)

        self.assertTrue(auto_signup)
        self.assertIsNone(response)
        self.assertEqual(
            sociallogin.user.email,
            "facebook-123456789@users.mladis.invalid",
        )
        self.assertEqual(
            sociallogin.email_addresses[0].email,
            "facebook-123456789@users.mladis.invalid",
        )
        self.assertFalse(sociallogin.email_addresses[0].verified)

    def test_generated_social_email_skips_confirmation_mail(self):
        request = self.factory.get("/accounts/login/")
        user = get_user_model()(username="peter")
        email_address = EmailAddress(
            user=user,
            email="facebook-123456789@users.mladis.invalid",
            verified=False,
            primary=True,
        )

        should_send = MLADISAccountAdapter().should_send_confirmation_mail(
            request,
            email_address,
            signup=True,
        )

        self.assertFalse(should_send)

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
        self.assertContains(response, "Business calendar")
        self.assertContains(response, reverse("admin:bookings_bookableitem_calendar"))

    def test_ops_reports_show_graphs_for_staff(self):
        staff = get_user_model().objects.create_user("reports", "reports@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        PageVisit.objects.create(path="/stays/test/")
        AgentConversation.objects.create(
            session_id="report-abc",
            last_user_message="Is there parking?",
            last_agent_reply="Setup mode.",
            question_topic="amenities",
        )
        BookingInquiry.objects.create(
            guest_name="Graph Guest",
            email="graph@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
        )

        response = self.client.get(reverse("bookings:ops-reports"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reporting")
        self.assertContains(response, "Reservations by status")
        self.assertContains(response, "Agent question topics")
        self.assertContains(response, "Feedback by source")
        self.assertContains(response, "Visits by day")
        self.assertContains(response, "Business calendar")
        self.assertContains(response, reverse("admin:bookings_bookableitem_calendar"))

    @override_settings(SOCIAL_AUTH_CANONICAL_ORIGIN="https://mladis.com")
    def test_oauth_diagnostics_shows_exact_callback_urls_for_staff(self):
        staff = get_user_model().objects.create_user("oauth", "oauth@example.com", "secret", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("bookings:oauth-diagnostics"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OAuth setup")
        self.assertContains(response, "https://mladis.com/oauth/facebook/login/callback/")
        self.assertContains(response, "https://mladis.com/oauth/github/login/callback/")


class DamageDepositTests(TestCase):
    @override_settings(STRIPE_SECRET_KEY="")
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
        self.assertEqual(deposit.payment_provider, DepositProvider.STRIPE)
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CONFIGURATION)

    @override_settings(PAYPAL_CLIENT_ID="", PAYPAL_CLIENT_SECRET="")
    def test_paypal_checkout_without_credentials_records_configuration_status(self):
        item = BookableItem.objects.create(
            name="PayPal Stay",
            slug="paypal-stay",
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
                "payment_provider": DepositProvider.PAYPAL,
            },
        )

        self.assertEqual(response.status_code, 302)
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.payment_provider, DepositProvider.PAYPAL)
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CONFIGURATION)

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request")
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_paypal_checkout_redirect_records_order(self, _mock_token, mock_api_request):
        item = BookableItem.objects.create(
            name="PayPal Stay Configured",
            slug="paypal-stay-configured",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        mock_api_request.return_value = {
            "id": "ORDER-123",
            "links": [
                {
                    "rel": "payer-action",
                    "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123",
                }
            ],
        }

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Taylor",
                "email": "taylor@example.com",
                "payment_provider": DepositProvider.PAYPAL,
            },
        )

        self.assertRedirects(
            response,
            "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123",
            fetch_redirect_response=False,
        )
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.payment_provider, DepositProvider.PAYPAL)
        self.assertEqual(deposit.paypal_order_id, "ORDER-123")
        self.assertEqual(deposit.status, DepositStatus.CHECKOUT_CREATED)

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request")
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_paypal_success_authorizes_deposit(self, _mock_token, mock_api_request):
        deposit = DamageDeposit.objects.create(
            guest_name="Taylor",
            email="taylor@example.com",
            payment_provider=DepositProvider.PAYPAL,
            paypal_order_id="ORDER-123",
        )
        mock_api_request.return_value = {
            "purchase_units": [
                {
                    "payments": {
                        "authorizations": [
                            {
                                "id": "AUTH-123",
                            }
                        ]
                    }
                }
            ]
        }

        response = self.client.get(
            reverse("bookings:deposit-paypal-success"),
            data={"token": "ORDER-123"},
        )

        self.assertRedirects(response, reverse("bookings:home") + "#deposit", fetch_redirect_response=False)
        deposit.refresh_from_db()
        self.assertEqual(deposit.paypal_authorization_id, "AUTH-123")
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CAPTURE)


@override_settings(STORAGES=TEST_STORAGES)
class DamageDepositAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = DamageDepositAdmin(DamageDeposit, AdminSite())
        self.user = get_user_model().objects.create_user(
            username="deposit-admin",
            email="deposit-admin@example.com",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def _request(self):
        request = self.factory.post("/admin/bookings/damagedeposit/")
        request.user = self.user
        return request

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request")
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_capture_selected_deposits_updates_only_authorized_paypal_deposits(
        self,
        _mock_token,
        mock_api_request,
        mock_message_user,
    ):
        paypal_deposit = DamageDeposit.objects.create(
            guest_name="Taylor",
            email="taylor@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.PAYPAL,
            status=DepositStatus.REQUIRES_CAPTURE,
            paypal_order_id="ORDER-123",
            paypal_authorization_id="AUTH-123",
        )
        stripe_deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.CANCELED,
            stripe_payment_intent_id="pi_123",
        )
        mock_api_request.return_value = {"id": "CAPTURE-123"}

        self.admin.capture_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk__in=[paypal_deposit.pk, stripe_deposit.pk]),
        )

        paypal_deposit.refresh_from_db()
        stripe_deposit.refresh_from_db()
        self.assertEqual(paypal_deposit.status, DepositStatus.CAPTURED)
        self.assertEqual(stripe_deposit.status, DepositStatus.CANCELED)
        self.assertIn("CAPTURE-123", paypal_deposit.notes)
        mock_api_request.assert_called_once_with(
            "post",
            "/v2/payments/authorizations/AUTH-123/capture",
            access_token="access-token",
            json_body={
                "amount": {"currency_code": "USD", "value": "200.00"},
                "final_capture": True,
            },
        )

        messages = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Captured 1 deposit hold(s).", messages)
        self.assertIn("Skipped 1 deposit(s) that were not active authorized holds.", messages)

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request", return_value={})
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_release_selected_deposits_voids_authorized_paypal_deposit(
        self,
        _mock_token,
        mock_api_request,
        mock_message_user,
    ):
        deposit = DamageDeposit.objects.create(
            guest_name="Taylor",
            email="taylor@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.PAYPAL,
            status=DepositStatus.REQUIRES_CAPTURE,
            paypal_order_id="ORDER-123",
            paypal_authorization_id="AUTH-123",
        )

        self.admin.release_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk=deposit.pk),
        )

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertIn("AUTH-123", deposit.notes)
        mock_api_request.assert_called_once_with(
            "post",
            "/v2/payments/authorizations/AUTH-123/void",
            access_token="access-token",
            json_body={},
        )

        messages = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Released 1 deposit hold(s).", messages)

    @override_settings(STRIPE_SECRET_KEY="stripe-secret")
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.stripe.PaymentIntent.capture")
    def test_capture_selected_deposits_updates_authorized_stripe_deposit(
        self,
        mock_capture,
        mock_message_user,
    ):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )
        mock_capture.return_value = {"id": "pi_123", "latest_charge": "ch_123"}

        self.admin.capture_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk=deposit.pk),
        )

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CAPTURED)
        self.assertIn("ch_123", deposit.notes)
        mock_capture.assert_called_once_with("pi_123")

        messages_seen = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Captured 1 deposit hold(s).", messages_seen)

    @override_settings(STRIPE_SECRET_KEY="stripe-secret")
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.stripe.PaymentIntent.cancel")
    def test_release_selected_deposits_cancels_authorized_stripe_deposit(
        self,
        mock_cancel,
        mock_message_user,
    ):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )
        mock_cancel.return_value = {"id": "pi_123"}

        self.admin.release_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk=deposit.pk),
        )

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertIn("pi_123", deposit.notes)
        mock_cancel.assert_called_once_with("pi_123")

        messages_seen = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Released 1 deposit hold(s).", messages_seen)

    def test_change_view_shows_confirmation_links_for_capturable_deposit(self):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )

        response = self.client.get(reverse("admin:bookings_damagedeposit_change", args=[deposit.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Capture deposit")
        self.assertContains(response, "Release deposit")

    @override_settings(STRIPE_SECRET_KEY="stripe-secret")
    @patch("bookings.services.stripe.PaymentIntent.cancel", return_value={"id": "pi_123"})
    def test_confirm_release_view_posts_and_redirects(self, _mock_cancel):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )

        response = self.client.post(
            reverse("admin:bookings_damagedeposit_deposit_action", args=[deposit.pk, "release"]),
            follow=True,
        )

        deposit.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertContains(response, "Released deposit")
        message_levels = [message.level for message in response.context["messages"]]
        self.assertIn(messages.SUCCESS, message_levels)


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


class CustomerMarketingConsentTests(TestCase):
    AIRBNB_SAMPLE_BODY = """
RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024

Remember: Airbnb will never ask you to wire money. Learn more.

Diana

It will be a pleasure

[Pre-approve / Decline](https://www.airbnb.com/hosting/thread/1773535134?thread_type=home_booking)

Respond to Diana by replying directly to this email.

[6 Bedrooms Vacation Home & Pool (Apartment G-102)](https://www.airbnb.com/rooms/588632365342578374)

Reservation details

6 Bedrooms Vacation Home & Pool (Apartment G-102)

Guests

10 guests

Check-In

Thursday

August 22, 2024

Check-out

Sunday

September 1, 2024
"""
    AIRBNB_INITIAL_INQUIRY_BODY = """
Respond to Ana’s inquiry

[Ana](https://www.airbnb.com/hosting/thread/1773535134?thread_type=home_booking)

Identity verified · 1 review

US

Hello Diana, my name is Ana im planning a trip to DR on August 22 to sept 1 with my volleyball team.

[6 Bedrooms Vacation Home & Pool (Apartment G-102)](https://www.airbnb.com/rooms/588632365342578374)

Check-in

Thu, Aug 22

3:00 PM

Checkout

Sun, Sep 1

11:00 AM

Guests

10 adults
"""
    AIRBNB_SPANISH_REPLY_BODY = """
Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may

Por tu seguridad y protección, comunícate siempre a través de la plataforma de Airbnb.

Yoel

Responsable de reservación

Hola dia a que hora es la salida?

Diana

Anfitrión

Saludos Yoel, es un apartamento de tres habitaciones.

[Revisar consulta](https://es-l.airbnb.com/hosting/thread/2520797227?thread_type=home_booking)

[3 Bedrooms Vacation Home & Pool (Apartment G-101)](https://es-l.airbnb.com/rooms/582161420407543691)

3 Bedrooms Vacation Home & Pool (Apartment G-101)

Alojamiento vacacional - Vivienda o apartamento entero, anfitrión: Piter

Check-in

lunes

4 de mayo de 2026

15:00

Check-out

martes

5 de mayo de 2026

11:00

Viajeros

7 adultos
"""

    def test_airbnb_email_parser_extracts_guest_stay_and_thread_data(self):
        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-123",
                "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                "body": self.AIRBNB_SAMPLE_BODY,
                "email_ts": "2024-04-04T16:18:54",
            }
        )

        self.assertEqual(payload.source_message_id, "gmail-123")
        self.assertEqual(payload.guest_name, "Diana")
        self.assertEqual(payload.airbnb_listing_id, "588632365342578374")
        self.assertEqual(payload.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/1773535134")
        self.assertEqual(payload.guests, 10)
        self.assertEqual(payload.check_in, date(2024, 8, 22))
        self.assertEqual(payload.check_out, date(2024, 9, 1))
        self.assertIn("It will be a pleasure", payload.message_excerpt)

    def test_airbnb_email_parser_extracts_guest_from_initial_inquiry(self):
        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-initial-123",
                "subject": "Inquiry for 6 Bedrooms Vacation Home & Pool (Apartment G-102) for Aug 22 – Sep 1, 2024",
                "body": self.AIRBNB_INITIAL_INQUIRY_BODY,
                "email_ts": "2024-04-04T15:44:13",
            }
        )

        self.assertEqual(payload.guest_name, "Ana")
        self.assertEqual(payload.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/1773535134")
        self.assertEqual(payload.airbnb_listing_id, "588632365342578374")

    def test_airbnb_email_parser_extracts_spanish_airbnb_reply(self):
        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-spanish-123",
                "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                "body": self.AIRBNB_SPANISH_REPLY_BODY,
                "email_ts": "2026-05-03T15:40:25",
            }
        )

        self.assertEqual(payload.guest_name, "Yoel")
        self.assertEqual(payload.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/2520797227")
        self.assertEqual(payload.airbnb_listing_id, "582161420407543691")
        self.assertEqual(payload.check_in, date(2026, 5, 4))
        self.assertEqual(payload.check_out, date(2026, 5, 5))
        self.assertEqual(payload.guests, 7)
        self.assertIn("Hola dia", payload.message_excerpt)

    def test_airbnb_email_parser_counts_spanish_children_as_travelers(self):
        body = self.AIRBNB_SPANISH_REPLY_BODY.replace("7 adultos", "5 adultos, 2 niños")

        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-spanish-family-123",
                "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                "body": body,
                "email_ts": "2026-05-03T15:40:25",
            }
        )

        self.assertEqual(payload.guests, 7)

    def test_airbnb_email_parser_counts_spanish_babies_as_travelers(self):
        body = self.AIRBNB_SPANISH_REPLY_BODY.replace("7 adultos", "1 adulto, 1 bebé")

        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-spanish-baby-123",
                "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                "body": body,
                "email_ts": "2026-05-03T15:40:25",
            }
        )

        self.assertEqual(payload.guests, 2)

    def test_airbnb_import_service_upserts_guest_records_from_json_file(self):
        item = BookableItem.objects.create(
            name="Six bedroom stay",
            slug="six-bedroom-stay",
            category=BookingCategory.STAY,
            short_description="A stay from Airbnb.",
            airbnb_listing_id="999999999999999999",
            is_active=True,
        )
        body = self.AIRBNB_SAMPLE_BODY.replace("588632365342578374", "999999999999999999")
        data = {
            "responses": [
                {
                    "id": "gmail-123",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": body,
                    "email_ts": "2024-04-04T16:18:54",
                }
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            service = AirbnbGuestImportService()

            first = service.import_file(path)
            second = service.import_file(path)

        self.assertEqual(first.created, 1)
        self.assertEqual(second.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.item, item)
        self.assertEqual(record.customer_profile.source, ContactSource.AIRBNB)
        self.assertEqual(record.customer_profile.marketing_consent_status, MarketingConsentStatus.UNKNOWN)
        feedback = CustomerFeedback.objects.get()
        self.assertEqual(feedback.airbnb_guest_record, record)
        self.assertEqual(feedback.customer_profile, record.customer_profile)
        self.assertEqual(feedback.item, item)
        self.assertIn("It will be a pleasure", feedback.feedback_text)

    def test_airbnb_import_service_imports_structured_guest_contact_list(self):
        data = {
            "guest_contact_list": [
                {
                    "guest_name": "Jessica",
                    "email": "",
                    "phone_number": "",
                    "airbnb_profile_name_or_id": "airbnb-profile-123",
                    "airbnb_thread_url": "https://www.airbnb.com/hosting/messages/2423037932",
                    "listing_apartment": "6 Bedrooms Vacation Home & Pool (Apartment G-102)",
                    "check_in_date": "Apr 17",
                    "check_out_date": "Apr 19",
                    "number_of_guests": "",
                    "message_summary": "Template message: discount offer + feedback request.",
                    "feedback_or_review_summary": "Feedback requested; review not shown.",
                    "permission_to_contact_outside_airbnb": "unknown",
                    "consent_status": "unknown",
                    "promotion_permission_notes": "Opt-in required before marketing.",
                }
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-contacts.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        current_year = timezone.localdate().year
        self.assertEqual(result.created, 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.guest_name, "Jessica")
        self.assertEqual(record.airbnb_listing_id, "588632365342578374")
        self.assertEqual(record.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/2423037932")
        self.assertEqual(record.check_in, date(current_year, 4, 17))
        self.assertEqual(record.check_out, date(current_year, 4, 19))
        self.assertIsNone(record.guests)
        self.assertIn("discount offer", record.message_excerpt)
        self.assertIn("Feedback requested", record.feedback_summary)
        self.assertIn("airbnb-profile-123", record.permission_notes)
        self.assertEqual(record.customer_profile.marketing_consent_status, MarketingConsentStatus.UNKNOWN)
        feedback = CustomerFeedback.objects.get()
        self.assertEqual(feedback.airbnb_guest_record, record)
        self.assertEqual(feedback.customer_profile, record.customer_profile)
        self.assertIn("Feedback requested", feedback.feedback_text)
        self.assertIn("airbnb-profile-123", feedback.permission_notes)

    def test_airbnb_import_service_coalesces_messages_from_same_thread(self):
        first_body = self.AIRBNB_SAMPLE_BODY
        second_body = self.AIRBNB_SAMPLE_BODY.replace("It will be a pleasure", "Can we use the pool?")
        data = {
            "responses": [
                {
                    "id": "gmail-thread-1",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": first_body,
                    "email_ts": "2024-04-04T16:18:54",
                },
                {
                    "id": "gmail-thread-2",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": second_body,
                    "email_ts": "2024-04-04T16:19:33",
                },
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/1773535134")
        self.assertIn("Can we use the pool?", record.message_excerpt)
        self.assertEqual(CustomerFeedback.objects.count(), 1)
        self.assertIn("Can we use the pool?", record.customer_feedback.feedback_text)

    def test_airbnb_import_service_coalesces_same_guest_listing_and_dates(self):
        first_body = self.AIRBNB_SPANISH_REPLY_BODY.replace("2520797227", "2520797000")
        second_body = self.AIRBNB_SPANISH_REPLY_BODY.replace("2520797227", "2520797999").replace(
            "Hola dia a que hora es la salida?",
            "Vamos otra vez y queremos confirmar la piscina.",
        )
        data = {
            "responses": [
                {
                    "id": "gmail-same-stay-1",
                    "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                    "body": first_body,
                    "email_ts": "2026-05-03T15:40:25",
                },
                {
                    "id": "gmail-same-stay-2",
                    "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                    "body": second_body,
                    "email_ts": "2026-05-03T15:42:25",
                },
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/2520797000")
        self.assertIn("confirmar la piscina", record.message_excerpt)
        self.assertEqual(CustomerFeedback.objects.count(), 1)
        self.assertIn("confirmar la piscina", record.customer_feedback.feedback_text)

    def test_airbnb_import_service_preserves_initial_inquiry_guest_identity(self):
        data = {
            "responses": [
                {
                    "id": "gmail-reply-first",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": self.AIRBNB_SAMPLE_BODY,
                    "email_ts": "2024-04-04T16:18:54",
                },
                {
                    "id": "gmail-initial-second",
                    "subject": "Inquiry for 6 Bedrooms Vacation Home & Pool (Apartment G-102) for Aug 22 – Sep 1, 2024",
                    "body": self.AIRBNB_INITIAL_INQUIRY_BODY,
                    "email_ts": "2024-04-04T15:44:13",
                },
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        self.assertEqual(AirbnbGuestRecord.objects.get().guest_name, "Ana")

    def test_airbnb_guest_record_tracks_stay_feedback_and_permission_notes(self):
        item = BookableItem.objects.create(
            name="Airbnb Stay",
            slug="airbnb-stay",
            category=BookingCategory.STAY,
            short_description="A stay from Airbnb.",
            is_active=True,
        )
        profile = CustomerProfile.objects.create(
            name="Diana",
            source=ContactSource.AIRBNB,
            marketing_consent_status=MarketingConsentStatus.UNKNOWN,
        )

        record = AirbnbGuestRecord.objects.create(
            customer_profile=profile,
            item=item,
            guest_name="Diana",
            listing_title="6 Bedrooms Vacation Home & Pool",
            airbnb_listing_id="588632365342578374",
            check_in=date(2024, 8, 22),
            check_out=date(2024, 9, 1),
            guests=10,
            feedback_summary="Positive Airbnb message thread.",
            permission_notes="Contact through Airbnb thread; no marketing opt-in yet.",
        )

        self.assertEqual(record.stay_dates, "2024-08-22 to 2024-09-01")
        self.assertFalse(profile.can_receive_promotions)
        feedback = CustomerFeedback.sync_from_airbnb_record(record)
        self.assertEqual(feedback.customer_profile, profile)
        self.assertEqual(feedback.item, item)
        self.assertEqual(feedback.feedback_text, "Positive Airbnb message thread.")

    def test_promotion_recipients_are_limited_to_opted_in_profiles(self):
        opted_in = CustomerProfile.objects.create(
            name="Opted In",
            email="opted@example.com",
            marketing_consent_status=MarketingConsentStatus.OPTED_IN,
        )
        CustomerProfile.objects.create(
            name="Unknown",
            email="unknown@example.com",
            marketing_consent_status=MarketingConsentStatus.UNKNOWN,
        )
        CustomerProfile.objects.create(
            name="Opted Out",
            email="out@example.com",
            marketing_consent_status=MarketingConsentStatus.OPTED_OUT,
        )
        promotion = Promotion.objects.create(
            title="Future Stay",
            subject="MLADIS future stay offer",
            message="A small thank-you offer.",
        )

        recipients = PromotionEmailService().build_recipients(promotion)

        self.assertEqual(len(recipients), 1)
        self.assertEqual(recipients[0].customer_profile, opted_in)
        self.assertEqual(recipients[0].email, "opted@example.com")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_manual_promotion_recipient_without_opt_in_is_not_sent(self):
        promotion = Promotion.objects.create(
            title="Manual recipient",
            subject="MLADIS future stay offer",
            message="A small thank-you offer.",
        )
        recipient = PromotionRecipient.objects.create(
            promotion=promotion,
            email="manual@example.com",
            name="Manual",
        )

        sent = PromotionEmailService().send_promotion(promotion)

        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)
        recipient.refresh_from_db()
        self.assertIn("not opted in", recipient.error)

    def test_admin_airbnb_guest_import_page_loads(self):
        user = get_user_model().objects.create_user(
            username="airbnb-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:bookings_airbnbguestrecord_import"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Import Airbnb guests")

    def test_admin_airbnb_guest_import_dry_run_does_not_write_records(self):
        user = get_user_model().objects.create_user(
            username="airbnb-dry-run-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        upload = SimpleUploadedFile(
            "airbnb-guests.json",
            self._airbnb_import_json("999999999999999998"),
            content_type="application/json",
        )

        response = self.client.post(
            reverse("admin:bookings_airbnbguestrecord_import"),
            {"import_file": upload, "dry_run": "on"},
        )

        self.assertRedirects(response, reverse("admin:bookings_airbnbguestrecord_changelist"))
        self.assertEqual(AirbnbGuestRecord.objects.count(), 0)

    def test_admin_airbnb_guest_import_creates_records(self):
        user = get_user_model().objects.create_user(
            username="airbnb-import-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        item = BookableItem.objects.create(
            name="Admin imported stay",
            slug="admin-imported-stay",
            category=BookingCategory.STAY,
            short_description="A stay from Airbnb.",
            airbnb_listing_id="999999999999999997",
            is_active=True,
        )
        upload = SimpleUploadedFile(
            "airbnb-guests.json",
            self._airbnb_import_json("999999999999999997"),
            content_type="application/json",
        )

        response = self.client.post(
            reverse("admin:bookings_airbnbguestrecord_import"),
            {"import_file": upload},
        )

        self.assertRedirects(response, reverse("admin:bookings_airbnbguestrecord_changelist"))
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.item, item)
        self.assertEqual(record.guest_name, "Diana")
        self.assertEqual(record.customer_profile.source, ContactSource.AIRBNB)
        self.assertEqual(CustomerFeedback.objects.get().airbnb_guest_record, record)

    def _airbnb_import_json(self, listing_id):
        body = self.AIRBNB_SAMPLE_BODY.replace("588632365342578374", listing_id)
        data = {
            "responses": [
                {
                    "id": f"gmail-{listing_id}",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": body,
                    "email_ts": "2024-04-04T16:18:54",
                }
            ]
        }
        return json.dumps(data).encode()

    def test_ops_reservations_requires_staff_login(self):
        response = self.client.get(reverse("bookings:ops-reservations"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_ops_reservations_lists_customer_groups_feedback_and_contact(self):
        user = get_user_model().objects.create_user(
            username="reservation-ops",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(user)
        profile = CustomerProfile.objects.create(
            name="Diana",
            email="diana@example.com",
            phone="631-555-0100",
            segment=ClientSegment.VIP,
            source=ContactSource.AIRBNB,
            marketing_consent_status=MarketingConsentStatus.REQUESTED,
        )
        record = AirbnbGuestRecord.objects.create(
            customer_profile=profile,
            guest_name="Diana",
            email="",
            phone="",
            listing_title="6 Bedrooms Vacation Home & Pool",
            airbnb_listing_id="588632365342578374",
            check_in=date(2024, 8, 22),
            check_out=date(2024, 9, 1),
            guests=10,
            feedback_summary="Loved the pool and the host support.",
            airbnb_thread_url="https://www.airbnb.com/hosting/thread/1773535134",
        )
        CustomerFeedback.sync_from_airbnb_record(record)

        response = self.client.get(reverse("bookings:ops-reservations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reservations")
        self.assertContains(response, "Diana")
        self.assertContains(response, "VIP")
        self.assertContains(response, "diana@example.com")
        self.assertContains(response, "Loved the pool")
        self.assertContains(response, "Feedback")
        self.assertContains(response, "Customer groups")

    def test_ops_reservations_filters_by_customer_group_and_exports_csv(self):
        user = get_user_model().objects.create_user(
            username="reservation-export-ops",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(user)
        vip_profile = CustomerProfile.objects.create(
            name="VIP Guest",
            email="vip@example.com",
            segment=ClientSegment.VIP,
            source=ContactSource.AIRBNB,
        )
        favorite_profile = CustomerProfile.objects.create(
            name="Favorite Guest",
            email="favorite@example.com",
            segment=ClientSegment.FAVORITE,
            source=ContactSource.AIRBNB,
        )
        AirbnbGuestRecord.objects.create(
            customer_profile=vip_profile,
            guest_name="VIP Guest",
            listing_title="VIP Stay",
            check_in=date(2024, 8, 22),
            check_out=date(2024, 8, 24),
        )
        AirbnbGuestRecord.objects.create(
            customer_profile=favorite_profile,
            guest_name="Favorite Guest",
            listing_title="Favorite Stay",
            check_in=date(2024, 9, 2),
            check_out=date(2024, 9, 4),
        )

        response = self.client.get(reverse("bookings:ops-reservations"), {"segment": ClientSegment.VIP})

        self.assertContains(response, "VIP Guest")
        self.assertNotContains(response, "Favorite Guest")

        csv_response = self.client.get(
            reverse("bookings:ops-reservations"),
            {"segment": ClientSegment.VIP, "format": "csv"},
        )

        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        content = csv_response.content.decode()
        self.assertIn("VIP Guest", content)
        self.assertNotIn("Favorite Guest", content)


@override_settings(STORAGES=TEST_STORAGES)
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
