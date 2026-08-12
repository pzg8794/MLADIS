import calendar
import base64
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import requests
import stripe

from .models import (
    AdminAccess,
    AgentKnowledgeSource,
    AgentConversation,
    AgentFAQ,
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
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
    MaintenanceEvent,
    MaintenancePhoto,
    MaintenanceWorkType,
    MaintenanceStatus,
    Promotion,
    PromotionRecipient,
    PromotionStatus,
    ReservationPaymentHold,
    SiteSettings,
    StayGalleryImage,
)


APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
MAX_AGENT_SOURCE_SNIPPETS = 12
MAX_TOTAL_AGENT_SOURCES = 6


def _build_openai_client(api_key):
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _stripe_object_id(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("id", "")
    return getattr(value, "id", "") or str(value)


def _stripe_object_status(value):
    if not value:
        return ""
    if isinstance(value, dict):
        return value.get("status", "")
    return getattr(value, "status", "")


def _stripe_object_value(value, key, default=""):
    if not value:
        return default
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _stripe_object_metadata(value):
    if not value:
        return {}
    metadata = value.get("metadata", {}) if isinstance(value, dict) else getattr(value, "metadata", {})
    if not metadata:
        return {}
    if isinstance(metadata, dict):
        return dict(metadata)
    if hasattr(metadata, "to_dict"):
        return metadata.to_dict()
    if hasattr(metadata, "items"):
        return dict(metadata.items())
    return {}


def _stripe_payment_intent_status(payment_intent):
    if not payment_intent:
        return ""
    status = _stripe_object_status(payment_intent)
    if status:
        return status
    payment_intent_id = _stripe_object_id(payment_intent)
    if not payment_intent_id:
        return ""
    retrieved = stripe.PaymentIntent.retrieve(payment_intent_id)
    return _stripe_object_status(retrieved)


def _stripe_checkout_successful(session):
    if getattr(session, "status", "") == "complete":
        return True
    payment_status = getattr(session, "payment_status", "")
    if payment_status in {"paid", "no_payment_required"}:
        return True
    return _stripe_payment_intent_status(getattr(session, "payment_intent", "")) in {
        "requires_capture",
        "succeeded",
    }


LOCAL_STRIPE_ENVIRONMENTS = {"local", "dev", "development", "test", "testing"}


@dataclass(frozen=True)
class StripeRuntimeConfig:
    """Resolved Stripe runtime state for the current request."""

    mode: str
    secret_key: str = ""
    error: str = ""

    @property
    def is_configured(self):
        return bool(self.secret_key) and not self.error

    def configure_api(self):
        if not self.is_configured:
            return False
        stripe.api_key = self.secret_key
        stripe.api_version = settings.STRIPE_API_VERSION
        return True


class StripeRuntimePolicy:
    """Chooses Stripe mode from environment/request without hardcoding a forever choice."""

    VALID_MODES = {"auto", "test", "live"}

    @classmethod
    def resolve(cls, api_key=None, request=None):
        configured_mode = (getattr(settings, "STRIPE_MODE", "auto") or "auto").strip().lower()
        if configured_mode not in cls.VALID_MODES:
            return StripeRuntimeConfig(
                mode=configured_mode,
                error="STRIPE_MODE must be auto, test, or live.",
            )

        mode = cls._mode(configured_mode, request=request)
        secret_key = cls._secret_key_for_mode(mode, api_key=api_key)
        if mode == "test" and secret_key.startswith("sk_live_"):
            return StripeRuntimeConfig(
                mode=mode,
                error=(
                    "Local Stripe checkout resolved to test mode, but a live Stripe key is configured. "
                    "Set STRIPE_TEST_SECRET_KEY=sk_test_... or STRIPE_SECRET_KEY=sk_test_... for local testing. "
                    "Set STRIPE_MODE=live only for an intentional live runtime."
                ),
            )
        if mode == "live" and secret_key.startswith("sk_test_"):
            return StripeRuntimeConfig(
                mode=mode,
                error=(
                    "Stripe live mode is selected, but the configured key is a test key. "
                    "Set STRIPE_LIVE_SECRET_KEY=sk_live_... or STRIPE_SECRET_KEY=sk_live_... for production."
                ),
            )
        return StripeRuntimeConfig(mode=mode, secret_key=secret_key)

    @classmethod
    def _mode(cls, configured_mode, request=None):
        if configured_mode in {"test", "live"}:
            return configured_mode
        return "test" if cls._is_local_runtime(request=request) else "live"

    @staticmethod
    def _is_local_runtime(request=None):
        environment = (getattr(settings, "MLADIS_ENVIRONMENT", "") or "").strip().lower()
        if getattr(settings, "DEBUG", False) or environment in LOCAL_STRIPE_ENVIRONMENTS:
            return True
        if not request:
            return False
        raw_host = request.get_host().strip().lower()
        if raw_host.startswith("["):
            host = raw_host.split("]", 1)[0] + "]"
        else:
            host = raw_host.split(":", 1)[0]
        local_hosts = {item.strip().lower() for item in getattr(settings, "STRIPE_LOCAL_HOSTS", [])}
        return host in local_hosts

    @staticmethod
    def _secret_key_for_mode(mode, api_key=None):
        if api_key is not None:
            return (api_key or "").strip()
        if mode == "test":
            return (
                (getattr(settings, "STRIPE_TEST_SECRET_KEY", "") or "").strip()
                or (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
            )
        return (
            (getattr(settings, "STRIPE_LIVE_SECRET_KEY", "") or "").strip()
            or (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
        )


class StripeServiceMixin:
    """Shared Stripe configuration for checkout/domain services."""

    def _init_stripe(self, api_key=None):
        self._explicit_api_key = api_key
        self._configure_for_request()

    @property
    def is_configured(self):
        return self.stripe_config.is_configured

    def _configure_for_request(self, request=None):
        self.stripe_config = StripeRuntimePolicy.resolve(
            api_key=self._explicit_api_key,
            request=request,
        )
        self.api_key = self.stripe_config.secret_key
        self.stripe_mode = self.stripe_config.mode
        self.configuration_error = self.stripe_config.error
        return self.stripe_config.configure_api()

    def _stripe_unavailable_message(self, default_message):
        return self.configuration_error or default_message


class PaymentAuthorization:
    """Payment object for a successful or unsuccessful provider return."""

    def __init__(self, record, session):
        self.record = record
        self.session = session
        self.payment_intent_id = _stripe_object_id(getattr(session, "payment_intent", ""))
        self.successful = _stripe_checkout_successful(session)

    def persist(self):
        if self.payment_intent_id:
            self.record.stripe_payment_intent_id = self.payment_intent_id
        if self.successful:
            self.record.status = DepositStatus.REQUIRES_CAPTURE
        self.record.save(update_fields=["status", "stripe_payment_intent_id", "updated_at"])
        return self.record

    def send_confirmation(self, email_service, request=None):
        if not self.successful:
            return False
        if isinstance(self.record, ReservationPaymentHold):
            return email_service.send_reservation_payment_confirmation(self.record, request=request)
        return email_service.send_damage_deposit_confirmation(self.record, request=request)


REPO_KNOWLEDGE_HEADINGS = (
    "## Initial Airbnb Listings",
    "## Marketing Pages",
)

REPO_KNOWLEDGE_TEMPLATE_PATHS = (
    "bookings/templates/bookings/terms.html",
    "bookings/templates/bookings/business.html",
    "bookings/templates/bookings/privacy_policy.html",
    "bookings/templates/bookings/data_deletion.html",
)

REPO_KNOWLEDGE_SECTION_PATHS = (
    ("bookings/templates/bookings/home.html", ("booking", "deposit")),
    ("bookings/templates/bookings/stay_detail.html", ("booking",)),
)


def _clean_knowledge_text(value):
    return " ".join(value.replace("`", "").split())


def _strip_template_markup(value):
    value = re.sub(r'{%\s*trans\s+"([^"]+)"\s*%}', r"\1", value)
    value = re.sub(r"{%\s*blocktrans.*?%}(.*?){%\s*endblocktrans\s*%}", r"\1", value, flags=re.DOTALL)
    value = re.sub(r"{%.*?%}", " ", value, flags=re.DOTALL)
    value = re.sub(r"{{.*?}}", " ", value, flags=re.DOTALL)
    return value


def _extract_markdown_bullets(source_text, heading):
    match = re.search(
        rf"^{re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        source_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return []
    return [_clean_knowledge_text(line[2:]) for line in match.group("body").splitlines() if line.startswith("- ")]


def _extract_html_list_items(source_text):
    items = []
    cleaned_text = _strip_template_markup(source_text)
    for raw_item in re.findall(r"<li[^>]*>(.*?)</li>", cleaned_text, flags=re.DOTALL | re.IGNORECASE):
        item = _clean_knowledge_text(re.sub(r"<[^>]+>", " ", raw_item))
        if item and not item.endswith(":"):
            items.append(item)
    return items


def _extract_html_paragraphs(source_text):
    items = []
    cleaned_text = _strip_template_markup(source_text)
    for raw_item in re.findall(r"<p[^>]*>(.*?)</p>", cleaned_text, flags=re.DOTALL | re.IGNORECASE):
        item = _clean_knowledge_text(re.sub(r"<[^>]+>", " ", raw_item))
        if item and not item.endswith(":"):
            items.append(item)
    return items


def _extract_html_section(source_text, section_id):
    match = re.search(
        rf'<section[^>]*id="{re.escape(section_id)}"[^>]*>(?P<body>.*?)</section>',
        source_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return ""
    return match.group("body")


@lru_cache(maxsize=1)
def _repo_knowledge_snippets():
    snippets = []

    readme_path = APP_ROOT / "README.md"
    if readme_path.exists():
        readme_text = readme_path.read_text(encoding="utf-8")
        for heading in REPO_KNOWLEDGE_HEADINGS:
            snippets.extend(_extract_markdown_bullets(readme_text, heading))

    for relative_path in REPO_KNOWLEDGE_TEMPLATE_PATHS:
        template_path = APP_ROOT / relative_path
        if template_path.exists():
            snippets.extend(_extract_html_list_items(template_path.read_text(encoding="utf-8")))

    for relative_path, section_ids in REPO_KNOWLEDGE_SECTION_PATHS:
        template_path = APP_ROOT / relative_path
        if not template_path.exists():
            continue
        template_text = template_path.read_text(encoding="utf-8")
        for section_id in section_ids:
            section_html = _extract_html_section(template_text, section_id)
            if section_html:
                snippets.extend(_extract_html_paragraphs(section_html))

    deduped = []
    seen = set()
    for snippet in snippets:
        if snippet and snippet not in seen:
            seen.add(snippet)
            deduped.append(snippet)
    return tuple(deduped[:40])


def _clean_snippet_collection(snippets, limit=None):
    deduped = []
    seen = set()
    for snippet in snippets:
        normalized = _clean_knowledge_text(snippet)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
        if limit and len(deduped) >= limit:
            break
    return tuple(deduped)


def _extract_generic_text_snippets(source_text):
    text = _strip_template_markup(source_text)
    snippets = []
    if "<li" in source_text or "<p" in source_text:
        snippets.extend(_extract_html_list_items(source_text))
        snippets.extend(_extract_html_paragraphs(source_text))

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "```")):
            continue
        if stripped.startswith(("- ", "* ")):
            snippets.append(stripped[2:])
            continue
        numbered = re.sub(r"^\d+\.\s*", "", stripped)
        if numbered != stripped:
            snippets.append(numbered)
            continue
        if len(stripped) <= 280:
            snippets.append(stripped)

    paragraphs = [
        _clean_knowledge_text(chunk)
        for chunk in re.split(r"\n\s*\n", text)
        if _clean_knowledge_text(chunk)
    ]
    snippets.extend(paragraphs)
    return _clean_snippet_collection(snippets, limit=MAX_AGENT_SOURCE_SNIPPETS)


def _normalize_source_url(source_value):
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$", source_value)
    if match:
        owner, repo, branch, path = match.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    return source_value


def _safe_repo_path(source_value):
    candidate = Path(source_value)
    resolved = candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        return None
    return resolved


@lru_cache(maxsize=64)
def _load_external_knowledge_source(source_type, source_value, body, updated_at_key):
    del updated_at_key
    if source_type == "inline":
        return _extract_generic_text_snippets(body)
    if source_type == "repo_file":
        path = _safe_repo_path(source_value)
        if not path or not path.exists() or not path.is_file():
            return tuple()
        return _extract_generic_text_snippets(path.read_text(encoding="utf-8"))
    if source_type == "url":
        try:
            response = requests.get(_normalize_source_url(source_value), timeout=5)
            response.raise_for_status()
        except requests.RequestException:
            return tuple()
        return _extract_generic_text_snippets(response.text)
    return tuple()


def _agent_knowledge_source_snippets():
    snippets = []
    sources = AgentKnowledgeSource.objects.filter(is_active=True).order_by("sort_order", "title")[:MAX_TOTAL_AGENT_SOURCES]
    for source in sources:
        snippets.extend(
            _load_external_knowledge_source(
                source.source_type,
                source.source_value,
                source.body,
                source.updated_at.isoformat(),
            )
        )
    return _clean_snippet_collection(snippets, limit=MAX_TOTAL_AGENT_SOURCES * MAX_AGENT_SOURCE_SNIPPETS)


@dataclass(frozen=True)
class AgentInstance:
    key: str
    name: str
    question_limit: int
    login_url: str

    @classmethod
    def from_request(cls, request):
        settings_obj = SiteSettings.current()
        return cls(
            key="public-booking-agent",
            name="Booking agent",
            question_limit=max(int(settings_obj.agent_question_limit or 0), 0),
            login_url=f"{reverse('bookings:login')}?next={reverse('bookings:dashboard')}",
        )


@dataclass(frozen=True)
class AgentUserContext:
    user: object
    agent: AgentInstance
    questions_used: int
    visitor_key: str

    @classmethod
    def from_request(cls, request):
        agent = AgentInstance.from_request(request)
        user = request.user
        try:
            setattr(user, "mladis_agent", agent)
        except Exception:
            pass
        questions_used = 0
        if getattr(user, "is_authenticated", False):
            questions_used = AgentConversation.objects.filter(user=user).count()
            visitor_key = f"user:{user.pk}"
        else:
            visitor_key = cls._anonymous_visitor_key(request)
        return cls(user=user, agent=agent, questions_used=questions_used, visitor_key=visitor_key)

    @staticmethod
    def _anonymous_visitor_key(request):
        session = getattr(request, "session", None)
        if session is None:
            return "anon:untracked"
        if session.session_key is None:
            session.save()
        return f"anon:{session.session_key}"

    @property
    def is_authenticated(self):
        return bool(getattr(self.user, "is_authenticated", False))


@dataclass(frozen=True)
class AgentAccessContext:
    actor: AgentUserContext

    @classmethod
    def from_request(cls, request):
        return cls(actor=AgentUserContext.from_request(request))

    @property
    def user(self):
        return self.actor.user

    @property
    def agent(self):
        return self.actor.agent

    @property
    def question_limit(self):
        return self.agent.question_limit

    @property
    def questions_used(self):
        return self.actor.questions_used

    @property
    def login_url(self):
        return self.agent.login_url

    @property
    def is_authenticated(self):
        return self.actor.is_authenticated

    @property
    def remaining_questions(self):
        if self.question_limit <= 0:
            return None
        return max(self.question_limit - self.questions_used, 0)

    @property
    def can_ask(self):
        if not self.is_authenticated:
            return False
        return self.question_limit <= 0 or self.questions_used < self.question_limit

    @property
    def denial_status(self):
        return 401 if not self.is_authenticated else 429

    def denial_payload(self):
        if not self.is_authenticated:
            return {
                "error": "Please sign in before asking the booking agent.",
                "code": "authentication_required",
                "login_url": self.login_url,
                **self.to_public_payload(),
            }
        return {
            "error": "You have reached the booking-agent question limit for this account.",
            "code": "question_limit_reached",
            "login_url": self.login_url,
            **self.to_public_payload(),
        }

    def to_public_payload(self):
        return {
            "agent_key": self.agent.key,
            "agent_name": self.agent.name,
            "is_authenticated": self.is_authenticated,
            "question_limit": self.question_limit,
            "questions_used": self.questions_used,
            "remaining_questions": self.remaining_questions,
            "can_ask": self.can_ask,
            "login_url": self.login_url,
        }


@dataclass(frozen=True)
class AgentRequest:
    message: str
    session_id: str
    item_id: int | None = None
    user_id: int | None = None
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


@dataclass(frozen=True)
class ReservationPricingPolicy:
    base_price_cents: int
    included_guests: int
    extra_guest_cents: int
    max_guests: int
    currency: str
    label: str


@dataclass(frozen=True)
class ReservationPricingQuote:
    policy: ReservationPricingPolicy
    guests: int
    nights: int
    nightly_cents: int
    subtotal_cents: int

    @property
    def extra_guest_count(self):
        return max(self.guests - self.policy.included_guests, 0)


class ReservationPricingService:
    THREE_BED_BASE_CENTS = 5000
    THREE_BED_EXTRA_GUEST_CENTS = 1000
    THREE_BED_INCLUDED_GUESTS = 1
    THREE_BED_MAX_GUESTS = 7
    SIX_BED_BASE_CENTS = 10000
    SIX_BED_INCLUDED_GUESTS = 12
    SIX_BED_EXTRA_GUEST_CENTS = 1000
    SIX_BED_MAX_GUESTS = 14

    def policy_for_item(self, item: BookableItem | None) -> ReservationPricingPolicy:
        currency = settings.DEPOSIT_CURRENCY
        if not item:
            return ReservationPricingPolicy(
                base_price_cents=0,
                included_guests=1,
                extra_guest_cents=0,
                max_guests=self.SIX_BED_MAX_GUESTS,
                currency=currency,
                label="Choose a stay for an exact quote.",
            )

        if self._is_six_bed_stay(item):
            return ReservationPricingPolicy(
                base_price_cents=self.SIX_BED_BASE_CENTS,
                included_guests=self.SIX_BED_INCLUDED_GUESTS,
                extra_guest_cents=self.SIX_BED_EXTRA_GUEST_CENTS,
                max_guests=self.SIX_BED_MAX_GUESTS,
                currency=currency,
                label="$100/night for 12 guests, then $10/night per added guest, max 14 guests.",
            )

        return ReservationPricingPolicy(
            base_price_cents=self.THREE_BED_BASE_CENTS,
            included_guests=self.THREE_BED_INCLUDED_GUESTS,
            extra_guest_cents=self.THREE_BED_EXTRA_GUEST_CENTS,
            max_guests=self.THREE_BED_MAX_GUESTS,
            currency=currency,
            label="$50/night for 1 guest, then $10/night per added guest, max 7 guests.",
        )

    def quote(self, item: BookableItem | None, guests=1, nights=1) -> ReservationPricingQuote:
        policy = self.policy_for_item(item)
        guests = max(int(guests or 1), 1)
        nights = max(int(nights or 1), 1)
        if guests > policy.max_guests:
            raise ValueError(f"This stay allows up to {policy.max_guests} guests.")
        extra_guest_count = max(guests - policy.included_guests, 0)
        nightly_cents = policy.base_price_cents + (extra_guest_count * policy.extra_guest_cents)
        return ReservationPricingQuote(
            policy=policy,
            guests=guests,
            nights=nights,
            nightly_cents=nightly_cents,
            subtotal_cents=nightly_cents * nights,
        )

    def preview_payload(self, item: BookableItem | None):
        policy = self.policy_for_item(item)
        return {
            "base_price_cents": policy.base_price_cents,
            "included_guests": policy.included_guests,
            "extra_guest_cents": policy.extra_guest_cents,
            "max_guests": policy.max_guests,
            "currency": policy.currency,
            "label": policy.label,
            "display_base_price": self.display_money(policy.base_price_cents, policy.currency),
            "display_extra_guest_price": self.display_money(policy.extra_guest_cents, policy.currency),
        }

    def display_money(self, cents, currency=None):
        currency = (currency or settings.DEPOSIT_CURRENCY).upper()
        return f"${int(cents or 0) / 100:,.2f} {currency}"

    def _is_six_bed_stay(self, item):
        name = (item.name or "").lower()
        return bool(
            (item.bedrooms and item.bedrooms >= 6)
            or (item.beds and item.beds >= 6)
            or (item.max_guests and item.max_guests >= self.SIX_BED_MAX_GUESTS)
            or re.search(r"\b6\s+(bed|beds|bedroom|bedrooms)\b", name)
        )


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


class CalendarOperationsService:
    """Presentation service for the server-rendered ops Booking Calendar page."""

    DEFAULT_FOCUS_DATE = date(2025, 6, 17)
    WINDOW_DAYS = 23
    MOCK_ROOMS = [
        {
            "title": "3 Beds Apt - Vacation Home & Pool - G-101",
            "unit": "G-101",
            "unit_count": "10",
            "beds": "3 Beds",
            "tone": "purple",
            "marker": "G-101",
        },
        {
            "title": "3 Beds Apt - Vacation Home & Pool - G-102",
            "unit": "G-102",
            "unit_count": "3",
            "beds": "3 Beds",
            "tone": "blue",
            "marker": "G-102",
        },
        {
            "title": "6 Beds Apts - Vacation Home & Pool - G-All",
            "unit": "G-All",
            "unit_count": "2",
            "beds": "6 Beds",
            "tone": "orange",
            "marker": "G-All",
        },
    ]

    def page_payload(self, *, request_path="", view_mode="month", focus_date_value="", selected_stay="", status_filter="all"):
        focus_date = self._focus_date(focus_date_value)
        view_mode = self._view_mode(view_mode)
        selected_stay = selected_stay if selected_stay and selected_stay != "all" else ""
        status_filter = status_filter if status_filter in {"all", "available", "reservation", "blocked", "override"} else "all"
        days = self._visible_days(focus_date, view_mode)
        window_start = days[0]
        window_end = days[-1]

        stays = list(
            BookableItem.objects.filter(category=BookingCategory.STAY, is_active=True)
            .prefetch_related("gallery_images")
            .order_by("name")[: len(self.MOCK_ROOMS)]
        )
        live = self._live_calendar_maps(stays, window_start, window_end)
        all_rows = [
            self._row_payload(index, stays[index] if index < len(stays) else None, days, focus_date, live)
            for index in range(len(self.MOCK_ROOMS))
        ]
        rows = self._selected_rows(all_rows, selected_stay)
        reservation_count = live["reservation_count"] or 24

        return {
            "calendar_section": self._section_from_path(request_path),
            "calendar_view": view_mode,
            "status_filter": status_filter,
            "selected_stay": selected_stay or "all",
            "focus_date_iso": focus_date.isoformat(),
            "month_label": focus_date.strftime("%B %Y"),
            "booking_count": reservation_count,
            "day_columns": [
                self._day_payload(day, focus_date, view_mode, selected_stay, status_filter)
                for day in days
            ],
            "calendar_rows": rows,
            "room_chips": [
                {
                    "label": row["unit"],
                    "count": row["count"],
                    "tone": row["tone"],
                    "active": bool(selected_stay) and selected_stay in {row["slug"], row["unit"]},
                    "href": self._calendar_url(view_mode=view_mode, focus_date=focus_date, selected_stay=row["slug"] or row["unit"], status_filter=status_filter),
                }
                for row in all_rows
            ],
            "all_properties_url": self._calendar_url(view_mode=view_mode, focus_date=focus_date, status_filter=status_filter),
            "property_options": self._property_options(stays, selected_stay),
            "view_tabs": [
                {
                    "label": label,
                    "value": value,
                    "active": view_mode == value,
                    "href": self._calendar_url(view_mode=value, focus_date=focus_date, selected_stay=selected_stay, status_filter=status_filter),
                }
                for value, label in (("month", "Month"), ("week", "Week"), ("day", "Day"))
            ],
            "previous_url": self._calendar_url(
                view_mode=view_mode,
                focus_date=self._previous_date(focus_date, view_mode),
                selected_stay=selected_stay,
                status_filter=status_filter,
            ),
            "next_url": self._calendar_url(
                view_mode=view_mode,
                focus_date=self._next_date(focus_date, view_mode),
                selected_stay=selected_stay,
                status_filter=status_filter,
            ),
            "today_url": self._calendar_url(view_mode=view_mode, focus_date=timezone.localdate(), selected_stay=selected_stay, status_filter=status_filter),
            "new_booking_url": reverse("admin:bookings_bookinginquiry_add"),
            "settings_url": reverse("admin:bookings_calendarfeed_changelist"),
            "calendar_block_api_url": reverse("bookings:ops-calendar-blocks-api"),
            "calendar_price_api_url": reverse("bookings:ops-calendar-prices-api"),
            "generated_at": timezone.now(),
        }

    @staticmethod
    def _view_mode(value):
        return value if value in {"month", "week", "day"} else "month"

    def _visible_days(self, focus_date, view_mode):
        if view_mode == "day":
            return [focus_date]
        if view_mode == "week":
            sunday_offset = (focus_date.weekday() + 1) % 7
            week_start = focus_date - timedelta(days=sunday_offset)
            return [week_start + timedelta(days=offset) for offset in range(7)]
        month_start = focus_date.replace(day=1)
        window_start = month_start - timedelta(days=1)
        return [window_start + timedelta(days=offset) for offset in range(self.WINDOW_DAYS)]

    @staticmethod
    def _selected_rows(rows, selected_stay):
        if not selected_stay:
            return rows
        selected = [
            row
            for row in rows
            if selected_stay in {row["slug"], row["unit"]}
        ]
        return selected or rows

    def _previous_date(self, focus_date, view_mode):
        if view_mode == "day":
            return focus_date - timedelta(days=1)
        if view_mode == "week":
            return focus_date - timedelta(days=7)
        return focus_date - timedelta(days=30)

    def _next_date(self, focus_date, view_mode):
        if view_mode == "day":
            return focus_date + timedelta(days=1)
        if view_mode == "week":
            return focus_date + timedelta(days=7)
        return focus_date + timedelta(days=30)

    @staticmethod
    def _calendar_url(*, view_mode, focus_date, selected_stay="", status_filter="all"):
        params = {
            "view": view_mode,
            "date": focus_date.isoformat(),
        }
        if selected_stay:
            params["stay"] = selected_stay
        if status_filter and status_filter != "all":
            params["status"] = status_filter
        return f"/ops/calendar/?{urlencode(params)}"

    def _live_calendar_maps(self, stays, window_start, window_end):
        item_ids = [stay.pk for stay in stays if stay and stay.pk]
        reservation_map = {}
        block_map = {}
        override_map = {}
        if not item_ids:
            return {
                "reservations": reservation_map,
                "blocks": block_map,
                "overrides": override_map,
                "reservation_count": 0,
            }

        reservations = list(
            BookingInquiry.objects.filter(
                item_id__in=item_ids,
                status__in=BookingCalendarService.ACTIVE_BOOKING_STATUSES,
                check_in__lte=window_end,
                check_out__gt=window_start,
            ).order_by("check_in", "id")
        )
        blocks = list(
            AvailabilityBlock.objects.filter(
                item_id__in=item_ids,
                is_active=True,
                start_date__lte=window_end,
                end_date__gte=window_start,
            ).order_by("start_date", "id")
        )
        overrides = list(
            DailyPriceOverride.objects.filter(
                item_id__in=item_ids,
                is_active=True,
                start_date__lte=window_end,
                end_date__gte=window_start,
            ).order_by("start_date", "id")
        )

        for reservation in reservations:
            for day in self._days_in_range(reservation.check_in, reservation.check_out - timedelta(days=1), window_start, window_end):
                reservation_map.setdefault(reservation.item_id, {}).setdefault(day, []).append(reservation)
        for block in blocks:
            for day in self._days_in_range(block.start_date, block.end_date, window_start, window_end):
                block_map.setdefault(block.item_id, {}).setdefault(day, []).append(block)
        for override in overrides:
            for day in self._days_in_range(override.start_date, override.end_date, window_start, window_end):
                override_map.setdefault(override.item_id, {}).setdefault(day, []).append(override)

        return {
            "reservations": reservation_map,
            "blocks": block_map,
            "overrides": override_map,
            "reservation_count": len(reservations),
        }

    @staticmethod
    def _days_in_range(start, end, lower_bound, upper_bound):
        current = max(start, lower_bound)
        end = min(end, upper_bound)
        while current <= end:
            yield current
            current += timedelta(days=1)

    def _row_payload(self, index, stay, days, focus_date, live):
        mock = self.MOCK_ROOMS[index]
        title = stay.business_display_name if stay else mock["title"]
        unit = self._unit_label(title) or mock["unit"]
        return {
            "title": title,
            "slug": stay.slug if stay else "",
            "item_id": stay.pk if stay else "",
            "unit": unit,
            "count": self._room_count(stay, index, live),
            "beds": self._bed_label(stay, mock),
            "tone": mock["tone"],
            "cells": [
                self._cell_payload(index, stay.pk if stay else None, day, offset, focus_date, live)
                for offset, day in enumerate(days)
            ],
        }

    def _cell_payload(self, row_index, item_id, day, offset, focus_date, live):
        if item_id:
            live_cell = self._live_cell(item_id, day, live)
            if live_cell:
                live_cell["is_active_day"] = day == focus_date
                live_cell["item_id"] = item_id
                live_cell["can_edit"] = True
                return live_cell

        cell = self._mock_cell(row_index, offset)
        cell.update(
            {
                "item_id": item_id or "",
                "record_id": "",
                "record_type": "",
                "can_edit": bool(item_id),
                "date": day,
                "date_iso": day.isoformat(),
                "is_active_day": day == focus_date,
                "href": f"/ops/calendar/?date={day.isoformat()}",
                "admin_href": "",
            }
        )
        return cell

    def _live_cell(self, item_id, day, live):
        reservations = live["reservations"].get(item_id, {}).get(day, [])
        if reservations:
            reservation = reservations[0]
            guests = reservation.guests or 1
            return {
                "status": "reservation",
                "label": f"{guests} guests",
                "meta": f"+{max(guests + 1, 2)}",
                "date": day,
                "date_iso": day.isoformat(),
                "record_type": "reservation",
                "record_id": reservation.pk,
                "href": reverse("admin:bookings_bookinginquiry_change", args=[reservation.pk]),
                "admin_href": reverse("admin:bookings_bookinginquiry_change", args=[reservation.pk]),
            }

        blocks = live["blocks"].get(item_id, {}).get(day, [])
        if blocks:
            block = blocks[0]
            return {
                "status": "blocked",
                "label": "Blocked",
                "meta": "",
                "date": day,
                "date_iso": day.isoformat(),
                "record_type": "block",
                "record_id": block.pk,
                "href": reverse("admin:bookings_availabilityblock_change", args=[block.pk]),
                "admin_href": reverse("admin:bookings_availabilityblock_change", args=[block.pk]),
            }

        overrides = live["overrides"].get(item_id, {}).get(day, [])
        if overrides:
            override = overrides[-1]
            return {
                "status": "override",
                "label": f"${override.nightly_price:,.0f}",
                "meta": "",
                "date": day,
                "date_iso": day.isoformat(),
                "record_type": "price",
                "record_id": override.pk,
                "href": reverse("admin:bookings_dailypriceoverride_change", args=[override.pk]),
                "admin_href": reverse("admin:bookings_dailypriceoverride_change", args=[override.pk]),
            }
        return None

    @staticmethod
    def _mock_cell(row_index, offset):
        if row_index == 1 and offset == 22:
            return {"status": "blocked", "label": "Blocked", "meta": ""}

        if row_index == 0 and offset >= 14:
            label_by_offset = {
                14: "3 guests",
                15: "3 guests",
                16: "3 guests",
                17: "1 guests",
                18: "1 guests",
                19: "1 guests",
                20: "1 guests",
                21: "1 guests",
                22: "2 guests",
            }
            meta_by_offset = {14: "+3", 15: "+7", 16: "+9", 17: "+5", 18: "+8", 19: "+8", 20: "+8", 21: "+9", 22: "+4"}
            return {
                "status": "reservation",
                "label": label_by_offset.get(offset, "1 guests"),
                "meta": meta_by_offset.get(offset, ""),
            }

        if row_index == 2 and offset >= 14:
            return {"status": "override", "label": "12 guests", "meta": ""}

        return {"status": "available", "label": "Available", "meta": ""}

    def _day_payload(self, day, focus_date, view_mode, selected_stay, status_filter):
        return {
            "date": day,
            "date_iso": day.isoformat(),
            "weekday": day.strftime("%a"),
            "day": day.day,
            "is_focus": day == focus_date,
            "href": self._calendar_url(view_mode=view_mode, focus_date=day, selected_stay=selected_stay, status_filter=status_filter),
        }

    @staticmethod
    def _focus_date(value):
        if value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                if len(value) == 7:
                    try:
                        return date.fromisoformat(f"{value}-17")
                    except ValueError:
                        pass
        return CalendarOperationsService.DEFAULT_FOCUS_DATE

    @staticmethod
    def _section_from_path(path):
        if "/list/" in path:
            return "list"
        if "/rooms/" in path:
            return "rooms"
        if "/analytics/" in path:
            return "analytics"
        return "calendar"

    @staticmethod
    def _unit_label(title):
        match = re.search(r"\b([A-Z])[-\s]?(All|\d{3})\b", title or "", flags=re.IGNORECASE)
        if not match:
            return ""
        return f"{match.group(1).upper()}-{match.group(2)}"

    @staticmethod
    def _bed_label(stay, mock):
        if stay and stay.bedrooms:
            return f"{stay.bedrooms} Beds"
        if stay and stay.beds:
            return f"{stay.beds} Beds"
        return mock["beds"]

    @staticmethod
    def _property_options(stays, selected_stay):
        options = [{"label": "All Properties", "value": "all", "active": not selected_stay}]
        options.extend(
            {
                "label": stay.business_display_name,
                "value": stay.slug,
                "active": stay.slug == selected_stay,
            }
            for stay in stays
        )
        return options

    def _room_count(self, stay, index, live):
        if not stay:
            return self.MOCK_ROOMS[index]["unit_count"]
        real_count = sum(len(day_rows) for day_rows in live["reservations"].get(stay.pk, {}).values())
        return str(real_count or self.MOCK_ROOMS[index]["unit_count"])


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

    ALLOWED_SESSION_AGENT_MODES = {"openai", "fallback", "setup"}

    def __init__(self, api_key=None, client=None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model = settings.OPENAI_AGENT_MODEL
        self.client = client

    def reply(self, request: AgentRequest) -> AgentResponse:
        item = self._get_item(request.item_id)
        topic = QuestionAnalyticsService.classify(request.message)
        metadata = {"topic": topic}

        if self._should_guardrail(request, item, topic):
            reply = self._guardrail_reply()
            metadata.update({"agent_mode": "guardrail", "guardrail_reason": "off_topic"})
        elif not self.api_key:
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
            user_id=request.user_id,
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

    def _should_guardrail(self, request, item, topic):
        if item or QuestionAnalyticsService.is_business_related(request.message, topic=topic):
            return False
        if self._has_booking_context(request.session_id) and QuestionAnalyticsService.is_contextual_follow_up(request.message):
            return False
        return True

    def _has_booking_context(self, session_id):
        if not session_id:
            return False
        last_conversation = AgentConversation.objects.filter(session_id=session_id).order_by("-created_at").first()
        if not last_conversation:
            return False
        return (last_conversation.metadata or {}).get("agent_mode") in self.ALLOWED_SESSION_AGENT_MODES

    def _guardrail_reply(self):
        return (
            "I can only help with MLADIS bookings, stays, deposits, rules, concierge services, guest accounts, "
            "and public business policies. Please ask about a stay, dates, guest count, availability, the damage-deposit hold, "
            "house rules, concierge help, account support, or MLADIS business information."
        )

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
        client = self.client or _build_openai_client(self.api_key)
        response = client.responses.create(
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
            "Ask for dates, guest count, preferred stay, full name, email, and phone when the guest wants to book. "
            "Do not promise discounts, "
            "early or late checkout, exact address details, private pool access, or waived house rules unless "
            "an admin has explicitly confirmed them. If a question needs owner action, direct the guest to "
            "submit the booking form or contact MLADIS. If a guest asks for unrelated general knowledge, jokes, or help outside MLADIS business topics, "
            "politely refuse and redirect them back to booking, guest support, account support, or business-policy questions. Default to well-organized plain text with short headings, "
            "numbered steps, and short bullet lists instead of dense paragraphs. For booking, availability, deposit, "
            "or next-step questions, use the preferred booking answer template from the prompt unless the guest asks for "
            "a much shorter reply. Keep the same section titles and order: opening line, Quick steps (English / Español), "
            "Important notes, and Next step - ready to book?. Include short Spanish lines after each numbered step. Keep each "
            "list item to one sentence when possible. Do not use markdown tables. Use the selected stay context, booking workflow, "
            "preferred booking answer template, repository-backed guest knowledge, and admin-provided knowledge sources from the prompt as your source of truth, "
            "but never mention the repository or internal files to the guest."
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
            "",
            "Preferred booking answer template:",
            self._response_template_context(),
            "",
            "Repository-backed guest knowledge:",
            self._repo_knowledge_context(),
            "",
            "Admin and external knowledge sources:",
            self._agent_knowledge_sources_context(),
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

    def _response_template_context(self):
        return (
            "Opening line: Great - I can help. Here's how to make a reservation and what to expect.\n"
            "Quick steps (English / Español)\n"
            "1) Choose a stay on our site, or offer the main options: G-101, G-102, 6-bedroom, or Custom Booking Concierge.\n"
            "   - Elige una estancia en nuestro sitio, u ofrece las opciones principales: G-101, G-102, 6 habitaciones o Custom Booking Concierge.\n"
            "2) Tell the guest to fill the booking form with stay, arrival and departure dates, guest count, full name, email, phone, coupon if any, and special requests.\n"
            "   - Indica al huesped que complete el formulario con estancia, fechas de llegada y salida, numero de huespedes, nombre completo, correo, telefono, cupon si tiene y peticiones especiales.\n"
            "3) Explain that after submitting, the site opens the refundable $200 USD damage-deposit authorization hold through Stripe Checkout or PayPal.\n"
            "   - Explica que despues de enviar, el sitio abre la retencion reembolsable de deposito por $200 USD mediante Stripe Checkout o PayPal.\n"
            "4) Explain that all reservation requests go to MLADIS admins for review and confirmation by email.\n"
            "   - Explica que todas las solicitudes pasan al equipo de MLADIS para revision y confirmacion por correo.\n"
            "Important notes\n"
            "- Say that availability, final pricing, discounts, address details, pool exceptions, and waived rules require admin confirmation.\n"
            "- Say that standard house rules apply: no parties or events, no indoor smoking, registered guests only, respect quiet hours, and protect keys or smart locks.\n"
            "- Say that concierge, airport pickup, and add-on requests should use Custom Booking Concierge or be written in the form.\n"
            "Next step - ready to book?\n"
            "- Ask for exact arrival and departure dates, guest count, preferred stay, full name, email, and phone number.\n"
            "- If the guest wants help choosing first, ask for group size and travel dates and recommend the best option."
        )

    def _repo_knowledge_context(self):
        snippets = _repo_knowledge_snippets()
        if not snippets:
            return "No additional repository-backed guest guidance loaded."
        return "\n".join(f"- {snippet}" for snippet in snippets)

    def _agent_knowledge_sources_context(self):
        snippets = _agent_knowledge_source_snippets()
        if not snippets:
            return "No admin-provided knowledge sources loaded."
        return "\n".join(f"- {snippet}" for snippet in snippets)

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
        "business": {
            "mladis",
            "business",
            "contact",
            "support",
            "policy",
            "privacy",
            "terms",
            "account",
            "login",
            "sign in",
            "signup",
            "invoice",
            "payment",
            "paypal",
            "stripe",
            "website",
            "airbnb",
            "concierge",
            "guest",
            "apartment",
            "stay",
            "special request",
            "g-101",
            "g-102",
            "6-bedroom",
            "6 bedroom",
        },
    }

    CONTEXT_FOLLOW_UP_HINTS = {
        "yes",
        "no",
        "ok",
        "okay",
        "sure",
        "si",
        "sí",
        "thanks",
        "thank you",
        "gracias",
        "tomorrow",
        "today",
        "tonight",
        "weekend",
        "friday",
        "saturday",
        "sunday",
        "lunes",
        "martes",
        "miercoles",
        "miércoles",
        "jueves",
        "viernes",
        "sabado",
        "sábado",
        "domingo",
        "g-101",
        "g-102",
        "concierge",
        "custom",
    }

    OFF_TOPIC_HINTS = {
        "joke",
        "weather",
        "news",
        "recipe",
        "poem",
        "song",
        "movie",
        "sports",
        "bitcoin",
        "stock",
        "president",
        "python",
        "code",
        "homework",
    }

    @classmethod
    def classify(cls, message):
        lowered = (message or "").lower()
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                return topic
        return "general"

    @classmethod
    def is_business_related(cls, message, topic=None):
        if topic and topic != "general":
            return True
        lowered = (message or "").lower()
        return any(keyword in lowered for keyword in cls.TOPIC_KEYWORDS["business"])

    @classmethod
    def is_contextual_follow_up(cls, message):
        raw = (message or "").strip()
        lowered = raw.lower()
        if not lowered or any(keyword in lowered for keyword in cls.OFF_TOPIC_HINTS):
            return False
        if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", raw, flags=re.IGNORECASE):
            return True
        if len(re.sub(r"\D", "", raw)) >= 7:
            return True
        if re.search(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?)\b", lowered):
            return True
        if any(keyword in lowered for keyword in cls.CONTEXT_FOLLOW_UP_HINTS):
            return True
        return "?" not in raw and len(lowered.split()) <= 4 and len(lowered) <= 40


class ReservationRequestService:
    def create_from_form(self, form, request):
        inquiry = form.save(commit=False)
        if request.user.is_authenticated:
            inquiry.user = request.user
        self.prepare(inquiry, coupon=form.coupon, redeem_coupon=True)
        inquiry.save()
        self.log_object_event(inquiry, "reservation_request.created", request=request)
        return inquiry

    def prepare(self, inquiry: BookingInquiry, coupon=None, redeem_coupon=False):
        inquiry.customer_profile = CustomerProfile.find_or_create_for_email(
            inquiry.email,
            defaults={
                "name": inquiry.guest_name,
                "phone": inquiry.phone,
            },
        )
        if inquiry.customer_profile and inquiry.user_id and not inquiry.customer_profile.user_id:
            inquiry.customer_profile.user = inquiry.user
            inquiry.customer_profile.save(update_fields=["user", "updated_at"])
        inquiry.is_blacklist_flagged = bool(
            inquiry.customer_profile and inquiry.customer_profile.segment == ClientSegment.BLACKLISTED
        )
        inquiry.cancellation_policy = inquiry.cancellation_policy or CancellationPolicy.default()
        inquiry.currency = settings.DEPOSIT_CURRENCY
        inquiry.deposit_cents = settings.DEPOSIT_AMOUNT_CENTS

        if inquiry.is_admin_test:
            inquiry.subtotal_cents = 0
            inquiry.discount_cents = 0
            inquiry.deposit_cents = 0
            inquiry.total_cents = 0
            return inquiry

        self.apply_pricing(inquiry)

        if coupon:
            inquiry.coupon = coupon
            inquiry.coupon_code = coupon.code
            inquiry.discount_cents = coupon.discount_for(inquiry.subtotal_cents)
            if redeem_coupon:
                type(coupon).objects.filter(pk=coupon.pk).update(redemption_count=F("redemption_count") + 1)
        elif not inquiry.coupon_id:
            inquiry.discount_cents = 0

        inquiry.total_cents = max(
            inquiry.reservation_payment_cents + inquiry.deposit_cents,
            0,
        )
        return inquiry

    def apply_pricing(self, inquiry: BookingInquiry):
        quote = ReservationPricingService().quote(
            inquiry.item,
            guests=inquiry.guests,
            nights=inquiry.nights or 1,
        )
        inquiry.subtotal_cents = quote.subtotal_cents
        inquiry.currency = quote.policy.currency
        return quote

    def log_object_event(self, inquiry, event_name, request=None):
        try:
            from .data_lake import DataLakeObjectEventWriter

            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_name,
                instance=inquiry,
                request=request,
                data={
                    "request_key": inquiry.request_key,
                    "status": inquiry.status,
                    "item_id": inquiry.item_id,
                    "customer_profile_id": inquiry.customer_profile_id,
                    "user_id": inquiry.user_id,
                    "email_delivery_status": inquiry.email_delivery_status,
                    "subtotal_cents": inquiry.subtotal_cents,
                    "reservation_payment_cents": inquiry.reservation_payment_cents,
                    "deposit_cents": inquiry.deposit_cents,
                    "total_cents": inquiry.total_cents,
                },
            )
        except Exception:
            # Data-lake writes are audit side effects and must not block a guest request.
            return


class MaintenanceService:
    """Application service for maintenance event creation and evidence logging."""

    REQUIRED_PHOTO_STATUSES = {
        MaintenanceStatus.LOGGED,
        MaintenanceStatus.SCHEDULED,
        MaintenanceStatus.IN_PROGRESS,
        MaintenanceStatus.COMPLETED,
        MaintenanceStatus.DOCUMENTED,
        MaintenanceStatus.BILLED,
        MaintenanceStatus.ARCHIVED,
    }

    DATETIME_FIELDS = ("reported_at", "started_at", "completed_at", "captured_at")

    def create_event(self, *, user, data, files, request=None):
        payload = self._mutable_payload(data)
        uploaded_photos = self._uploaded_photos(files)
        status = payload.get("status") or MaintenanceStatus.COMPLETED
        if status in self.REQUIRED_PHOTO_STATUSES and not uploaded_photos:
            raise ValidationError({"photos": "Add at least one photo for maintenance evidence."})

        booking = self._booking(payload.get("booking"))
        item_id = payload.get("item") or (booking.item_id if booking else None)
        if booking and not item_id:
            raise ValidationError({"booking": "Selected reservation is not attached to a listing."})

        with transaction.atomic():
            event = MaintenanceEvent(
                item_id=item_id,
                booking=booking,
                title=(payload.get("title") or "").strip(),
                work_type=payload.get("work_type") or "cleaning",
                status=status,
                cost_amount=self._decimal(payload.get("cost_amount")),
                cost_currency=(payload.get("cost_currency") or "USD").strip().upper(),
                reported_at=self._datetime(payload.get("reported_at")) or timezone.now(),
                started_at=self._datetime(payload.get("started_at")),
                completed_at=self._datetime(payload.get("completed_at")),
                timezone_name=(payload.get("timezone_name") or "America/Santo_Domingo").strip(),
                vendor_name=(payload.get("vendor_name") or "").strip(),
                vendor_contact=(payload.get("vendor_contact") or "").strip(),
                invoice_number=(payload.get("invoice_number") or "").strip(),
                proof_of_payment_ref=(payload.get("proof_of_payment_ref") or "").strip(),
                payment_status=payload.get("payment_status") or "pending",
                tax_category_code=(payload.get("tax_category_code") or "").strip(),
                description=(payload.get("description") or "").strip(),
                admin_notes=(payload.get("admin_notes") or "").strip(),
                created_by=user,
            )
            event.full_clean()
            event.save()

            captions = self._list_values(data, "photo_captions")
            captured_values = self._list_values(data, "photo_captured_at")
            for index, upload in enumerate(uploaded_photos):
                photo = MaintenancePhoto(
                    event=event,
                    image=upload,
                    caption=(captions[index] if index < len(captions) else upload.name).strip(),
                    sort_order=index,
                    is_cover=index == 0,
                    checksum_sha256=self._checksum(upload),
                    mime_type=getattr(upload, "content_type", "") or "",
                    file_size_bytes=getattr(upload, "size", 0) or 0,
                    captured_at=self._datetime(captured_values[index]) if index < len(captured_values) else None,
                )
                photo.full_clean()
                photo.save()

        self.log_object_event(event, "maintenance_event.created", request=request)
        return event

    def agent_payload(self, event):
        return event.to_agent_payload()

    def generate_ai_description(self, event, request=None):
        result = MaintenanceVisionAgent().describe(event)
        event.ai_description = result.description
        event.ai_description_generated_at = timezone.now()
        event.ai_description_model = result.model
        event.ai_description_metadata = {
            "confidence": result.confidence,
            "observations": result.observations,
        }
        event.use_ai_description = True
        if not event.description:
            event.description = result.description
        event.full_clean()
        event.save(
            update_fields=[
                "description",
                "ai_description",
                "ai_description_generated_at",
                "ai_description_model",
                "ai_description_metadata",
                "use_ai_description",
                "updated_at",
            ]
        )
        self.log_object_event(event, "maintenance_event.ai_description_generated", request=request)
        return event

    def preview_ai_description(self, *, data, files):
        payload = self._mutable_payload(data)
        uploaded_photos = self._uploaded_photos(files)
        if not uploaded_photos:
            raise ValidationError({"photos": "Add at least one photo before auto-generating the work description."})

        item_name = ""
        item_id = payload.get("item")
        if item_id:
            item = BookableItem.objects.filter(pk=item_id).first()
            item_name = item.business_display_name if item else ""

        work_type = payload.get("work_type") or "cleaning"
        status = payload.get("status") or MaintenanceStatus.COMPLETED
        amount = self._decimal(payload.get("cost_amount"))
        currency = (payload.get("cost_currency") or "USD").strip().upper()
        context = MaintenanceDescriptionContext(
            title=(payload.get("title") or "Maintenance work").strip(),
            item_name=item_name,
            work_type_label=dict(MaintenanceWorkType.choices).get(work_type, work_type),
            status_label=dict(MaintenanceStatus.choices).get(status, status),
            display_cost=f"{currency} {amount:,.2f}",
            manual_notes=(payload.get("description") or "").strip(),
        )
        return MaintenanceVisionAgent().describe_uploads(context, uploaded_photos)

    def log_object_event(self, event, event_name, request=None):
        try:
            from .data_lake import DataLakeObjectEventWriter

            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_name,
                instance=event,
                request=request,
                data={
                    "item_id": event.item_id,
                    "booking_id": event.booking_id,
                    "work_type": event.work_type,
                    "status": event.status,
                    "cost_amount": str(event.cost_amount),
                    "cost_currency": event.cost_currency,
                    "photo_count": event.photo_count,
                    "is_tax_ready": event.is_tax_ready,
                },
            )
        except Exception:
            return

    @staticmethod
    def _mutable_payload(data):
        return {key: data.get(key) for key in data.keys()}

    @staticmethod
    def _uploaded_photos(files):
        if hasattr(files, "getlist"):
            return list(files.getlist("photos") or files.getlist("photo") or [])
        photo = files.get("photos") or files.get("photo") if files else None
        return [photo] if photo else []

    @staticmethod
    def _list_values(data, key):
        if hasattr(data, "getlist"):
            return [value for value in data.getlist(key) if value]
        value = data.get(key) if data else ""
        if isinstance(value, (list, tuple)):
            return [item for item in value if item]
        return [value] if value else []

    @staticmethod
    def _datetime(value):
        if not value:
            return None
        if isinstance(value, datetime):
            parsed = value
        else:
            parsed = parse_datetime(str(value))
        if parsed and timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

    @staticmethod
    def _decimal(value):
        if value in (None, ""):
            return Decimal("0.00")
        return Decimal(str(value))

    @staticmethod
    def _booking(value):
        if not value:
            return None
        try:
            booking_id = int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"booking": "Choose a valid reservation."}) from exc
        booking = BookingInquiry.objects.select_related("item").filter(pk=booking_id).first()
        if not booking:
            raise ValidationError({"booking": "Selected reservation was not found."})
        return booking

    @staticmethod
    def _checksum(upload):
        digest = hashlib.sha256()
        position = None
        if hasattr(upload, "tell") and hasattr(upload, "seek"):
            position = upload.tell()
            upload.seek(0)
        for chunk in upload.chunks():
            digest.update(chunk)
        if position is not None:
            upload.seek(position)
        return digest.hexdigest()


