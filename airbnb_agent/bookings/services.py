from dataclasses import dataclass

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
import stripe

from .models import (
    AdminAccess,
    AgentConversation,
    BookableItem,
    BookingInquiry,
    CancellationPolicy,
    ClientSegment,
    CustomerProfile,
    DamageDeposit,
    DepositStatus,
    Donation,
    DonationStatus,
    EmailDeliveryStatus,
    Invoice,
    InvoiceStatus,
    Promotion,
    PromotionRecipient,
    PromotionStatus,
)


@dataclass(frozen=True)
class AgentRequest:
    message: str
    session_id: str
    item_id: int | None = None
    visitor_name: str = ""
    visitor_email: str = ""


@dataclass(frozen=True)
class AgentResponse:
    reply: str
    conversation_id: int | None = None


@dataclass(frozen=True)
class DepositCheckoutResult:
    success: bool
    message: str
    checkout_url: str = ""


class AdminAccessService:
    """Promotes known owner/admin emails after password or social login."""

    def apply_to_user(self, user):
        if not user or not getattr(user, "email", ""):
            return None

        access = AdminAccess.objects.filter(email__iexact=user.email, is_active=True).first()
        if not access:
            return None

        user_fields = []
        if access.grant_staff_access and not user.is_staff:
            user.is_staff = True
            user_fields.append("is_staff")
        if access.grant_superuser_access and not user.is_superuser:
            user.is_superuser = True
            user_fields.append("is_superuser")

        name_parts = access.name.split()
        if name_parts and not user.first_name:
            user.first_name = name_parts[0]
            user_fields.append("first_name")
        if len(name_parts) > 1 and not user.last_name:
            user.last_name = " ".join(name_parts[1:])
            user_fields.append("last_name")

        if user_fields:
            user.save(update_fields=[*user_fields, "last_login"] if user.last_login else user_fields)

        self._sync_customer_profile(user, access)
        return access

    def _sync_customer_profile(self, user, access):
        profile = CustomerProfile.objects.filter(user=user).first()
        if not profile and user.email:
            profile = CustomerProfile.objects.filter(email__iexact=user.email, user__isnull=True).first()
        if not profile:
            CustomerProfile.objects.create(
                user=user,
                name=access.name,
                email=access.email,
                phone=access.phone,
                segment=ClientSegment.VIP,
            )
            return

        changed = []
        if profile.user_id != user.id:
            profile.user = user
            changed.append("user")
        for field, value in {
            "name": access.name,
            "email": access.email,
            "phone": access.phone,
            "segment": ClientSegment.VIP,
        }.items():
            if value and getattr(profile, field) != value:
                setattr(profile, field, value)
                changed.append(field)
        if changed:
            profile.save(update_fields=[*changed, "updated_at"])


class BookingAgentService:
    """Boundary for current stub behavior and future model-backed booking logic."""

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY

    def reply(self, request: AgentRequest) -> AgentResponse:
        item = self._get_item(request.item_id)
        topic = QuestionAnalyticsService.classify(request.message)

        if not self.api_key:
            reply = self._setup_reply(item)
        else:
            reply = self._stubbed_reply(request.message, item)

        conversation = AgentConversation.objects.create(
            session_id=request.session_id,
            item=item,
            visitor_name=request.visitor_name,
            visitor_email=request.visitor_email,
            last_user_message=request.message,
            last_agent_reply=reply,
            question_topic=topic,
            metadata={"agent_mode": "stub", "topic": topic},
        )
        return AgentResponse(reply=reply, conversation_id=conversation.id)

    def _get_item(self, item_id):
        if not item_id:
            return None
        return BookableItem.objects.filter(id=item_id, is_active=True).first()

    def _setup_reply(self, item):
        subject = item.name if item else "your booking"
        return (
            f"I can help with {subject}, dates, guest count, amenities, and custom services. "
            "The live AI key is not configured yet, so I am running in setup mode."
        )

    def _stubbed_reply(self, message, item):
        subject = item.name if item else "MLADIS bookings"
        return (
            f"I am ready to help with {subject}. I received: \"{message}\". "
            "Next step: connect this service to live availability, pricing, and direct booking."
        )


