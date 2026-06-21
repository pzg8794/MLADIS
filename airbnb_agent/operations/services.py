from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import OperationsWorkItem, WorkItemPriority, WorkItemStatus
from .repositories import WorkItemRepository


class WorkboardAccessPolicy:
    def __init__(self):
        self.owner_emails = {email.lower() for email in getattr(settings, "MLADIS_WORKBOARD_OWNER_EMAILS", [])}
        self.owner_usernames = {name.lower() for name in getattr(settings, "MLADIS_WORKBOARD_OWNER_USERNAMES", [])}

    def can_manage(self, user):
        if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
            return False
        # Any active staff member may access the workboard.
        if getattr(user, "is_staff", False):
            return True
        # Fallback: configured owner emails / usernames also grant access.
        email = (getattr(user, "email", "") or "").lower()
        username = (getattr(user, "username", "") or "").lower()
        return bool(email and email in self.owner_emails) or bool(username and username in self.owner_usernames)

    def require_owner(self, user):
        if not self.can_manage(user):
            raise PermissionDenied("Workboard access requires staff privileges.")


class WorkboardService:
    STATUS_ORDER = [
        WorkItemStatus.CAPTURED,
        WorkItemStatus.PLANNED,
        WorkItemStatus.IN_PROGRESS,
        WorkItemStatus.BLOCKED,
        WorkItemStatus.PAUSED,
        WorkItemStatus.DONE,
    ]
    PRIORITY_WEIGHT = {
        WorkItemPriority.CRITICAL: 4,
        WorkItemPriority.HIGH: 3,
        WorkItemPriority.MEDIUM: 2,
        WorkItemPriority.LOW: 1,
    }

    def __init__(self, repository=None, access_policy=None):
        self.repository = repository or WorkItemRepository()
        self.access_policy = access_policy or WorkboardAccessPolicy()

    def snapshot_for(self, user):
        self.access_policy.require_owner(user)
        items = list(self.repository.all_items())
        focus_items = self.repository.focus_items()
        return {
            "summary_cards": self._summary_cards(items),
            "lists": [self._list_payload(name, list_items) for name, list_items in self.repository.groups_by_list().items()],
            "status_columns": self._status_columns(items),
            "focus_items": [self._item_payload(item) for item in focus_items],
            "generated_at": timezone.now().isoformat(),
        }

    @transaction.atomic
    def set_completion(self, user, pk, completed):
        self.access_policy.require_owner(user)
        item = self.repository.get(pk)
        if completed:
            item.mark_done()
        else:
            item.reopen(WorkItemStatus.PLANNED)
        item.save(update_fields=["status", "completed_at", "updated_at"])
        return self._item_payload(item)

    def _summary_cards(self, items):
        total = len(items)
        done = sum(1 for item in items if item.status == WorkItemStatus.DONE)
        blocked = sum(1 for item in items if item.status == WorkItemStatus.BLOCKED)
        critical = sum(1 for item in items if item.priority == WorkItemPriority.CRITICAL and item.status != WorkItemStatus.DONE)
        return [
            {"label": "Total", "value": total, "caption": "Tracked work items."},
            {"label": "Done", "value": done, "caption": "Completed and logged."},
            {"label": "Active", "value": total - done, "caption": "Not completed yet."},
            {"label": "Blocked", "value": blocked, "caption": "Needs owner or external action."},
            {"label": "Critical", "value": critical, "caption": "Highest priority open work."},
        ]

    def _list_payload(self, name, items):
        sorted_items = sorted(items, key=self._sort_key)
        done = sum(1 for item in sorted_items if item.status == WorkItemStatus.DONE)
        return {
            "name": name,
            "total": len(sorted_items),
            "done": done,
            "open": len(sorted_items) - done,
            "items": [self._item_payload(item) for item in sorted_items],
        }

    def _status_columns(self, items):
        return [
            {
                "status": status,
                "label": WorkItemStatus(status).label,
                "items": [self._item_payload(item) for item in items if item.status == status],
            }
            for status in self.STATUS_ORDER
        ]

    def _item_payload(self, item):
        return {
            "id": item.pk,
            "title": item.title,
            "description": item.description,
            "list_name": item.list_name,
            "neuron": item.neuron,
            "neuron_label": item.get_neuron_display(),
            "status": item.status,
            "status_label": item.get_status_display(),
            "priority": item.priority,
            "priority_label": item.get_priority_display(),
            "next_action": item.next_action,
            "source_url": item.source_url,
            "github_url": item.github_url,
            "drive_url": item.drive_url,
            "due_date": item.due_date.isoformat() if item.due_date else "",
            "completed_at": item.completed_at.isoformat() if item.completed_at else "",
            "updated_at": item.updated_at.isoformat() if item.updated_at else "",
            "is_done": item.is_done,
        }

    def _sort_key(self, item):
        return (
            item.status == WorkItemStatus.DONE,
            item.sort_order,
            -self.PRIORITY_WEIGHT.get(item.priority, 0),
            item.title.lower(),
        )