@dataclass(frozen=True)
class MaintenanceDescriptionResult:
    description: str
    observations: list[str]
    confidence: str
    model: str


@dataclass(frozen=True)
class MaintenanceDescriptionContext:
    title: str
    item_name: str
    work_type_label: str
    status_label: str
    display_cost: str
    manual_notes: str


class MaintenanceVisionAgent:
    """Vision-backed agent for turning maintenance photos into work notes."""

    MAX_PHOTOS = 6

    def __init__(self, api_key=None, model=None, max_photos=None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model = (
            model
            or getattr(settings, "OPENAI_MAINTENANCE_VISION_MODEL", "")
            or settings.OPENAI_AGENT_MODEL
        )
        self.max_photos = max_photos or getattr(settings, "MAINTENANCE_AI_MAX_PHOTOS", self.MAX_PHOTOS)

    def describe(self, event):
        if not self.api_key:
            raise ValidationError(
                {"ai_description": "OpenAI is not configured. Set OPENAI_API_KEY before using AI descriptions."}
            )

        photos = list(event.photos.all().order_by("sort_order", "uploaded_at")[: self.max_photos])
        if not photos:
            raise ValidationError({"photos": "Add at least one photo before generating an AI work description."})

        context = MaintenanceDescriptionContext(
            title=event.title,
            item_name=event.item.business_display_name if event.item else "",
            work_type_label=event.get_work_type_display(),
            status_label=event.get_status_display(),
            display_cost=event.display_cost,
            manual_notes=event.description or "",
        )
        response_text = self._call_model(context, [self._photo_data_url(photo) for photo in photos])
        result = self._parse_response(response_text)
        if not result.description:
            raise ValidationError({"ai_description": "The maintenance agent did not return a usable description."})
        return result

    def describe_uploads(self, context, uploads):
        if not self.api_key:
            raise ValidationError(
                {"ai_description": "OpenAI is not configured. Set OPENAI_API_KEY before using AI descriptions."}
            )
        image_urls = [self._upload_data_url(upload) for upload in uploads[: self.max_photos]]
        response_text = self._call_model(context, image_urls)
        result = self._parse_response(response_text)
        if not result.description:
            raise ValidationError({"ai_description": "The maintenance agent did not return a usable description."})
        return result

    def _call_model(self, context, image_urls):
        client = _build_openai_client(self.api_key)
        content = [
            {
                "type": "input_text",
                "text": self._prompt(context),
            }
        ]
        for data_url in image_urls:
            if data_url:
                content.append({"type": "input_image", "image_url": data_url, "detail": "low"})

        if len(content) == 1:
            raise ValidationError({"photos": "The attached photos could not be read for AI description."})

        response = client.responses.create(
            model=self.model,
            input=[{"role": "user", "content": content}],
            max_output_tokens=700,
        )
        return getattr(response, "output_text", "") or ""

    def _prompt(self, context):
        return (
            "You are a maintenance documentation assistant for MLADIS property operations. "
            "Inspect the attached maintenance photos and create concise, business-ready work notes. "
            "Use only evidence visible in the photos plus the provided record metadata; do not invent vendor names, "
            "costs, dates, causes, or completed work that is not visible. "
            "Return JSON only with keys: description, observations, confidence. "
            "The description should be 2 to 4 sentences and suitable for a bill, tax record, or admin review. "
            f"Record title: {context.title}. "
            f"Stay: {context.item_name}. "
            f"Work type: {context.work_type_label}. "
            f"Status: {context.status_label}. "
            f"Cost: {context.display_cost}. "
            f"Manual notes: {context.manual_notes or 'none'}."
        )

    def _photo_data_url(self, photo):
        try:
            photo.image.open("rb")
            raw = photo.image.read()
        finally:
            try:
                photo.image.close()
            except Exception:
                pass
        if not raw:
            return ""
        mime_type = photo.mime_type or "image/jpeg"
        if not mime_type.startswith("image/"):
            mime_type = "image/jpeg"
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _upload_data_url(self, upload):
        position = None
        raw = b""
        try:
            if hasattr(upload, "tell") and hasattr(upload, "seek"):
                position = upload.tell()
                upload.seek(0)
            if hasattr(upload, "chunks"):
                raw = b"".join(upload.chunks())
            else:
                raw = upload.read()
        finally:
            if position is not None:
                upload.seek(position)
        if not raw:
            return ""
        mime_type = getattr(upload, "content_type", "") or "image/jpeg"
        if not mime_type.startswith("image/"):
            mime_type = "image/jpeg"
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _parse_response(self, response_text):
        text = (response_text or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {"description": text, "observations": [], "confidence": "medium"}

        description = str(payload.get("description") or "").strip()
        observations = payload.get("observations") or []
        if not isinstance(observations, list):
            observations = [str(observations)]
        confidence = str(payload.get("confidence") or "medium").strip().lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "medium"
        return MaintenanceDescriptionResult(
            description=description,
            observations=[str(item).strip() for item in observations if str(item).strip()],
            confidence=confidence,
            model=self.model,
        )


class BookingEmailService:
    DAMAGE_DEPOSIT_EMAIL_MARKER = "email_confirmed:damage_deposit_authorized"
    RESERVATION_PAYMENT_EMAIL_MARKER = "email_confirmed:reservation_payment_authorized"

    def send_inquiry_notifications(self, inquiry: BookingInquiry, request=None):
        site_settings = SiteSettings.current()
        if not site_settings.request_notifications_email:
            inquiry.email_delivery_status = EmailDeliveryStatus.PENDING
            inquiry.email_error = "Admin email notifications disabled in Site Settings."
            inquiry.save(update_fields=["email_delivery_status", "email_error", "updated_at"])
            return False

        recipients = settings.BOOKING_INQUIRY_RECIPIENTS
        if not recipients:
            inquiry.email_delivery_status = EmailDeliveryStatus.FAILED
            inquiry.email_error = "No BOOKING_INQUIRY_RECIPIENTS configured."
            inquiry.save(update_fields=["email_delivery_status", "email_error", "updated_at"])
            return False

        subject = self._subject(
            f"{inquiry.request_key} | New reservation request | {inquiry.guest_name}"
        )
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
                self._subject("We received your MLADIS reservation request"),
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

    def send_damage_deposit_confirmation(self, deposit: DamageDeposit, request=None):
        if not deposit or self.DAMAGE_DEPOSIT_EMAIL_MARKER in (deposit.notes or ""):
            return False
        if deposit.status not in {DepositStatus.REQUIRES_CAPTURE, DepositStatus.CAPTURED}:
            return False

        sent = self._send_transaction_confirmation(
            code="MLADIS_DAMAGE_DEPOSIT_CONFIRMATION_V1",
            subject=f"{self._request_key(deposit)} | Security deposit hold recorded | {deposit.guest_name}",
            customer_subject="Your security deposit hold is recorded",
            guest_name=deposit.guest_name,
            guest_email=deposit.email,
            amount=deposit.display_amount,
            item_name=self._item_name(deposit),
            status=deposit.status,
            request_key=self._request_key(deposit),
            admin_url=self._admin_url(request, "damagedeposit", deposit.id),
            confirmation_url=self._payment_confirmation_url(request, deposit),
            extra_lines=[
                "transaction_type=security_deposit_hold",
                f"damage_deposit_id={deposit.id}",
                f"booking_inquiry_id={deposit.inquiry_id or ''}",
                f"payment_provider={deposit.payment_provider}",
                f"stripe_checkout_session_id={deposit.stripe_checkout_session_id}",
                f"stripe_payment_intent_id={deposit.stripe_payment_intent_id}",
                "capture_rule=refundable hold; capture only if needed for damages or approved charges",
            ],
            customer_note="The security deposit is a refundable authorization hold and is captured only if needed for approved damages or charges.",
            provider=deposit.payment_provider,
        )
        if sent:
            deposit.notes = self._append_note(
                deposit.notes,
                f"{self.DAMAGE_DEPOSIT_EMAIL_MARKER} at {timezone.now().isoformat()}",
            )
            deposit.save(update_fields=["notes", "updated_at"])
            self._log_email_event(deposit, "damage_deposit.email_confirmed", request)
        return sent

    def send_reservation_payment_confirmation(self, hold: ReservationPaymentHold, request=None):
        if not hold or self.RESERVATION_PAYMENT_EMAIL_MARKER in (hold.notes or ""):
            return False
        if hold.status not in {DepositStatus.REQUIRES_CAPTURE, DepositStatus.CAPTURED}:
            return False

        sent = self._send_transaction_confirmation(
            code="MLADIS_RESERVATION_PAYMENT_CONFIRMATION_V1",
            subject=f"{self._request_key(hold)} | Reservation payment hold recorded | {hold.guest_name}",
            customer_subject="Your reservation payment hold is recorded",
            guest_name=hold.guest_name,
            guest_email=hold.email,
            amount=hold.display_amount,
            item_name=self._item_name(hold),
            status=hold.status,
            request_key=self._request_key(hold),
            admin_url=self._admin_url(request, "reservationpaymenthold", hold.id),
            confirmation_url=self._payment_confirmation_url(request, hold),
            extra_lines=[
                "transaction_type=reservation_payment_hold",
                f"reservation_payment_hold_id={hold.id}",
                f"booking_inquiry_id={hold.inquiry_id or ''}",
                f"payment_provider={hold.payment_provider}",
                f"stripe_checkout_session_id={hold.stripe_checkout_session_id}",
                f"stripe_payment_intent_id={hold.stripe_payment_intent_id}",
                f"capture_after={hold.capture_after.isoformat() if hold.capture_after else ''}",
                "capture_rule=manual capture 24 hours before check-in",
            ],
            customer_note="The reservation payment hold is captured 24 hours before check-in unless the request is changed or canceled under the active policy.",
            provider=hold.payment_provider,
        )
        if sent:
            hold.notes = self._append_note(
                hold.notes,
                f"{self.RESERVATION_PAYMENT_EMAIL_MARKER} at {timezone.now().isoformat()}",
            )
            hold.save(update_fields=["notes", "updated_at"])
            self._log_email_event(hold, "reservation_payment_hold.email_confirmed", request)
        return sent

    def _send_transaction_confirmation(
        self,
        *,
        code,
        subject,
        customer_subject,
        guest_name,
        guest_email,
        amount,
        item_name,
        status,
        request_key,
        admin_url,
        confirmation_url,
        extra_lines,
        customer_note,
        provider,
    ):
        recipients = settings.BOOKING_INQUIRY_RECIPIENTS
        if not recipients or not guest_email:
            return False

        mode = self._mode_label(provider)
        admin_body = "\n".join(
            [
                code,
                "",
                "[transaction]",
                f"mode={mode}",
                f"request_key={request_key}",
                f"guest_name={guest_name}",
                f"guest_email={guest_email}",
                f"item={item_name}",
                f"amount={amount}",
                f"status={status}",
                *extra_lines,
                "",
                "[links]",
                f"admin_url={admin_url}",
                f"payment_confirmation_url={confirmation_url}",
            ]
        )
        confirmation_lines = []
        if confirmation_url:
            confirmation_lines = [
                f"Confirmation: {confirmation_url}",
                "",
            ]
        customer_body = "\n".join(
            [
                f"Hi {guest_name},",
                "",
                f"{self._mode_header(provider)}Your {amount} authorization hold is recorded for {item_name}.",
                f"Reference: {request_key}",
                f"Status: {status}",
                "",
                "This is an authorization hold, not a final capture at this step.",
                customer_note,
                "",
                *confirmation_lines,
                "MLADIS",
            ]
        )

        try:
            send_mail(
                self._subject(subject, provider=provider),
                admin_body,
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=False,
            )
            send_mail(
                self._subject(customer_subject, provider=provider),
                customer_body,
                settings.DEFAULT_FROM_EMAIL,
                [guest_email],
                fail_silently=False,
            )
        except Exception:
            return False
        return True

    def _admin_body(self, inquiry, request=None):
        item_name = inquiry.item.business_display_name if inquiry.item else "Flexible / help me choose"
        admin_url = ""
        if request:
            admin_url = request.build_absolute_uri(f"/admin/bookings/bookinginquiry/{inquiry.id}/change/")
        return "\n".join(
            [
                "MLADIS_RESERVATION_REQUEST_V1",
                "",
                "[request]",
                f"mode={self._mode_label()}",
                f"request_key={inquiry.request_key}",
                f"request_id={inquiry.id}",
                f"status={inquiry.status}",
                f"created_at={inquiry.created_at.isoformat() if inquiry.created_at else ''}",
                "",
                "[guest]",
                f"name={inquiry.guest_name}",
                f"email={inquiry.email}",
                f"phone={inquiry.phone or ''}",
                f"customer_profile_id={inquiry.customer_profile_id or ''}",
                f"user_id={inquiry.user_id or ''}",
                "",
                "[stay]",
                f"item_id={inquiry.item_id or ''}",
                f"item={item_name}",
                f"check_in={inquiry.check_in}",
                f"check_out={inquiry.check_out}",
                f"nights={inquiry.nights}",
                f"guests={inquiry.guests}",
                "",
                "[pricing]",
                f"coupon={inquiry.coupon_code or ''}",
                f"subtotal_cents={inquiry.subtotal_cents}",
                f"discount_cents={inquiry.discount_cents}",
                f"reservation_payment_cents={inquiry.reservation_payment_cents}",
                f"deposit_cents={inquiry.deposit_cents}",
                f"total_cents={inquiry.total_cents}",
                f"currency={inquiry.currency}",
                "",
                "[flags]",
                f"admin_test={'true' if inquiry.is_admin_test else 'false'}",
                f"blacklist_flagged={'true' if inquiry.is_blacklist_flagged else 'false'}",
                "",
                "[message]",
                inquiry.message or "",
                "",
                "[links]",
                f"admin_url={admin_url}",
            ]
        )

    def _customer_body(self, inquiry):
        item_name = inquiry.item.name if inquiry.item else "your MLADIS stay"
        return "\n".join(
            [
                f"Hi {inquiry.guest_name},",
                "",
                f"{self._mode_header()}We received your request for {item_name}.",
                f"Dates: {inquiry.check_in} to {inquiry.check_out}",
                f"Guests: {inquiry.guests}",
                f"Reservation payment hold: {inquiry.display_reservation_payment}",
                f"Security deposit hold: {inquiry.display_deposit}",
                f"Estimated total authorization: {inquiry.display_total}",
                "",
                "This is an admin-confirmed request. We will review availability and follow up with the next step.",
                "",
                "MLADIS",
            ]
        )

    def _subject(self, subject, provider=None):
        prefix = "(TEST) " if self._is_test_mode(provider) and not subject.startswith("(TEST)") else ""
        return f"{prefix}{subject}"

    def _mode_header(self, provider=None):
        return "(TEST) " if self._is_test_mode(provider) else ""

    def _mode_label(self, provider=None):
        return "TEST" if self._is_test_mode(provider) else "LIVE"

    def _is_test_mode(self, provider=None):
        email_backend = getattr(settings, "EMAIL_BACKEND", "")
        if getattr(settings, "DEBUG", False):
            return True
        if email_backend.endswith(".console.EmailBackend") or email_backend.endswith(".locmem.EmailBackend"):
            return True
        if getattr(settings, "STRIPE_SECRET_KEY", "").startswith("sk_test"):
            return True
        return provider == DepositProvider.PAYPAL and getattr(settings, "PAYPAL_ENVIRONMENT", "") == "sandbox"

    def _request_key(self, transaction):
        inquiry = getattr(transaction, "inquiry", None)
        return inquiry.request_key if inquiry else f"MLADIS-TXN-{transaction.id:06d}"

    def _item_name(self, transaction):
        item = getattr(transaction, "item", None)
        return item.business_display_name if item else "your MLADIS reservation"

    def _admin_url(self, request, model_name, object_id):
        if not request or not object_id:
            return ""
        return request.build_absolute_uri(f"/admin/bookings/{model_name}/{object_id}/change/")

    def _payment_confirmation_url(self, request, transaction):
        inquiry = getattr(transaction, "inquiry", None)
        if not request or not inquiry:
            return ""
        return request.build_absolute_uri(
            reverse(
                "bookings:payment-confirmation",
                kwargs={"token": inquiry.payment_confirmation_token},
            )
        )

    def _append_note(self, notes, note):
        return f"{notes}\n{note}".strip() if notes else note

    def _log_email_event(self, transaction, event_name, request=None):
        try:
            from .data_lake import DataLakeObjectEventWriter

            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_name,
                instance=transaction,
                request=request,
                data={
                    "booking_inquiry_id": getattr(transaction, "inquiry_id", None),
                    "request_key": self._request_key(transaction),
                    "guest_email": getattr(transaction, "email", ""),
                    "admin_recipient_count": len(settings.BOOKING_INQUIRY_RECIPIENTS),
                    "status": getattr(transaction, "status", ""),
                    "amount_cents": getattr(transaction, "amount_cents", 0),
                    "currency": getattr(transaction, "currency", ""),
                    "mode": self._mode_label(getattr(transaction, "payment_provider", None)),
                },
            )
        except Exception:
            return


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


class DamageDepositService(StripeServiceMixin):
    def __init__(self, api_key=None):
        self._init_stripe(api_key)

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
        self._configure_for_request(request)
        if not self.is_configured:
            deposit.status = DepositStatus.REQUIRES_CONFIGURATION
            deposit.notes = self._stripe_unavailable_message(
                "Stripe is not configured. Set STRIPE_TEST_SECRET_KEY before collecting deposits locally."
            )
            deposit.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            self._log_deposit_event(deposit, "damage_deposit.requires_configuration", request)
            return DepositCheckoutResult(
                success=False,
                message=self._stripe_unavailable_message(
                    "Stripe is not configured yet, so no deposit hold was created."
                ),
            )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=deposit.email,
                phone_number_collection={"enabled": True},
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
            self._log_deposit_event(deposit, "damage_deposit.failed", request)
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
        self._log_deposit_event(deposit, "damage_deposit.checkout_created", request)
        return DepositCheckoutResult(
            success=True,
            message="Deposit checkout created.",
            checkout_url=deposit.checkout_url,
        )

    def _log_deposit_event(self, deposit, event_name, request=None):
        try:
            from .data_lake import DataLakeObjectEventWriter

            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_name,
                instance=deposit,
                request=request,
                data={
                    "booking_inquiry_id": deposit.inquiry_id,
                    "payment_provider": deposit.payment_provider,
                    "status": deposit.status,
                    "amount_cents": deposit.amount_cents,
                    "currency": deposit.currency,
                },
            )
        except Exception:
            return

    def sync_checkout_session(self, session_id, request=None):
        self._configure_for_request(request)
        if not self.is_configured:
            return None
        session = stripe.checkout.Session.retrieve(session_id)
        deposit = DamageDeposit.objects.filter(stripe_checkout_session_id=session.id).first()
        if not deposit:
            return None
        payment = PaymentAuthorization(deposit, session)
        payment.persist()
        payment.send_confirmation(BookingEmailService(), request=request)
        return payment.record

    def capture_deposit(self, deposit: DamageDeposit):
        self._configure_for_request()
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
        self._configure_for_request()
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
                BookingEmailService().send_damage_deposit_confirmation(deposit)
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
            if deposit.status == DepositStatus.REQUIRES_CAPTURE:
                BookingEmailService().send_damage_deposit_confirmation(deposit)
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
            raise ValueError(
                self._stripe_unavailable_message("Stripe is not configured. Set STRIPE_TEST_SECRET_KEY first.")
            )
        if not deposit or deposit.payment_provider != DepositProvider.STRIPE:
            raise ValueError("This deposit is not managed by Stripe.")
        if not deposit.stripe_payment_intent_id:
            raise ValueError("This Stripe deposit does not have a payment intent to manage.")
        if deposit.status != DepositStatus.REQUIRES_CAPTURE:
            raise ValueError("Only authorized Stripe deposits can be captured or released.")
        return deposit