class QuestionAnalyticsService:
    TOPIC_KEYWORDS = {
        "pricing": {"price", "cost", "rate", "discount", "coupon", "deal", "deposit", "pago", "precio"},
        "availability": {"available", "availability", "dates", "calendar", "book", "reserve", "fecha", "reservar"},
        "location": {"location", "embassy", "embajada", "mall", "airport", "playa", "beach", "where", "address"},
        "amenities": {"pool", "bed", "bedroom", "bath", "kitchen", "wifi", "parking", "amenity", "piscina"},
        "rules": {"rules", "party", "smoking", "pet", "quiet", "cancel", "refund", "regla", "cancelar"},
        "services": {"transport", "pickup", "cleaning", "tour", "restaurant", "service", "limpieza"},
    }

    @classmethod
    def classify(cls, message):
        lowered = (message or "").lower()
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return topic
        return "general"


class ReservationRequestService:
    def prepare(self, inquiry: BookingInquiry, coupon=None):
        inquiry.customer_profile = CustomerProfile.find_or_create_for_email(
            inquiry.email,
            defaults={
                "name": inquiry.guest_name,
                "phone": inquiry.phone,
            },
        )
        inquiry.is_blacklist_flagged = bool(
            inquiry.customer_profile and inquiry.customer_profile.segment == ClientSegment.BLACKLISTED
        )
        inquiry.cancellation_policy = inquiry.cancellation_policy or CancellationPolicy.default()
        inquiry.currency = settings.DEPOSIT_CURRENCY
        inquiry.deposit_cents = settings.DEPOSIT_AMOUNT_CENTS

        if coupon:
            inquiry.coupon = coupon
            inquiry.coupon_code = coupon.code
            inquiry.discount_cents = coupon.discount_for(inquiry.subtotal_cents)
            type(coupon).objects.filter(pk=coupon.pk).update(redemption_count=F("redemption_count") + 1)

        if inquiry.is_admin_test:
            inquiry.subtotal_cents = 0
            inquiry.discount_cents = 0
            inquiry.deposit_cents = 0
            inquiry.total_cents = 0
        else:
            inquiry.total_cents = max(
                inquiry.subtotal_cents - inquiry.discount_cents + inquiry.deposit_cents,
                0,
            )
        return inquiry


class BookingEmailService:
    def send_inquiry_notifications(self, inquiry: BookingInquiry, request=None):
        recipients = settings.BOOKING_INQUIRY_RECIPIENTS
        if not recipients:
            inquiry.email_delivery_status = EmailDeliveryStatus.FAILED
            inquiry.email_error = "No BOOKING_INQUIRY_RECIPIENTS configured."
            inquiry.save(update_fields=["email_delivery_status", "email_error", "updated_at"])
            return False

        subject = f"New MLADIS booking request: {inquiry.guest_name}"
        body = self._admin_body(inquiry, request)
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False,
            )
            send_mail(
                "We received your MLADIS reservation request",
                self._customer_body(inquiry),
                settings.DEFAULT_FROM_EMAIL,
                [inquiry.email],
                fail_silently=False,
            )
        except Exception as error:  # SMTP providers raise a few different exception classes.
            inquiry.email_delivery_status = EmailDeliveryStatus.FAILED
            inquiry.email_error = str(error)
            inquiry.save(update_fields=["email_delivery_status", "email_error", "updated_at"])
            return False

        inquiry.email_delivery_status = EmailDeliveryStatus.SENT
        inquiry.email_sent_at = timezone.now()
        inquiry.email_error = ""
        inquiry.save(update_fields=["email_delivery_status", "email_sent_at", "email_error", "updated_at"])
        return True

    def _admin_body(self, inquiry, request=None):
        item_name = inquiry.item.name if inquiry.item else "Flexible / help me choose"
        admin_url = ""
        if request:
            admin_url = request.build_absolute_uri(f"/admin/bookings/bookinginquiry/{inquiry.id}/change/")
        return "\n".join(
            [
                "New MLADIS booking request",
                "",
                f"Guest: {inquiry.guest_name}",
                f"Email: {inquiry.email}",
                f"Phone: {inquiry.phone or '-'}",
                f"Stay: {item_name}",
                f"Dates: {inquiry.check_in} to {inquiry.check_out} ({inquiry.nights} nights)",
                f"Guests: {inquiry.guests}",
                f"Coupon: {inquiry.coupon_code or '-'}",
                f"Admin test: {'yes' if inquiry.is_admin_test else 'no'}",
                f"Blacklisted flag: {'yes' if inquiry.is_blacklist_flagged else 'no'}",
                "",
                inquiry.message or "No extra message.",
                "",
                admin_url,
            ]
        )

    def _customer_body(self, inquiry):
        item_name = inquiry.item.name if inquiry.item else "your MLADIS stay"
        return "\n".join(
            [
                f"Hi {inquiry.guest_name},",
                "",
                f"We received your request for {item_name}.",
                f"Dates: {inquiry.check_in} to {inquiry.check_out}",
                f"Guests: {inquiry.guests}",
                "",
                "This is an admin-confirmed request. We will review availability and follow up with the next step.",
                "",
                "MLADIS",
            ]
        )


