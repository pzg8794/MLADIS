import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from openai import OpenAI
import requests
import stripe

from .models import (
    AdminAccess,
    AgentConversation,
    AvailabilityBlock,
    BookableItem,
    BookingInquiry,
    BookingStatus,
    CancellationPolicy,
    ClientSegment,
    CustomerProfile,
    DamageDeposit,
    DailyPriceOverride,
    DepositProvider,
    DepositStatus,
    Donation,
    DonationStatus,
    EmailDeliveryStatus,
    Invoice,
    InvoiceStatus,
    MarketingConsentStatus,
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


class PayPalAPIError(Exception):
    pass


class BookingCalendarService:
    ACTIVE_BOOKING_STATUSES = {
        BookingStatus.NEW,
        BookingStatus.REVIEWING,
        BookingStatus.QUOTED,
        BookingStatus.CONFIRMED,
    }

    def build_month(self, item: BookableItem, month_start: date | None = None):
        month_start = (month_start or timezone.localdate()).replace(day=1)
        weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(month_start.year, month_start.month)
        visible_start = weeks[0][0]
        visible_end = weeks[-1][-1]

        reservations = list(
            BookingInquiry.objects.filter(
                item=item,
                status__in=self.ACTIVE_BOOKING_STATUSES,
                check_in__lt=visible_end + timedelta(days=1),
                check_out__gt=visible_start,
            ).order_by("check_in", "id")
        )
        blocks = list(
            AvailabilityBlock.objects.filter(
                item=item,
                is_active=True,
                start_date__lte=visible_end,
                end_date__gte=visible_start,
            ).order_by("start_date", "id")
        )
        overrides = list(
            DailyPriceOverride.objects.filter(
                item=item,
                is_active=True,
                start_date__lte=visible_end,
                end_date__gte=visible_start,
            ).order_by("start_date", "created_at", "id")
        )

        reservation_map = self._reservation_map(reservations, visible_start, visible_end)
        block_map = self._range_map(blocks, visible_start, visible_end)
        override_map = self._range_map(overrides, visible_start, visible_end)
        default_price = self._default_price(item)

        month_weeks = []
        for week in weeks:
            cells = []
            for day in week:
                reservation_entries = reservation_map.get(day, [])
                block_entries = block_map.get(day, [])
                override_entries = override_map.get(day, [])
                price_override = override_entries[-1] if override_entries else None
                price_value = price_override.nightly_price if price_override else default_price
                if reservation_entries:
                    status = "booked"
                elif block_entries:
                    status = "blocked"
                else:
                    status = "available"
                cells.append(
                    {
                        "date": day,
                        "in_month": day.month == month_start.month,
                        "is_today": day == timezone.localdate(),
                        "status": status,
                        "reservations": reservation_entries,
                        "blocks": block_entries,
                        "price_override": price_override,
                        "price": price_value,
                        "price_display": self._display_price(price_value),
                        "price_source": "override" if price_override else "default",
                        "price_label": price_override.label if price_override else "Default nightly price",
                    }
                )
            month_weeks.append(cells)

        return {
            "month_start": month_start,
            "weeks": month_weeks,
            "reservations": reservations,
            "blocks": blocks,
            "price_overrides": overrides,
        }

    def _reservation_map(self, reservations, visible_start, visible_end):
        result = {}
        for reservation in reservations:
            start = max(reservation.check_in, visible_start)
            end = min(reservation.check_out - timedelta(days=1), visible_end)
            day = start
            while day <= end:
                result.setdefault(day, []).append(reservation)
                day += timedelta(days=1)
        return result

    def _range_map(self, entries, visible_start, visible_end):
        result = {}
        for entry in entries:
            start = max(entry.start_date, visible_start)
            end = min(entry.end_date, visible_end)
            day = start
            while day <= end:
                result.setdefault(day, []).append(entry)
                day += timedelta(days=1)
        return result

    def _default_price(self, item):
        if item.starting_price is None:
            return None
        return item.starting_price

    def _display_price(self, value):
        if value is None:
            return ""
        return f"${value:,.2f}"


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
    """Boundary for the public booking agent and future deeper automation."""

    def __init__(self, api_key=None, client=None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model = settings.OPENAI_AGENT_MODEL
        self.client = client or (OpenAI(api_key=self.api_key) if self.api_key else None)

    def reply(self, request: AgentRequest) -> AgentResponse:
        item = self._get_item(request.item_id)
        topic = QuestionAnalyticsService.classify(request.message)
        metadata = {"topic": topic}

        if not self.api_key:
            reply = self._setup_reply(item)
            metadata["agent_mode"] = "setup"
        else:
            try:
                reply, response_id = self._openai_reply(request, item)
            except Exception as error:  # The public endpoint should degrade instead of failing hard.
                reply = self._fallback_reply(item)
                metadata.update(
                    {
                        "agent_mode": "fallback",
                        "model": self.model,
                        "error": str(error)[:500],
                    }
                )
            else:
                metadata.update(
                    {
                        "agent_mode": "openai",
                        "model": self.model,
                        "openai_response_id": response_id,
                    }
                )

        conversation = AgentConversation.objects.create(
            session_id=request.session_id,
            item=item,
            visitor_name=request.visitor_name,
            visitor_email=request.visitor_email,
            last_user_message=request.message,
            last_agent_reply=reply,
            question_topic=topic,
            metadata=metadata,
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
            "The live AI key is not configured yet, so I am running in setup mode. "
            "To start a reservation, choose the stay, dates, guest count, name, email, and phone in the booking form. "
            "After you submit it, the secure $200 damage-deposit hold step appears."
        )

    def _fallback_reply(self, item):
        subject = item.name if item else "MLADIS bookings"
        return (
            f"I can still help with {subject}: choose your stay, dates, guest count, name, email, and phone in the booking form. "
            "Then use Make secure deposit hold to open the refundable $200 damage-deposit authorization through Stripe or PayPal. "
            "A MLADIS admin reviews availability and confirms the reservation by email. "
            "The live AI assistant is temporarily unavailable, so please include any special questions in the booking message."
        )

    def _openai_reply(self, request, item):
        response = self.client.responses.create(
            model=self.model,
            instructions=self._instructions(),
            input=self._prompt(request, item),
        )
        reply = self._response_text(response).strip()
        if not reply:
            reply = self._fallback_reply(item)
        return reply, getattr(response, "id", "")

    def _instructions(self):
        return (
            "You are the MLADIS website booking assistant for Santo Domingo Norte vacation stays. "
            "Be warm, concise, bilingual when useful, and focused on helping guests choose a stay, "
            "understand rules, deposits, location, amenities, and next steps. Do not promise live "
            "availability, final pricing, refunds, or reservation confirmation. Explain that bookings "
            "are admin-confirmed and that the $200 damage deposit is an authorization hold. When a guest "
            "is ready to book, guide them to the booking form and tell them to enter the stay, dates, "
            "guest count, name, email, phone, coupon if any, and special requests. Explain that after "
            "submitting the booking form, the secure deposit-hold step appears through Stripe or PayPal. "
            "Ask for dates, guest count, email, and phone when the guest wants to book. Do not promise discounts, "
            "early or late checkout, exact address details, private pool access, or waived house rules unless "
            "an admin has explicitly confirmed them. If a question needs owner action, direct the guest to "
            "submit the booking form or contact MLADIS."
        )

    def _prompt(self, request, item):
        parts = [
            "Guest message:",
            request.message,
            "",
            "Selected stay:",
            self._item_context(item) if item else "No stay selected yet.",
            "",
            "MLADIS stay catalog:",
            self._catalog_context(selected_item=item),
            "",
            "Booking workflow:",
            self._booking_workflow_context(),
        ]
        history = self._recent_history(request.session_id)
        if history:
            parts.extend(["", "Recent conversation in this browser session:", history])
        return "\n".join(parts)

    def _item_context(self, item):
        if not item:
            return ""
        stats = ", ".join(item.stat_list) or "details not listed"
        rules = "; ".join(
            rule.title for rule in item.house_rules.filter(is_active=True).order_by("sort_order", "title")[:6]
        )
        highlights = "; ".join(
            highlight.title for highlight in item.guest_review_highlights.order_by("sort_order", "id")[:4]
        )
        return (
            f"{item.name}. {item.short_description} {item.marketing_description or item.description} "
            f"Location: {item.location_label or 'Santo Domingo Norte'}. Stats: {stats}. "
            f"Rating: {item.review_label}. Price signal: {item.headline_price}. "
            f"Rules: {rules or 'standard MLADIS house rules'}. "
            f"Guest highlights: {highlights or 'Airbnb review signals are available on the page'}. "
            f"Airbnb URL: {item.airbnb_embed_url or 'not available'}."
        )

    def _catalog_context(self, selected_item=None):
        items = BookableItem.objects.filter(is_active=True).order_by("category", "name")[:12]
        lines = []
        for item in items:
            marker = "selected" if selected_item and selected_item.pk == item.pk else "option"
            lines.append(f"- ({marker}) {self._item_context(item)}")
        return "\n".join(lines)

    def _booking_workflow_context(self):
        deposit_amount = settings.DEPOSIT_AMOUNT_CENTS / 100
        deposit_currency = settings.DEPOSIT_CURRENCY.upper()
        return (
            "Guests book from the website booking section. Required reservation details are stay, dates, "
            "guest count, name, email, and phone. Coupon code is optional. The form button says "
            "Make secure deposit hold. After submitting, guests complete a refundable damage-deposit "
            f"authorization for ${deposit_amount:,.0f} {deposit_currency} through Stripe Checkout or PayPal. "
            "The deposit is an authorization hold, not a captured charge unless there is a valid damage claim. "
            "Reservation requests are stored for admin review and confirmation by email. Guests can create an "
            "account to view and manage reservations."
        )

    def _recent_history(self, session_id, limit=6):
        if not session_id:
            return ""
        conversations = list(
            AgentConversation.objects.filter(session_id=session_id).order_by("-created_at")[:limit]
        )
        lines = []
        for conversation in reversed(conversations):
            lines.append(f"Guest: {conversation.last_user_message}")
            lines.append(f"MLADIS agent: {conversation.last_agent_reply}")
        return "\n".join(lines)

    def _response_text(self, response):
        output_text = getattr(response, "output_text", "")
        if output_text:
            return output_text
        chunks = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", "")
                if text:
                    chunks.append(text)
        return "\n".join(chunks)


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
        profiles = CustomerProfile.objects.exclude(email="").filter(
            marketing_consent_status=MarketingConsentStatus.OPTED_IN,
        )
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
            if not self._recipient_has_opted_in(recipient):
                recipient.status = EmailDeliveryStatus.FAILED
                recipient.error = "Promotion not sent because this recipient has not opted in."
                recipient.save(update_fields=["status", "error"])
                continue
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

    def _recipient_has_opted_in(self, recipient):
        profile = recipient.customer_profile
        if profile is None:
            return False
        return profile.can_receive_promotions and recipient.email.lower() == profile.email.lower()


class MarketingConsentEmailService:
    def send_request(self, profile: CustomerProfile):
        if not profile.email:
            return False

        body = (
            f"Hi {profile.name or 'there'},\n\n"
            "Thank you for staying with MLADIS. We would like your permission to contact you "
            "with occasional future-stay discounts, travel tips, and direct-booking offers.\n\n"
            "Please reply YES if you would like to receive those messages, or NO if you would prefer not to. "
            "We will not send promotional offers unless you opt in.\n\n"
            "Thank you,\nMLADIS"
        )
        send_mail(
            "Permission to send future MLADIS offers?",
            body,
            settings.DEFAULT_FROM_EMAIL,
            [profile.email],
            fail_silently=False,
        )
        profile.marketing_consent_status = MarketingConsentStatus.REQUESTED
        profile.marketing_consent_requested_at = timezone.now()
        profile.marketing_consent_source = "email consent request"
        profile.save(
            update_fields=[
                "marketing_consent_status",
                "marketing_consent_requested_at",
                "marketing_consent_source",
                "updated_at",
            ]
        )
        return True


class DamageDepositService:
    def __init__(self, api_key=None):
        self.api_key = api_key if api_key is not None else settings.STRIPE_SECRET_KEY
        stripe.api_key = self.api_key
        stripe.api_version = settings.STRIPE_API_VERSION

    @property
    def is_configured(self):
        return bool(self.api_key)

    def create_checkout_for_inquiry(self, inquiry, request) -> DepositCheckoutResult:
        deposit = DamageDeposit.objects.filter(inquiry=inquiry).order_by("-created_at").first()
        if not deposit:
            deposit = DamageDeposit(inquiry=inquiry)

        deposit.item = inquiry.item
        deposit.guest_name = inquiry.guest_name
        deposit.email = inquiry.email
        deposit.payment_provider = DepositProvider.STRIPE
        deposit.amount_cents = settings.DEPOSIT_AMOUNT_CENTS
        deposit.currency = settings.DEPOSIT_CURRENCY
        deposit.save()

        return self.create_checkout_session(deposit, request)

    def create_checkout_session(self, deposit: DamageDeposit, request) -> DepositCheckoutResult:
        deposit.payment_provider = DepositProvider.STRIPE
        if not self.is_configured:
            deposit.status = DepositStatus.REQUIRES_CONFIGURATION
            deposit.notes = "Stripe is not configured. Set STRIPE_SECRET_KEY before collecting deposits."
            deposit.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
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
            deposit.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            return DepositCheckoutResult(success=False, message=str(error))

        deposit.status = DepositStatus.CHECKOUT_CREATED
        deposit.paypal_order_id = ""
        deposit.paypal_authorization_id = ""
        deposit.stripe_checkout_session_id = session.id
        deposit.checkout_url = session.url or ""
        if session.payment_intent:
            deposit.stripe_payment_intent_id = session.payment_intent
        deposit.save(
            update_fields=[
                "payment_provider",
                "status",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "paypal_order_id",
                "paypal_authorization_id",
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

    def capture_deposit(self, deposit: DamageDeposit):
        deposit = self._require_capturable_deposit(deposit)
        payment_intent = stripe.PaymentIntent.capture(deposit.stripe_payment_intent_id)
        charge_id = payment_intent.get("latest_charge", "")

        note = f"Stripe payment intent {deposit.stripe_payment_intent_id} captured"
        if charge_id:
            note += f" as charge {charge_id}"
        note += f" at {timezone.now().isoformat()}"
        deposit.status = DepositStatus.CAPTURED
        deposit.notes = self._append_note(deposit.notes, note)
        deposit.save(update_fields=["status", "notes", "updated_at"])
        return deposit

    def release_deposit(self, deposit: DamageDeposit):
        deposit = self._require_capturable_deposit(deposit)
        stripe.PaymentIntent.cancel(deposit.stripe_payment_intent_id)

        note = (
            f"Stripe payment intent {deposit.stripe_payment_intent_id} canceled at "
            f"{timezone.now().isoformat()}"
        )
        deposit.status = DepositStatus.CANCELED
        deposit.notes = self._append_note(deposit.notes, note)
        deposit.save(update_fields=["status", "notes", "updated_at"])
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

    def _append_note(self, notes, note):
        return f"{notes}\n{note}".strip() if notes else note

    def _require_capturable_deposit(self, deposit):
        if not self.is_configured:
            raise ValueError("Stripe is not configured. Set STRIPE_SECRET_KEY first.")
        if not deposit or deposit.payment_provider != DepositProvider.STRIPE:
            raise ValueError("This deposit is not managed by Stripe.")
        if not deposit.stripe_payment_intent_id:
            raise ValueError("This Stripe deposit does not have a payment intent to manage.")
        if deposit.status != DepositStatus.REQUIRES_CAPTURE:
            raise ValueError("Only authorized Stripe deposits can be captured or released.")
        return deposit


class PayPalDamageDepositService:
    def __init__(self, client_id=None, client_secret=None, environment=None):
        self.client_id = client_id if client_id is not None else settings.PAYPAL_CLIENT_ID
        self.client_secret = client_secret if client_secret is not None else settings.PAYPAL_CLIENT_SECRET
        self.environment = environment if environment is not None else settings.PAYPAL_ENVIRONMENT

    @property
    def is_configured(self):
        return bool(self.client_id and self.client_secret)

    @property
    def base_url(self):
        if self.environment in {"live", "production"}:
            return "https://api-m.paypal.com"
        return "https://api-m.sandbox.paypal.com"

    def create_checkout_session(self, deposit: DamageDeposit, request) -> DepositCheckoutResult:
        deposit.payment_provider = DepositProvider.PAYPAL
        if not self.is_configured:
            deposit.status = DepositStatus.REQUIRES_CONFIGURATION
            deposit.notes = "PayPal is not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET before collecting deposits."
            deposit.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            return DepositCheckoutResult(
                success=False,
                message="PayPal is not configured yet, so no deposit hold was created.",
            )

        try:
            access_token = self._create_access_token()
            order = self._paypal_api_request(
                "post",
                "/v2/checkout/orders",
                access_token=access_token,
                json_body=self._create_order_payload(deposit, request),
            )
            checkout_url = self._extract_checkout_url(order)
            if not checkout_url:
                raise PayPalAPIError("PayPal did not return an approval link for the deposit hold.")
        except (PayPalAPIError, requests.RequestException) as error:
            deposit.status = DepositStatus.FAILED
            deposit.notes = str(error)
            deposit.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            return DepositCheckoutResult(success=False, message=str(error))

        deposit.status = DepositStatus.CHECKOUT_CREATED
        deposit.stripe_checkout_session_id = ""
        deposit.stripe_payment_intent_id = ""
        deposit.paypal_order_id = order.get("id", "")
        deposit.paypal_authorization_id = ""
        deposit.checkout_url = checkout_url
        deposit.save(
            update_fields=[
                "payment_provider",
                "status",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "paypal_order_id",
                "paypal_authorization_id",
                "checkout_url",
                "updated_at",
            ]
        )
        return DepositCheckoutResult(
            success=True,
            message="PayPal deposit checkout created.",
            checkout_url=deposit.checkout_url,
        )

    def authorize_order(self, order_id):
        if not self.is_configured or not order_id:
            return None

        deposit = DamageDeposit.objects.filter(paypal_order_id=order_id).first()
        if not deposit:
            return None
        if deposit.paypal_authorization_id:
            if deposit.status != DepositStatus.REQUIRES_CAPTURE:
                deposit.status = DepositStatus.REQUIRES_CAPTURE
                deposit.save(update_fields=["status", "updated_at"])
            return deposit

        access_token = self._create_access_token()
        order = self._paypal_api_request(
            "post",
            f"/v2/checkout/orders/{order_id}/authorize",
            access_token=access_token,
            json_body={},
        )
        authorization_id = self._extract_authorization_id(order)
        if not authorization_id:
            raise PayPalAPIError("PayPal did not return an authorization for this deposit.")

        deposit.payment_provider = DepositProvider.PAYPAL
        deposit.paypal_authorization_id = authorization_id
        deposit.status = DepositStatus.REQUIRES_CAPTURE
        deposit.save(update_fields=["payment_provider", "paypal_authorization_id", "status", "updated_at"])
        return deposit

    def capture_deposit(self, deposit: DamageDeposit):
        return self.capture_authorization(deposit)

    def release_deposit(self, deposit: DamageDeposit):
        return self.void_authorization(deposit)

    def capture_authorization(self, deposit: DamageDeposit):
        deposit = self._require_authorized_deposit(deposit)
        access_token = self._create_access_token()
        capture = self._paypal_api_request(
            "post",
            f"/v2/payments/authorizations/{deposit.paypal_authorization_id}/capture",
            access_token=access_token,
            json_body={
                "amount": {
                    "currency_code": deposit.currency.upper(),
                    "value": self._amount_value(deposit),
                },
                "final_capture": True,
            },
        )

        capture_id = capture.get("id", "")
        note = f"PayPal authorization {deposit.paypal_authorization_id} captured"
        if capture_id:
            note += f" as capture {capture_id}"
        note += f" at {timezone.now().isoformat()}"
        deposit.status = DepositStatus.CAPTURED
        deposit.notes = self._append_note(deposit.notes, note)
        deposit.save(update_fields=["status", "notes", "updated_at"])
        return deposit

    def void_authorization(self, deposit: DamageDeposit):
        deposit = self._require_authorized_deposit(deposit)
        access_token = self._create_access_token()
        self._paypal_api_request(
            "post",
            f"/v2/payments/authorizations/{deposit.paypal_authorization_id}/void",
            access_token=access_token,
            json_body={},
        )

        note = (
            f"PayPal authorization {deposit.paypal_authorization_id} voided at "
            f"{timezone.now().isoformat()}"
        )
        deposit.status = DepositStatus.CANCELED
        deposit.notes = self._append_note(deposit.notes, note)
        deposit.save(update_fields=["status", "notes", "updated_at"])
        return deposit

    def cancel_order(self, order_id):
        if not order_id:
            return None
        deposit = DamageDeposit.objects.filter(paypal_order_id=order_id).first()
        if deposit and deposit.status == DepositStatus.CHECKOUT_CREATED:
            deposit.status = DepositStatus.CANCELED
            deposit.save(update_fields=["status", "updated_at"])
        return deposit

    def _create_access_token(self):
        response = requests.post(
            f"{self.base_url}/v1/oauth2/token",
            auth=(self.client_id, self.client_secret),
            data={"grant_type": "client_credentials"},
            headers={
                "Accept": "application/json",
                "Accept-Language": "en_US",
            },
            timeout=30,
        )
        payload = self._parse_response(response)
        access_token = payload.get("access_token", "")
        if not access_token:
            raise PayPalAPIError("PayPal did not return an access token.")
        return access_token

    def _paypal_api_request(self, method, path, access_token, json_body=None):
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=json_body,
            timeout=30,
        )
        return self._parse_response(response)

    def _parse_response(self, response):
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {}

        if response.ok:
            return payload

        message = payload.get("message") if isinstance(payload, dict) else ""
        details = payload.get("details") if isinstance(payload, dict) else None
        if not message and isinstance(details, list) and details:
            message = details[0].get("description") or details[0].get("issue") or ""
        if not message:
            message = response.text.strip() or "PayPal request failed."
        raise PayPalAPIError(message)

    def _create_order_payload(self, deposit, request):
        return {
            "intent": "AUTHORIZE",
            "purchase_units": [
                {
                    "reference_id": f"damage-deposit-{deposit.id}",
                    "custom_id": str(deposit.id),
                    "description": "MLADIS refundable damage deposit hold",
                    "amount": {
                        "currency_code": deposit.currency.upper(),
                        "value": self._amount_value(deposit),
                    },
                }
            ],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "brand_name": settings.PAYPAL_BRAND_NAME,
                        "landing_page": "LOGIN",
                        "shipping_preference": "NO_SHIPPING",
                        "user_action": "PAY_NOW",
                        "return_url": request.build_absolute_uri(reverse("bookings:deposit-paypal-success")),
                        "cancel_url": request.build_absolute_uri(reverse("bookings:deposit-paypal-cancel")),
                    }
                }
            },
        }

    def _amount_value(self, deposit):
        amount = Decimal(deposit.amount_cents) / Decimal("100")
        return f"{amount:.2f}"

    def _append_note(self, notes, note):
        return f"{notes}\n{note}".strip() if notes else note

    def _require_authorized_deposit(self, deposit):
        if not self.is_configured:
            raise PayPalAPIError("PayPal is not configured. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET first.")
        if not deposit or deposit.payment_provider != DepositProvider.PAYPAL:
            raise PayPalAPIError("This deposit is not managed by PayPal.")
        if not deposit.paypal_authorization_id:
            raise PayPalAPIError("This PayPal deposit does not have an authorization to manage.")
        if deposit.status != DepositStatus.REQUIRES_CAPTURE:
            raise PayPalAPIError("Only authorized PayPal deposits can be captured or released.")
        return deposit

    def _extract_checkout_url(self, order):
        for link in order.get("links", []):
            if link.get("rel") in {"payer-action", "approve"} and link.get("href"):
                return link["href"]
        return ""

    def _extract_authorization_id(self, order):
        for purchase_unit in order.get("purchase_units", []):
            authorizations = purchase_unit.get("payments", {}).get("authorizations", [])
            for authorization in authorizations:
                authorization_id = authorization.get("id")
                if authorization_id:
                    return authorization_id
        return ""


def get_damage_deposit_service(provider):
    if provider == DepositProvider.PAYPAL:
        return PayPalDamageDepositService()
    return DamageDepositService()


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
