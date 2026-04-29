from django.db import models
from django.urls import reverse


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
    DECLINED = "declined", "Declined"


class DepositStatus(models.TextChoices):
    NEW = "new", "New"
    REQUIRES_CONFIGURATION = "requires_configuration", "Requires Stripe configuration"
    CHECKOUT_CREATED = "checkout_created", "Checkout created"
    REQUIRES_CAPTURE = "requires_capture", "Authorized"
    CAPTURED = "captured", "Captured"
    CANCELED = "canceled", "Canceled"
    FAILED = "failed", "Failed"


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
    location_label = models.CharField(max_length=160, blank=True)
    image = models.CharField(max_length=240, blank=True)
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
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
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


class BookingInquiry(models.Model):
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
    status = models.CharField(
        max_length=24,
        choices=BookingStatus.choices,
        default=BookingStatus.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        item_name = self.item.name if self.item else "Any booking"
        return f"{self.guest_name} - {item_name}"

    @property
    def nights(self):
        return max((self.check_out - self.check_in).days, 0)


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
    status = models.CharField(
        max_length=32,
        choices=DepositStatus.choices,
        default=DepositStatus.NEW,
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
        item_name = self.item.name if self.item else "booking"
        return f"{self.display_amount} deposit for {item_name}"

    @property
    def amount(self):
        return self.amount_cents / 100

    @property
    def display_amount(self):
        return f"${self.amount:,.0f} {self.currency.upper()}"


class AgentConversation(models.Model):
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
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Agent conversation {self.session_id}"
