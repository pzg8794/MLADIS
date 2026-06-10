from django.conf import settings
from django.db import models
from django.utils import timezone


class WorkItem(models.Model):
    """Operations.WorkItem tracks MLADIS work without owning other neurons' logic."""

    class Neuron(models.TextChoices):
        OPERATIONS = "operations", "Operations"
        BOOKING = "booking", "Booking"
        FINANCE = "finance", "Finance"
        RESEARCH = "research", "Research"
        EDUCATION = "education", "Education"
        FITNESS = "fitness", "Fitness"
        PORTFOLIO = "portfolio", "Portfolio"
        PYRAMID = "pyramid", "Pyramid"
        FAIR_AGENT = "fair_agent", "FairAgent"

    class Status(models.TextChoices):
        CAPTURED = "captured", "Captured"
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        BLOCKED = "blocked", "Blocked"
        PAUSED = "paused", "Paused"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    neuron = models.CharField(max_length=32, choices=Neuron.choices, default=Neuron.OPERATIONS)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CAPTURED)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    next_action = models.CharField(max_length=255, blank=True)

    source_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    drive_url = models.URLField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_work_items",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_work_items",
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "sort_order", "-updated_at"]
        indexes = [
            models.Index(fields=["status", "sort_order"]),
            models.Index(fields=["neuron", "status"]),
            models.Index(fields=["priority", "status"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_done(self):
        return self.status == self.Status.DONE

    @property
    def is_blocked(self):
        return self.status == self.Status.BLOCKED

    def mark_done(self):
        self.status = self.Status.DONE
        self.completed_at = timezone.now()

    def reopen(self, status=None):
        self.status = status or self.Status.PLANNED
        self.completed_at = None
