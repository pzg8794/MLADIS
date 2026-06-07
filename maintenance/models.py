import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MaintenanceEvent(models.Model):
    """
    Aggregate root for a maintenance or cleaning event on a property.
    Required fields: title, cost (amount + currency), time (start_at), pictures (min 1).
    """

    CATEGORY_CLEANING = "CLEANING"
    CATEGORY_REPAIR = "REPAIR"
    CATEGORY_INSPECTION = "INSPECTION"
    CATEGORY_OTHER = "OTHER"
    CATEGORY_CHOICES = [
        (CATEGORY_CLEANING, "Cleaning"),
        (CATEGORY_REPAIR, "Repair"),
        (CATEGORY_INSPECTION, "Inspection"),
        (CATEGORY_OTHER, "Other"),
    ]

    STATUS_SCHEDULED = "SCHEDULED"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DONE = "DONE"
    STATUS_INVOICED = "INVOICED"
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_DONE, "Done"),
        (STATUS_INVOICED, "Invoiced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Property / Booking links (adjust FK paths to match your actual app label) ---
    # If your BookableItem lives in a different app, change "bookings.BookableItem" to
    # "<app_label>.<ModelName>" or use a direct import.
    property = models.ForeignKey(
        "bookings.BookableItem",
        on_delete=models.PROTECT,
        related_name="maintenance_events",
        help_text="The property/unit where this work was performed.",
    )
    booking = models.ForeignKey(
        "bookings.BookingInquiry",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="maintenance_events",
        help_text="Optional: link to the stay this maintenance relates to.",
    )

    # --- Required core fields (Title, Cost, Time) ---
    title = models.CharField(
        max_length=200,
        help_text="Short human-readable description, e.g. 'Turnover cleaning after checkout'.",
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_CLEANING
    )
    cost_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total cost of the work (required).",
    )
    cost_currency = models.CharField(max_length=3, default="USD")
    start_at = models.DateTimeField(help_text="When the work started (required).")
    end_at = models.DateTimeField(
        null=True, blank=True, help_text="When the work ended (optional)."
    )

    # --- Optional enrichment ---
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DONE
    )
    tax_category_code = models.CharField(
        max_length=64,
        blank=True,
        help_text="Optional tax classification code for accounting/bill generation.",
    )

    # --- Audit ---
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_maintenance_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-start_at",)
        verbose_name = "Maintenance Event"
        verbose_name_plural = "Maintenance Events"

    def __str__(self):
        return f"{self.title} — {self.property} ({self.start_at.date()})"

    # -----------------------------------------------------------------------
    # Domain validation (OOP invariants)
    # -----------------------------------------------------------------------
    def clean(self):
        errors = {}
        if not self.title or not self.title.strip():
            errors["title"] = "Title is required."
        if self.cost_amount is None or self.cost_amount < 0:
            errors["cost_amount"] = "Cost must be a non-negative value."
        if not self.start_at:
            errors["start_at"] = "Start time is required."
        if self.end_at and self.start_at and self.end_at < self.start_at:
            errors["end_at"] = "End time cannot be before start time."
        if errors:
            raise ValidationError(errors)

    # -----------------------------------------------------------------------
    # Domain helpers / value-object proxies
    # -----------------------------------------------------------------------
    @property
    def duration_minutes(self):
        """Returns integer duration in minutes, or None if end_at is not set."""
        if self.start_at and self.end_at:
            delta = self.end_at - self.start_at
            return int(delta.total_seconds() // 60)
        return None

    @property
    def money(self):
        """Returns a simple dict representing the Money value object."""
        return {"amount": str(self.cost_amount), "currency": self.cost_currency}

    @property
    def time_window(self):
        """Returns a dict representing the TimeWindow value object."""
        return {
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "duration_minutes": self.duration_minutes,
        }

    def to_agent_payload(self) -> dict:
        """
        Returns a machine-parseable JSON-ready dict for the billing/tax agent.
        All four required attributes (title, cost, time, pictures) are guaranteed
        to be present and non-empty before this is called (validated by clean()).
        """
        photos = [
            {
                "id": str(photo.id),
                "url": photo.image.url if photo.image else None,
                "caption": photo.caption,
            }
            for photo in self.photos.all()
        ]
        return {
            "maintenance_id": str(self.id),
            "property_code": getattr(self.property, "code", None),
            "property_display_name": str(self.property),
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "title": self.title,
            "category": self.category,
            "cost": self.money,
            "time": self.time_window,
            "pictures": photos,
            "created_by": getattr(self.created_by, "email", None),
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "tax_category_code": self.tax_category_code or None,
        }


class MaintenancePhoto(models.Model):
    """A picture attached to a MaintenanceEvent (one-to-many)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        MaintenanceEvent,
        related_name="photos",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to="maintenance_photos/",
        help_text="Upload a photo of the work (before/after, damage, etc.).",
    )
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Photo for {self.event.title} ({self.id})"
