from django.contrib import admin

from .models import (
    AgentConversation,
    BookableItem,
    BookingInquiry,
    CalendarFeed,
    CancellationPolicy,
    Coupon,
    CustomerProfile,
    DamageDeposit,
    Donation,
    ExtraBillTemplate,
    GuestReviewHighlight,
    HouseRule,
    Invoice,
    InvoiceLineItem,
    MissionCause,
    PageVisit,
    Promotion,
    PromotionRecipient,
    ReviewTheme,
    SiteContentBlock,
    SiteSettings,
    StayGalleryImage,
)
from .services import InvoiceEmailService, PromotionEmailService


admin.site.site_header = "MLADIS Admin"
admin.site.site_title = "MLADIS Admin"
admin.site.index_title = "Booking platform controls"


class StayGalleryImageInline(admin.TabularInline):
    model = StayGalleryImage
    extra = 0


class ReviewThemeInline(admin.TabularInline):
    model = ReviewTheme
    extra = 0


class GuestReviewHighlightInline(admin.TabularInline):
    model = GuestReviewHighlight
    extra = 0


class HouseRuleInline(admin.TabularInline):
    model = HouseRule
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
    inlines = (StayGalleryImageInline, ReviewThemeInline, GuestReviewHighlightInline, HouseRuleInline, CalendarFeedInline)


@admin.register(BookingInquiry)
class BookingInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "guest_name",
        "email",
        "item",
        "check_in",
        "check_out",
        "guests",
        "status",
        "coupon_code",
        "is_admin_test",
        "is_blacklist_flagged",
        "email_delivery_status",
        "created_at",
    )
    list_filter = ("status", "check_in", "item", "is_admin_test", "is_blacklist_flagged", "email_delivery_status")
    search_fields = ("guest_name", "email", "phone", "message")
    readonly_fields = ("created_at", "updated_at", "nights", "email_sent_at", "email_error")
    autocomplete_fields = ("item", "user", "customer_profile", "coupon", "cancellation_policy")
    actions = ("create_invoice_for_requests",)

    @admin.action(description="Create draft invoices for selected reservations")
    def create_invoice_for_requests(self, request, queryset):
        created = 0
        for inquiry in queryset:
            invoice, was_created = Invoice.objects.get_or_create(
                inquiry=inquiry,
                recipient_email=inquiry.email,
                defaults={
                    "customer_profile": inquiry.customer_profile,
                    "recipient_name": inquiry.guest_name,
                    "currency": inquiry.currency,
                    "discount_cents": inquiry.discount_cents,
                    "deposit_cents": inquiry.deposit_cents,
                    "notes": "Admin-confirmed MLADIS reservation invoice.",
                },
            )
            if was_created:
                item_name = inquiry.item.name if inquiry.item else "MLADIS reservation"
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=f"{item_name} ({inquiry.check_in} to {inquiry.check_out})",
                    quantity=max(inquiry.nights, 1),
                    unit_amount_cents=0,
                    amount_cents=inquiry.subtotal_cents,
                )
                invoice.recalculate_totals()
                created += 1
        self.message_user(request, f"Created {created} draft invoice(s).")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "amount_cents", "percent_off", "is_active", "expires_at", "redemption_count")
    list_filter = ("discount_type", "is_active", "currency")
    search_fields = ("code", "description")


@admin.register(CancellationPolicy)
class CancellationPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "allow_guest_cancellation", "hours_before_check_in", "is_default", "is_active")
    list_filter = ("allow_guest_cancellation", "is_default", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "segment", "preferred_language", "updated_at")
    list_filter = ("segment", "preferred_language")
    search_fields = ("name", "email", "phone", "notes")
    autocomplete_fields = ("user",)


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


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "recipient_name", "recipient_email", "display_total", "status", "email_status", "created_at")
    list_filter = ("status", "email_status", "currency")
    search_fields = ("invoice_number", "recipient_name", "recipient_email", "notes")
    readonly_fields = ("public_token", "sent_at", "email_error", "created_at", "updated_at", "display_total")
    autocomplete_fields = ("inquiry", "customer_profile")
    inlines = (InvoiceLineItemInline,)
    actions = ("send_invoices",)

    @admin.action(description="Send selected invoices by email")
    def send_invoices(self, request, queryset):
        sent = sum(1 for invoice in queryset if InvoiceEmailService().send_invoice(invoice, request=request))
        self.message_user(request, f"Sent {sent} invoice email(s).")


@admin.register(ExtraBillTemplate)
class ExtraBillTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "default_amount_cents", "currency", "is_active", "sort_order")
    list_filter = ("is_active", "currency")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


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


class PromotionRecipientInline(admin.TabularInline):
    model = PromotionRecipient
    extra = 0
    readonly_fields = ("status", "sent_at", "error", "created_at")


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "target_segment", "discount_percent", "status", "sent_at", "created_at")
    list_filter = ("target_segment", "status")
    search_fields = ("title", "subject", "message")
    autocomplete_fields = ("coupon", "created_by")
    readonly_fields = ("sent_at", "created_at", "updated_at")
    inlines = (PromotionRecipientInline,)
    actions = ("send_promotions",)

    @admin.action(description="Build recipients and send selected promotions")
    def send_promotions(self, request, queryset):
        sent = sum(PromotionEmailService().send_promotion(promotion) for promotion in queryset)
        self.message_user(request, f"Sent {sent} promotion email(s).")


@admin.register(CalendarFeed)
class CalendarFeedAdmin(admin.ModelAdmin):
    list_display = ("item", "google_calendar_name", "is_configured", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("item__name", "airbnb_ical_url", "google_calendar_name", "notes")
    readonly_fields = ("created_at", "updated_at", "last_checked_at")


@admin.register(AgentConversation)
class AgentConversationAdmin(admin.ModelAdmin):
    list_display = ("session_id", "item", "question_topic", "visitor_email", "updated_at")
    list_filter = ("item", "question_topic", "created_at")
    search_fields = ("session_id", "visitor_email", "last_user_message", "last_agent_reply")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display = ("path", "user", "language", "created_at")
    list_filter = ("language", "created_at")
    search_fields = ("path", "session_key", "user_agent")
    readonly_fields = ("path", "user", "session_key", "language", "user_agent", "created_at")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "public_address_label", "updated_at")


@admin.register(SiteContentBlock)
class SiteContentBlockAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("key", "title", "body")


admin.site.register(GuestReviewHighlight)
admin.site.register(HouseRule)