class InvoiceEmailService:
    def send_invoice(self, invoice: Invoice, request=None):
        invoice_url = ""
        if request:
            invoice_url = request.build_absolute_uri(reverse("bookings:invoice-print", kwargs={"token": invoice.public_token}))
        body = "\n".join(
            [
                f"Hi {invoice.recipient_name},",
                "",
                f"Your MLADIS invoice {invoice.invoice_number} is ready.",
                f"Total: {invoice.display_total}",
                invoice_url,
                "",
                invoice.notes or "Thank you for booking with MLADIS.",
            ]
        )
        try:
            send_mail(
                invoice.subject if hasattr(invoice, "subject") else f"MLADIS invoice {invoice.invoice_number}",
                body,
                settings.DEFAULT_FROM_EMAIL,
                [invoice.recipient_email],
                fail_silently=False,
            )
        except Exception as error:
            invoice.email_status = EmailDeliveryStatus.FAILED
            invoice.email_error = str(error)
            invoice.save(update_fields=["email_status", "email_error", "updated_at"])
            return False
        invoice.status = InvoiceStatus.SENT
        invoice.email_status = EmailDeliveryStatus.SENT
        invoice.sent_at = timezone.now()
        invoice.email_error = ""
        invoice.save(update_fields=["status", "email_status", "sent_at", "email_error", "updated_at"])
        return True


class PromotionEmailService:
    def build_recipients(self, promotion: Promotion):
        profiles = CustomerProfile.objects.exclude(email="")
        if promotion.target_segment != "all":
            profiles = profiles.filter(segment=promotion.target_segment)
        recipients = []
        for profile in profiles:
            recipient, _created = PromotionRecipient.objects.get_or_create(
                promotion=promotion,
                email=profile.email,
                defaults={
                    "customer_profile": profile,
                    "name": profile.name,
                },
            )
            recipients.append(recipient)
        return recipients

    def send_promotion(self, promotion: Promotion):
        recipients = list(promotion.recipients.all()) or self.build_recipients(promotion)
        sent = 0
        for recipient in recipients:
            body = promotion.message
            if promotion.coupon:
                body += f"\n\nCoupon code: {promotion.coupon.code}"
            if promotion.discount_percent:
                body += f"\n\nPromotion discount: {promotion.discount_percent}%"
            try:
                send_mail(
                    promotion.subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    fail_silently=False,
                )
            except Exception as error:
                recipient.status = EmailDeliveryStatus.FAILED
                recipient.error = str(error)
                recipient.save(update_fields=["status", "error"])
                continue
            recipient.status = EmailDeliveryStatus.SENT
            recipient.sent_at = timezone.now()
            recipient.error = ""
            recipient.save(update_fields=["status", "sent_at", "error"])
            sent += 1

        promotion.status = PromotionStatus.SENT if sent else PromotionStatus.FAILED
        promotion.sent_at = timezone.now() if sent else None
        promotion.save(update_fields=["status", "sent_at", "updated_at"])
        return sent


