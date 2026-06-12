from decimal import Decimal
from datetime import datetime, time, timedelta
import hashlib
import re
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class BookingCategory(models.TextChoices):
    STAY = "stay", "Stay"
    EXPERIENCE = "experience", "Experience"
    SERVICE = "service", "Service"
    TRANSPORT = "transport", "Transport"


class BookingStatus(models.TextChoices):
    NEW = "new", "New"
    REVIEWING = "reviewing", "Reviewing"
    QUOTED = "quoted", "Quoted"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELED = "canceled", "Canceled"
    DECLINED = "declined", "Declined"


class ClientSegment(models.TextChoices):
    FAVORITE = "favorite", "Favorite"
    VIP = "vip", "VIP"
    AVERAGE = "average", "Average"
    BLACKLISTED = "blacklisted", "Blacklisted"


class ContactSource(models.TextChoices):
    DIRECT = "direct", "Direct booking"
    AIRBNB = "airbnb", "Airbnb"
    SOCIAL = "social", "Social login"
    MANUAL = "manual", "Manual entry"


class MarketingConsentStatus(models.TextChoices):
    UNKNOWN = "unknown", "Unknown"
    REQUESTED = "requested", "Requested"
    OPTED_IN = "opted_in", "Opted in"
    OPTED_OUT = "opted_out", "Opted out"


class CouponDiscountType(models.TextChoices):
    FIXED = "fixed", "Fixed amount"
    PERCENT = "percent", "Percentage"


class EmailDeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    PAID = "paid", "Paid"
    CANCELED = "canceled", "Canceled"


class PromotionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class DepositProvider(models.TextChoices):
    STRIPE = "stripe", "Stripe"
    PAYPAL = "paypal", "PayPal"


class DepositStatus(models.TextChoices):
    NEW = "new", "New"
    REQUIRES_CONFIGURATION = "requires_configuration", "Requires payment configuration"
    CHECKOUT_CREATED = "checkout_created", "Checkout created"
    REQUIRES_CAPTURE = "requires_capture", "Authorized"
    CAPTURED = "captured", "Captured"
    CANCELED = "canceled", "Canceled"
    FAILED = "failed", "Failed"


class DonationStatus(models.TextChoices):
    NEW = "new", "New"
    REQUIRES_CONFIGURATION = "requires_configuration", "Requires Stripe configuration"
    CHECKOUT_CREATED = "checkout_created", "Checkout created"
    PAID = "paid", "Paid"
    CANCELED = "canceled", "Canceled"
    FAILED = "failed", "Failed"


class MaintenanceWorkType(models.TextChoices):
    CLEANING = "cleaning", "Cleaning"
    REPAIR = "repair", "Repair"
    REPLACEMENT = "replacement", "Replacement"
    INSPECTION = "inspection", "Inspection"
    SUPPLIES = "supplies", "Supplies"
    PENALTY = "penalty", "Penalty"
    OTHER = "other", "Other"


class MaintenanceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    LOGGED = "logged", "Logged"
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    DOCUMENTED = "documented", "Documented"
    BILLED = "billed", "Billed"
    ARCHIVED = "archived", "Archived"


class MaintenancePaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "Unpaid"
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    REIMBURSED = "reimbursed", "Reimbursed"
    DISPUTED = "disputed", "Disputed"


class AgentKnowledgeSourceType(models.TextChoices):
    INLINE = "inline", "Inline text"
    REPO_FILE = "repo_file", "Repo file"
    URL = "url", "Public URL or GitHub link"


class AgentFAQCategory(models.TextChoices):
    AVAILABILITY = "availability", "Availability"
    BOOKING = "booking", "Booking"
    CONTACT = "contact", "Contact"
    DEPOSIT = "deposit", "Deposit"
    PAYMENT = "payment", "Payment"
    PRICING = "pricing", "Pricing"
    RULES = "rules", "Rules"
    AGENT_SCOPE = "agent_scope", "Agent scope"
    GENERAL = "general", "General"


