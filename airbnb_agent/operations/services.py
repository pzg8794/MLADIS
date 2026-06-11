from django.utils import timezone

from .models import WorkItem
from .repositories import WorkItemRepository


class WorkboardService:
    """Business boundary for the Operations Workboard."""

    def __init__(self, repository=None):
        self.repository = repository or WorkItemRepository()

    def get_board_context(self):
        columns = []
        grouped_items = self.repository.group_by_status()
        for status, items in grouped_items.items():
            columns.append(
                {
                    "key": status,
                    "label": WorkItem.Status(status).label,
                    "items": items,
                    "count": len(items),
                }
            )

        return {
            "columns": columns,
            "today_focus": self.get_today_focus(),
            "blocked_items": self.repository.list_blocked(),
            "recent_items": self.repository.list_recently_updated(),
        }

    def get_today_focus(self):
        candidates = list(self.repository.list_focus_candidates(limit=5))
        main_focus = next((item for item in candidates if item.status == WorkItem.Status.IN_PROGRESS), None)
        if main_focus is None and candidates:
            main_focus = candidates[0]

        support_items = [item for item in candidates if item.pk != getattr(main_focus, "pk", None)][:2]
        return {
            "main": main_focus,
            "support": support_items,
            "next_action": main_focus.next_action if main_focus else "Create or select the next tiny action.",
        }

    def get_report_context_for_listing(self, item):
        work_items = list(self.repository.list_for_listing(item))
        return {
            "listing": item,
            "work_items": work_items,
            "work_item_payloads": [work_item.to_report_context() for work_item in work_items],
        }

    def get_report_context_for_reservation(self, inquiry):
        work_items = list(self.repository.list_for_reservation(inquiry))
        return {
            "reservation": inquiry,
            "listing": inquiry.item,
            "work_items": work_items,
            "work_item_payloads": [work_item.to_report_context() for work_item in work_items],
        }

    def move_item(self, item, status):
        status_values = {choice.value for choice in WorkItem.Status}
        if status not in status_values:
            raise ValueError(f"Unsupported WorkItem status: {status}")

        if status == WorkItem.Status.DONE:
            item.mark_done()
        else:
            item.status = status
            item.completed_at = None
        item.save(update_fields=["status", "completed_at", "updated_at"])
        return item

    def complete_item(self, item):
        item.mark_done()
        item.completed_at = item.completed_at or timezone.now()
        item.save(update_fields=["status", "completed_at", "updated_at"])
        return item
