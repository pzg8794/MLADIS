"""Public stay information and explicit, verified offers preferences."""
import hashlib
import ipaddress
import secrets
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django import forms
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import get_connection, send_mail
from django.db import transaction
from django.db.models import F
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

from .models import (
    AudienceSubscription, Coupon, CouponDiscountType, CustomerProfile,
    MarketingConsentStatus, PublicOfferRateLimit, AudienceCampaignSettings,
)


PUBLIC_ORIGIN = "https://mladis.com"
CONSENT_VERSION = "2026-10-29"
DISCOUNT_CONSENT = "Get a 10% welcome discount after confirming my email."
SEASONAL_CONSENT = "Email me occasional seasonal offers and future discounts from MLADIS Bookings."
GENERIC_PENDING = "If your request can be processed, we will email a confirmation link. Check your inbox and spam folder. A recent request may already be waiting there."


class OffersSignupForm(forms.Form):
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    welcome_discount = forms.BooleanField(required=False, label=DISCOUNT_CONSENT)
    seasonal_offers = forms.BooleanField(required=False, label=SEASONAL_CONSENT)
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("welcome_discount") and not cleaned.get("seasonal_offers"):
            raise forms.ValidationError("Choose the welcome discount, seasonal offers, or both.")
        return cleaned


class AudienceService:
    confirm_salt = "mladis.offers.confirm.v1"
    unsubscribe_salt = "mladis.offers.unsubscribe.v1"

    @staticmethod
    def absolute_url(name, **kwargs):
        return PUBLIC_ORIGIN + reverse(name, kwargs=kwargs or None)

    def confirmation_token(self, member):
        return signing.dumps(
            {"id": str(member.public_id), "nonce": str(member.verification_nonce)},
            salt=self.confirm_salt,
        )

    def unsubscribe_token(self, member):
        return signing.dumps(
            {"id": str(member.public_id), "nonce": str(member.unsubscribe_nonce)},
            salt=self.unsubscribe_salt,
        )

    def unsubscribe_url(self, member):
        return self.absolute_url("bookings:offers-unsubscribe", token=self.unsubscribe_token(member))

    def resolve(self, token, *, unsubscribe=False, lock=False):
        try:
            payload = signing.loads(
                token, salt=self.unsubscribe_salt if unsubscribe else self.confirm_salt,
                max_age=None if unsubscribe else 48 * 60 * 60,
            )
            queryset = AudienceSubscription.objects
            if lock:
                queryset = queryset.select_for_update()
            member = queryset.get(public_id=payload["id"])
            nonce = member.unsubscribe_nonce if unsubscribe else member.verification_nonce
            if not secrets.compare_digest(str(nonce), str(payload["nonce"])):
                raise signing.BadSignature("Superseded link")
            return member
        except (signing.BadSignature, KeyError, TypeError, ValueError, ValidationError, AudienceSubscription.DoesNotExist):
            raise ValidationError("This link is invalid, expired, or has been replaced. Please request a new confirmation.")

    def allow_request(self, request):
        """A DB-backed per-source hourly cap shared by all application workers."""
        remote = request.META.get("REMOTE_ADDR", "")
        try:
            address = ipaddress.ip_address(remote)
            if address.is_loopback and request.META.get("HTTP_X_FORWARDED_FOR"):
                remote = request.META["HTTP_X_FORWARDED_FOR"].split(",")[-1].strip()
                ipaddress.ip_address(remote)
        except ValueError:
            remote = "unknown"
        now = timezone.now()
        window = now.replace(minute=0, second=0, microsecond=0)
        key = hashlib.sha256(f"{settings.SECRET_KEY}:offers:{remote}:{window.isoformat()}".encode()).hexdigest()
        PublicOfferRateLimit.objects.filter(window_start__lt=now - timedelta(days=1)).delete()
        with transaction.atomic():
            row, _ = PublicOfferRateLimit.objects.get_or_create(key=key, defaults={"window_start": window})
            return bool(PublicOfferRateLimit.objects.filter(pk=row.pk, request_count__lt=30).update(request_count=F("request_count") + 1))

    def request_signup(self, *, email, welcome_discount, seasonal_offers):
        now = timezone.now()
        with transaction.atomic():
            member, _ = AudienceSubscription.objects.get_or_create(email=email.strip().lower())
            member = AudienceSubscription.objects.select_for_update().get(pk=member.pk)
            if member.requested_at and member.requested_at > now - timedelta(minutes=15):
                return
            member.pending_welcome_discount = welcome_discount
            member.pending_seasonal_offers = seasonal_offers
            member.requested_at = now
            member.verification_nonce = uuid4()
            member.verification_used_at = None
            member.save()
        link = self.absolute_url("bookings:offers-confirm", token=self.confirmation_token(member))
        choices = []
        if welcome_discount:
            choices.append("a 10% welcome discount for one eligible future direct booking")
        if seasonal_offers:
            choices.append("occasional seasonal offers and future discounts")
        body = (
            "Someone entered this email address on MLADIS Bookings and requested "
            + " and ".join(choices)
            + ".\n\nTo confirm that it was you, open this link and select Confirm my email:\n"
            + link
            + "\n\nThe link expires in 48 hours. Nothing is activated until you confirm. "
            "If you did not request this, ignore this email or cancel the request here:\n"
            + self.unsubscribe_url(member)
            + "\n\nMLADIS Bookings\nThis email confirms a request; it is not a booking or payment request."
        )
        # Do not report a console/dummy backend as real production delivery.
        non_delivery = ("console.EmailBackend", "dummy.EmailBackend", "filebased.EmailBackend")
        if any(settings.EMAIL_BACKEND.endswith(item) for item in non_delivery) and not settings.DEBUG:
            return
        try:
            send_mail("Confirm your MLADIS email preferences", body, settings.DEFAULT_FROM_EMAIL, [member.email], fail_silently=False, connection=get_connection(timeout=10))
        except Exception:
            # Public response stays generic and no benefits/marketing are activated.
            return

    def confirm(self, token):
        with transaction.atomic():
            member = self.resolve(token, lock=True)
            if member.verification_used_at:
                return member
            now = timezone.now()
            if member.pending_welcome_discount and not member.coupon_id:
                member.coupon = Coupon.objects.create(
                    code="WELCOME10-" + secrets.token_hex(10).upper(),
                    description="Verified public offers welcome code — one direct booking request",
                    discount_type=CouponDiscountType.PERCENT,
                    percent_off=Decimal("10.00"), max_redemptions=1,
                )
            if member.pending_seasonal_offers:
                profile = CustomerProfile.find_or_create_for_email(member.email)
                profile.marketing_consent_status = MarketingConsentStatus.OPTED_IN
                profile.marketing_consent_at = now
                profile.marketing_consent_source = "verified public offers form " + CONSENT_VERSION
                profile.save(update_fields=["marketing_consent_status", "marketing_consent_at", "marketing_consent_source", "updated_at"])
                member.customer_profile = profile
                member.seasonal_offers = True
                member.unsubscribed_at = None
            member.confirmed_at = now
            member.verification_used_at = now
            member.consent_version = CONSENT_VERSION
            member.consent_text = "\n".join(
                text for selected, text in (
                    (member.pending_welcome_discount, DISCOUNT_CONSENT),
                    (member.pending_seasonal_offers, SEASONAL_CONSENT),
                ) if selected
            )
            member.save()
            return member

    def unsubscribe(self, token):
        with transaction.atomic():
            member = self.resolve(token, unsubscribe=True, lock=True)
            member.seasonal_offers = False
            member.pending_seasonal_offers = False
            member.pending_welcome_discount = False
            member.unsubscribed_at = timezone.now()
            member.verification_nonce = uuid4()
            member.save()
            # Suppress duplicate legacy profiles sharing the same email as well.
            for profile in CustomerProfile.objects.filter(email__iexact=member.email):
                profile.marketing_consent_status = MarketingConsentStatus.OPTED_OUT
                profile.marketing_consent_source = "public offers unsubscribe"
                profile.save(update_fields=["marketing_consent_status", "marketing_consent_source", "updated_at"])
            return member