def format_stay_display_name(value, *, separator=", "):
    clean = re.sub(r"\s+", " ", value or "").strip()
    clean = re.sub(r"^MLADIS\s*[-–—]\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bBedrooms?\b", "Beds", clean, flags=re.IGNORECASE)
    unit_match = re.search(r"\b([A-Z])[-\s]?(\d{3}|All)\b", clean, flags=re.IGNORECASE)
    bed_match = re.search(r"\b(\d+)\s+Beds?\b", clean, flags=re.IGNORECASE)
    title = re.sub(r"\b[A-Z][-\s]?(?:\d{3}|All)\b", "", clean, flags=re.IGNORECASE)
    title = re.sub(r"\b\d+\s+Beds?\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\(?\bapartments?\b\)?", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*[-–—]\s*", " ", title)
    title = re.sub(r"\s+", " ", title).strip() or "Vacation Home & Pool"
    if not bed_match:
        return clean
    property_type = "Apts" if bed_match.group(1) == "6" and not unit_match else "Apt"
    unit = ""
    if unit_match:
        unit = f"{unit_match.group(1).upper()}-{unit_match.group(2)}"
    return separator.join(part for part in [f"{bed_match.group(1)} Beds {property_type}", title, unit] if part)


class CancellationPolicy(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    allow_guest_cancellation = models.BooleanField(default=True)
    hours_before_check_in = models.PositiveSmallIntegerField(default=24)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "name"]
        verbose_name_plural = "cancellation policies"

    def __str__(self):
        return self.business_display_name

    @property
    def business_display_name(self):
        return format_stay_display_name(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        if self.is_default:
            CancellationPolicy.objects.exclude(pk=self.pk).update(is_default=False)

    @classmethod
    def default(cls):
        return cls.objects.filter(is_active=True, is_default=True).first() or cls.objects.filter(
            is_active=True
        ).first()

    def can_cancel(self, check_in, at_time=None):
        if not self.allow_guest_cancellation or not check_in:
            return False
        at_time = at_time or timezone.now()
        check_in_start = timezone.make_aware(datetime.combine(check_in, time.min), timezone.get_current_timezone())
        deadline = check_in_start - timedelta(hours=self.hours_before_check_in)
        return at_time <= deadline


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=180, blank=True)
    discount_type = models.CharField(
        max_length=12,
        choices=CouponDiscountType.choices,
        default=CouponDiscountType.FIXED,
    )
    amount_cents = models.PositiveIntegerField(default=0)
    percent_off = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=3, default="usd")
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_redemptions = models.PositiveIntegerField(null=True, blank=True)
    redemption_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.currency = self.currency.lower()
        super().save(*args, **kwargs)

    def is_valid(self, at_time=None):
        if not self.is_active:
            return False
        at_time = at_time or timezone.now()
        if self.starts_at and at_time < self.starts_at:
            return False
        if self.expires_at and at_time > self.expires_at:
            return False
        if self.max_redemptions is not None and self.redemption_count >= self.max_redemptions:
            return False
        return True

    def discount_for(self, subtotal_cents):
        if subtotal_cents <= 0:
            return 0
        if self.discount_type == CouponDiscountType.PERCENT:
            discount = int((Decimal(subtotal_cents) * self.percent_off / Decimal("100")).quantize(Decimal("1")))
            return min(discount, subtotal_cents)
        return min(self.amount_cents, subtotal_cents)


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=160, blank=True)
    email = models.EmailField(db_index=True, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    segment = models.CharField(
        max_length=24,
        choices=ClientSegment.choices,
        default=ClientSegment.AVERAGE,
    )
    source = models.CharField(
        max_length=24,
        choices=ContactSource.choices,
        default=ContactSource.DIRECT,
    )
    marketing_consent_status = models.CharField(
        max_length=24,
        choices=MarketingConsentStatus.choices,
        default=MarketingConsentStatus.UNKNOWN,
    )
    marketing_consent_requested_at = models.DateTimeField(null=True, blank=True)
    marketing_consent_at = models.DateTimeField(null=True, blank=True)
    marketing_consent_source = models.CharField(max_length=120, blank=True)
    preferred_language = models.CharField(max_length=8, default="en")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["segment", "email", "name"]

    def __str__(self):
        return self.name or self.email or f"Customer {self.pk}"

    @property
    def is_blacklisted(self):
        return self.segment == ClientSegment.BLACKLISTED

    @property
    def can_receive_promotions(self):
        return self.marketing_consent_status == MarketingConsentStatus.OPTED_IN and bool(self.email)

    @classmethod
    def find_or_create_for_email(cls, email, defaults=None):
        normalized = (email or "").strip().lower()
        defaults = defaults or {}
        if not normalized:
            return None
        profile = cls.objects.filter(email__iexact=normalized).first()
        if profile:
            changed = []
            for field, value in defaults.items():
                if value and not getattr(profile, field):
                    setattr(profile, field, value)
                    changed.append(field)
            if changed:
                profile.save(update_fields=changed + ["updated_at"])
            return profile
        return cls.objects.create(email=normalized, **defaults)


class AirbnbGuestRecord(models.Model):
    customer_profile = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        related_name="airbnb_guest_records",
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        "BookableItem",
        on_delete=models.SET_NULL,
        related_name="airbnb_guest_records",
        null=True,
        blank=True,
    )
    guest_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    listing_title = models.CharField(max_length=240, blank=True)
    airbnb_listing_id = models.CharField(max_length=40, blank=True)
    airbnb_thread_url = models.URLField(max_length=600, blank=True)
    source_message_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    source_email_subject = models.CharField(max_length=300, blank=True)
    source_email_timestamp = models.DateTimeField(null=True, blank=True)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    guests = models.PositiveSmallIntegerField(null=True, blank=True)
    message_excerpt = models.TextField(blank=True)
    feedback_summary = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    permission_notes = models.TextField(
        blank=True,
        help_text="Track how we can contact this Airbnb guest and whether they gave permission for future offers.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-check_in", "guest_name"]
        verbose_name = "Airbnb guest record"
        verbose_name_plural = "Airbnb guest records"

    def __str__(self):
        return f"{self.guest_name} - {self.listing_title or self.airbnb_listing_id or 'Airbnb'}"

    @property
    def stay_dates(self):
        if self.check_in and self.check_out:
            return f"{self.check_in} to {self.check_out}"
        if self.check_in:
            return str(self.check_in)
        return ""