class DamageDepositService:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key
        stripe.api_version = settings.STRIPE_API_VERSION

    @property
    def is_configured(self):
        return bool(self.api_key)

    def create_checkout_session(self, deposit: DamageDeposit, request) -> DepositCheckoutResult:
        if not self.is_configured:
            deposit.status = DepositStatus.REQUIRES_CONFIGURATION
            deposit.notes = "Stripe is not configured. Set STRIPE_SECRET_KEY before collecting deposits."
            deposit.save(update_fields=["status", "notes", "updated_at"])
            return DepositCheckoutResult(
                success=False,
                message="Stripe is not configured yet, so no deposit hold was created.",
            )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=deposit.email,
                line_items=[
                    {
                        "price_data": {
                            "currency": deposit.currency,
                            "product_data": {
                                "name": "MLADIS refundable damage deposit",
                                "description": "Authorization hold for possible damages. Captured only if needed.",
                            },
                            "unit_amount": deposit.amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                payment_intent_data={
                    "capture_method": "manual",
                    "description": "MLADIS refundable damage deposit hold",
                    "metadata": self._metadata(deposit),
                },
                metadata=self._metadata(deposit),
                success_url=request.build_absolute_uri(reverse("bookings:deposit-success"))
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=request.build_absolute_uri(reverse("bookings:home")) + "#deposit",
            )
        except stripe.StripeError as error:
            deposit.status = DepositStatus.FAILED
            deposit.notes = str(error)
            deposit.save(update_fields=["status", "notes", "updated_at"])
            return DepositCheckoutResult(success=False, message=str(error))

        deposit.status = DepositStatus.CHECKOUT_CREATED
        deposit.stripe_checkout_session_id = session.id
        deposit.checkout_url = session.url or ""
        if session.payment_intent:
            deposit.stripe_payment_intent_id = session.payment_intent
        deposit.save(
            update_fields=[
                "status",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "checkout_url",
                "updated_at",
            ]
        )
        return DepositCheckoutResult(
            success=True,
            message="Deposit checkout created.",
            checkout_url=deposit.checkout_url,
        )

    def sync_checkout_session(self, session_id):
        if not self.is_configured:
            return None
        session = stripe.checkout.Session.retrieve(session_id)
        deposit = DamageDeposit.objects.filter(stripe_checkout_session_id=session.id).first()
        if not deposit:
            return None
        if session.payment_intent:
            deposit.stripe_payment_intent_id = session.payment_intent
        if session.payment_status == "paid":
            deposit.status = DepositStatus.REQUIRES_CAPTURE
        deposit.save(update_fields=["status", "stripe_payment_intent_id", "updated_at"])
        return deposit

    def handle_event(self, event):
        event_type = event.get("type")
        payload = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            deposit = DamageDeposit.objects.filter(stripe_checkout_session_id=payload.get("id")).first()
            if deposit:
                deposit.stripe_payment_intent_id = payload.get("payment_intent") or ""
                deposit.status = DepositStatus.REQUIRES_CAPTURE
                deposit.save(update_fields=["stripe_payment_intent_id", "status", "updated_at"])
            return deposit

        if event_type in {
            "payment_intent.amount_capturable_updated",
            "payment_intent.succeeded",
            "payment_intent.canceled",
        }:
            deposit = DamageDeposit.objects.filter(stripe_payment_intent_id=payload.get("id")).first()
            if not deposit:
                return None
            if event_type == "payment_intent.succeeded":
                deposit.status = DepositStatus.CAPTURED
            elif event_type == "payment_intent.canceled":
                deposit.status = DepositStatus.CANCELED
            else:
                deposit.status = DepositStatus.REQUIRES_CAPTURE
            deposit.save(update_fields=["status", "updated_at"])
            return deposit

        return None

    def _metadata(self, deposit):
        return {
            "damage_deposit_id": str(deposit.id),
            "bookable_item_id": str(deposit.item_id or ""),
            "booking_inquiry_id": str(deposit.inquiry_id or ""),
        }


class DonationService:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key
        stripe.api_version = settings.STRIPE_API_VERSION

    @property
    def is_configured(self):
        return bool(self.api_key)

    def create_checkout_session(self, donation: Donation, request) -> DepositCheckoutResult:
        if not self.is_configured:
            donation.status = DonationStatus.REQUIRES_CONFIGURATION
            donation.notes = "Stripe is not configured. Set STRIPE_SECRET_KEY before accepting donations."
            donation.save(update_fields=["status", "notes", "updated_at"])
            return DepositCheckoutResult(
                success=False,
                message="Stripe is not configured yet, so no donation checkout was created.",
            )

        cause_name = donation.cause.name if donation.cause else "MLADIS mission fund"
        checkout_kwargs = {
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": donation.currency,
                        "product_data": {
                            "name": f"Donation to {cause_name}",
                            "description": "MLADIS mission donation for community support.",
                        },
                        "unit_amount": donation.amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            "payment_intent_data": {
                "description": f"MLADIS donation to {cause_name}",
                "metadata": self._metadata(donation),
            },
            "metadata": self._metadata(donation),
            "success_url": request.build_absolute_uri(reverse("bookings:donation-success"))
            + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": request.build_absolute_uri(reverse("bookings:about")) + "#mission",
        }
        if donation.email:
            checkout_kwargs["customer_email"] = donation.email

        try:
            session = stripe.checkout.Session.create(**checkout_kwargs)
        except stripe.StripeError as error:
            donation.status = DonationStatus.FAILED
            donation.notes = str(error)
            donation.save(update_fields=["status", "notes", "updated_at"])
            return DepositCheckoutResult(success=False, message=str(error))

        donation.status = DonationStatus.CHECKOUT_CREATED
        donation.stripe_checkout_session_id = session.id
        donation.checkout_url = session.url or ""
        if session.payment_intent:
            donation.stripe_payment_intent_id = session.payment_intent
        donation.save(
            update_fields=[
                "status",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "checkout_url",
                "updated_at",
            ]
        )
        return DepositCheckoutResult(
            success=True,
            message="Donation checkout created.",
            checkout_url=donation.checkout_url,
        )

    def sync_checkout_session(self, session_id):
        if not self.is_configured:
            return None
        session = stripe.checkout.Session.retrieve(session_id)
        donation = Donation.objects.filter(stripe_checkout_session_id=session.id).first()
        if not donation:
            return None
        if session.payment_intent:
            donation.stripe_payment_intent_id = session.payment_intent
        if session.payment_status == "paid":
            donation.status = DonationStatus.PAID
        donation.save(update_fields=["status", "stripe_payment_intent_id", "updated_at"])
        return donation

    def handle_event(self, event):
        event_type = event.get("type")
        payload = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            donation = Donation.objects.filter(stripe_checkout_session_id=payload.get("id")).first()
            if donation:
                donation.stripe_payment_intent_id = payload.get("payment_intent") or ""
                donation.status = DonationStatus.PAID
                donation.save(update_fields=["stripe_payment_intent_id", "status", "updated_at"])
            return donation

        if event_type == "payment_intent.succeeded":
            donation = Donation.objects.filter(stripe_payment_intent_id=payload.get("id")).first()
            if donation:
                donation.status = DonationStatus.PAID
                donation.save(update_fields=["status", "updated_at"])
            return donation

        if event_type == "payment_intent.canceled":
            donation = Donation.objects.filter(stripe_payment_intent_id=payload.get("id")).first()
            if donation:
                donation.status = DonationStatus.CANCELED
                donation.save(update_fields=["status", "updated_at"])
            return donation

        return None

    def _metadata(self, donation):
        return {
            "donation_id": str(donation.id),
            "mission_cause_id": str(donation.cause_id or ""),
        }
