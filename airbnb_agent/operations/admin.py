from django.contrib import admin

from .models import WorkItem


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "neuron",
        "status",
        "priority",
        "assigned_to",
        "due_date",
        "updated_at",
    )
    list_filter = ("status", "priority", "neuron", "assigned_to", "due_date")
    search_fields = ("title", "description", "next_action", "source_url", "github_url", "drive_url")
    list_editable = ("status", "priority")
    autocomplete_fields = ("created_by", "assigned_to")
    readonly_fields = ("created_at", "updated_at", "completed_at")
    fieldsets = (
        ("Work", {"fields": ("title", "description", "neuron", "status", "priority", "next_action")}),
        ("Ownership", {"fields": ("created_by", "assigned_to", "due_date", "sort_order")}),
        ("Links", {"fields": ("source_url", "github_url", "drive_url")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "completed_at")}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