class AdminAccess(models.Model):
    name = models.CharField(max_length=160)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    grant_staff_access = models.BooleanField(default=True)
    grant_superuser_access = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "email"]
        verbose_name = "admin access"
        verbose_name_plural = "admin access"

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.name} <{self.email}> ({status})"

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)


class BookableItem(models.Model):
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    category = models.CharField(
        max_length=24,
        choices=BookingCategory.choices,
        default=BookingCategory.STAY,
    )
    short_description = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    marketing_headline = models.CharField(max_length=180, blank=True)
    marketing_description = models.TextField(blank=True)
    location_label = models.CharField(max_length=160, blank=True)
    image = models.CharField(max_length=240, blank=True)
    image_alt = models.CharField(max_length=180, blank=True)
    starting_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    price_unit = models.CharField(max_length=40, default="night")
    max_guests = models.PositiveSmallIntegerField(null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    beds = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    bathroom_label = models.CharField(max_length=80, blank=True)
    airbnb_listing_id = models.CharField(max_length=40, blank=True)
    airbnb_url = models.URLField(blank=True)
    airbnb_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    review_count = models.PositiveSmallIntegerField(null=True, blank=True)
    rating_accuracy = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    rating_checkin = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    rating_cleanliness = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    rating_communication = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    rating_location = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    rating_value = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.business_display_name

    @property
    def business_display_name(self):
        return format_stay_display_name(self.name)

    def get_absolute_url(self):
        if self.category == BookingCategory.STAY:
            return reverse("bookings:stay-detail", kwargs={"slug": self.slug})
        return reverse("bookings:home") + f"#item-{self.slug}"

    @property
    def headline_price(self):
        if self.starting_price is None:
            return "Quote based"
        return f"From ${self.starting_price:,.0f}/{self.price_unit}"

    @property
    def public_booking_url(self):
        return self.airbnb_url or self.get_absolute_url()

    @property
    def airbnb_embed_url(self):
        if self.airbnb_url:
            return self.airbnb_url
        if self.airbnb_listing_id:
            return f"https://www.airbnb.com/rooms/{self.airbnb_listing_id}?guests=1&adults=1&s=66&source=embed_widget"
        return ""

    @property
    def airbnb_embed_summary(self):
        if "Santo Domingo" in self.location_label:
            parts = ["Vacation home in Santo Domingo"]
        else:
            parts = [self.name]
        if self.airbnb_rating:
            parts.append(f"★{self.airbnb_rating}")
        parts.extend(self.stat_list)
        return " · ".join(parts)

    @property
    def stat_list(self):
        stats = []
        if self.max_guests:
            stats.append(f"{self.max_guests} guests")
        if self.bedrooms:
            stats.append(f"{self.bedrooms} bedrooms")
        if self.beds:
            stats.append(f"{self.beds} beds")
        if self.bathroom_label:
            stats.append(self.bathroom_label)
        elif self.bathrooms:
            stats.append(f"{self.bathrooms:g} baths")
        return stats

    @property
    def review_label(self):
        if self.airbnb_rating and self.review_count:
            return f"{self.airbnb_rating} from {self.review_count} Airbnb reviews"
        if self.airbnb_rating:
            return f"{self.airbnb_rating} Airbnb rating"
        return "Airbnb listing"

    @property
    def rating_breakdown(self):
        ratings = [
            ("Accuracy", self.rating_accuracy),
            ("Check-in", self.rating_checkin),
            ("Cleanliness", self.rating_cleanliness),
            ("Communication", self.rating_communication),
            ("Location", self.rating_location),
            ("Value", self.rating_value),
        ]
        return [(label, rating) for label, rating in ratings if rating is not None]


class CustomerFeedback(models.Model):
    customer_profile = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        related_name="feedback_entries",
        null=True,
        blank=True,
    )
    airbnb_guest_record = models.OneToOneField(
        AirbnbGuestRecord,
        on_delete=models.CASCADE,
        related_name="customer_feedback",
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.SET_NULL,
        related_name="customer_feedback_entries",
        null=True,
        blank=True,
    )
    source = models.CharField(
        max_length=24,
        choices=ContactSource.choices,
        default=ContactSource.DIRECT,
    )
    source_label = models.CharField(max_length=120, default="Website feedback")
    source_url = models.URLField(max_length=1000, blank=True)
    guest_name = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    feedback_text = models.TextField()
    feedback_summary = models.TextField(blank=True)
    permission_notes = models.TextField(blank=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Only publish exact feedback when we have permission to display it publicly.",
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "customer feedback"
        verbose_name_plural = "customer feedback"

    def __str__(self):
        label = self.guest_name or (self.customer_profile.name if self.customer_profile else "Guest")
        return f"{label} feedback"

    @classmethod
    def sync_from_airbnb_record(cls, record):
        feedback_text = (record.feedback_summary or record.message_excerpt or "").strip()
        if not feedback_text and record.rating is None:
            return None

        profile = record.customer_profile
        defaults = {
            "customer_profile": profile,
            "item": record.item,
            "source": ContactSource.AIRBNB,
            "source_label": "Airbnb message import",
            "source_url": record.airbnb_thread_url,
            "guest_name": record.guest_name,
            "email": record.email or (profile.email if profile else ""),
            "phone": record.phone or (profile.phone if profile else ""),
            "rating": record.rating,
            "feedback_text": feedback_text or "Airbnb rating captured without written feedback.",
            "feedback_summary": record.feedback_summary,
            "permission_notes": record.permission_notes,
        }
        feedback, _created = cls.objects.update_or_create(
            airbnb_guest_record=record,
            defaults=defaults,
        )
        return feedback


class GuestReviewHighlight(models.Model):
    item = models.ForeignKey(BookableItem, on_delete=models.CASCADE, related_name="guest_review_highlights")
    title = models.CharField(max_length=100)
    body = models.CharField(max_length=260)
    source_label = models.CharField(max_length=120, default="Airbnb review signal")
    source_url = models.URLField(blank=True, max_length=1000)
    is_paraphrased = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["item", "sort_order", "id"]

    def __str__(self):
        return f"{self.item.name}: {self.title}"


class HouseRule(models.Model):
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.CASCADE,
        related_name="house_rules",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=260)
    source_label = models.CharField(max_length=120, blank=True)
    source_url = models.URLField(blank=True, max_length=1000)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["item", "sort_order", "title"]

    def __str__(self):
        scope = self.item.name if self.item else "All stays"
        return f"{scope}: {self.title}"


