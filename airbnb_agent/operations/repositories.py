from collections import OrderedDict

from .models import WorkItem


class WorkItemRepository:
    """Query boundary for Operations.WorkItem data access."""

    active_statuses = [
        WorkItem.Status.CAPTURED,
        WorkItem.Status.PLANNED,
        WorkItem.Status.IN_PROGRESS,
        WorkItem.Status.BLOCKED,
        WorkItem.Status.PAUSED,
    ]

    board_statuses = [
        WorkItem.Status.CAPTURED,
        WorkItem.Status.PLANNED,
        WorkItem.Status.IN_PROGRESS,
        WorkItem.Status.BLOCKED,
        WorkItem.Status.DONE,
    ]

    def base_queryset(self):
        return WorkItem.objects.select_related("item", "inquiry", "created_by", "assigned_to")

    def list_active(self):
        return self.base_queryset().filter(status__in=self.active_statuses)

    def list_blocked(self):
        return self.base_queryset().filter(status=WorkItem.Status.BLOCKED)

    def list_recently_updated(self, limit=10):
        return self.base_queryset().order_by("-updated_at")[:limit]

    def list_focus_candidates(self, limit=5):
        return self.base_queryset().filter(
            status__in=[WorkItem.Status.IN_PROGRESS, WorkItem.Status.PLANNED, WorkItem.Status.BLOCKED]
        ).order_by("status", "sort_order", "-updated_at")[:limit]

    def list_for_listing(self, item):
        return self.base_queryset().filter(item=item).order_by("status", "sort_order", "-updated_at")

    def list_for_reservation(self, inquiry):
        return self.base_queryset().filter(inquiry=inquiry).order_by("status", "sort_order", "-updated_at")

    def group_by_status(self):
        grouped = OrderedDict((status, []) for status in self.board_statuses)
        for item in self.base_queryset().filter(status__in=self.board_statuses).order_by("status", "sort_order", "-updated_at"):
            grouped.setdefault(item.status, []).append(item)
        return grouped

    def get(self, pk):
        return self.base_queryset().get(pk=pk)