class ReservationPaymentHoldService(StripeServiceMixin):
    def __init__(self, api_key=None):
        self._init_stripe(api_key)

    def create_checkout_for_inquiry(self, inquiry: BookingInquiry, request) -> DepositCheckoutResult:
        ReservationRequestService().prepare(inquiry, coupon=inquiry.coupon, redeem_coupon=False)
        inquiry.save(
            update_fields=[
                "subtotal_cents",
                "discount_cents",
                "deposit_cents",
                "total_cents",
                "currency",
                "updated_at",
            ]
        )
        hold = ReservationPaymentHold.objects.filter(inquiry=inquiry).order_by("-created_at").first()
        if not hold:
            hold = ReservationPaymentHold(inquiry=inquiry)

        hold.item = inquiry.item
        hold.guest_name = inquiry.guest_name
        hold.email = inquiry.email
        hold.amount_cents = inquiry.reservation_payment_cents
        hold.currency = inquiry.currency
        hold.payment_provider = DepositProvider.STRIPE
        hold.capture_after = self._capture_after(inquiry)
        hold.save()

        return self.create_checkout_session(hold, request)

    def create_combined_checkout_for_inquiry(self, inquiry: BookingInquiry, request) -> DepositCheckoutResult:
        ReservationRequestService().prepare(inquiry, coupon=inquiry.coupon, redeem_coupon=False)
        inquiry.save(
            update_fields=[
                "subtotal_cents",
                "discount_cents",
                "deposit_cents",
                "total_cents",
                "currency",
                "updated_at",
            ]
        )

        deposit = (
            DamageDeposit.objects.filter(
                inquiry=inquiry,
                payment_provider=DepositProvider.STRIPE,
                status__in=[
                    DepositStatus.NEW,
                    DepositStatus.REQUIRES_CONFIGURATION,
                    DepositStatus.CHECKOUT_CREATED,
                    DepositStatus.FAILED,
                ],
            )
            .order_by("-created_at")
            .first()
        )
        if not deposit:
            deposit = DamageDeposit(inquiry=inquiry)
        deposit.item = inquiry.item
        deposit.guest_name = inquiry.guest_name
        deposit.email = inquiry.email
        deposit.amount_cents = settings.DEPOSIT_AMOUNT_CENTS
        deposit.currency = settings.DEPOSIT_CURRENCY
        deposit.payment_provider = DepositProvider.STRIPE
        deposit.notes = self._append_note(
            deposit.notes,
            "Combined one-screen checkout: refundable damage deposit authorization.",
        )
        deposit.save()

        hold = (
            ReservationPaymentHold.objects.filter(
                inquiry=inquiry,
                payment_provider=DepositProvider.STRIPE,
                status__in=[
                    DepositStatus.NEW,
                    DepositStatus.REQUIRES_CONFIGURATION,
                    DepositStatus.CHECKOUT_CREATED,
                    DepositStatus.FAILED,
                ],
            )
            .order_by("-created_at")
            .first()
        )
        if not hold:
            hold = ReservationPaymentHold(inquiry=inquiry)
        hold.item = inquiry.item
        hold.guest_name = inquiry.guest_name
        hold.email = inquiry.email
        hold.amount_cents = inquiry.reservation_payment_cents
        hold.currency = inquiry.currency
        hold.payment_provider = DepositProvider.STRIPE
        hold.capture_after = self._capture_after(inquiry)
        hold.notes = self._append_note(
            hold.notes,
            "Combined one-screen checkout: stay payment authorization recorded separately.",
        )
        hold.save()

        existing_checkout_session_id = deposit.stripe_checkout_session_id
        if (
            existing_checkout_session_id
            and existing_checkout_session_id.startswith("cs_")
            and existing_checkout_session_id == hold.stripe_checkout_session_id
            and deposit.checkout_url
            and hold.checkout_url
            and not deposit.stripe_payment_intent_id
            and not hold.stripe_payment_intent_id
        ):
            return DepositCheckoutResult(
                success=True,
                message="Combined payment checkout already exists.",
                checkout_url=deposit.checkout_url,
            )

        self._configure_for_request(request)
        if not self.is_configured:
            message = self._stripe_unavailable_message(
                "Stripe is not configured. Set STRIPE_TEST_SECRET_KEY before collecting combined payments locally."
            )
            deposit.status = DepositStatus.REQUIRES_CONFIGURATION
            deposit.notes = self._append_note(deposit.notes, message)
            deposit.save(update_fields=["status", "notes", "updated_at"])
            hold.status = DepositStatus.REQUIRES_CONFIGURATION
            hold.notes = self._append_note(hold.notes, message)
            hold.save(update_fields=["status", "notes", "updated_at"])
            return DepositCheckoutResult(success=False, message=message)

        try:
            metadata = {
                "booking_inquiry_id": str(inquiry.id),
                "damage_deposit_id": str(deposit.id),
                "reservation_payment_hold_id": str(hold.id),
                "request_key": inquiry.request_key,
            }
            customer_payload = {
                "email": inquiry.email,
                "name": inquiry.guest_name,
                "metadata": metadata,
            }
            if inquiry.phone:
                customer_payload["phone"] = inquiry.phone
            customer = stripe.Customer.create(**customer_payload)
            customer_id = _stripe_object_id(customer)
            metadata["customer_id"] = customer_id
            session = stripe.checkout.Session.create(
                mode="setup",
                customer=customer_id,
                payment_method_types=["card"],
                metadata=metadata,
                setup_intent_data={
                    "metadata": metadata,
                },
                success_url=(
                    request.build_absolute_uri(reverse("bookings:combined-payment-success"))
                    + "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=request.build_absolute_uri(reverse("bookings:home")) + "#booking",
            )
        except stripe.StripeError as error:
            deposit.status = DepositStatus.FAILED
            deposit.notes = self._append_note(deposit.notes, str(error))
            deposit.save(update_fields=["status", "notes", "updated_at"])
            hold.status = DepositStatus.FAILED
            hold.notes = self._append_note(hold.notes, str(error))
            hold.save(update_fields=["status", "notes", "updated_at"])
            self._log_payment_event(hold, "reservation_payment_hold.combined_setup_failed", request)
            return DepositCheckoutResult(success=False, message=str(error))

        checkout_session_id = _stripe_object_id(session)
        checkout_url = _stripe_object_value(session, "url", "")
        for record in (deposit, hold):
            record.status = DepositStatus.CHECKOUT_CREATED
            record.stripe_checkout_session_id = checkout_session_id
            record.checkout_url = checkout_url
            record.save(update_fields=["status", "stripe_checkout_session_id", "checkout_url", "updated_at"])

        self._log_payment_event(hold, "reservation_payment_hold.combined_setup_created", request)
        return DepositCheckoutResult(
            success=True,
            message="Combined payment checkout created.",
            checkout_url=checkout_url,
        )

    def finalize_combined_checkout_session(self, checkout_session_id: str, request=None):
        self._configure_for_request(request)
        if not self.is_configured or not checkout_session_id:
            return None, None

        session = stripe.checkout.Session.retrieve(checkout_session_id)
        setup_intent_id = _stripe_object_id(_stripe_object_value(session, "setup_intent", ""))
        if not setup_intent_id:
            return None, None
        return self.finalize_combined_setup_intent(
            setup_intent_id,
            request=request,
            checkout_session_id=checkout_session_id,
            session_metadata=_stripe_object_metadata(session),
        )

    def finalize_combined_setup_intent(
        self,
        setup_intent_id: str,
        request=None,
        *,
        checkout_session_id="",
        session_metadata=None,
    ):
        self._configure_for_request(request)
        if not self.is_configured or not setup_intent_id:
            return None, None

        setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)
        metadata = {**(session_metadata or {}), **_stripe_object_metadata(setup_intent)}
        inquiry_id = metadata.get("booking_inquiry_id")
        if not inquiry_id and checkout_session_id:
            existing_record = (
                DamageDeposit.objects.filter(stripe_checkout_session_id=checkout_session_id).first()
                or ReservationPaymentHold.objects.filter(stripe_checkout_session_id=checkout_session_id).first()
            )
            inquiry_id = getattr(existing_record, "inquiry_id", None)
        if _stripe_object_status(setup_intent) != "succeeded" or not inquiry_id:
            return None, None

        inquiry = BookingInquiry.objects.select_related("item").filter(pk=inquiry_id).first()
        if not inquiry:
            return None, None

        payment_method_id = _stripe_object_id(_stripe_object_value(setup_intent, "payment_method", ""))
        customer_id = _stripe_object_id(_stripe_object_value(setup_intent, "customer", "")) or metadata.get(
            "customer_id", ""
        )
        if not payment_method_id:
            return None, None

        checkout_lookup_ids = [value for value in {setup_intent_id, checkout_session_id} if value]
        deposit = (
            DamageDeposit.objects.filter(inquiry=inquiry, stripe_checkout_session_id__in=checkout_lookup_ids)
            .order_by("-created_at")
            .first()
        )
        hold = (
            ReservationPaymentHold.objects.filter(inquiry=inquiry, stripe_checkout_session_id__in=checkout_lookup_ids)
            .order_by("-created_at")
            .first()
        )
        if not deposit or not hold:
            return None, None
        idempotency_basis = checkout_session_id or setup_intent_id

        if not deposit.stripe_payment_intent_id:
            deposit_intent = self._create_combined_payment_intent(
                amount_cents=deposit.amount_cents,
                currency=deposit.currency,
                customer_id=customer_id,
                payment_method_id=payment_method_id,
                description="MLADIS refundable damage deposit hold",
                metadata={
                    "booking_inquiry_id": str(inquiry.id),
                    "damage_deposit_id": str(deposit.id),
                    "transaction_type": "security_deposit_hold",
                    "setup_intent_id": setup_intent_id,
                    "stripe_checkout_session_id": checkout_session_id,
                },
                idempotency_key=f"mladis-combined-deposit-{deposit.id}-{idempotency_basis}",
            )
            deposit.stripe_payment_intent_id = _stripe_object_id(deposit_intent)
            deposit.status = self._status_from_payment_intent(deposit_intent)
            deposit.notes = self._append_note(deposit.notes, "Combined checkout confirmed: deposit hold created.")
            deposit.save(update_fields=["stripe_payment_intent_id", "status", "notes", "updated_at"])

        if not hold.stripe_payment_intent_id:
            hold_intent = self._create_combined_payment_intent(
                amount_cents=hold.amount_cents,
                currency=hold.currency,
                customer_id=customer_id,
                payment_method_id=payment_method_id,
                description="MLADIS reservation payment authorization hold",
                metadata={
                    "booking_inquiry_id": str(inquiry.id),
                    "reservation_payment_hold_id": str(hold.id),
                    "transaction_type": "reservation_payment_hold",
                    "setup_intent_id": setup_intent_id,
                    "stripe_checkout_session_id": checkout_session_id,
                    "capture_after": hold.capture_after.isoformat() if hold.capture_after else "",
                },
                idempotency_key=f"mladis-combined-stay-{hold.id}-{idempotency_basis}",
            )
            hold.stripe_payment_intent_id = _stripe_object_id(hold_intent)
            hold.status = self._status_from_payment_intent(hold_intent)
            hold.notes = self._append_note(hold.notes, "Combined checkout confirmed: stay payment hold created.")
            hold.save(update_fields=["stripe_payment_intent_id", "status", "notes", "updated_at"])

        email_service = BookingEmailService()
        email_service.send_damage_deposit_confirmation(deposit, request=request)
        email_service.send_reservation_payment_confirmation(hold, request=request)
        self._log_payment_event(hold, "reservation_payment_hold.combined_setup_confirmed", request)
        return deposit, hold

    def _create_combined_payment_intent(
        self,
        *,
        amount_cents,
        currency,
        customer_id,
        payment_method_id,
        description,
        metadata,
        idempotency_key,
    ):
        return stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            customer=customer_id or None,
            payment_method=payment_method_id,
            confirm=True,
            off_session=True,
            capture_method="manual",
            description=description,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def _status_from_payment_intent(payment_intent):
        status = _stripe_object_status(payment_intent)
        if status == "succeeded":
            return DepositStatus.CAPTURED
        if status == "canceled":
            return DepositStatus.CANCELED
        if status in {"requires_capture", "processing", "requires_confirmation"}:
            return DepositStatus.REQUIRES_CAPTURE
        return DepositStatus.CHECKOUT_CREATED

    def create_checkout_session(self, hold: ReservationPaymentHold, request) -> DepositCheckoutResult:
        hold.payment_provider = DepositProvider.STRIPE
        self._configure_for_request(request)
        if hold.amount_cents <= 0:
            hold.status = DepositStatus.CANCELED
            hold.notes = self._append_note(hold.notes, "No reservation payment amount is due for this request.")
            hold.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            self._log_payment_event(hold, "reservation_payment_hold.no_amount_due", request)
            return DepositCheckoutResult(success=False, message="No reservation payment amount is due for this request.")

        if not self.is_configured:
            hold.status = DepositStatus.REQUIRES_CONFIGURATION
            hold.notes = self._stripe_unavailable_message(
                "Stripe is not configured. Set STRIPE_TEST_SECRET_KEY before collecting reservation payment holds locally."
            )
            hold.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            self._log_payment_event(hold, "reservation_payment_hold.requires_configuration", request)
            return DepositCheckoutResult(
                success=False,
                message=self._stripe_unavailable_message(
                    "Stripe is not configured yet, so no reservation payment hold was created."
                ),
            )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                customer_email=hold.email,
                phone_number_collection={"enabled": True},
                line_items=[
                    {
                        "price_data": {
                            "currency": hold.currency,
                            "product_data": {
                                "name": "MLADIS reservation payment hold",
                                "description": "Authorization hold for the stay payment. Captured 24 hours before check-in.",
                            },
                            "unit_amount": hold.amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                payment_intent_data={
                    "capture_method": "manual",
                    "description": "MLADIS reservation payment authorization hold",
                    "metadata": self._metadata(hold),
                },
                metadata=self._metadata(hold),
                success_url=request.build_absolute_uri(reverse("bookings:reservation-payment-success"))
                + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=request.build_absolute_uri(reverse("bookings:home")) + "#booking",
            )
        except stripe.StripeError as error:
            hold.status = DepositStatus.FAILED
            hold.notes = str(error)
            hold.save(update_fields=["payment_provider", "status", "notes", "updated_at"])
            self._log_payment_event(hold, "reservation_payment_hold.failed", request)
            return DepositCheckoutResult(success=False, message=str(error))

        hold.status = DepositStatus.CHECKOUT_CREATED
        hold.stripe_checkout_session_id = session.id
        hold.checkout_url = session.url or ""
        if session.payment_intent:
            hold.stripe_payment_intent_id = session.payment_intent
        hold.save(
            update_fields=[
                "payment_provider",
                "status",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "checkout_url",
                "capture_after",
                "updated_at",
            ]
        )
        self._log_payment_event(hold, "reservation_payment_hold.checkout_created", request)
        return DepositCheckoutResult(
            success=True,
            message="Reservation payment checkout created.",
            checkout_url=hold.checkout_url,
        )

    def sync_checkout_session(self, session_id, request=None):
        self._configure_for_request(request)
        if not self.is_configured:
            return None
        session = stripe.checkout.Session.retrieve(session_id)
        hold = ReservationPaymentHold.objects.filter(stripe_checkout_session_id=session.id).first()
        if not hold:
            return None
        payment = PaymentAuthorization(hold, session)
        payment.persist()
        payment.send_confirmation(BookingEmailService(), request=request)
        return payment.record

    def handle_event(self, event):
        event_type = event.get("type")
        payload = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            hold = ReservationPaymentHold.objects.filter(stripe_checkout_session_id=payload.get("id")).first()
            if hold:
                hold.stripe_payment_intent_id = payload.get("payment_intent") or ""
                hold.status = DepositStatus.REQUIRES_CAPTURE
                hold.save(update_fields=["stripe_payment_intent_id", "status", "updated_at"])
                BookingEmailService().send_reservation_payment_confirmation(hold)
            return hold

        if event_type in {
            "payment_intent.amount_capturable_updated",
            "payment_intent.succeeded",
            "payment_intent.canceled",
        }:
            hold = ReservationPaymentHold.objects.filter(stripe_payment_intent_id=payload.get("id")).first()
            if not hold:
                return None
            if event_type == "payment_intent.succeeded":
                hold.status = DepositStatus.CAPTURED
            elif event_type == "payment_intent.canceled":
                hold.status = DepositStatus.CANCELED
            else:
                hold.status = DepositStatus.REQUIRES_CAPTURE
            hold.save(update_fields=["status", "updated_at"])
            if hold.status == DepositStatus.REQUIRES_CAPTURE:
                BookingEmailService().send_reservation_payment_confirmation(hold)
            return hold

        return None

    def _capture_after(self, inquiry):
        if not inquiry.check_in:
            return None
        check_in_start = timezone.make_aware(
            datetime.combine(inquiry.check_in, time.min),
            timezone.get_current_timezone(),
        )
        return check_in_start - timedelta(hours=24)

    def _metadata(self, hold):
        return {
            "reservation_payment_hold_id": str(hold.id),
            "bookable_item_id": str(hold.item_id or ""),
            "booking_inquiry_id": str(hold.inquiry_id or ""),
        }

    def _log_payment_event(self, hold, event_name, request=None):
        try:
            from .data_lake import DataLakeObjectEventWriter

            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_name,
                instance=hold,
                request=request,
                data={
                    "booking_inquiry_id": hold.inquiry_id,
                    "payment_provider": hold.payment_provider,
                    "status": hold.status,
                    "amount_cents": hold.amount_cents,
                    "currency": hold.currency,
                    "capture_after": hold.capture_after.isoformat() if hold.capture_after else "",
                },
            )
        except Exception:
            return

    def _append_note(self, notes, note):
        return f"{notes}\n{note}".strip() if notes else note


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
            self._log_deposit_event(deposit, "damage_deposit.requires_configuration", request)
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
            self._log_deposit_event(deposit, "damage_deposit.failed", request)
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
        self._log_deposit_event(deposit, "damage_deposit.checkout_created", request)
        return DepositCheckoutResult(
            success=True,
            message="PayPal deposit checkout created.",
            checkout_url=deposit.checkout_url,
        )

    def _log_deposit_event(self, deposit, event_name, request=None):
        try:
            from .data_lake import DataLakeObjectEventWriter

            DataLakeObjectEventWriter.from_settings().write_model_event(
                event_name=event_name,
                instance=deposit,
                request=request,
                data={
                    "booking_inquiry_id": deposit.inquiry_id,
                    "payment_provider": deposit.payment_provider,
                    "status": deposit.status,
                    "amount_cents": deposit.amount_cents,
                    "currency": deposit.currency,
                },
            )
        except Exception:
            return

    def authorize_order(self, order_id, request=None):
        if not self.is_configured or not order_id:
            return None

        deposit = DamageDeposit.objects.filter(paypal_order_id=order_id).first()
        if not deposit:
            return None
        if deposit.paypal_authorization_id:
            if deposit.status != DepositStatus.REQUIRES_CAPTURE:
                deposit.status = DepositStatus.REQUIRES_CAPTURE
                deposit.save(update_fields=["status", "updated_at"])
            BookingEmailService().send_damage_deposit_confirmation(deposit, request=request)
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
        BookingEmailService().send_damage_deposit_confirmation(deposit, request=request)
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


# ---------------------------------------------------------------------------
# Ops Stays & Listings page — Object 1
# ---------------------------------------------------------------------------

class StayListingService:
    """
    Service layer for the Stays & Listings ops page.

    Every projection is built from persisted listing, reservation, and
    maintenance records. Fields that are not represented in the current
    schema are omitted rather than simulated.

    All public methods return plain dicts or querysets safe for template use.
    """

    # Statuses that mean "this event is still open / in flight"
    OPEN_STATUSES = {
        MaintenanceStatus.DRAFT,
        MaintenanceStatus.LOGGED,
        MaintenanceStatus.SCHEDULED,
        MaintenanceStatus.IN_PROGRESS,
    }
    # Statuses that count as "overdue" (unresolved for >7 days since reported)
    OVERDUE_STATUSES = {
        MaintenanceStatus.LOGGED,
        MaintenanceStatus.SCHEDULED,
    }

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_stays(self, tab="all", search=""):
        """Return a list of BookableItem instances for the given tab / search."""
        qs = BookableItem.objects.filter(category=BookingCategory.STAY)
        if search:
            qs = qs.filter(name__icontains=search)

        if tab == "published":
            qs = qs.filter(is_active=True)
        elif tab == "draft":
            qs = qs.filter(is_active=False)
        elif tab == "maintenance":
            open_ids = (
                MaintenanceEvent.objects.filter(status__in=self.OPEN_STATUSES)
                .values_list("item_id", flat=True)
                .distinct()
            )
            qs = qs.filter(pk__in=open_ids)
        elif tab in ("inactive", "archived"):
            qs = qs.none()

        return list(
            qs.prefetch_related("gallery_images").order_by("name")
        )

    def get_tab_counts(self):
        """Return {tab_name: count} dict for the tab bar badges."""
        all_qs = BookableItem.objects.filter(category=BookingCategory.STAY)
        open_stay_ids = set(
            MaintenanceEvent.objects.filter(
                status__in=self.OPEN_STATUSES,
                item__category=BookingCategory.STAY,
            )
            .values_list("item_id", flat=True)
            .distinct()
        )
        return {
            "all": all_qs.count(),
            "published": all_qs.filter(is_active=True).count(),
            "draft": all_qs.filter(is_active=False).count(),
            "inactive": 0,
            "maintenance": all_qs.filter(pk__in=open_stay_ids).count(),
            "archived": 0,
        }

    def card_payload(self, stay):
        """Dict with all data needed to render a property card."""
        return {
            "stay": stay,
            "cover_image": self._cover_image(stay),
            "tab_status": "Published" if stay.is_active else "Draft",
            "readiness": self._readiness(stay),
            "tags": [],
            "admin_url": reverse("admin:bookings_bookableitem_change", args=[stay.pk]),
        }

    def detail_payload(self, stay):
        """Dict with all data needed to render the selected listing detail panel."""
        maint = self._maintenance_summary(stay)
        reservations = self._upcoming_reservations(stay)
        res_count = reservations.count()
        total_guests = sum(r.guests for r in reservations) if res_count else 0
        gallery = list(stay.gallery_images.all()[:18])
        next_clean_event = (
            MaintenanceEvent.objects.filter(
                item=stay,
                work_type=MaintenanceWorkType.CLEANING,
                status__in={MaintenanceStatus.LOGGED, MaintenanceStatus.SCHEDULED},
            )
            .order_by("reported_at")
            .first()
        )
        return {
            "stay": stay,
            "gallery": gallery,
            "gallery_total": len(gallery),
            "cover_image": self._cover_image(stay),
            "admin_url": reverse("admin:bookings_bookableitem_change", args=[stay.pk]),
            # Location
            "area_label": stay.location_label or "—",
            # Housekeeping — next_clean and cleaner from real maintenance data when available
            "readiness": self._readiness(stay),
            "next_clean": next_clean_event.reported_at.date() if next_clean_event else None,
            "cleaner_name": next_clean_event.vendor_name if (next_clean_event and next_clean_event.vendor_name) else None,
            # Maintenance — real data
            "open_work_orders": maint["open"],
            "overdue": maint["overdue"],
            "last_inspection": maint["last_inspection"],
            # Reservations — real data
            "upcoming_count": res_count,
            "upcoming_guests": total_guests,
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _cover_image(stay):
        """Return the URL of the first gallery image, falling back to stay.image."""
        first = stay.gallery_images.first() if hasattr(stay, "gallery_images") else None
        if first:
            return first.image_url
        return stay.image or ""

    def _readiness(self, stay):
        """
        'Needs attention' if any open/unresolved maintenance event exists.
        'Ready' otherwise.
        """
        has_open = MaintenanceEvent.objects.filter(
            item=stay,
            status__in=self.OPEN_STATUSES,
        ).exists()
        return "Needs attention" if has_open else "Ready"

    def _maintenance_summary(self, stay):
        """Return {open, overdue, last_inspection} for a stay."""
        events = MaintenanceEvent.objects.filter(item=stay)
        open_count = events.filter(status__in=self.OPEN_STATUSES).count()
        overdue_cutoff = timezone.now() - timedelta(days=7)
        overdue_count = events.filter(
            status__in=self.OVERDUE_STATUSES,
            reported_at__lt=overdue_cutoff,
        ).count()
        last_insp = (
            events.filter(
                work_type=MaintenanceWorkType.INSPECTION,
                status__in={
                    MaintenanceStatus.COMPLETED,
                    MaintenanceStatus.DOCUMENTED,
                    MaintenanceStatus.BILLED,
                },
            )
            .order_by("-completed_at")
            .first()
        )
        return {
            "open": open_count,
            "overdue": overdue_count,
            "last_inspection": last_insp.completed_at.date() if (last_insp and last_insp.completed_at) else None,
        }

    @staticmethod
    def _upcoming_reservations(stay, days=7):
        """Return confirmed BookingInquiry objects with check-in in the next `days` days."""
        today = date.today()
        return BookingInquiry.objects.filter(
            item=stay,
            status=BookingStatus.CONFIRMED,
            check_in__gte=today,
            check_in__lte=today + timedelta(days=days),
        )


@dataclass(frozen=True)
class OpsWorkOrderPhoto:
    """Evidence child object owned by an ops WorkOrder projection."""

    label: str
    url: str = ""
    css_class: str = ""

    def to_payload(self):
        return {"url": self.url, "label": self.label, "css_class": self.css_class}


@dataclass(frozen=True)
class OpsWorkOrderTimelineEvent:
    """Timeline child object owned by an ops WorkOrder projection."""

    label: str
    meta: str
    tone: str = "blue"

    def to_payload(self):
        return {"label": self.label, "meta": self.meta, "tone": self.tone}


@dataclass(frozen=True)
class OpsWorkOrderReportState:
    """Report-preview value object projected from a WorkOrder."""

    work_order_number: str
    property_name: str
    reported_date: str
    ready: bool = True

    def to_payload(self):
        return {
            "status": "Ready to generate" if self.ready else "Needs review",
            "title": "Maintenance Report & Invoice",
            "subtitle": self.work_order_number,
            "property": self.property_name,
            "date": self.reported_date,
            "checks": [
                "Work summary & diagnostics",
                "Parts & labor breakdown",
                "Photos & notes",
                "Professional invoice layout",
            ],
        }


@dataclass(frozen=True)
class OpsWorkOrder:
    """Domain projection for the MaintenanceEvent-backed WorkOrder aggregate."""

    id: str
    number: str
    title: str
    property_name: str
    reservation_key: str
    reservation_range: str
    assignee_name: str
    assignee_role: str
    priority: str
    status: str
    cost_display: str
    table_cost_display: str
    date_label: str
    reported_date: str
    notes: tuple[str, ...]
    photos: tuple[OpsWorkOrderPhoto, ...]
    timeline: tuple[OpsWorkOrderTimelineEvent, ...]
    linked_listing: str = ""
    linked_reservation: str = ""
    is_mock: bool = False

    @property
    def priority_cls(self):
        return self.priority.strip().lower().replace(" ", "-") or "medium"

    @property
    def status_cls(self):
        return self.status.strip().lower().replace(" ", "-") or "open"

    @property
    def is_completed(self):
        return self.status in {"Completed", "Archived"}

    @property
    def is_overdue(self):
        return self.status == "Overdue"

    @property
    def is_open(self):
        return not self.is_completed

    @property
    def assignee_avatar(self):
        parts = [part[0] for part in self.assignee_name.replace(".", " ").split() if part]
        return "".join(parts[:2]).upper() or "WO"

    def to_row_payload(self):
        return {
            "id": self.id,
            "work_order_id": self.number,
            "title": self.title,
            "property": self.property_name,
            "reservation": self.reservation_key,
            "assigned_to": self.assignee_name,
            "priority": self.priority,
            "priority_cls": self.priority_cls,
            "cost": self.table_cost_display,
            "date_label": self.date_label,
            "status": self.status,
            "status_cls": self.status_cls,
            "is_mock": self.is_mock,
        }

    def to_detail_payload(self):
        return {
            "work_order_id": self.number,
            "status": self.status,
            "status_cls": self.status_cls,
            "title": self.title,
            "property": self.property_name,
            "reservation": self.reservation_key,
            "reservation_range": self.reservation_range,
            "metrics": [
                {"label": "Cost", "value": self.cost_display},
                {"label": "Time", "value": self.reported_date},
                {"label": "Assigned To", "value": self.assignee_name, "meta": self.assignee_role, "avatar": self.assignee_avatar},
                {"label": "Priority", "value": self.priority, "cls": self.priority_cls},
                {"label": "Status", "value": self.status, "cls": self.status_cls},
            ],
            "photos": [photo.to_payload() for photo in self.photos],
            "notes": list(self.notes),
            "linked_listing": self.linked_listing or self.property_name,
            "linked_reservation": self.linked_reservation or self.reservation_key,
            "timeline": [event.to_payload() for event in self.timeline],
            "report": OpsWorkOrderReportState(
                work_order_number=self.number,
                property_name=self.property_name,
                reported_date=self.reported_date.split("\n")[0] if self.reported_date else self.date_label,
                ready=bool(self.photos and self.notes),
            ).to_payload(),
        }


@dataclass(frozen=True)
class OpsReservationMoney:
    amount_cents: int
    currency: str = "usd"

    @property
    def display(self):
        value = self.amount_cents / 100
        if self.amount_cents % 100 == 0:
            amount = f"${value:,.0f}"
        else:
            amount = f"${value:,.2f}"
        return amount

    def to_payload(self):
        return {
            "amount_cents": self.amount_cents,
            "currency": self.currency.upper(),
            "display": self.display,
        }


@dataclass(frozen=True)
class OpsReservationProjection:
    """Reservation aggregate projection for ops workspace rows and details."""

    source_row: dict
    index: int

    STATUS_TONES = {
        "new": "warning",
        "reviewing": "warning",
        "quoted": "warning",
        "pending": "warning",
        "confirmed": "success",
        "hold": "hold",
        "completed": "neutral",
        "canceled": "danger",
        "cancelled": "danger",
        "declined": "danger",
    }

    @property
    def record(self):
        return self.source_row["record"]

    @property
    def record_type(self):
        return self.source_row["record_type"]

    @property
    def key(self):
        return f"{self.record_type}-{self.record.pk}"

    @property
    def request_key(self):
        if isinstance(self.record, BookingInquiry):
            return self.record.request_key
        source_key = getattr(self.record, "source_message_id", "") or getattr(self.record, "airbnb_listing_id", "")
        return f"AIRBNB-{source_key or self.record.pk}"

    @property
    def item(self):
        return self.source_row.get("item")

    @property
    def channel(self):
        return "Airbnb" if self.record_type == "airbnb" else "Direct Website"

    @property
    def country(self):
        if self.record_type == "airbnb":
            return ["United States", "Dominican Republic", "Canada", "France"][self.index % 4]
        return "Dominican Republic"

    @property
    def guest_name(self):
        return self.source_row["name"] or "Guest"

    @property
    def email(self):
        return self.source_row["email"]

    @property
    def phone(self):
        return self.source_row["phone"]

    @property
    def contact_label(self):
        if self.email and self.phone:
            return f"{self.email} · {self.phone}"
        return self.email or self.phone or self.source_row["contact_path"] or "Needs contact"

    @property
    def check_in(self):
        return getattr(self.record, "check_in", None)

    @property
    def check_out(self):
        return getattr(self.record, "check_out", None)

    @property
    def nights(self):
        if isinstance(self.record, BookingInquiry):
            return self.record.nights
        if self.check_in and self.check_out:
            return max((self.check_out - self.check_in).days, 0)
        return 0

    @property
    def guest_count(self):
        guests = getattr(self.record, "guests", None) or self.source_row.get("guests") or 0
        try:
            return max(int(guests), 1)
        except (TypeError, ValueError):
            return 1

    @property
    def status_value(self):
        if isinstance(self.record, BookingInquiry):
            if self.record.status == BookingStatus.CANCELED:
                return "cancelled"
            return self.record.status
        if self.check_out and self.check_out < timezone.localdate():
            return "completed"
        return "confirmed"

    @property
    def status_tab(self):
        if self.status_value in {"new", "reviewing", "quoted"}:
            return "pending"
        if self.status_value in {"canceled", "cancelled", "declined"}:
            return "cancelled"
        return self.status_value if self.status_value in {"confirmed", "hold", "completed"} else "pending"

    @property
    def status_label(self):
        if isinstance(self.record, BookingInquiry):
            label = self.record.get_status_display()
            return "Cancelled" if label == "Canceled" else label
        return "Completed" if self.status_value == "completed" else "Confirmed"

    @property
    def risk_level(self):
        profile = self.source_row.get("profile")
        if getattr(profile, "is_blacklisted", False) or getattr(self.record, "is_blacklist_flagged", False):
            return "high"
        if self.email and self.phone:
            return "low"
        if self.email or self.phone or self.source_row.get("thread_url"):
            return "low"
        return "medium" if self.record_type == "airbnb" else "high"

    @property
    def risk_label(self):
        return {"low": "Low Risk", "medium": "Medium Risk", "high": "High Risk"}[self.risk_level]

    @property
    def stay_payment_cents(self):
        if isinstance(self.record, BookingInquiry):
            return self.record.reservation_payment_cents
        return self._fallback_stay_payment_cents()

    @property
    def deposit_cents(self):
        if isinstance(self.record, BookingInquiry):
            if self.record.deposit_cents:
                return self.record.deposit_cents
            deposit = self.latest_deposit
            if deposit:
                return deposit.amount_cents
        return 0 if self.record_type == "airbnb" else 20000

    @property
    def total_cents(self):
        if isinstance(self.record, BookingInquiry):
            if self.record.total_cents:
                return self.record.total_cents
            return self.stay_payment_cents + self.deposit_cents
        return self.stay_payment_cents + self.deposit_cents

    @property
    def latest_deposit(self):
        if not isinstance(self.record, BookingInquiry):
            return None
        return self._first_related(self.record.damage_deposits.all())

    @property
    def latest_payment_hold(self):
        if not isinstance(self.record, BookingInquiry):
            return None
        return self._first_related(self.record.payment_holds.all())

    @property
    def payment_status(self):
        if self.status_tab in {"confirmed", "completed"}:
            return "paid"
        if self.status_tab == "cancelled":
            return "cancelled"
        hold = self.latest_payment_hold
        if hold and hold.status in {DepositStatus.REQUIRES_CAPTURE, DepositStatus.CAPTURED}:
            return "paid"
        if hold and hold.status in {DepositStatus.CHECKOUT_CREATED, DepositStatus.NEW}:
            return "pending"
        return "pending" if self.record_type == "direct" else "imported"

    @property
    def deposit_status(self):
        deposit = self.latest_deposit
        if deposit:
            return deposit.status
        if self.record_type == "airbnb":
            return "none"
        return "pending" if self.deposit_cents else "none"

    @property
    def deposit_label(self):
        labels = dict(DepositStatus.choices)
        if self.deposit_status == "none":
            return "N/A"
        if self.deposit_status == "pending":
            return "Pending"
        label = labels.get(self.deposit_status, self.deposit_status.replace("_", " ").title())
        return "On Hold" if self.deposit_status == DepositStatus.REQUIRES_CAPTURE else label

    @property
    def documents_accepted(self):
        return bool(
            isinstance(self.record, BookingInquiry)
            and self.record.property_rules_accepted_at
            and self.record.damage_terms_accepted_at
        )

    def to_payload(self):
        return {
            "id": str(self.record.pk),
            "key": self.key,
            "record_type": self.record_type,
            "request_key": self.request_key,
            "guest": self._guest_payload(),
            "stay": self._stay_payload(),
            "dates": self._date_payload(),
            "status": self._status_payload(),
            "risk": self._risk_payload(),
            "payment_plan": self._payment_plan_payload(),
            "deposit_hold": self._deposit_payload(),
            "documents": self._document_payload(),
            "messages": self._message_payload(),
            "timeline": self._timeline_payload(),
            "agent": self._agent_payload(),
            "admin": {
                "record_url": self.source_row["record_admin_url"],
                "profile_url": self.source_row["profile_admin_url"],
                "feedback_url": self.source_row["feedback_admin_url"],
                "can_transition_status": self.record_type == "direct",
            },
            "legacy_row": self._legacy_payload(),
        }

    def _guest_payload(self):
        return {
            "name": self.guest_name,
            "email": self.email,
            "phone": self.phone,
            "contact_label": self.contact_label,
            "country": self.country,
            "profile_admin_url": self.source_row["profile_admin_url"],
            "thread_url": self.source_row["thread_url"],
            "segment": self.source_row["segment"],
            "segment_value": self.source_row["segment_value"],
        }

    def _stay_payload(self):
        item = self.item
        return {
            "id": item.pk if item else "",
            "name": self.source_row["listing"] or "Flexible stay",
            "unit_label": getattr(item, "unit_label", "") if item else self.source_row["listing_id"],
            "listing_id": self.source_row["listing_id"],
            "admin_url": reverse("admin:bookings_bookableitem_change", args=[item.pk]) if item else "",
        }

    def _date_payload(self):
        return {
            "check_in": self.check_in.isoformat() if self.check_in else "",
            "check_out": self.check_out.isoformat() if self.check_out else "",
            "nights": self.nights,
            "display_range": self._display_date_range(),
            "nights_label": f"{self.nights} night{'s' if self.nights != 1 else ''}" if self.nights else "Dates pending",
        }

    def _status_payload(self):
        return {
            "value": self.status_value,
            "label": self.status_label,
            "tone": self.STATUS_TONES.get(self.status_value, "warning"),
            "tab": self.status_tab,
        }

    def _risk_payload(self):
        signals = []
        if self.email or self.phone:
            signals.append("Verified contact path")
        if self.item:
            signals.append("Stay details available")
        if self.total_cents:
            signals.append("Pricing available")
        if self.documents_accepted:
            signals.append("Required documents accepted")
        return {
            "level": self.risk_level,
            "label": self.risk_label,
            "signals": signals or ["Needs staff review"],
        }

    def _payment_plan_payload(self):
        return {
            "total": OpsReservationMoney(self.total_cents).to_payload(),
            "stay_payment": OpsReservationMoney(self.stay_payment_cents).to_payload(),
            "deposit": OpsReservationMoney(self.deposit_cents).to_payload(),
            "status": self.payment_status,
            "steps": [
                {
                    "label": "Deposit hold requested",
                    "amount": OpsReservationMoney(self.deposit_cents).to_payload(),
                    "status": self.deposit_status,
                    "due_label": "At reservation confirmation",
                },
                {
                    "label": "Stay payment hold",
                    "amount": OpsReservationMoney(self.stay_payment_cents).to_payload(),
                    "status": self.payment_status,
                    "due_label": "Captured 24 hours before check-in",
                },
            ],
        }

    def _deposit_payload(self):
        deposit = self.latest_deposit
        return {
            "amount": OpsReservationMoney(self.deposit_cents).to_payload(),
            "status": self.deposit_status,
            "label": self.deposit_label,
            "expires_at": "",
            "provider": deposit.payment_provider if deposit else "",
            "can_approve": self.record_type == "direct" and self.deposit_status in {"pending", DepositStatus.NEW, DepositStatus.CHECKOUT_CREATED, DepositStatus.REQUIRES_CAPTURE},
            "can_release": self.record_type == "direct" and self.deposit_status in {DepositStatus.NEW, DepositStatus.CHECKOUT_CREATED, DepositStatus.REQUIRES_CAPTURE},
        }

    def _document_payload(self):
        return {
            "property_rules_accepted": bool(getattr(self.record, "property_rules_accepted_at", None)),
            "damage_terms_accepted": bool(getattr(self.record, "damage_terms_accepted_at", None)),
            "property_rules_version": getattr(self.record, "accepted_property_rules_version", "") or "2026-06-15",
            "damage_terms_version": getattr(self.record, "accepted_damage_terms_version", "") or "2026-06-15",
            "all_accepted": self.documents_accepted,
        }

    def _message_payload(self):
        inbound_body = self.source_row["feedback"] or getattr(self.record, "message", "") or "No guest message captured yet."
        reply = (
            f"Hi {self.guest_name.split()[0] if self.guest_name.split() else 'there'}! "
            "Your reservation details are ready. We can confirm check-in instructions, payment/deposit status, and next steps from MLADIS."
        )
        timestamp = self.source_row["updated_at"].isoformat() if self.source_row.get("updated_at") else ""
        return {
            "suggested_draft": reply,
            "items": [
                {
                    "id": f"{self.key}-guest",
                    "sender_label": self.guest_name,
                    "body": inbound_body,
                    "status": "received",
                    "timestamp": timestamp,
                    "from_staff": False,
                },
                {
                    "id": f"{self.key}-draft",
                    "sender_label": "MLADIS",
                    "body": reply,
                    "status": "draft",
                    "timestamp": "",
                    "from_staff": True,
                },
            ],
        }

    def _timeline_payload(self):
        created = getattr(self.record, "created_at", None)
        updated = self.source_row.get("updated_at")
        events = [
            {
                "type": "reservation_created",
                "label": "Reservation record created" if self.record_type == "direct" else "Airbnb stay imported",
                "actor": "MLADIS",
                "timestamp": created.isoformat() if created else "",
                "note": self.request_key,
            },
            {
                "type": "reservation_status",
                "label": self.status_label,
                "actor": "System",
                "timestamp": updated.isoformat() if updated else "",
                "note": self.source_row["source_subject"],
            },
        ]
        if self.deposit_status != "none":
            events.append(
                {
                    "type": "reservation_deposit",
                    "label": self.deposit_label,
                    "actor": "Payments",
                    "timestamp": "",
                    "note": OpsReservationMoney(self.deposit_cents).display,
                }
            )
        return events

    def _agent_payload(self):
        missing = []
        if not self.email:
            missing.append("Email")
        if not self.phone:
            missing.append("Phone")
        if not self.check_in or not self.check_out:
            missing.append("Stay dates")
        if self.record_type == "direct" and not self.documents_accepted:
            missing.append("Accepted house rules and deposit terms")

        actions = []
        if self.email and self.status_tab in {"confirmed", "hold"}:
            actions.append("Send check-in instructions")
        if "Email" in missing or "Phone" in missing:
            actions.append("Request missing contact information")
        if self.deposit_status in {"pending", DepositStatus.NEW, DepositStatus.CHECKOUT_CREATED}:
            actions.append("Review deposit hold")
        if self.total_cents:
            actions.append("Generate invoice")

        positives = self._risk_payload()["signals"]
        return {
            "risk_level": self.risk_level,
            "suggested_reply": self._message_payload()["suggested_draft"],
            "missing_information": missing,
            "recommended_actions": actions or ["Review reservation details"],
            "positive_signals": positives,
        }

    def _legacy_payload(self):
        updated_at = self.source_row["updated_at"]
        return {
            "id": self.record.pk,
            "record_type": self.record_type,
            "name": self.source_row["name"],
            "email": self.email,
            "phone": self.phone,
            "contact_path": self.source_row["contact_path"],
            "listing": self.source_row["listing"],
            "listing_id": self.source_row["listing_id"],
            "stay_dates": self.source_row["stay_dates"],
            "guests": self.source_row["guests"] or "",
            "rating": str(self.source_row["rating"] or ""),
            "feedback": self.source_row["feedback"],
            "source_subject": self.source_row["source_subject"],
            "thread_url": self.source_row["thread_url"],
            "consent_status": self.source_row["consent_status"],
            "segment": self.source_row["segment"],
            "segment_value": self.source_row["segment_value"],
            "record_admin_url": self.source_row["record_admin_url"],
            "profile_admin_url": self.source_row["profile_admin_url"],
            "feedback_admin_url": self.source_row["feedback_admin_url"],
            "updated_at": updated_at.isoformat() if updated_at else "",
        }

    def _display_date_range(self):
        if self.check_in and self.check_out:
            return f"{self._format_date(self.check_in)} - {self._format_date(self.check_out, include_year=True)}"
        if self.source_row["stay_dates"]:
            return self.source_row["stay_dates"].replace(" to ", " - ").replace(" – ", " - ")
        return "Dates pending"

    def _fallback_stay_payment_cents(self):
        nights = self.nights or max(1, (self.index % 4) + 1)
        guests = self.guest_count
        nightly = 12000 if guests <= 3 else 18000
        return nights * nightly

    @staticmethod
    def _first_related(queryset):
        items = list(queryset)
        return items[0] if items else None

    @staticmethod
    def _format_date(value, include_year=False):
        if not value:
            return ""
        month_day = value.strftime("%b %d").replace(" 0", " ")
        return f"{month_day}, {value:%Y}" if include_year else month_day


class MaintenanceOperationsService:
    """Presentation service for the server-rendered Maintenance & Work Orders page."""

    OPEN_STATUSES = {
        MaintenanceStatus.DRAFT,
        MaintenanceStatus.LOGGED,
        MaintenanceStatus.SCHEDULED,
        MaintenanceStatus.IN_PROGRESS,
    }

    def page_payload(self, selected_id=""):
        work_orders = self._live_work_orders()
        using_mock = len(work_orders) < 8
        if using_mock:
            seen_ids = {work_order.id for work_order in work_orders}
            work_orders = [
                *work_orders,
                *[
                    work_order
                    for work_order in self.mock_work_orders()
                    if work_order.id not in seen_ids
                ],
            ][:8]

        rows = [work_order.to_row_payload() for work_order in work_orders]
        rows = self._with_toggle_urls(rows, selected_id=selected_id)
        selected = next((work_order for work_order in work_orders if work_order.id == selected_id), None) if selected_id else None
        return {
            "summary_cards": self._summary_cards(work_orders=work_orders),
            "tabs": self._tabs(using_mock=using_mock, rows=rows),
            "rows": rows,
            "detail": selected.to_detail_payload() if selected else None,
            "selected_work_order_id": selected.id if selected else "",
            "total_results_display": "19" if using_mock else f"{len(rows):,}",
            "work_order_admin_url": reverse("admin:bookings_maintenanceevent_changelist"),
            "new_work_order_url": reverse("admin:bookings_maintenanceevent_add"),
            "generated_at": timezone.now(),
        }

    @staticmethod
    def _with_toggle_urls(rows, selected_id=""):
        base_url = reverse("bookings:ops-maintenance")
        decorated_rows = []
        for row in rows:
            detail_url = f"{base_url}?work_order={row['id']}"
            decorated = {**row, "detail_url": detail_url}
            decorated["toggle_url"] = base_url if row["id"] == selected_id else detail_url
            decorated_rows.append(decorated)
        return decorated_rows

    def _summary_cards(self, work_orders):
        open_count = sum(1 for work_order in work_orders if work_order.is_open)
        overdue_count = sum(1 for work_order in work_orders if work_order.is_overdue)
        month_cost = sum(
            Decimal(work_order.cost_display.replace("$", "").replace(",", "").split()[0])
            for work_order in work_orders
            if work_order.cost_display not in {"—", ""}
        )
        completed_count = sum(1 for work_order in work_orders if work_order.is_completed)
        return [
            {"label": "Open Work Orders", "value": f"{open_count:,}", "trend": "Needs action", "tone": "blue"},
            {"label": "Overdue Items", "value": f"{overdue_count:,}", "trend": "Older than 7 days", "tone": "orange"},
            {"label": "This Month Cost", "value": f"${month_cost:,.0f}", "trend": "Live maintenance ledger", "tone": "violet"},
            {"label": "Completed Jobs", "value": f"{completed_count:,}", "trend": "Closed records", "tone": "green"},
        ]

    @staticmethod
    def _tabs(using_mock=False, rows=None):
        if using_mock:
            return [
                {"label": "All", "count": "19", "active": True},
                {"label": "Open", "count": "12", "active": False},
                {"label": "In Progress", "count": "3", "active": False},
                {"label": "Pending", "count": "1", "active": False},
                {"label": "Completed", "count": "27", "active": False},
                {"label": "Overdue", "count": "3", "active": False},
            ]

        rows = rows or []
        counts = {
            "Open": sum(1 for row in rows if row["status"] == "Open"),
            "In Progress": sum(1 for row in rows if row["status"] == "In Progress"),
            "Pending": sum(1 for row in rows if row["status"] == "Pending"),
            "Completed": sum(1 for row in rows if row["status"] == "Completed"),
            "Overdue": 0,
        }
        return [
            {"label": "All", "count": f"{len(rows):,}", "active": True},
            *[
                {"label": label, "count": f"{count:,}", "active": False}
                for label, count in counts.items()
            ],
        ]

    def _live_work_orders(self):
        events = list(
            MaintenanceEvent.objects.select_related("item", "booking", "created_by")
            .prefetch_related("photos")
            .order_by("-reported_at", "-created_at")[:8]
        )
        work_orders = []
        for index, event in enumerate(events, start=1):
            status = self._status_label(event.status)
            priority = self._priority_for_event(event)
            booking = event.booking
            work_order_number = f"WO-{event.reported_at:%Y}-{1000 + index:04d}" if event.reported_at else f"WO-LIVE-{index:04d}"
            work_orders.append(
                OpsWorkOrder(
                    id=str(event.pk),
                    number=work_order_number,
                    title=event.title,
                    property_name=event.item.business_display_name if event.item else "Unassigned property",
                    reservation_key=booking.request_key if booking else "—",
                    reservation_range=f"{booking.check_in:%b %-d} – {booking.check_out:%b %-d, %Y}" if booking else "Not linked",
                    assignee_name=event.vendor_name or "Maintenance Team",
                    assignee_role="Vendor" if event.vendor_name else "Internal",
                    priority=priority,
                    status=status,
                    cost_display=event.display_cost.replace(" USD", ""),
                    table_cost_display=f"${event.cost_amount:,.0f}",
                    date_label=event.reported_at.strftime("%b %-d, %-I:%M %p") if event.reported_at else "—",
                    reported_date=event.reported_at.strftime("%b %-d, %Y\n%-I:%M %p") if event.reported_at else "—",
                    notes=tuple(
                        note
                        for note in [
                            event.effective_description or "Guest reported an issue. Maintenance notes will appear here after review.",
                            event.admin_notes or "Recommend follow-up after completion.",
                        ]
                        if note
                    ),
                    photos=tuple(
                        OpsWorkOrderPhoto(url=photo.image_url, label=photo.caption or "Evidence photo")
                        for photo in list(event.photos.all()[:3])
                    )
                    or self._mock_photos(),
                    timeline=self._timeline_for_work_order(
                        number=work_order_number,
                        status=status,
                        assignee=event.vendor_name or "Maintenance Team",
                        reported_at=event.reported_at,
                        actor=getattr(event.created_by, "get_full_name", lambda: "")() or getattr(event.created_by, "username", "Staff"),
                        photo_count=event.photo_count,
                    ),
                    linked_listing=event.item.business_display_name if event.item else "Unassigned property",
                    linked_reservation=f"{booking.request_key} | {booking.check_in:%b %-d} – {booking.check_out:%b %-d, %Y}" if booking else "—",
                    is_mock=False,
                )
            )
        return work_orders

    def mock_work_orders(self):
        return [
            self._mock_work_order("wo-2026-0104", "WO-2026-0104", "AC not cooling", "3 Beds Apt, Vacation Home & Pool, G-101", "R-1042", "Jun 8 – Jun 14, 2026", "Carlos M.", "Technician", "High", "$180.00", "Jun 10, 9:30 AM", "Jun 10, 2026\n9:30 AM", "In Progress", ["Guest reported AC not cooling properly. Checked thermostat and filter. Refrigerant was low. Recharged unit and tested - now cooling well.", "Recommend full AC service in next 30 days."]),
            self._mock_work_order("wo-2026-0103", "WO-2026-0103", "Leak in bathroom sink", "2 Beds Apt, Pool", "R-1035", "Jun 9 – Jun 11, 2026", "Plumbing Pro", "Vendor", "Medium", "$95.00", "Jun 9, 2:15 PM", "Jun 9, 2026\n2:15 PM", "Open", ["Bathroom sink leak reported by guest. Vendor needs to inspect trap and supply line.", "Keep the guest updated after the first visit."]),
            self._mock_work_order("wo-2026-0102", "WO-2026-0102", "Replace ceiling light", "Meeting Room 1", "—", "Not linked", "Maintenance Team", "Internal", "Low", "$40.00", "Jun 9, 11:00 AM", "Jun 9, 2026\n11:00 AM", "Open", ["Ceiling light flickers during evening setup. Replace bulb and test fixture.", "No reservation is linked to this internal work order."]),
            self._mock_work_order("wo-2026-0101", "WO-2026-0101", "Pool pump not working", "6 Beds Apt, Vacation Home & Pool", "R-1040", "Jun 8 – Jun 12, 2026", "Carlos M.", "Technician", "High", "$225.00", "Jun 8, 10:45 AM", "Jun 8, 2026\n10:45 AM", "Pending", ["Pool circulation issue found during turnover check. Waiting for replacement part confirmation.", "Do not mark completed until pump pressure is verified."]),
            self._mock_work_order("wo-2026-0100", "WO-2026-0100", "Door lock issue", "2 Beds Apt, Pool", "—", "Not linked", "Lock & Key Co.", "Vendor", "Medium", "$120.00", "Jun 7, 4:30 PM", "Jun 7, 2026\n4:30 PM", "Completed", ["Smart lock keypad was intermittently failing. Vendor replaced battery pack and tested access.", "Guest access code should be regenerated before the next check-in."]),
            self._mock_work_order("wo-2026-0099", "WO-2026-0099", "Refrigerator not cooling", "3 Beds Apt, G-101", "R-1028", "Jun 7 – Jun 9, 2026", "Appliance Fixers", "Vendor", "High", "$160.00", "Jun 7, 1:20 PM", "Jun 7, 2026\n1:20 PM", "Completed", ["Refrigerator temperature was above safe range. Condenser cleaned and thermostat reset.", "Monitor for 24 hours after completion."]),
            self._mock_work_order("wo-2026-0098", "WO-2026-0098", "TV not turning on", "6 Beds Apt, Pool", "—", "Not linked", "Tech Support", "Vendor", "Low", "$60.00", "Jun 6, 9:10 AM", "Jun 6, 2026\n9:10 AM", "Completed", ["Living room TV was not powering on. Power adapter was loose behind the console.", "Remote batteries were replaced."]),
            self._mock_work_order("wo-2026-0097", "WO-2026-0097", "Paint touch-up", "Conference Room A", "—", "Not linked", "Maintenance Team", "Internal", "Low", "$75.00", "Jun 6, 8:30 AM", "Jun 6, 2026\n8:30 AM", "Completed", ["Wall scuffs near the entrance were patched and repainted.", "Touch-up matched existing paint color."]),
        ]

    def _mock_work_order(self, row_id, number, title, property_name, reservation_key, reservation_range, assignee, assignee_role, priority, cost, date_label, reported_date, status, notes):
        return OpsWorkOrder(
            id=row_id,
            number=number,
            title=title,
            property_name=property_name,
            reservation_key=reservation_key,
            reservation_range=reservation_range,
            assignee_name=assignee,
            assignee_role=assignee_role,
            priority=priority,
            status=status,
            cost_display=cost,
            table_cost_display=cost.replace(".00", ""),
            date_label=date_label,
            reported_date=reported_date,
            notes=tuple(notes),
            photos=self._mock_photos(),
            timeline=self._timeline_for_work_order(
                number=number,
                status=status,
                assignee=assignee,
                reported_at=None,
                actor="Piter Garcia",
                photo_count=3,
                date_label=date_label,
            ),
            linked_listing=property_name,
            linked_reservation=f"{reservation_key} | {reservation_range}" if reservation_key != "—" else "—",
            is_mock=True,
        )

    @staticmethod
    def _mock_photos():
        return (
            OpsWorkOrderPhoto(label="Outdoor unit", css_class="unit"),
            OpsWorkOrderPhoto(label="Compressor fan", css_class="fan"),
            OpsWorkOrderPhoto(label="Interior vent", css_class="vent"),
        )

    @staticmethod
    def _timeline_for_work_order(number, status, assignee, reported_at, actor, photo_count, date_label=""):
        if reported_at:
            created_label = reported_at.strftime("%b %-d, %Y %-I:%M %p")
            assigned_label = reported_at.strftime("%b %-d, %Y %-I:%M %p")
        else:
            created_label = date_label
            assigned_label = date_label
        timeline = [
            OpsWorkOrderTimelineEvent("Work order created", f"{created_label}\nby {actor}"),
            OpsWorkOrderTimelineEvent(f"Assigned to {assignee}", assigned_label),
            OpsWorkOrderTimelineEvent(f"Status changed to {status}", assigned_label),
            OpsWorkOrderTimelineEvent("Note added", assigned_label),
        ]
        if photo_count:
            timeline.append(OpsWorkOrderTimelineEvent(f"Picture added ({photo_count})", assigned_label))
        return tuple(timeline)

    @staticmethod
    def _priority_for_event(event):
        if event.cost_amount >= Decimal("150"):
            return "High"
        if event.cost_amount >= Decimal("90"):
            return "Medium"
        return "Low"

    @staticmethod
    def _status_label(status):
        labels = {
            MaintenanceStatus.DRAFT: "Pending",
            MaintenanceStatus.LOGGED: "Open",
            MaintenanceStatus.SCHEDULED: "Open",
            MaintenanceStatus.IN_PROGRESS: "In Progress",
            MaintenanceStatus.COMPLETED: "Completed",
            MaintenanceStatus.DOCUMENTED: "Completed",
            MaintenanceStatus.BILLED: "Completed",
            MaintenanceStatus.ARCHIVED: "Completed",
        }
        return labels.get(status, str(status).replace("_", " ").title())

    @staticmethod
    def _status_class(status):
        return str(status).strip().lower().replace(" ", "-") or "open"


class AgentIntelligenceOperationsService:
    """Presentation service for the FairAgent / Agent Intelligence ops page."""

    MOCK_CONVERSATIONS = [
        {
            "visitor": "Maria Rodriguez",
            "initials": "MR",
            "tone": "green",
            "item": "3 Beds Apt, Vacation Home & Pool, G-101",
            "question": "Do you have availability for June 20-23?",
            "time_label": "Just now",
            "sentiment": "Positive",
        },
        {
            "visitor": "John Smith",
            "initials": "JS",
            "tone": "blue",
            "item": "2 Beds Apt, Pool",
            "question": "Is early check-in possible on Jun 12?",
            "time_label": "1m ago",
            "sentiment": "Positive",
        },
        {
            "visitor": "Ana Lopez",
            "initials": "AL",
            "tone": "sky",
            "item": "Meeting Room 1",
            "question": "Can I get a receipt for my payment?",
            "time_label": "2m ago",
            "sentiment": "Neutral",
        },
        {
            "visitor": "David Brown",
            "initials": "DW",
            "tone": "violet",
            "item": "6 Beds Apt, G-101",
            "question": "What's the neighborhood like?",
            "time_label": "3m ago",
            "sentiment": "Positive",
        },
    ]

    MOCK_INTENTS = [
        {"question": "Check availability", "detail": "Do you have availability for June 20-23?", "category": "Availability", "total": 342, "trend": "+18%", "tone": "green"},
        {"question": "Early check-in request", "detail": "Is early check-in possible?", "category": "Check-in", "total": 156, "trend": "+9%", "tone": "green"},
        {"question": "Deposit information", "detail": "How much is the deposit?", "category": "Payments", "total": 138, "trend": "-6%", "tone": "red"},
        {"question": "Neighborhood info", "detail": "What is the area like?", "category": "Local Info", "total": 122, "trend": "+12%", "tone": "green"},
        {"question": "Parking availability", "detail": "Do you have parking?", "category": "Amenities", "total": 98, "trend": "+7%", "tone": "green"},
    ]

    def page_payload(self):
        conversations = AgentConversation.objects.select_related("item").order_by("-updated_at")
        faqs = AgentFAQ.objects.select_related("item").order_by("-priority", "category", "question")
        total_conversations = conversations.count()
        faq_total = faqs.count()
        faq_conversations = conversations.filter(metadata__agent_mode="faq").count()
        openai_conversations = conversations.filter(metadata__agent_mode="openai").count()
        fallback_conversations = conversations.exclude(metadata__agent_mode__in=["faq", "openai"]).count()
        booking_conversations = conversations.filter(
            Q(question_topic__icontains="booking")
            | Q(question_topic__icontains="availability")
            | Q(last_user_message__icontains="book")
            | Q(last_user_message__icontains="availability")
        ).count()
        coverage = round((faq_conversations / total_conversations) * 100) if total_conversations else (87 if faq_total else 87)
        topic_rows = list(
            conversations.values("question_topic")
            .annotate(total=Count("id"))
            .order_by("-total", "question_topic")[:5]
        )
        max_topic_total = max([row["total"] for row in topic_rows] or [0])

        return {
            "summary_cards": self._summary_cards(
                total_conversations=total_conversations,
                fallback_conversations=fallback_conversations,
                booking_conversations=booking_conversations,
                openai_conversations=openai_conversations,
            ),
            "insight": {
                "active_conversations": f"{self._active_conversation_count(conversations):,}" if total_conversations else "12",
                "engagement_rate": f"{coverage if total_conversations else 92}%",
                "sentiment": "Positive",
            },
            "conversation_rows": self._conversation_rows(conversations[:4]),
            "intent_rows": self._intent_rows(topic_rows, max_topic_total),
            "recommendations": self._recommendations(),
            "faq_match": self._faq_match_payload(coverage=coverage, total_conversations=total_conversations, faq_total=faq_total),
            "suggestions": self._suggestions(),
            "guardrails": self._guardrails(),
            "topic_rows": self._topic_volume_rows(topic_rows, max_topic_total),
            "faq_admin_url": reverse("admin:bookings_agentfaq_changelist"),
            "conversation_admin_url": reverse("admin:bookings_agentconversation_changelist"),
            "agent_api_url": reverse("bookings:ops-agent-api"),
            "generated_at": timezone.now(),
        }

    def _summary_cards(self, total_conversations, fallback_conversations, booking_conversations, openai_conversations):
        escalation_value = fallback_conversations if total_conversations else 32
        booking_value = booking_conversations if total_conversations else 186
        return [
            {
                "label": "Total Conversations",
                "value": f"{(total_conversations or 1248):,}",
                "trend": "+18% vs Jun 29 - Jul 5" if not total_conversations else "Live conversation log",
                "tone": "green",
                "spark": "M0 18 L9 20 L18 15 L28 11 L38 17 L48 20 L58 17 L68 19 L78 14 L88 18 L100 12 L112 16 L122 18 L132 10 L142 15 L154 14 L164 20 L176 17 L188 12 L200 15",
                "icon": "chat",
            },
            {
                "label": "Escalations",
                "value": f"{escalation_value:,}",
                "trend": "-11% vs Jun 29 - Jul 5" if not total_conversations else f"{openai_conversations:,} model assists",
                "tone": "orange",
                "spark": "M0 20 L12 18 L24 11 L36 17 L48 13 L60 19 L72 15 L84 20 L96 14 L108 11 L120 16 L132 21 L144 18 L156 13 L168 10 L180 14 L192 18 L200 16",
                "icon": "alert",
            },
            {
                "label": "Booking Conversions",
                "value": f"{booking_value:,}",
                "trend": "+14% vs Jun 29 - Jul 5" if not total_conversations else "Availability and booking intents",
                "tone": "violet",
                "spark": "M0 18 L12 18 L24 12 L36 10 L48 16 L60 18 L72 12 L84 14 L96 17 L108 21 L120 15 L132 19 L144 14 L156 17 L168 13 L180 19 L192 17 L200 20",
                "icon": "check",
            },
            {
                "label": "Avg. Response Time",
                "value": "1m 18s",
                "trend": "-8s vs Jun 29 - Jul 5",
                "tone": "blue",
                "spark": "M0 15 L12 14 L24 18 L36 13 L48 11 L60 12 L72 15 L84 13 L96 16 L108 14 L120 20 L132 21 L144 20 L156 17 L168 21 L180 18 L192 20 L200 17",
                "icon": "clock",
            },
        ]

    @staticmethod
    def _active_conversation_count(conversations):
        since = timezone.now() - timedelta(hours=24)
        return conversations.filter(updated_at__gte=since).count()

    def _conversation_rows(self, live_rows):
        rows = [self._conversation_payload(row, index) for index, row in enumerate(live_rows)]
        if len(rows) < len(self.MOCK_CONVERSATIONS):
            rows.extend(self.MOCK_CONVERSATIONS[len(rows):])
        return rows[:4]

    def _conversation_payload(self, row, index):
        visitor = row.visitor_name or self._visitor_from_email(row.visitor_email) or "Website visitor"
        mode = (row.metadata or {}).get("agent_mode", "fallback")
        return {
            "visitor": visitor,
            "initials": self._initials(visitor),
            "tone": ["green", "blue", "sky", "violet"][index % 4],
            "item": row.item.business_display_name if row.item else "General MLADIS",
            "question": self._trim(row.last_user_message, 88),
            "time_label": self._time_ago(row.updated_at),
            "sentiment": "Neutral" if mode == "guardrail" else "Positive",
        }

    def _intent_rows(self, topic_rows, max_topic_total):
        rows = []
        for index, row in enumerate(topic_rows[:5]):
            topic = row["question_topic"] or "general"
            total = row["total"]
            mock = self.MOCK_INTENTS[index] if index < len(self.MOCK_INTENTS) else self.MOCK_INTENTS[-1]
            rows.append(
                {
                    "question": self._topic_title(topic),
                    "detail": mock["detail"],
                    "category": self._category_for_topic(topic),
                    "total": total,
                    "trend": f"+{max(3, min(18, int((total / max_topic_total) * 18) if max_topic_total else 6))}%",
                    "tone": "green",
                }
            )
        if len(rows) < len(self.MOCK_INTENTS):
            rows.extend(self.MOCK_INTENTS[len(rows):])
        return rows[:5]

    @classmethod
    def _topic_volume_rows(cls, topic_rows, max_topic_total):
        rows = []
        for index, row in enumerate(topic_rows[:5]):
            total = row["total"]
            rows.append(
                {
                    "topic": cls._topic_title(row["question_topic"] or "general"),
                    "total": total,
                    "percent": int((total / max_topic_total) * 100) if max_topic_total else 0,
                    "bar": int((total / max_topic_total) * 100) if max_topic_total else 0,
                }
            )
        if len(rows) < len(cls.MOCK_INTENTS):
            for mock in cls.MOCK_INTENTS[len(rows):]:
                rows.append(
                    {
                        "topic": mock["category"] if mock["category"] != "Check-in" else "Check-in / Out",
                        "total": mock["total"],
                        "percent": {"Availability": 27, "Check-in": 12, "Payments": 11, "Local Info": 10, "Amenities": 8}.get(mock["category"], 8),
                        "bar": {"Availability": 100, "Check-in": 52, "Payments": 44, "Local Info": 39, "Amenities": 32}.get(mock["category"], 30),
                    }
                )
        return rows[:5]

    @staticmethod
    def _recommendations():
        return [
            {"title": "Follow up on availability holds", "body": "3 guests asked about availability but haven't booked.", "tone": "red", "priority": "High"},
            {"title": "Send deposit policy reminder", "body": "Multiple guests asked about deposits. Proactive info can reduce friction.", "tone": "orange", "priority": "Medium"},
            {"title": "Suggest alternate dates", "body": "2 guests are looking for sold-out dates.", "tone": "orange", "priority": "Medium"},
            {"title": "Promote early check-in", "body": "High intent detected for early check-in on Jun 12-14.", "tone": "green", "priority": "Low"},
        ]

    @staticmethod
    def _suggestions():
        return [
            {"title": "Send follow-up", "body": "Follow up with Maria Rodriguez about 3 Beds Apt, G-101 availability.", "impact": "High Impact", "tone": "red"},
            {"title": "Offer alternate stay", "body": "Recommend 2 Beds Apt, Pool for sold-out dates (Jun 18-20).", "impact": "Medium Impact", "tone": "orange"},
            {"title": "Release deposit info", "body": "Send deposit policy and payment options to recent inquiries.", "impact": "Medium Impact", "tone": "orange"},
        ]

    @staticmethod
    def _guardrails():
        return [
            {"title": "Never share government IDs", "body": "Guest ID and documents are protected."},
            {"title": "No off-platform bookings", "body": "Bookings must be made on mladis.com."},
            {"title": "No pricing overrides", "body": "Prices shown are final and policy-compliant."},
            {"title": "No personal data requests", "body": "We do not ask for sensitive personal data."},
        ]

    @staticmethod
    def _faq_match_payload(coverage, total_conversations, faq_total):
        match_rate = coverage if total_conversations else 87
        matched = max(1, total_conversations or 1086)
        return {
            "rate": f"{match_rate}%",
            "matched": f"{matched:,}",
            "partial": f"{max(faq_total, 112):,}",
            "missing": f"{max(0, (total_conversations - matched) if total_conversations else 50):,}",
        }

    @staticmethod
    def _visitor_from_email(email):
        if not email:
            return ""
        return email.split("@", 1)[0].replace(".", " ").replace("_", " ").title()

    @staticmethod
    def _initials(value):
        parts = [part for part in re.split(r"\s+", value.strip()) if part]
        if not parts:
            return "AI"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return f"{parts[0][0]}{parts[-1][0]}".upper()

    @staticmethod
    def _time_ago(value):
        if not value:
            return "Just now"
        delta = timezone.now() - value
        if delta.days:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours:
            return f"{hours}h ago"
        minutes = max(1, delta.seconds // 60)
        return f"{minutes}m ago"

    @staticmethod
    def _trim(value, length):
        value = (value or "").strip()
        if len(value) <= length:
            return value
        return f"{value[: length - 1].rstrip()}..."

    @staticmethod
    def _topic_title(topic):
        label = str(topic or "general").replace("_", " ").replace("-", " ").strip().title()
        if label.lower() in {"Faq", "General"}:
            return "General question"
        return label

    @staticmethod
    def _category_for_topic(topic):
        topic = str(topic or "").lower()
        if "deposit" in topic or "payment" in topic or "invoice" in topic:
            return "Payments"
        if "check" in topic or "arrival" in topic:
            return "Check-in"
        if "parking" in topic or "pool" in topic or "amenity" in topic:
            return "Amenities"
        if "area" in topic or "local" in topic or "neighborhood" in topic:
            return "Local Info"
        if "availability" in topic or "book" in topic:
            return "Availability"
        return "General"


class CustomersCRMService:
    """Service layer for the server-rendered Customers CRM page."""

    COUNTRY_POOL = [
        "Dominican Republic",
        "United States",
        "Canada",
        "France",
        "Spain",
        "Mexico",
        "Colombia",
    ]

    def get_profiles(self, tab="all", search=""):
        qs = (
            CustomerProfile.objects.annotate(
                direct_reservations=Count("booking_inquiries", distinct=True),
                airbnb_reservations=Count("airbnb_guest_records", distinct=True),
                feedback_total=Count("feedback_entries", distinct=True),
                invoice_total=Count("invoices", distinct=True),
                total_spend_cents=Coalesce(Sum("invoices__total_cents"), 0),
            )
            .prefetch_related("booking_inquiries__item", "feedback_entries__item")
            .order_by("-updated_at", "name", "email")
        )

        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        if tab == "vip":
            qs = qs.filter(segment=ClientSegment.VIP)
        elif tab == "blocked":
            qs = qs.filter(segment=ClientSegment.BLACKLISTED)
        elif tab == "repeat":
            qs = qs.filter(Q(direct_reservations__gte=2) | Q(airbnb_reservations__gte=2))
        elif tab == "new":
            qs = qs.filter(direct_reservations=0, airbnb_reservations=0)

        return list(qs)

    def get_tab_counts(self):
        base = CustomerProfile.objects.annotate(
            direct_reservations=Count("booking_inquiries", distinct=True),
            airbnb_reservations=Count("airbnb_guest_records", distinct=True),
        )
        repeat_q = Q(direct_reservations__gte=2) | Q(airbnb_reservations__gte=2)
        return {
            "all": base.count(),
            "repeat": base.filter(repeat_q).count(),
            "vip": base.filter(segment=ClientSegment.VIP).count(),
            "new": base.filter(direct_reservations=0, airbnb_reservations=0).count(),
            "blocked": base.filter(segment=ClientSegment.BLACKLISTED).count(),
        }

    @staticmethod
    def mock_tab_counts():
        return {
            "all": 1283,
            "repeat": 412,
            "vip": 128,
            "new": 743,
            "blocked": 8,
        }

    def mock_table_rows(self):
        return [
            self._mock_row(
                row_id="mock-maria-rodriguez",
                name="Maria Rodriguez",
                email="maria.rodriguez@gmail.com",
                country="Dominican Republic",
                country_code="DO",
                channel="Direct Website",
                channel_cls="direct",
                past_stays=5,
                total_spend="$4,320",
                status="VIP",
                status_cls="vip",
                last_contact_label="Jun 5, 2026",
                avatar_cls="a1",
                contact_icon="✉",
            ),
            self._mock_row(
                row_id="mock-john-smith",
                name="John Smith",
                email="john.smith@gmail.com",
                country="United States",
                country_code="US",
                channel="Airbnb",
                channel_cls="airbnb",
                past_stays=2,
                total_spend="$1,250",
                status="Repeat",
                status_cls="repeat",
                last_contact_label="Jun 4, 2026",
                avatar_cls="a2",
                contact_icon="💬",
            ),
            self._mock_row(
                row_id="mock-ana-lopez",
                name="Ana Lopez",
                email="ana.lopez@yahoo.com",
                country="Dominican Republic",
                country_code="DO",
                channel="Booking.com",
                channel_cls="manual",
                past_stays=1,
                total_spend="$650",
                status="New",
                status_cls="new",
                last_contact_label="Jun 3, 2026",
                avatar_cls="a3",
                contact_icon="✉",
            ),
            self._mock_row(
                row_id="mock-david-brown",
                name="David Brown",
                email="david.brown@outlook.com",
                country="Canada",
                country_code="CA",
                channel="Vrbo",
                channel_cls="manual",
                past_stays=3,
                total_spend="$2,100",
                status="Repeat",
                status_cls="repeat",
                last_contact_label="Jun 2, 2026",
                avatar_cls="a4",
                contact_icon="📞",
            ),
            self._mock_row(
                row_id="mock-sophie-martin",
                name="Sophie Martin",
                email="sophie.martin@gmail.com",
                country="France",
                country_code="FR",
                channel="Direct Website",
                channel_cls="direct",
                past_stays=4,
                total_spend="$3,780",
                status="VIP",
                status_cls="vip",
                last_contact_label="Jun 1, 2026",
                avatar_cls="a5",
                contact_icon="✉",
            ),
        ]

    def mock_detail_payload(self):
        return {
            "profile": None,
            "display_name": "Maria Rodriguez",
            "avatar": "MR",
            "status_label": "VIP Guest",
            "status_cls": "vip",
            "country": "Dominican Republic",
            "country_code": "DO",
            "phone": "+1 (809) 555-0198",
            "preferred_language": "EN",
            "birthday": "May 18, 1987",
            "travel_style": "Leisure",
            "guest_since": "Jan 12, 2024",
            "tags": ["Family", "Pool Lover", "Repeat"],
            "notes": "Loves the top-floor units. Prefers late check-out when available. Traveling with kids.",
            "messages": [
                {
                    "author": "Maria Rodriguez",
                    "time": "Jun 5, 2026 9:14 AM",
                    "body": "Hi! We'll be arriving around 3pm. Is early check-in possible?",
                    "is_agent": False,
                },
                {
                    "author": "You",
                    "time": "Jun 5, 2026 9:32 AM",
                    "body": "Hi Maria! Yes, early check-in is available. Your apartment will be ready by 1pm. Let us know if you need transport or local recommendations!",
                    "is_agent": True,
                },
                {
                    "author": "Maria Rodriguez",
                    "time": "Jun 5, 2026 9:45 AM",
                    "body": "Perfect, thank you!",
                    "is_agent": False,
                },
            ],
            "last_stays": [
                {
                    "label": "3 Beds Apt, Vacation Home & Pool, G-101",
                    "date_range": "Jun 8 – Jun 12, 2026",
                    "amount": "$1,250.00 USD",
                    "status": "Completed",
                    "status_cls": "completed",
                },
                {
                    "label": "2 Beds Apt, Vacation Home & Pool, B-204",
                    "date_range": "Mar 14 – Mar 18, 2026",
                    "amount": "$880.00 USD",
                    "status": "Completed",
                    "status_cls": "completed",
                },
                {
                    "label": "Studio, Beachfront View, A-07",
                    "date_range": "Nov 2 – Nov 5, 2025",
                    "amount": "$620.00 USD",
                    "status": "Completed",
                    "status_cls": "completed",
                },
                {
                    "label": "3 Beds Apt, Vacation Home & Pool, G-101",
                    "date_range": "Aug 10 – Aug 14, 2025",
                    "amount": "$1,100.00 USD",
                    "status": "Completed",
                    "status_cls": "completed",
                },
                {
                    "label": "2 Beds Apt, Vacation Home & Pool, B-204",
                    "date_range": "May 22 – May 25, 2025",
                    "amount": "$750.00 USD",
                    "status": "Completed",
                    "status_cls": "completed",
                },
            ],
            "upcoming_stay": {
                "label": "2 Beds Apt, Vacation Home & Pool",
                "date_range": "Jun 20 - Jun 24, 2026",
                "amount": "$950.00 USD",
                "status": "Confirmed",
            },
            "linked_reservations": [
                {"request_key": "RR-1042", "date_range": "Jun 8 - Jun 12, 2026", "amount": "$1,250.00", "status": "Completed", "status_cls": "ok"},
                {"request_key": "RR-1125", "date_range": "Apr 2 - Apr 6, 2026", "amount": "$980.00", "status": "Completed", "status_cls": "ok"},
                {"request_key": "RR-1268", "date_range": "Jun 20 - Jun 24, 2026", "amount": "$950.00", "status": "Confirmed", "status_cls": "ok"},
            ],
            "missing_information": ["Government ID not on file", "Purpose of travel", "Emergency contact"],
            "risk_assessment": [
                ("Verified email and phone", "low"),
                ("Payment history (5 stays)", "low"),
                ("No chargebacks", "low"),
                ("Profile 100% complete", "low"),
            ],
            "recommended_actions": ["Send check-in instructions", "Share local guide", "Offer airport pickup"],
        }

    _COUNTRY_FLAGS = {
        "DO": "🇩🇴", "US": "🇺🇸", "CA": "🇨🇦", "FR": "🇫🇷",
        "ES": "🇪🇸", "MX": "🇲🇽", "CO": "🇨🇴",
    }

    @staticmethod
    def _mock_row(row_id, name, email, country, country_code, channel, channel_cls, past_stays, total_spend, status, status_cls, last_contact_label, avatar_cls="a1", contact_icon="✉"):
        return {
            "id": row_id,
            "name": name,
            "email": email,
            "phone": "",
            "avatar": "".join([part[0] for part in name.split()[:2]]).upper(),
            "avatar_cls": avatar_cls,
            "country": country,
            "country_code": country_code,
            "country_flag": CustomersCRMService._COUNTRY_FLAGS.get(country_code, "🌍"),
            "channel": channel,
            "channel_cls": channel_cls,
            "past_stays": past_stays,
            "total_spend": total_spend,
            "status": status,
            "status_cls": status_cls,
            "last_contact": timezone.now(),
            "last_contact_label": last_contact_label,
            "contact_icon": contact_icon,
            "segment": ClientSegment.VIP if status == "VIP" else ClientSegment.AVERAGE,
            "is_mock": True,
        }

    def table_rows(self, profiles, limit=4):
        rows = [self.mock_anchor_row()]
        rows.extend(self.table_row_payload(profile) for profile in profiles[:limit])
        return rows

    def table_row_payload(self, profile):
        total_res = self._total_reservations(profile)
        status_label, status_cls = self._status_badge(profile)
        country_code = self._country_code(profile)
        return {
            "id": profile.pk,
            "name": profile.name or profile.email or f"Customer {profile.pk}",
            "email": profile.email,
            "phone": profile.phone,
            "avatar": self._avatar(profile),
            "avatar_cls": "a1",
            "country": self._country(profile),
            "country_code": country_code,
            "country_flag": self._COUNTRY_FLAGS.get(country_code, "🌍"),
            "channel": profile.get_source_display(),
            "channel_cls": self._channel_cls(profile),
            "past_stays": total_res,
            "total_spend": self._money(profile.total_spend_cents),
            "status": status_label,
            "status_cls": status_cls,
            "last_contact": profile.updated_at,
            "last_contact_label": profile.updated_at.strftime("%b %-d, %Y"),
            "contact_icon": "✉",
            "segment": profile.segment,
            "is_mock": False,
        }

    @staticmethod
    def mock_anchor_row():
        return {
            "id": "mock-maria-rodriguez",
            "name": "Maria Rodriguez",
            "email": "maria.rodriguez@mladis.com",
            "phone": "+1 (809) 555-0198",
            "avatar": "MR",
            "avatar_cls": "a1",
            "country": "Dominican Republic",
            "country_code": "DO",
            "country_flag": "🇩🇴",
            "channel": "Direct Website",
            "channel_cls": "direct",
            "past_stays": 5,
            "total_spend": "$4,320",
            "status": "VIP",
            "status_cls": "vip",
            "last_contact": timezone.now(),
            "last_contact_label": "Jun 5, 2026",
            "contact_icon": "✉",
            "segment": ClientSegment.VIP,
            "is_mock": True,
        }

    def detail_payload(self, profile):
        bookings = list(
            profile.booking_inquiries.select_related("item").order_by("-check_in", "-updated_at")[:12]
        )
        upcoming = [b for b in bookings if b.check_in and b.check_in >= date.today()]
        latest = bookings[0] if bookings else None
        next_stay = upcoming[0] if upcoming else None
        feedback = list(profile.feedback_entries.select_related("item").order_by("-created_at")[:2])

        linked = [
            {
                "request_key": booking.request_key,
                "date_range": f"{booking.check_in:%b %-d} - {booking.check_out:%b %-d, %Y}",
                "amount": booking.display_total,
                "status": booking.get_status_display(),
                "status_cls": "ok" if booking.status == BookingStatus.CONFIRMED else "warn",
            }
            for booking in bookings[:3]
        ]

        return {
            "profile": profile,
            "display_name": profile.name or profile.email or f"Customer {profile.pk}",
            "avatar": self._avatar(profile),
            "status_label": self._status_badge(profile)[0],
            "status_cls": self._status_badge(profile)[1],
            "country": self._country(profile),
            "country_code": self._country_code(profile),
            "phone": profile.phone or "-",
            "preferred_language": (profile.preferred_language or "en").upper(),
            "birthday": self._mock_birthday(profile),
            "travel_style": self._mock_travel_style(profile),
            "guest_since": profile.created_at.strftime("%b %-d, %Y"),
            "tags": self._tags(profile),
            "notes": profile.notes or "Loves curated stays and fast communication.",
            "messages": self._messages(profile, feedback),
            "last_stay": self._stay_card(latest),
            "upcoming_stay": self._stay_card(next_stay),
            "linked_reservations": linked,
            "missing_information": self._missing_information(profile),
            "risk_assessment": self._risk_assessment(profile),
            "recommended_actions": self._recommended_actions(profile),
        }

    @staticmethod
    def _total_reservations(profile):
        return (profile.direct_reservations or 0) + (profile.airbnb_reservations or 0)

    @staticmethod
    def _money(cents):
        return f"${(cents or 0) / 100:,.0f}"

    @staticmethod
    def _avatar(profile):
        text = (profile.name or profile.email or "CU").strip()
        parts = [chunk for chunk in text.split() if chunk]
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return text[:2].upper()

    def _country(self, profile):
        return self.COUNTRY_POOL[profile.pk % len(self.COUNTRY_POOL)]

    def _country_code(self, profile):
        mapping = {
            "Dominican Republic": "DO",
            "United States": "US",
            "Canada": "CA",
            "France": "FR",
            "Spain": "ES",
            "Mexico": "MX",
            "Colombia": "CO",
        }
        return mapping.get(self._country(profile), "UN")

    @staticmethod
    def _channel_cls(profile):
        mapping = {
            "direct": "direct",
            "airbnb": "airbnb",
            "social": "social",
            "manual": "manual",
        }
        return mapping.get(profile.source, "manual")

    def _status_badge(self, profile):
        if profile.segment == ClientSegment.BLACKLISTED:
            return ("Blocked", "blocked")
        if profile.segment == ClientSegment.VIP:
            return ("VIP", "vip")
        if self._total_reservations(profile) >= 2:
            return ("Repeat", "repeat")
        if self._total_reservations(profile) == 0:
            return ("New", "new")
        return ("Active", "active")

    @staticmethod
    def _mock_birthday(profile):
        day = (profile.pk % 27) + 1
        month = (profile.pk % 11) + 1
        year = 1980 + (profile.pk % 18)
        return date(year, month, day).strftime("%b %-d, %Y")

    @staticmethod
    def _mock_travel_style(profile):
        styles = ["Leisure", "Business", "Family", "Remote work"]
        return styles[profile.pk % len(styles)]

    def _tags(self, profile):
        tags = [profile.get_segment_display()]
        tags.append(profile.get_source_display())
        if self._total_reservations(profile) >= 2:
            tags.append("Repeat")
        return tags

    def _messages(self, profile, feedback):
        if feedback:
            primary = feedback[0]
            return [
                {
                    "author": profile.name or "Guest",
                    "time": primary.created_at.strftime("%b %-d, %Y %I:%M %p"),
                    "body": primary.feedback_text[:160],
                    "is_agent": False,
                },
                {
                    "author": "You",
                    "time": timezone.now().strftime("%b %-d, %Y %I:%M %p"),
                    "body": "Thanks for the update. We have your preferences noted and your next stay is prepared.",
                    "is_agent": True,
                },
            ]
        return [
            {
                "author": "You",
                "time": timezone.now().strftime("%b %-d, %Y %I:%M %p"),
                "body": "Welcome to MLADIS. Let us know your check-in preferences and arrival details.",
                "is_agent": True,
            }
        ]

    @staticmethod
    def _stay_card(booking):
        if not booking:
            return None
        stay_name = booking.item.business_display_name if booking.item else "Unassigned stay"
        return {
            "label": stay_name,
            "date_range": f"{booking.check_in:%b %-d} - {booking.check_out:%b %-d, %Y}",
            "amount": booking.display_total,
            "status": booking.get_status_display(),
        }

    @staticmethod
    def _missing_information(profile):
        rows = []
        if not profile.phone:
            rows.append("Phone number missing")
        if not profile.email:
            rows.append("Email not available")
        if profile.marketing_consent_status != MarketingConsentStatus.OPTED_IN:
            rows.append("Promotion consent not confirmed")
        if not rows:
            rows.append("No blockers")
        return rows

    def _risk_assessment(self, profile):
        risks = []
        if profile.segment == ClientSegment.BLACKLISTED:
            risks.append(("Profile marked as blacklisted", "high"))
        if self._total_reservations(profile) >= 2:
            risks.append(("Payment history available", "low"))
        if profile.feedback_total:
            risks.append(("Guest feedback history available", "low"))
        if not risks:
            risks.append(("Limited history, request extra verification", "medium"))
        return risks

    @staticmethod
    def _recommended_actions(profile):
        actions = ["Send check-in instructions", "Share local guide"]
        if profile.can_receive_promotions:
            actions.append("Send loyalty offer")
        if profile.segment == ClientSegment.BLACKLISTED:
            actions = ["Require manual approval", "Request ID verification"]
        return actions


class PaymentsTransactionsService:
    """Service layer for the server-rendered Payments & Transactions page."""

    def page_payload(self, selected_id=""):
        rows = self._live_rows()
        using_mock = not rows
        if using_mock:
            rows = self.mock_rows()

        selected = next((row for row in rows if row["id"] == selected_id), rows[0] if rows else None)
        detail = self._detail_payload(selected, using_mock=using_mock) if selected else None
        total_results_display = "126" if using_mock else f"{len(rows):,}"

        return {
            "summary_cards": self._summary_cards(using_mock=using_mock),
            "rows": rows,
            "detail": detail,
            "selected_transaction_id": selected["id"] if selected else "",
            "total_results": len(rows),
            "total_results_display": total_results_display,
            "generated_at": timezone.now(),
            "date_range_label": "Jun 6 – Jun 12, 2026" if using_mock else "Live ledger",
        }

    def _summary_cards(self, using_mock=False):
        if using_mock:
            return [
                {"label": "Total Collected", "value": "$18,540", "trend": "+15% vs last 7 days", "tone": "green"},
                {"label": "Pending Payments", "value": "$4,320", "trend": "-8% vs last 7 days", "tone": "blue"},
                {"label": "Refunded", "value": "$620", "trend": "+5% vs last 7 days", "tone": "orange"},
                {"label": "Payouts in Transit", "value": "$2,100", "trend": "2 payouts", "tone": "violet"},
            ]

        paid_total = Invoice.objects.filter(status=InvoiceStatus.PAID).aggregate(total=Sum("total_cents"))["total"] or 0
        pending_total = Invoice.objects.filter(status__in=[InvoiceStatus.DRAFT, InvoiceStatus.SENT]).aggregate(total=Sum("total_cents"))["total"] or 0
        refunded_total = DamageDeposit.objects.filter(status=DepositStatus.CANCELED).aggregate(total=Sum("amount_cents"))["total"] or 0
        transit_total = ReservationPaymentHold.objects.filter(status=DepositStatus.REQUIRES_CAPTURE).aggregate(total=Sum("amount_cents"))["total"] or 0

        return [
            {"label": "Total Collected", "value": self._money(paid_total), "trend": f"{Invoice.objects.filter(status=InvoiceStatus.PAID).count()} paid invoices", "tone": "green"},
            {"label": "Pending Payments", "value": self._money(pending_total), "trend": f"{Invoice.objects.filter(status__in=[InvoiceStatus.DRAFT, InvoiceStatus.SENT]).count()} open invoices", "tone": "blue"},
            {"label": "Refunded", "value": self._money(refunded_total), "trend": f"{DamageDeposit.objects.filter(status=DepositStatus.CANCELED).count()} canceled deposits", "tone": "orange"},
            {"label": "Payouts in Transit", "value": self._money(transit_total), "trend": f"{ReservationPaymentHold.objects.filter(status=DepositStatus.REQUIRES_CAPTURE).count()} authorized holds", "tone": "violet"},
        ]

    def _live_rows(self):
        invoices = list(
            Invoice.objects.select_related("inquiry__item", "customer_profile")
            .order_by("-issue_date", "-created_at")[:10]
        )
        if not invoices:
            return []

        inquiry_ids = [invoice.inquiry_id for invoice in invoices if invoice.inquiry_id]
        deposits = list(
            DamageDeposit.objects.select_related("inquiry", "item")
            .filter(inquiry_id__in=inquiry_ids)
            .order_by("-created_at")
        )
        holds = list(
            ReservationPaymentHold.objects.select_related("inquiry", "item")
            .filter(inquiry_id__in=inquiry_ids)
            .order_by("-created_at")
        )

        deposits_by_inquiry = {}
        for deposit in deposits:
            deposits_by_inquiry.setdefault(deposit.inquiry_id, []).append(deposit)

        holds_by_inquiry = {}
        for hold in holds:
            holds_by_inquiry.setdefault(hold.inquiry_id, []).append(hold)

        rows = []
        for invoice in invoices:
            inquiry = invoice.inquiry
            invoice_deposits = deposits_by_inquiry.get(invoice.inquiry_id, [])
            invoice_holds = holds_by_inquiry.get(invoice.inquiry_id, [])
            primary_payment = invoice_holds[0] if invoice_holds else (invoice_deposits[0] if invoice_deposits else None)
            rows.append(
                {
                    "id": f"invoice-{invoice.pk}",
                    "transaction_id": invoice.invoice_number,
                    "guest": invoice.recipient_name,
                    "reservation": inquiry.request_key if inquiry else "—",
                    "listing": inquiry.item.business_display_name if inquiry and inquiry.item else "Manual invoice",
                    "channel": "Direct Website" if inquiry else "Manual Invoice",
                    "method": self._payment_method_label(primary_payment),
                    "date_label": invoice.issue_date.strftime("%b %-d, %Y") if invoice.issue_date else "—",
                    "time_label": invoice.created_at.strftime("%-I:%M %p") if invoice.created_at else "—",
                    "amount": invoice.display_total,
                    "status": self._invoice_status_label(invoice),
                    "status_cls": self._invoice_status_class(invoice),
                    "invoice_icon": "↗",
                    "invoice_url": reverse("bookings:invoice-print", args=[invoice.public_token]),
                    "is_mock": False,
                    "_invoice": invoice,
                    "_deposits": invoice_deposits,
                    "_holds": invoice_holds,
                }
            )
        return rows

    def mock_rows(self):
        return [
            self._mock_row("mock-txn-10541", "TXN-2026-10541", "Maria Rodriguez", "R-1042", "3 Beds Apt, G-101", "Direct Website", "VISA •••• 4242", "Jun 12, 2026", "9:30 AM", "$1,250.00", "Paid", "paid"),
            self._mock_row("mock-txn-10540", "TXN-2026-10540", "John Smith", "R-1040", "2 Beds Apt, Pool", "Airbnb", "MC •••• 5655", "Jun 11, 2026", "4:15 PM", "$550.00", "Paid", "paid"),
            self._mock_row("mock-txn-10539", "TXN-2026-10539", "Ana Lopez", "R-1039", "Meeting Room 1", "Corporate Booking", "ACH Transfer", "Jun 10, 2026", "11:20 AM", "$250.00", "Paid", "paid"),
            self._mock_row("mock-txn-10538", "TXN-2026-10538", "David Brown", "R-1038", "6 Beds Apt, G-101", "Vrbo", "VISA •••• 1111", "Jun 9, 2026", "2:45 PM", "$2,100.00", "Settled", "settled"),
            self._mock_row("mock-txn-10537", "TXN-2026-10537", "Sophie Martin", "R-1037", "3 Beds Apt, G-101", "Booking.com", "MC •••• 8888", "Jun 9, 2026", "10:05 AM", "$500.00", "Pending", "pending"),
            self._mock_row("mock-txn-10536", "TXN-2026-10536", "Carlos Mendez", "R-1036", "2 Beds Apt, Pool", "Direct Website", "Amex •••• 1005", "Jun 8, 2026", "8:20 PM", "$1,320.00", "Paid", "paid"),
            self._mock_row("mock-txn-10535", "TXN-2026-10535", "Emily Johnson", "R-1035", "Conference Room A", "Direct Website", "VISA •••• 4242", "Jun 8, 2026", "1:10 PM", "$180.00", "Refunded", "refunded"),
            self._mock_row("mock-txn-10534", "TXN-2026-10534", "Michael Lee", "R-1034", "6 Beds Apt, Pool", "Airbnb", "MC •••• 2222", "Jun 7, 2026", "6:40 PM", "$2,350.00", "Paid", "paid"),
            self._mock_row("mock-txn-10533", "TXN-2026-10533", "Laura Garcia", "R-1033", "3 Beds Apt, G-101", "Corporate Booking", "ACH Transfer", "Jun 7, 2026", "9:00 AM", "$300.00", "Pending", "pending"),
            self._mock_row("mock-txn-10532", "TXN-2026-10532", "Robert Wilson", "R-1032", "2 Beds Apt, Pool", "Vrbo", "VISA •••• 9009", "Jun 6, 2026", "3:15 PM", "$720.00", "Paid", "paid"),
        ]

    def _detail_payload(self, row, using_mock=False):
        if not row:
            return None
        if using_mock or row.get("is_mock"):
            return self._mock_detail_payload(row)

        invoice = row["_invoice"]
        deposits = row.get("_deposits", [])
        holds = row.get("_holds", [])
        linked_reservation = invoice.inquiry

        deposit_history = []
        for deposit in deposits:
            deposit_history.append(
                {
                    "label": "Damage deposit",
                    "amount": deposit.display_amount,
                    "status": deposit.get_status_display(),
                    "status_cls": self._deposit_status_class(deposit.status),
                    "meta": deposit.created_at.strftime("%b %-d, %Y") if deposit.created_at else "—",
                }
            )
        for hold in holds:
            deposit_history.append(
                {
                    "label": "Reservation payment hold",
                    "amount": hold.display_amount,
                    "status": hold.get_status_display(),
                    "status_cls": self._deposit_status_class(hold.status),
                    "meta": hold.created_at.strftime("%b %-d, %Y") if hold.created_at else "—",
                }
            )

        timeline = [
            {
                "label": "Invoice created",
                "meta": invoice.created_at.strftime("%b %-d, %Y · %-I:%M %p") if invoice.created_at else "—",
                "tone": "complete",
            },
        ]
        if holds:
            timeline.append(
                {
                    "label": "Reservation hold recorded",
                    "meta": holds[0].created_at.strftime("%b %-d, %Y · %-I:%M %p") if holds[0].created_at else "—",
                    "tone": "active",
                }
            )
        if deposits:
            timeline.append(
                {
                    "label": "Deposit workflow linked",
                    "meta": deposits[0].created_at.strftime("%b %-d, %Y · %-I:%M %p") if deposits[0].created_at else "—",
                    "tone": "active",
                }
            )
        timeline.append(
            {
                "label": f"Invoice {invoice.get_status_display().lower()}",
                "meta": invoice.updated_at.strftime("%b %-d, %Y · %-I:%M %p") if invoice.updated_at else "—",
                "tone": "complete" if invoice.status == InvoiceStatus.PAID else "pending",
            }
        )

        return {
            "transaction_id": row["transaction_id"],
            "status": row["status"],
            "status_cls": row["status_cls"],
            "amount": row["amount"],
            "date_label": row["date_label"],
            "time_label": row["time_label"],
            "invoice_number": invoice.invoice_number,
            "invoice_url": row["invoice_url"],
            "issue_date": invoice.issue_date.strftime("%b %-d, %Y") if invoice.issue_date else "—",
            "due_date": invoice.due_date.strftime("%b %-d, %Y") if invoice.due_date else "—",
            "amount_due": invoice.display_total,
            "linked_reservation": {
                "request_key": linked_reservation.request_key if linked_reservation else "—",
                "listing": linked_reservation.item.business_display_name if linked_reservation and linked_reservation.item else "—",
                "date_range": f"{linked_reservation.check_in:%b %-d} – {linked_reservation.check_out:%b %-d, %Y}" if linked_reservation and linked_reservation.check_in and linked_reservation.check_out else "—",
                "guest": linked_reservation.guest_name if linked_reservation else row["guest"],
                "url": reverse("bookings:ops-reservations") if linked_reservation else reverse("bookings:ops-reservations"),
            },
            "deposit_history": deposit_history or [{"label": "No linked deposit records", "amount": "—", "status": "Waiting", "status_cls": "pending", "meta": "Create one from Deposits"}],
            "timeline": timeline,
            "notes": invoice.notes or "Invoice, reservation payment hold, and deposit ledger are linked across Payments and Deposits.",
            "quick_actions": [
                {"label": "Send invoice", "url": row["invoice_url"]},
                {"label": "Mark as paid", "url": row["invoice_url"]},
                {"label": "Download receipt", "url": row["invoice_url"]},
                {"label": "Issue refund", "url": reverse("bookings:ops-deposits")},
                {"label": "Open reservation", "url": reverse("bookings:ops-reservations")},
            ],
        }

    @staticmethod
    def _money(cents):
        return f"${(cents or 0) / 100:,.2f}"

    @staticmethod
    def _payment_method_label(payment_record):
        if not payment_record:
            return "Direct invoice"
        if payment_record.payment_provider == DepositProvider.PAYPAL:
            return "PayPal"
        if isinstance(payment_record, ReservationPaymentHold):
            return "Card hold"
        return "Card on file"

    @staticmethod
    def _invoice_status_label(invoice):
        if invoice.status == InvoiceStatus.PAID:
            return "Paid"
        if invoice.status == InvoiceStatus.CANCELED:
            return "Refunded"
        return "Pending"

    @staticmethod
    def _invoice_status_class(invoice):
        if invoice.status == InvoiceStatus.PAID:
            return "paid"
        if invoice.status == InvoiceStatus.CANCELED:
            return "refunded"
        return "pending"

    @staticmethod
    def _deposit_status_class(status):
        if status in {DepositStatus.CAPTURED, DepositStatus.REQUIRES_CAPTURE}:
            return "paid"
        if status in {DepositStatus.CANCELED, DepositStatus.FAILED}:
            return "refunded"
        return "pending"

    @staticmethod
    def _mock_row(row_id, transaction_id, guest, reservation, listing, channel, method, date_label, time_label, amount, status, status_cls):
        return {
            "id": row_id,
            "transaction_id": transaction_id,
            "guest": guest,
            "reservation": reservation,
            "listing": listing,
            "channel": channel,
            "method": method,
            "date_label": date_label,
            "time_label": time_label,
            "amount": amount,
            "status": status,
            "status_cls": status_cls,
            "invoice_icon": "↗",
            "invoice_url": "#",
            "is_mock": True,
        }

    def _mock_detail_payload(self, row):
        return {
            "transaction_id": row["transaction_id"],
            "status": row["status"],
            "status_cls": row["status_cls"],
            "amount": row["amount"],
            "date_label": row["date_label"],
            "time_label": row["time_label"],
            "invoice_number": "INV-2026-3314",
            "invoice_url": "#",
            "issue_date": "Jun 12, 2026",
            "due_date": "Jun 12, 2026",
            "amount_due": row["amount"],
            "linked_reservation": {
                "request_key": row["reservation"],
                "listing": "3 Beds Apt, Vacation Home & Pool, G-101",
                "date_range": "Jun 8 – Jun 14, 2026 · 6 nights",
                "guest": row["guest"],
                "url": "/ops/reservations/",
            },
            "deposit_history": [
                {"label": "Deposit required (50%)", "amount": "$625.00", "status": "Paid", "status_cls": "paid", "meta": "Due: May 25, 2026"},
                {"label": "Remaining balance", "amount": "$625.00", "status": "Paid", "status_cls": "paid", "meta": "Due: Jun 12, 2026"},
            ],
            "timeline": [
                {"label": "Payment received", "meta": "$1,250.00 · Visa •••• 4242 · Jun 12, 2026 9:30 AM", "tone": "complete", "action_label": "Download receipt", "action_url": "#"},
                {"label": "Invoice sent", "meta": "INV-2026-3314 · Jun 12, 2026 9:28 AM", "tone": "active", "action_label": "", "action_url": ""},
                {"label": "Booking confirmed", "meta": "R-1042 · Jun 6, 2026 9:12 AM", "tone": "pending", "action_label": "Open reservation", "action_url": "/ops/reservations/"},
            ],
            "notes": "Direct booking via mladis.com.",
            "quick_actions": [
                {"label": "Send invoice", "url": "#"},
                {"label": "Mark as paid", "url": "#"},
                {"label": "Download receipt", "url": "#"},
                {"label": "Issue refund", "url": "#"},
                {"label": "Open reservation", "url": "/ops/reservations/"},
            ],
        }