class StayGalleryImage(models.Model):
    item = models.ForeignKey(BookableItem, on_delete=models.CASCADE, related_name="gallery_images")
    image_url = models.URLField(max_length=1000)
    alt_text = models.CharField(max_length=180)
    caption = models.CharField(max_length=160, blank=True)
    is_demo = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["item", "sort_order", "id"]

    def __str__(self):
        return f"{self.item.name} image {self.sort_order}"


class ReviewTheme(models.Model):
    item = models.ForeignKey(BookableItem, on_delete=models.CASCADE, related_name="review_themes")
    label = models.CharField(max_length=80)
    description = models.CharField(max_length=180)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["item", "sort_order", "label"]

    def __str__(self):
        return f"{self.item.name}: {self.label}"


class BookingInquiry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="booking_inquiries",
        null=True,
        blank=True,
    )
    customer_profile = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        related_name="booking_inquiries",
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.SET_NULL,
        related_name="inquiries",
        null=True,
        blank=True,
    )
    guest_name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1)
    message = models.TextField(blank=True)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        related_name="booking_inquiries",
        null=True,
        blank=True,
    )
    coupon_code = models.CharField(max_length=40, blank=True)
    cancellation_policy = models.ForeignKey(
        CancellationPolicy,
        on_delete=models.SET_NULL,
        related_name="booking_inquiries",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=24,
        choices=BookingStatus.choices,
        default=BookingStatus.NEW,
    )
    subtotal_cents = models.PositiveIntegerField(default=0)
    discount_cents = models.PositiveIntegerField(default=0)
    deposit_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="usd")
    is_admin_test = models.BooleanField(default=False)
    is_blacklist_flagged = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_delivery_status = models.CharField(
        max_length=24,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.PENDING,
    )
    email_error = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        item_name = self.item.business_display_name if self.item else "Any booking"
        return f"{self.guest_name} - {item_name}"

    @property
    def request_key(self):
        if not self.pk:
            return "MLADIS-REQ-PENDING"
        created = self.created_at or timezone.now()
        return f"MLADIS-REQ-{created:%Y%m%d}-{self.pk:06d}"

    @property
    def nights(self):
        if not self.check_in or not self.check_out:
            return 0
        return max((self.check_out - self.check_in).days, 0)

    @property
    def display_subtotal(self):
        return self._display_money(self.subtotal_cents)

    @property
    def display_discount(self):
        return self._display_money(self.discount_cents)

    @property
    def display_deposit(self):
        return self._display_money(self.deposit_cents)

    @property
    def display_total(self):
        return self._display_money(self.total_cents)

    @property
    def reservation_payment_cents(self):
        return max(self.subtotal_cents - self.discount_cents, 0)

    @property
    def display_reservation_payment(self):
        return self._display_money(self.reservation_payment_cents)

    @property
    def can_customer_cancel(self):
        if self.status in {BookingStatus.CANCELED, BookingStatus.DECLINED}:
            return False
        policy = self.cancellation_policy or CancellationPolicy.default()
        return bool(policy and policy.can_cancel(self.check_in))

    def cancel(self, reason="", by_user=None):
        self.status = BookingStatus.CANCELED
        self.canceled_at = timezone.now()
        self.cancellation_reason = reason
        update_fields = ["status", "canceled_at", "cancellation_reason", "updated_at"]
        if by_user and not self.user_id:
            self.user = by_user
            update_fields.append("user")
        self.save(update_fields=update_fields)

    def _display_money(self, cents):
        return f"${cents / 100:,.2f} {self.currency.upper()}"


