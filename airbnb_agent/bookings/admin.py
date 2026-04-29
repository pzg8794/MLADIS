from django.contrib import admin

from .models import AgentConversation, BookableItem, BookingInquiry, DamageDeposit


@admin.register(BookableItem)
class BookableItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "location_label", "headline_price", "is_featured", "is_active")
    list_filter = ("category", "is_featured", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "short_description", "location_label", "airbnb_listing_id")


@admin.register(BookingInquiry)
class BookingInquiryAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "item", "check_in", "check_out", "guests", "status", "created_at")
    list_filter = ("status", "check_in", "item")
    search_fields = ("guest_name", "email", "phone", "message")
    readonly_fields = ("created_at", "updated_at", "nights")


@admin.register(DamageDeposit)
class DamageDepositAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "item", "display_amount", "status", "created_at")
    list_filter = ("status", "currency", "item")
    search_fields = (
        "guest_name",
        "email",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
    )
    readonly_fields = ("created_at", "updated_at", "display_amount")


@admin.register(AgentConversation)
class AgentConversationAdmin(admin.ModelAdmin):
    list_display = ("session_id", "item", "visitor_email", "updated_at")
    list_filter = ("item", "created_at")
    search_fields = ("session_id", "visitor_email", "last_user_message", "last_agent_reply")
    readonly_fields = ("created_at", "updated_at")
