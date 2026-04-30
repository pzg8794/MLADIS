import os
import json
from datetime import timedelta
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.internal.flows.signup import process_auto_signup
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .adapters import MLADISAccountAdapter, MLADISSocialAccountAdapter
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
    SiteSettings,
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


class LegalPageTests(TestCase):
    def setUp(self):
        site_settings = SiteSettings.current()
        site_settings.contact_email = "privacy@example.com"
        site_settings.save(update_fields=["contact_email", "updated_at"])

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
        self.assertContains(response, "Visits by day")


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