class AvailabilityBlock(models.Model):
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.CASCADE,
        related_name="availability_blocks",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item__name", "start_date", "end_date", "id"]

    def __str__(self):
        return f"{self.item.name}: {self.start_date} to {self.end_date}"

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date must be on or after start date."})


class DailyPriceOverride(models.Model):
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.CASCADE,
        related_name="daily_price_overrides",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    nightly_price = models.DecimalField(max_digits=8, decimal_places=2)
    label = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item__name", "start_date", "end_date", "id"]

    def __str__(self):
        return f"{self.item.name}: ${self.nightly_price:,.2f} from {self.start_date} to {self.end_date}"

    def clean(self):
        errors = {}
        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors["end_date"] = "End date must be on or after start date."
        if self.nightly_price is not None and self.nightly_price < 0:
            errors["nightly_price"] = "Nightly price must be zero or greater."
        if errors:
            raise ValidationError(errors)


def maintenance_upload_path(instance, filename):
    event_id = instance.event_id or "pending"
    clean_name = slugify(str(filename).rsplit("/", 1)[-1].rsplit(".", 1)[0]) or "photo"
    extension = ""
    if "." in filename:
        extension = "." + filename.rsplit(".", 1)[-1].lower()
    return f"maintenance/events/{event_id}/{uuid4().hex}-{clean_name}{extension}"


class MaintenanceEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.PROTECT,
        related_name="maintenance_events",
    )
    booking = models.ForeignKey(
        BookingInquiry,
        on_delete=models.SET_NULL,
        related_name="maintenance_events",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    work_type = models.CharField(
        max_length=24,
        choices=MaintenanceWorkType.choices,
        default=MaintenanceWorkType.CLEANING,
    )
    status = models.CharField(
        max_length=24,
        choices=MaintenanceStatus.choices,
        default=MaintenanceStatus.COMPLETED,
    )
    cost_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cost_currency = models.CharField(max_length=3, default="USD")
    reported_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    timezone_name = models.CharField(max_length=64, default="America/Santo_Domingo")
    vendor_name = models.CharField(max_length=160, blank=True)
    vendor_contact = models.CharField(max_length=160, blank=True)
    invoice_number = models.CharField(max_length=80, blank=True)
    proof_of_payment_ref = models.CharField(max_length=180, blank=True)
    payment_status = models.CharField(
        max_length=24,
        choices=MaintenancePaymentStatus.choices,
        default=MaintenancePaymentStatus.PENDING,
    )
    tax_category_code = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    ai_description = models.TextField(blank=True)
    ai_description_generated_at = models.DateTimeField(null=True, blank=True)
    ai_description_model = models.CharField(max_length=120, blank=True)
    ai_description_metadata = models.JSONField(default=dict, blank=True)
    use_ai_description = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_maintenance_events",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_maintenance_events",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reported_at", "-created_at"]
        verbose_name = "maintenance event"
        verbose_name_plural = "maintenance events"

    def __str__(self):
        return f"{self.title} - {self.item.business_display_name}"

    def clean(self):
        errors = {}
        if self.cost_amount is not None and self.cost_amount < 0:
            errors["cost_amount"] = "Cost must be zero or greater."
        currency = (self.cost_currency or "").strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            errors["cost_currency"] = "Use a three-letter currency code such as USD."
        else:
            self.cost_currency = currency
        if self.started_at and self.completed_at and self.completed_at < self.started_at:
            errors["completed_at"] = "Completed time must be after started time."
        if self.payment_status in {MaintenancePaymentStatus.PAID, MaintenancePaymentStatus.REIMBURSED}:
            if not (self.proof_of_payment_ref or self.invoice_number):
                errors["proof_of_payment_ref"] = "Paid or reimbursed maintenance needs a receipt, invoice, or payment reference."
        if self.booking_id and self.item_id and self.booking and self.booking.item_id and self.booking.item_id != self.item_id:
            errors["booking"] = "Linked booking must belong to the selected stay."
        if errors:
            raise ValidationError(errors)

    @property
    def duration_minutes(self):
        if not self.started_at or not self.completed_at:
            return None
        return max(int((self.completed_at - self.started_at).total_seconds() // 60), 0)

    @property
    def money(self):
        return {
            "amount": str(self.cost_amount),
            "currency": self.cost_currency,
            "display": self.display_cost,
        }

    @property
    def time_window(self):
        return {
            "reported_at": self.reported_at.isoformat() if self.reported_at else "",
            "started_at": self.started_at.isoformat() if self.started_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "duration_minutes": self.duration_minutes,
            "timezone": self.timezone_name,
        }

    @property
    def display_cost(self):
        return f"${self.cost_amount:,.2f} {self.cost_currency}"

    @property
    def photo_count(self):
        if not self.pk:
            return 0
        return self.photos.count()

    @property
    def is_tax_ready(self):
        return bool(
            self.title
            and self.cost_amount is not None
            and self.reported_at
            and self.photo_count
            and (self.effective_description or self.invoice_number or self.proof_of_payment_ref)
        )

    @property
    def effective_description(self):
        if self.use_ai_description and self.ai_description:
            return self.ai_description
        return self.description or self.ai_description

    def to_agent_payload(self):
        booking = self.booking
        return {
            "maintenance_event_id": str(self.pk),
            "title": self.title,
            "work_type": self.work_type,
            "work_type_label": self.get_work_type_display(),
            "status": self.status,
            "status_label": self.get_status_display(),
            "property": {
                "id": self.item_id,
                "name": self.item.business_display_name if self.item else "",
                "slug": self.item.slug if self.item else "",
            },
            "booking_request_id": self.booking_id,
            "reservation": {
                "id": booking.pk if booking else None,
                "request_key": booking.request_key if booking else "",
                "guest_name": booking.guest_name if booking else "",
                "guest_email": booking.email if booking else "",
                "status": booking.status if booking else "",
                "status_label": booking.get_status_display() if booking else "",
                "check_in": booking.check_in.isoformat() if booking and booking.check_in else "",
                "check_out": booking.check_out.isoformat() if booking and booking.check_out else "",
                "nights": booking.nights if booking else 0,
                "guests": booking.guests if booking else 0,
                "reservation_total": booking.display_total if booking else "",
            },
            "cost": self.money,
            "time": self.time_window,
            "vendor": {
                "name": self.vendor_name,
                "contact": self.vendor_contact,
            },
            "payment": {
                "status": self.payment_status,
                "status_label": self.get_payment_status_display(),
                "invoice_number": self.invoice_number,
                "proof_reference": self.proof_of_payment_ref,
                "tax_category_code": self.tax_category_code,
            },
            "description": self.effective_description,
            "work_description": {
                "active": "ai" if self.use_ai_description and self.ai_description else "manual",
                "manual": self.description,
                "ai": self.ai_description,
                "ai_generated_at": self.ai_description_generated_at.isoformat() if self.ai_description_generated_at else "",
                "ai_model": self.ai_description_model,
                "ai_metadata": self.ai_description_metadata,
                "use_ai_description": self.use_ai_description,
            },
            "admin_notes": self.admin_notes,
            "created_by_id": self.created_by_id,
            "approved_by_id": self.approved_by_id,
            "is_tax_ready": self.is_tax_ready,
            "pictures": [photo.to_agent_payload() for photo in self.photos.all()],
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }


class MaintenancePhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.ForeignKey(
        MaintenanceEvent,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.FileField(upload_to=maintenance_upload_path)
    caption = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_cover = models.BooleanField(default=False)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    file_size_bytes = models.PositiveIntegerField(default=0)
    captured_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["event", "sort_order", "uploaded_at"]
        verbose_name = "maintenance photo"
        verbose_name_plural = "maintenance photos"

    def __str__(self):
        return self.caption or f"Photo for {self.event.title}"

    def save(self, *args, **kwargs):
        if self.image:
            self.file_size_bytes = getattr(self.image, "size", self.file_size_bytes) or self.file_size_bytes
            content_type = getattr(self.image.file, "content_type", "") or getattr(self.image, "content_type", "")
            if content_type and not self.mime_type:
                self.mime_type = content_type
            if not self.checksum_sha256:
                self.checksum_sha256 = self._checksum()
        super().save(*args, **kwargs)

    @property
    def image_url(self):
        try:
            return self.image.url
        except ValueError:
            return ""

    def _checksum(self):
        digest = hashlib.sha256()
        position = None
        if hasattr(self.image, "tell") and hasattr(self.image, "seek"):
            position = self.image.tell()
            self.image.seek(0)
        for chunk in self.image.chunks():
            digest.update(chunk)
        if position is not None:
            self.image.seek(position)
        return digest.hexdigest()

    def to_agent_payload(self):
        return {
            "photo_id": str(self.pk),
            "url": self.image_url,
            "caption": self.caption,
            "sort_order": self.sort_order,
            "is_cover": self.is_cover,
            "checksum_sha256": self.checksum_sha256,
            "mime_type": self.mime_type,
            "file_size_bytes": self.file_size_bytes,
            "captured_at": self.captured_at.isoformat() if self.captured_at else "",
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else "",
        }


class DamageDeposit(models.Model):
    inquiry = models.ForeignKey(
        BookingInquiry,
        on_delete=models.SET_NULL,
        related_name="damage_deposits",
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.SET_NULL,
        related_name="damage_deposits",
        null=True,
        blank=True,
    )
    guest_name = models.CharField(max_length=160)
    email = models.EmailField()
    amount_cents = models.PositiveIntegerField(default=20000)
    currency = models.CharField(max_length=3, default="usd")
    payment_provider = models.CharField(
        max_length=20,
        choices=DepositProvider.choices,
        default=DepositProvider.STRIPE,
    )
    status = models.CharField(
        max_length=32,
        choices=DepositStatus.choices,
        default=DepositStatus.NEW,
    )
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    paypal_order_id = models.CharField(max_length=255, blank=True)
    paypal_authorization_id = models.CharField(max_length=255, blank=True)
    checkout_url = models.URLField(blank=True, max_length=1000)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        item_name = self.item.name if self.item else "booking"
        return f"{self.display_amount} deposit for {item_name}"

    @property
    def amount(self):
        return self.amount_cents / 100

    @property
    def display_amount(self):
        return f"${self.amount:,.0f} {self.currency.upper()}"


class ReservationPaymentHold(models.Model):
    inquiry = models.ForeignKey(
        BookingInquiry,
        on_delete=models.SET_NULL,
        related_name="payment_holds",
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.SET_NULL,
        related_name="payment_holds",
        null=True,
        blank=True,
    )
    guest_name = models.CharField(max_length=160)
    email = models.EmailField()
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="usd")
    payment_provider = models.CharField(
        max_length=20,
        choices=DepositProvider.choices,
        default=DepositProvider.STRIPE,
    )
    status = models.CharField(
        max_length=32,
        choices=DepositStatus.choices,
        default=DepositStatus.NEW,
    )
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    checkout_url = models.URLField(blank=True, max_length=1000)
    capture_after = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "reservation payment hold"
        verbose_name_plural = "reservation payment holds"

    def __str__(self):
        item_name = self.item.business_display_name if self.item else "booking"
        return f"{self.display_amount} reservation hold for {item_name}"

    @property
    def amount(self):
        return self.amount_cents / 100

    @property
    def display_amount(self):
        return f"${self.amount:,.0f} {self.currency.upper()}"


class MissionCause(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Donation(models.Model):
    cause = models.ForeignKey(
        MissionCause,
        on_delete=models.SET_NULL,
        related_name="donations",
        null=True,
        blank=True,
    )
    donor_name = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="usd")
    status = models.CharField(
        max_length=32,
        choices=DonationStatus.choices,
        default=DonationStatus.NEW,
    )
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    checkout_url = models.URLField(blank=True, max_length=1000)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        cause_name = self.cause.name if self.cause else "MLADIS mission"
        return f"{self.display_amount} donation to {cause_name}"

    @property
    def amount(self):
        return self.amount_cents / 100

    @property
    def display_amount(self):
        return f"${self.amount:,.0f} {self.currency.upper()}"


class Invoice(models.Model):
    inquiry = models.ForeignKey(
        BookingInquiry,
        on_delete=models.SET_NULL,
        related_name="invoices",
        null=True,
        blank=True,
    )
    customer_profile = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        related_name="invoices",
        null=True,
        blank=True,
    )
    invoice_number = models.CharField(max_length=40, unique=True, blank=True)
    public_token = models.UUIDField(default=uuid4, editable=False, unique=True)
    recipient_name = models.CharField(max_length=160)
    recipient_email = models.EmailField()
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="usd")
    subtotal_cents = models.PositiveIntegerField(default=0)
    discount_cents = models.PositiveIntegerField(default=0)
    deposit_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    logo_snapshot_url = models.URLField(blank=True, max_length=1000)
    notes = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    email_status = models.CharField(
        max_length=24,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.PENDING,
    )
    email_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.invoice_number or f"Invoice {self.pk}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"MLD-{timezone.now():%Y%m%d}-{uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def display_total(self):
        return f"${self.total_cents / 100:,.2f} {self.currency.upper()}"

    @property
    def display_subtotal(self):
        return f"${self.subtotal_cents / 100:,.2f} {self.currency.upper()}"

    @property
    def display_discount(self):
        return f"${self.discount_cents / 100:,.2f} {self.currency.upper()}"

    @property
    def display_deposit(self):
        return f"${self.deposit_cents / 100:,.2f} {self.currency.upper()}"

    def recalculate_totals(self, save=True):
        subtotal = sum(line.amount_cents for line in self.line_items.all())
        self.subtotal_cents = subtotal
        self.total_cents = max(subtotal - self.discount_cents + self.deposit_cents, 0)
        if save:
            self.save(update_fields=["subtotal_cents", "total_cents", "updated_at"])


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="line_items")
    description = models.CharField(max_length=180)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("1.00"))
    unit_amount_cents = models.PositiveIntegerField(default=0)
    amount_cents = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["invoice", "sort_order", "id"]

    def __str__(self):
        return self.description

    @property
    def display_amount(self):
        return f"${self.amount_cents / 100:,.2f} {self.invoice.currency.upper()}"

    def save(self, *args, **kwargs):
        if not self.amount_cents:
            self.amount_cents = int(self.quantity * self.unit_amount_cents)
        super().save(*args, **kwargs)


