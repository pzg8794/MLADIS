from django.contrib import admin

from .models import (
    AgentConversation,
    BookableItem,
    BookingInquiry,
    CalendarFeed,
    DamageDeposit,
    Donation,
    MissionCause,
    ReviewTheme,
    StayGalleryImage,
)


class StayGalleryImageInline(admin.TabularInline):
    model = StayGalleryImage
    extra = 0


class ReviewThemeInline(admin.TabularInline):
    model = ReviewTheme
    extra = 0


class CalendarFeedInline(admin.StackedInline):
    model = CalendarFeed
    extra = 0
    max_num = 1


@admin.register(BookableItem)
class BookableItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "location_label",
        "headline_price",
        "airbnb_rating",
        "review_count",
        "is_featured",
        "is_active",
    )
    list_filter = ("category", "is_featured", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "short_description", "location_label", "airbnb_listing_id")
    inlines = (StayGalleryImageInline, ReviewThemeInline, CalendarFeedInline)


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


@admin.register(MissionCause)
class MissionCauseAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("donor_name", "email", "cause", "display_amount", "status", "created_at")
    list_filter = ("status", "currency", "cause")
    search_fields = (
        "donor_name",
        "email",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
    )
    readonly_fields = ("created_at", "updated_at", "display_amount")


@admin.register(CalendarFeed)
class CalendarFeedAdmin(admin.ModelAdmin):
    list_display = ("item", "google_calendar_name", "is_configured", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("item__name", "airbnb_ical_url", "google_calendar_name", "notes")
    readonly_fields = ("created_at", "updated_at", "last_checked_at")


@admin.register(AgentConversation)
class AgentConversationAdmin(admin.ModelAdmin):
    list_display = ("session_id", "item", "visitor_email", "updated_at")
    list_filter = ("item", "created_at")
    search_fields = ("session_id", "visitor_email", "last_user_message", "last_agent_reply")
    readonly_fields = ("created_at", "updated_at")