def validate_welcome_coupon(coupon, email, *, redeem=False, inquiry=None):
    """Leave existing coupons alone; bind new welcome codes to their verified email."""
    member = AudienceSubscription.objects.filter(coupon=coupon).first()
    if member is None:
        return False
    if not member.confirmed_at or member.email != (email or "").strip().lower():
        raise ValidationError("This welcome code is not available for this email or has already been used.")
    if not redeem and inquiry is not None and inquiry.pk and member.redeemed_inquiry_id == inquiry.pk:
        # Checkout may reprice its own existing request without redeeming again.
        return True
    if not coupon.is_valid():
        raise ValidationError("This welcome code is not available for this email or has already been used.")
    if redeem:
        # The surrounding reservation transaction rolls this back on any later failure.
        if not Coupon.objects.filter(pk=coupon.pk, is_active=True, redemption_count=0).update(redemption_count=1):
            raise ValidationError("This welcome code has already been used.")
    return True


class AirbnbStayGuideView(TemplateView):
    template_name = "bookings/airbnb_stay_guide.html"


class OffersPrivacyView(TemplateView):
    template_name = "bookings/offers_privacy.html"


@method_decorator(never_cache, name="dispatch")
class OffersSignupView(View):
    @staticmethod
    def signup_available():
        config = AudienceCampaignSettings.current()
        return bool(config and config.signup_enabled)

    def get(self, request):
        return render(request, "bookings/offers_signup.html", {"form": OffersSignupForm(), "signup_available": self.signup_available()})

    def post(self, request):
        if not self.signup_available():
            return render(request, "bookings/offers_signup.html", {"form": OffersSignupForm(), "signup_available": False}, status=503)
        form = OffersSignupForm(request.POST)
        if not form.is_valid():
            return render(request, "bookings/offers_signup.html", {"form": form, "signup_available": True}, status=400)
        service = AudienceService()
        if not form.cleaned_data["website"] and service.allow_request(request):
            service.request_signup(
                email=form.cleaned_data["email"],
                welcome_discount=form.cleaned_data["welcome_discount"],
                seasonal_offers=form.cleaned_data["seasonal_offers"],
            )
        return render(request, "bookings/offers_status.html", {"title": "Check your inbox", "message": GENERIC_PENDING})