class ExtraBillTemplate(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=240)
    default_amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="usd")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Promotion(models.Model):
    title = models.CharField(max_length=140)
    subject = models.CharField(max_length=180)
    message = models.TextField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, related_name="promotions", null=True, blank=True)
    target_segment = models.CharField(
        max_length=24,
        choices=[("all", "All clients"), *ClientSegment.choices],
        default="all",
    )
    status = models.CharField(max_length=20, choices=PromotionStatus.choices, default=PromotionStatus.DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_promotions",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class PromotionRecipient(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="recipients")
    customer_profile = models.ForeignKey(
        CustomerProfile,
        on_delete=models.SET_NULL,
        related_name="promotion_recipients",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=160, blank=True)
    email = models.EmailField()
    status = models.CharField(
        max_length=24,
        choices=EmailDeliveryStatus.choices,
        default=EmailDeliveryStatus.PENDING,
    )
    error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["promotion", "email"]

    def __str__(self):
        return f"{self.email} for {self.promotion}"


class CalendarFeed(models.Model):
    item = models.OneToOneField(BookableItem, on_delete=models.CASCADE, related_name="calendar_feed")
    airbnb_ical_url = models.URLField(blank=True, max_length=1000)
    google_calendar_name = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item__name"]

    def __str__(self):
        return f"Calendar feed for {self.item.name}"

    @property
    def is_configured(self):
        return bool(self.airbnb_ical_url)


class AgentConversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="agent_conversations",
        null=True,
        blank=True,
    )
    session_id = models.CharField(max_length=80, db_index=True)
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.SET_NULL,
        related_name="agent_conversations",
        null=True,
        blank=True,
    )
    visitor_name = models.CharField(max_length=160, blank=True)
    visitor_email = models.EmailField(blank=True)
    last_user_message = models.TextField()
    last_agent_reply = models.TextField()
    question_topic = models.CharField(max_length=80, default="general")
    language = models.CharField(max_length=8, default="en")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Agent conversation {self.session_id}"


