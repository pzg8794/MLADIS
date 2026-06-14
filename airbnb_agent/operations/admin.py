from django.contrib import admin

from .models import OperationsWorkItem


@admin.register(OperationsWorkItem)
class OperationsWorkItemAdmin(admin.ModelAdmin):
    list_display = ("title", "list_name", "neuron", "status", "priority", "assigned_to", "completed_at", "updated_at")
    list_filter = ("list_name", "neuron", "status", "priority")
    search_fields = ("title", "description", "next_action")
    autocomplete_fields = ("created_by", "assigned_to")
    list_editable = ("status", "priority")
    readonly_fields = ("created_at", "updated_at", "completed_at")
    fieldsets = (
        ("Work item", {"fields": ("title", "slug", "description", "list_name", "neuron", "status", "priority", "next_action")}),
        ("Links", {"fields": ("source_url", "github_url", "drive_url")}),
        ("Ownership", {"fields": ("created_by", "assigned_to", "due_date", "sort_order")}),
        ("Audit", {"fields": ("completed_at", "created_at", "updated_at")}),
    )
