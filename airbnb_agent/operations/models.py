from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class WorkItemStatus(models.TextChoices):
    CAPTURED = "captured", "Captured"
    PLANNED = "planned", "Planned"
    IN_PROGRESS = "in_progress", "In progress"
    BLOCKED = "blocked", "Blocked"
    PAUSED = "paused", "Paused"
    DONE = "done", "Done"


class WorkItemPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class WorkItemNeuron(models.TextChoices):
    OPERATIONS = "operations", "Operations"
    BOOKING = "booking", "Booking"
    FINANCE = "finance", "Finance"
    RESEARCH = "research", "Research"
    EDUCATION = "education", "Education"
    FITNESS = "fitness", "Fitness"
    PORTFOLIO = "portfolio", "Portfolio"
    PYRAMID = "pyramid", "Pyramid"
    FAIR_AGENT = "fair_agent", "FairAgent"


class OperationsWorkItem(models.Model):
    """Operations neuron object for owner-managed MLADIS work tracking."""

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    list_name = models.CharField(max_length=80, default="Business tasks")
    neuron = models.CharField(
        max_length=24,
        choices=WorkItemNeuron.choices,
        default=WorkItemNeuron.OPERATIONS,
    )
    status = models.CharField(
        max_length=24,
        choices=WorkItemStatus.choices,
        default=WorkItemStatus.CAPTURED,
    )
    priority = models.CharField(
        max_length=16,
        choices=WorkItemPriority.choices,
        default=WorkItemPriority.MEDIUM,
    )
    next_action = models.CharField(max_length=240, blank=True)
    source_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    drive_url = models.URLField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_operations_work_items",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_operations_work_items",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["list_name", "sort_order", "title"]
        indexes = [
            models.Index(fields=["list_name", "status"], name="ops_wi_list_status_idx"),
            models.Index(fields=["neuron", "priority"], name="ops_wi_neuron_prio_idx"),
            models.Index(fields=["updated_at"], name="ops_wi_updated_idx"),
        ]

    def __str__(self):
        return self.title

    @property
    def is_done(self):
        return self.status == WorkItemStatus.DONE

    def mark_done(self):
        self.status = WorkItemStatus.DONE
        self.completed_at = self.completed_at or timezone.now()

    def reopen(self, status=WorkItemStatus.PLANNED):
        self.status = status
        self.completed_at = None

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        if self.status == WorkItemStatus.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status != WorkItemStatus.DONE:
            self.completed_at = None
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base_slug = slugify(self.title)[:180] or "work-item"
        slug = base_slug
        suffix = 2
        while OperationsWorkItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{suffix}"[:220]
            suffix += 1
        return slug
