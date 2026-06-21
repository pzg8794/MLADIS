# Backend Code Stubs

These are implementation stubs, not final production code. They show the intended object shape and service boundaries.

## Django model vocabulary

```python
from uuid import uuid4
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class WorkOrderStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    OVERDUE = "overdue", "Overdue"
    CANCELLED = "cancelled", "Cancelled"
    ARCHIVED = "archived", "Archived"


class WorkOrderPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class WorkOrderType(models.TextChoices):
    CLEANING = "cleaning", "Cleaning"
    REPAIR = "repair", "Repair"
    REPLACEMENT = "replacement", "Replacement"
    INSPECTION = "inspection", "Inspection"
    SUPPLIES = "supplies", "Supplies"
    SAFETY = "safety", "Safety"
    OTHER = "other", "Other"


class WorkOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    work_order_number = models.CharField(max_length=32, unique=True)
    item = models.ForeignKey("bookings.BookableItem", on_delete=models.PROTECT, related_name="work_orders")
    booking = models.ForeignKey("bookings.BookingInquiry", on_delete=models.SET_NULL, null=True, blank=True, related_name="work_orders")

    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=280, blank=True)
    description = models.TextField(blank=True)

    work_type = models.CharField(max_length=24, choices=WorkOrderType.choices, default=WorkOrderType.REPAIR)
    status = models.CharField(max_length=24, choices=WorkOrderStatus.choices, default=WorkOrderStatus.OPEN)
    priority = models.CharField(max_length=24, choices=WorkOrderPriority.choices, default=WorkOrderPriority.MEDIUM)

    cost_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_currency = models.CharField(max_length=3, default="USD")

    reported_at = models.DateTimeField(default=timezone.now)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)

    vendor_name = models.CharField(max_length=160, blank=True)
    vendor_contact = models.CharField(max_length=160, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_work_orders")
    assigned_to_name = models.CharField(max_length=160, blank=True)
    assigned_role_label = models.CharField(max_length=80, blank=True)

    manual_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    ai_summary = models.TextField(blank=True)
    ai_diagnostics = models.TextField(blank=True)
    ai_recommendation = models.TextField(blank=True)
    ai_metadata = models.JSONField(default=dict, blank=True)
    use_ai_summary = models.BooleanField(default=False)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_work_orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reported_at", "-created_at"]

    def clean(self):
        errors = {}
        if self.cost_amount is not None and self.cost_amount < 0:
            errors["cost_amount"] = "Cost must be zero or greater."
        if self.started_at and self.completed_at and self.completed_at < self.started_at:
            errors["completed_at"] = "Completed time must be after started time."
        if self.booking_id and self.item_id and self.booking.item_id != self.item_id:
            errors["booking"] = "Linked booking must belong to the selected stay."
        if errors:
            raise ValidationError(errors)

    @property
    def display_cost(self):
        return f"${self.cost_amount:,.2f} {self.cost_currency.upper()}"

    @property
    def duration_minutes(self):
        if not self.started_at or not self.completed_at:
            return None
        return max(int((self.completed_at - self.started_at).total_seconds() // 60), 0)

    @property
    def is_report_ready(self):
        return bool(self.title and self.item_id and (self.manual_notes or self.ai_summary) and self.photos.exists())
```

## Child evidence object

```python
class WorkOrderPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="photos")
    image = models.FileField(upload_to="work-orders/photos/")
    caption = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_cover = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def image_url(self):
        try:
            return self.image.url
        except ValueError:
            return ""
```

## Service boundary

```python
class WorkOrderService:
    @transaction.atomic
    def create_work_order(self, payload, actor):
        work_order = WorkOrder(created_by=actor, **payload)
        work_order.full_clean()
        work_order.save()
        return work_order

    @transaction.atomic
    def transition_status(self, work_order, next_status, actor, note=""):
        if not work_order.can_transition_to(next_status):
            raise ValidationError({"status": "Invalid status transition."})
        previous = work_order.status
        work_order.status = next_status
        if next_status == WorkOrderStatus.COMPLETED and not work_order.completed_at:
            work_order.completed_at = timezone.now()
        work_order.full_clean()
        work_order.save(update_fields=["status", "completed_at", "updated_at"])
        return work_order
```
