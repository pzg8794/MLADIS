"""Application-layer services for MaintenanceEvent.
Controllers and views call these instead of writing business logic themselves.
"""

from django.db import transaction
from .models import MaintenanceEvent, MaintenancePhoto


class MaintenanceService:
    """
    Orchestrates creation and status transitions for MaintenanceEvent.
    Enforces invariants (title, cost, time, >=1 photo) in one place.
    """

    @staticmethod
    @transaction.atomic
    def create_event(
        *,
        property_obj,
        title: str,
        cost_amount,
        cost_currency: str = "USD",
        start_at,
        end_at=None,
        pictures: list,  # list of InMemoryUploadedFile or similar
        category: str = MaintenanceEvent.CATEGORY_CLEANING,
        description: str = "",
        status: str = MaintenanceEvent.STATUS_DONE,
        tax_category_code: str = "",
        created_by,
        booking=None,
    ) -> MaintenanceEvent:
        """Validate invariants, persist event + photos atomically."""
        if not title or not title.strip():
            raise ValueError("title is required")
        if cost_amount is None or float(cost_amount) < 0:
            raise ValueError("cost_amount must be >= 0")
        if not start_at:
            raise ValueError("start_at is required")
        if not pictures:
            raise ValueError("At least one picture is required")

        event = MaintenanceEvent.objects.create(
            property=property_obj,
            booking=booking,
            title=title.strip(),
            category=category,
            cost_amount=cost_amount,
            cost_currency=cost_currency,
            start_at=start_at,
            end_at=end_at,
            description=description,
            status=status,
            tax_category_code=tax_category_code,
            created_by=created_by,
        )

        for pic in pictures:
            caption = getattr(pic, "name", "") or ""
            MaintenancePhoto.objects.create(event=event, image=pic, caption=caption)

        return event

    @staticmethod
    def mark_invoiced(event: MaintenanceEvent) -> MaintenanceEvent:
        event.status = MaintenanceEvent.STATUS_INVOICED
        event.save(update_fields=["status", "updated_at"])
        return event


class MaintenanceExportService:
    """
    Writes maintenance events to the Drive data-lake in JSONL format,
    following the same convention as the existing export_data_lake commands.
    """

    @staticmethod
    def to_jsonl_record(event: MaintenanceEvent) -> str:
        import json
        return json.dumps(event.to_agent_payload(), ensure_ascii=False, default=str)

    @staticmethod
    def export_event(event: MaintenanceEvent):
        """
        Append a single event's JSON record to the Drive data-lake.
        Wire this into a post_save signal or call it explicitly from the service layer.
        Call pattern mirrors the existing export_data_lake management command.
        """
        import os, datetime
        record = MaintenanceExportService.to_jsonl_record(event)
        # Build path:  maintenance_events/YYYY/MM/maintenance_events-YYYY-MM.jsonl
        today = datetime.date.today()
        rel_path = (
            f"maintenance_events/{today.year}/{today.month:02d}/"
            f"maintenance_events-{today.year}-{today.month:02d}.jsonl"
        )
        # TODO: replace with your GoogleDriveDataLake.append(rel_path, record)
        # Example stub:
        # from core.drive import data_lake
        # data_lake.append(rel_path, record + "\n")
        return rel_path, record