@method_decorator(never_cache, name="dispatch")
class OffersConfirmView(View):
    def get(self, request, token):
        try:
            AudienceService().resolve(token)
        except ValidationError as error:
            return render(request, "bookings/offers_status.html", {"title": "Link unavailable", "message": error.messages[0]}, status=400)
        return render(request, "bookings/offers_status.html", {"title": "Confirm your email", "message": "Activate only the choices you selected. This does not change any reservation.", "confirmation": True})

    def post(self, request, token):
        service = AudienceService()
        try:
            member = service.confirm(token)
        except ValidationError as error:
            return render(request, "bookings/offers_status.html", {"title": "Link unavailable", "message": error.messages[0]}, status=400)
        return render(request, "bookings/offers_status.html", {
            "title": "Your email is confirmed", "message": "Your selected preferences are active. Save your welcome code below if you requested one.",
            "coupon_code": member.coupon.code if member.coupon_id else "",
            "unsubscribe_url": service.unsubscribe_url(member),
        })


@method_decorator(never_cache, name="dispatch")
class OffersUnsubscribeView(View):
    def get(self, request, token):
        try:
            AudienceService().resolve(token, unsubscribe=True)
        except ValidationError:
            return render(request, "bookings/offers_status.html", {"title": "Link unavailable", "message": "This unsubscribe link is invalid."}, status=400)
        return render(request, "bookings/offers_status.html", {"title": "Unsubscribe from offers", "message": "Confirm to stop seasonal offers and cancel any pending email confirmation. Your reservation and any already issued welcome code stay unchanged.", "confirmation": True, "button_label": "Unsubscribe"})

    def post(self, request, token):
        try:
            AudienceService().unsubscribe(token)
        except ValidationError:
            return render(request, "bookings/offers_status.html", {"title": "Link unavailable", "message": "This unsubscribe link is invalid."}, status=400)
        return render(request, "bookings/offers_status.html", {"title": "You are unsubscribed", "message": "Seasonal offers have been stopped. Your reservation and any already issued welcome code are unchanged."})