class PageVisit(models.Model):
    path = models.CharField(max_length=500)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="page_visits",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=80, blank=True, db_index=True)
    language = models.CharField(max_length=8, default="en")
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.path


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=80, default="MLADIS LLC")
    logo = models.FileField(upload_to="site/", blank=True)
    logo_url = models.URLField(blank=True, max_length=1000)
    contact_email = models.EmailField(blank=True)
    request_notifications_email = models.BooleanField(
        default=True,
        help_text="Send new reservation requests to admin email recipients.",
    )
    request_notifications_sms = models.BooleanField(
        default=False,
        help_text="Future channel flag. Requires an SMS provider before messages can be sent.",
    )
    request_notifications_whatsapp = models.BooleanField(
        default=False,
        help_text="Future channel flag. Requires a WhatsApp provider before messages can be sent.",
    )
    public_address_label = models.CharField(
        max_length=220,
        default="Santo Domingo Norte, Dominican Republic",
    )
    agent_question_limit = models.PositiveSmallIntegerField(
        default=5,
        help_text="Maximum public agent questions per signed-in user. Use 0 for unlimited.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.site_name

    def uploaded_logo_is_displayable(self):
        if not self.logo:
            return False

        name = self.logo.name.lower()
        if "test-logo" in name:
            return False
        try:
            if not self.logo.storage.exists(self.logo.name):
                return False
            with self.logo.storage.open(self.logo.name, "rb") as logo_file:
                header = logo_file.read(512)
        except (OSError, ValueError):
            return False

        if not header:
            return False
        if name.endswith(".svg"):
            return b"<svg" in header.lower()
        if header.startswith((b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a")):
            return True
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"

    @property
    def logo_display_url(self):
        if self.uploaded_logo_is_displayable():
            return self.logo.url
        return self.logo_url

    @classmethod
    def current(cls):
        settings_obj, _created = cls.objects.get_or_create(pk=1)
        return settings_obj


class AgentFAQ(models.Model):
    category = models.CharField(
        max_length=80,
        choices=AgentFAQCategory.choices,
        default=AgentFAQCategory.GENERAL,
        blank=True,
    )
    question = models.CharField(max_length=240, unique=True)
    answer = models.TextField()
    keywords = models.CharField(
        max_length=600,
        blank=True,
        help_text="Comma-separated trigger words or phrases.",
    )
    item = models.ForeignKey(
        BookableItem,
        on_delete=models.SET_NULL,
        related_name="agent_faqs",
        null=True,
        blank=True,
    )
    language = models.CharField(max_length=8, default="en")
    min_score = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.55"))
    priority = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "category", "question"]
        verbose_name = "agent FAQ"
        verbose_name_plural = "agent FAQs"

    def __str__(self):
        return self.question


class AgentKnowledgeSource(models.Model):
    title = models.CharField(max_length=160)
    source_type = models.CharField(
        max_length=24,
        choices=AgentKnowledgeSourceType.choices,
        default=AgentKnowledgeSourceType.INLINE,
    )
    source_value = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Repo-relative file path or public URL, depending on source type.",
    )
    body = models.TextField(
        blank=True,
        help_text="Paste guest-facing text here for inline sources.",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "agent knowledge source"
        verbose_name_plural = "agent knowledge sources"

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.source_type == AgentKnowledgeSourceType.INLINE:
            if not self.body.strip():
                raise ValidationError({"body": "Inline text sources need pasted content."})
        elif not self.source_value.strip():
            raise ValidationError({"source_value": "File and URL sources need a source value."})


class SiteContentBlock(models.Model):
    key = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True)
    image_url = models.URLField(blank=True, max_length=1000)
    link_url = models.URLField(blank=True, max_length=1000)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "key"]

    def __str__(self):
        return self.title
