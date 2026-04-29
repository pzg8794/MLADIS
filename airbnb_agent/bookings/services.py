from dataclasses import dataclass

from django.conf import settings
from django.urls import reverse
import stripe

from .models import AgentConversation, BookableItem, DamageDeposit, DepositStatus, Donation, DonationStatus


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


class BookingAgentService:
    """Boundary for current stub behavior and future model-backed booking logic."""

    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY

    def reply(self, request: AgentRequest) -> AgentResponse:
        item = self._get_item(request.item_id)

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
            metadata={"agent_mode": "stub"},
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
