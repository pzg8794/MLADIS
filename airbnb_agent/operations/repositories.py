from collections import OrderedDict

from .models import OperationsWorkItem, WorkItemStatus


class WorkItemRepository:
    def all_items(self):
        return OperationsWorkItem.objects.select_related("assigned_to", "created_by").all()

    def active_items(self):
        return self.all_items().exclude(status=WorkItemStatus.DONE)

    def get(self, pk):
        return self.all_items().get(pk=pk)

    def groups_by_list(self):
        groups = OrderedDict()
        for item in self.all_items():
            groups.setdefault(item.list_name, []).append(item)
        return groups

    def focus_items(self, limit=5):
        return list(
            self.active_items()
            .filter(status__in=[WorkItemStatus.IN_PROGRESS, WorkItemStatus.BLOCKED, WorkItemStatus.PLANNED])
            .order_by("sort_order", "-updated_at")[:limit]
        )
