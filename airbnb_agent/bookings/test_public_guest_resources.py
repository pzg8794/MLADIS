"""Security and behavior tests for public guest offers."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client, RequestFactory, TestCase, override_settings
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone

from .models import (
    AudienceSubscription, AudienceCampaignSettings, BookableItem, BookingInquiry, Coupon, CouponDiscountType, CustomerProfile, Promotion,
    MarketingConsentStatus, PublicOfferRateLimit, PromotionRecipient,
)
from .public_guest_resources import AudienceService, validate_welcome_coupon
from .forms import BookingInquiryForm
from .services import PromotionEmailService, ReservationRequestService


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
class PublicOffersTests(TestCase):
    def setUp(self):
        AudienceCampaignSettings.objects.create(signup_enabled=True)
        self.service = AudienceService()
        self.signup_url = reverse("bookings:offers-signup")

    def signup(self, email="guest@example.com", **choices):
        data = {"email": email, **choices}
        return self.client.post(self.signup_url, data)

    def requested(self, email="guest@example.com", welcome=True, seasonal=False):
        self.service.request_signup(email=email, welcome_discount=welcome, seasonal_offers=seasonal)
        return AudienceSubscription.objects.get(email=email.lower())

    def test_choices_and_honeypot(self):
        self.assertEqual(self.signup().status_code, 400)
        response = self.signup(welcome_discount="on", website="spam.example")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AudienceSubscription.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_pending_is_generic_duplicate_and_cooldown(self):
        first = self.signup("Guest@Example.com", welcome_discount="on")
        second = self.signup("guest@example.com", seasonal_offers="on")
        self.assertEqual(first.content, second.content)
        self.assertEqual(AudienceSubscription.objects.count(), 1)
        member = AudienceSubscription.objects.get()
        self.assertTrue(member.pending_welcome_discount)
        self.assertFalse(member.pending_seasonal_offers)
        self.assertIsNone(member.confirmed_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertFalse(CustomerProfile.objects.filter(email__iexact="guest@example.com").exists())

    def test_limit_is_persistent_and_stops_at_30(self):
        for i in range(31):
            self.signup(f"visitor{i}@example.com", seasonal_offers="on")
        self.assertEqual(AudienceSubscription.objects.count(), 30)
        self.assertEqual(len(mail.outbox), 30)
        row = PublicOfferRateLimit.objects.get()
        self.assertEqual(row.request_count, 30)
        self.assertNotIn("127.0.0.1", row.key)

    def test_get_confirm_is_read_only_post_activates_discount_only(self):
        member = self.requested()
        token = self.service.confirmation_token(member)
        url = reverse("bookings:offers-confirm", kwargs={"token": token})
        self.assertEqual(self.client.get(url).status_code, 200)
        member.refresh_from_db()
        self.assertIsNone(member.confirmed_at)
        self.assertIsNone(member.coupon_id)
        self.assertEqual(self.client.post(url).status_code, 200)
        member.refresh_from_db()
        self.assertIsNotNone(member.confirmed_at)
        self.assertFalse(member.seasonal_offers)
        self.assertFalse(CustomerProfile.objects.filter(email__iexact="guest@example.com").exists())
        self.assertEqual(member.coupon.percent_off, Decimal("10.00"))
        self.assertEqual(member.coupon.max_redemptions, 1)
        original_coupon = member.coupon_id
        self.assertEqual(self.client.post(url).status_code, 200)
        member.refresh_from_db()
        self.assertEqual(member.coupon_id, original_coupon)

    def test_expired_tampered_and_superseded_confirmation_fail(self):
        member = self.requested()
        token = self.service.confirmation_token(member)
        with patch("django.core.signing.time.time", return_value=timezone.now().timestamp() + 49 * 3600):
            with self.assertRaises(ValidationError):
                self.service.confirm(token)
        with self.assertRaises(ValidationError):
            self.service.confirm(token + "bad")
        member.requested_at = timezone.now() - timedelta(minutes=16)
        member.save(update_fields=["requested_at"])
        self.service.request_signup(email=member.email, welcome_discount=False, seasonal_offers=True)
        with self.assertRaises(ValidationError):
            self.service.confirm(token)
        member.refresh_from_db()
        self.assertIsNone(member.confirmed_at)
        self.assertFalse(CustomerProfile.objects.filter(email__iexact="guest@example.com").exists())

    def test_unsubscribe_get_readonly_post_suppresses_duplicate_profiles_and_pending(self):
        member = self.requested(welcome=False, seasonal=True)
        self.service.confirm(self.service.confirmation_token(member))
        member.refresh_from_db()
        self.assertTrue(member.can_receive_promotions)
        other = CustomerProfile.objects.create(email="GUEST@example.com", marketing_consent_status=MarketingConsentStatus.OPTED_IN)
        member.requested_at = timezone.now() - timedelta(minutes=16)
        member.save(update_fields=["requested_at"])
        self.service.request_signup(email=member.email, welcome_discount=True, seasonal_offers=True)
        member.refresh_from_db()
        pending = self.service.confirmation_token(member)
        token = self.service.unsubscribe_token(member)
        url = reverse("bookings:offers-unsubscribe", kwargs={"token": token})
        self.assertEqual(self.client.get(url).status_code, 200)
        member.refresh_from_db()
        self.assertTrue(member.can_receive_promotions)
        self.assertEqual(self.client.post(url).status_code, 200)
        member.refresh_from_db()
        self.assertFalse(member.can_receive_promotions)
        self.assertFalse(member.pending_welcome_discount)
        self.assertFalse(member.pending_seasonal_offers)
        self.assertFalse(CustomerProfile.objects.filter(email__iexact=member.email).exclude(marketing_consent_status=MarketingConsentStatus.OPTED_OUT).exists())
        with self.assertRaises(ValidationError):
            self.service.confirm(pending)
        other.refresh_from_db()
        self.assertEqual(other.marketing_consent_status, MarketingConsentStatus.OPTED_OUT)

    def test_csrf_is_required_for_public_mutations(self):
        member = self.requested()
        confirm_url = reverse("bookings:offers-confirm", kwargs={"token": self.service.confirmation_token(member)})
        unsubscribe_url = reverse("bookings:offers-unsubscribe", kwargs={"token": self.service.unsubscribe_token(member)})
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.signup_url, {"email": "x@example.com", "welcome_discount": "on"}).status_code, 403)
        self.assertEqual(client.post(confirm_url).status_code, 403)
        self.assertEqual(client.post(unsubscribe_url).status_code, 403)
        self.assertEqual(client.get(confirm_url).status_code, 200)
        csrf = client.cookies["csrftoken"].value
        self.assertEqual(client.post(confirm_url, {"csrfmiddlewaretoken": csrf}).status_code, 200)

    def test_welcome_coupon_email_binding_and_single_redemption(self):
        member = self.requested()
        self.service.confirm(self.service.confirmation_token(member))
        member.refresh_from_db()
        stale_coupon = Coupon.objects.get(pk=member.coupon_id)
        with self.assertRaises(ValidationError):
            validate_welcome_coupon(member.coupon, "other@example.com", redeem=True)
        self.assertTrue(validate_welcome_coupon(member.coupon, "GUEST@example.com", redeem=True))
        with self.assertRaises(ValidationError):
            validate_welcome_coupon(stale_coupon, member.email, redeem=True)
        ordinary = Coupon.objects.create(code="ORDINARY", discount_type=CouponDiscountType.PERCENT, percent_off=Decimal("5"))
        self.assertFalse(validate_welcome_coupon(ordinary, "other@example.com", redeem=True))
        ordinary.refresh_from_db()
        self.assertEqual(ordinary.redemption_count, 0)

    def test_discount_only_blocks_promotional_send_even_with_legacy_optin(self):
        member = self.requested()
        self.service.confirm(self.service.confirmation_token(member))
        profile = CustomerProfile.objects.create(email=member.email, marketing_consent_status=MarketingConsentStatus.OPTED_IN)
        recipient = PromotionRecipient(email=member.email, customer_profile=profile)
        self.assertFalse(PromotionEmailService()._recipient_has_opted_in(recipient))

    def test_seasonal_consent_only_after_confirmation(self):
        member = self.requested(welcome=False, seasonal=True)
        self.assertFalse(CustomerProfile.objects.filter(email__iexact="guest@example.com").exists())
        self.service.confirm(self.service.confirmation_token(member))
        member.refresh_from_db()
        profile = CustomerProfile.objects.get(email=member.email)
        self.assertEqual(profile.marketing_consent_status, MarketingConsentStatus.OPTED_IN)
        self.assertTrue(member.can_receive_promotions)
        self.assertIsNone(member.coupon_id)
        self.assertIn("seasonal", member.consent_text.lower())

    def test_send_failure_never_activates_preferences(self):
        with patch("bookings.public_guest_resources.send_mail", side_effect=RuntimeError("unavailable")):
            response = self.signup(welcome_discount="on", seasonal_offers="on")
        self.assertEqual(response.status_code, 200)
        member = AudienceSubscription.objects.get()
        self.assertIsNone(member.confirmed_at)
        self.assertIsNone(member.coupon_id)
        self.assertFalse(member.can_receive_promotions)
        self.assertFalse(CustomerProfile.objects.filter(email__iexact="guest@example.com").exists())

    def test_guide_has_no_signup_offer_checkout_time_or_new_contract(self):
        response = self.client.get(reverse("bookings:airbnb-stay-guide"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode().lower()
        for listing_id in ("582161420407543691", "587194328968598250", "588632365342578374"):
            self.assertIn(listing_id, body)
        for prohibited in ("/offers/", "subscribe", "10%", "11:00 am", "12:00 pm", "accept the", "security deposit"):
            self.assertNotIn(prohibited, body)
        self.assertIn("does not change a booking", body)
        self.assertIn("your reservation’s airbnb house rules", body)

    def test_welcome_coupon_form_binding_service_redemption_and_rollback(self):
        member = self.requested()
        self.service.confirm(self.service.confirmation_token(member))
        member.refresh_from_db()
        item = BookableItem.objects.create(name="Test home", slug="offers-test-home", short_description="Test", starting_price=Decimal("100.00"))
        today = timezone.localdate()
        data = {"item": item.pk, "guest_name": "Guest", "email": "other@example.com", "phone": "5550100", "check_in": today + timedelta(days=30), "check_out": today + timedelta(days=32), "guests": 2, "coupon_code": member.coupon.code}
        wrong = BookingInquiryForm(data=data)
        self.assertFalse(wrong.is_valid())
        self.assertIn("coupon_code", wrong.errors)
        data["email"] = member.email
        form = BookingInquiryForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        request = RequestFactory().post("/")
        request.user = AnonymousUser()
        request.session = {}
        with patch.object(BookingInquiry, "save", side_effect=RuntimeError("failed")):
            with self.assertRaises(RuntimeError):
                ReservationRequestService().create_from_form(form, request)
        member.coupon.refresh_from_db()
        self.assertEqual(member.coupon.redemption_count, 0)
        inquiry = ReservationRequestService().create_from_form(form, request)
        member.coupon.refresh_from_db()
        self.assertEqual(member.coupon.redemption_count, 1)
        self.assertGreater(inquiry.subtotal_cents, 0)
        self.assertEqual(inquiry.discount_cents, member.coupon.discount_for(inquiry.subtotal_cents))
        member.refresh_from_db()
        self.assertEqual(member.redeemed_inquiry_id, inquiry.pk)
        fresh = BookingInquiry.objects.select_related("coupon").get(pk=inquiry.pk)
        original_discount = fresh.discount_cents
        ReservationRequestService().prepare(fresh, coupon=fresh.coupon, redeem_coupon=False)
        self.assertEqual(fresh.discount_cents, original_discount)
        member.coupon.refresh_from_db()
        self.assertEqual(member.coupon.redemption_count, 1)
        another = BookingInquiry.objects.create(item=item, guest_name="Guest", email=member.email, check_in=data["check_in"], check_out=data["check_out"], guests=2)
        with self.assertRaises(ValidationError):
            ReservationRequestService().prepare(another, coupon=member.coupon, redeem_coupon=False)
        fresh.email = "different@example.com"
        with self.assertRaises(ValidationError):
            ReservationRequestService().prepare(fresh, coupon=fresh.coupon, redeem_coupon=False)

    def test_seasonal_send_requires_address_then_unsubscribe_stops_it(self):
        member = self.requested(welcome=False, seasonal=True)
        self.service.confirm(self.service.confirmation_token(member))
        member.refresh_from_db()
        promotion = Promotion.objects.create(title="Seasonal", subject="Seasonal offer", message="A future offer")
        recipient = PromotionRecipient.objects.create(promotion=promotion, customer_profile=member.customer_profile, email=member.email)
        with patch("bookings.services.send_mail") as sender:
            self.assertEqual(PromotionEmailService().send_promotion(promotion), 0)
            sender.assert_not_called()
            recipient.refresh_from_db()
            self.assertIn("mailing address", recipient.error)
            config = AudienceCampaignSettings.current()
            config.postal_address = "Example public mailing address"
            config.save()
            self.assertEqual(PromotionEmailService().send_promotion(promotion), 1)
            sender.assert_called_once()
            self.assertIn("Unsubscribe", sender.call_args.args[1])
            self.assertIn("Example public mailing address", sender.call_args.args[1])
            self.service.unsubscribe(self.service.unsubscribe_token(member))
            sender.reset_mock()
            self.assertEqual(PromotionEmailService().send_promotion(promotion), 0)
            sender.assert_not_called()

    def test_disabled_signup_is_explicit_and_creates_no_records_or_mail(self):
        config = AudienceCampaignSettings.current()
        config.signup_enabled = False
        config.save()
        page = self.client.get(self.signup_url)
        self.assertContains(page, "Email signup is temporarily unavailable")
        self.assertNotContains(page, 'name="email"')
        response = self.signup("blocked@example.com", welcome_discount="on")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(AudienceSubscription.objects.filter(email="blocked@example.com").exists())
        self.assertFalse(CustomerProfile.objects.filter(email="blocked@example.com").exists())
        self.assertEqual(len(mail.outbox), 0)
