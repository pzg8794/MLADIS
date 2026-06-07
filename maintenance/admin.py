from django.contrib import admin
from .models import MaintenanceEvent, MaintenancePhoto


class MaintenancePhotoInline(admin.TabularInline):
    model = MaintenancePhoto
    extra = 1
    fields = ("image", "caption")


@admin.register(MaintenanceEvent)
class MaintenanceEventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "property",
        "category",
        "start_at",
        "cost_amount",
        "cost_currency",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("category", "status", "property")
    search_fields = ("title", "description", "property__name")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("booking",)
    inlines = [MaintenancePhotoInline]
    fieldsets = (
        (
            "Required",
            {
                "fields": (
                    "id",
                    "property",
                    "title",
                    "category",
                    "cost_amount",
                    "cost_currency",
                    "start_at",
                    "end_at",
                )
            },
        ),
        (
            "Optional",
            {"fields": ("booking", "description", "status", "tax_category_code")},
        ),
        (
            "Audit",
            {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(MaintenancePhoto)
class MaintenancePhotoAdmin(admin.ModelAdmin):
    list_display = ("event", "caption", "created_at")
    readonly_fields = ("id", "created_at")
