import csv
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlencode

import requests
import stripe

from django.contrib import admin, messages
from django.contrib.admin.utils import quote
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .airbnb_import import AirbnbGuestImportService
from .forms import AirbnbGuestImportForm
from .models import (
    AdminAccess,
    AgentKnowledgeSource,
    AgentFAQ,
    AgentConversation,
    AirbnbGuestRecord,
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    CalendarFeed,
    CancellationPolicy,
    Coupon,
    CustomerFeedback,
    CustomerProfile,
    DamageDeposit,
    DailyPriceOverride,
    DepositProvider,
    DepositStatus,
    Donation,
    ExtraBillTemplate,
    GuestReviewHighlight,
    HouseRule,
    Invoice,
    InvoiceLineItem,
    MarketingConsentStatus,
    MissionCause,
    PageVisit,
    Promotion,
    PromotionRecipient,
    ReservationPaymentHold,
    ReviewTheme,
    SiteContentBlock,
    SiteSettings,
    StayGalleryImage,
)
from .services import (
    InvoiceEmailService,
    MarketingConsentEmailService,
    PayPalAPIError,
    PromotionEmailService,
    get_damage_deposit_service,
)


admin.site.site_header = "MLADIS Admin"
admin.site.site_title = "MLADIS Admin"
admin.site.index_title = "Booking platform controls"


@admin.register(AdminAccess)
class AdminAccessAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "grant_staff_access", "grant_superuser_access", "is_active", "updated_at")
    list_filter = ("is_active", "grant_staff_access", "grant_superuser_access")
    search_fields = ("name", "email", "phone", "notes")


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
    change_list_template = "admin/bookings/bookableitem/change_list.html"
    list_display = (
        "name",
        "category",
        "location_label",
        "headline_price",
        "airbnb_rating",
        "review_count",
        "is_featured",
        "is_active",
        "calendar_link",
    )
    list_filter = ("category", "is_featured", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "short_description", "location_label", "airbnb_listing_id")
    inlines = (StayGalleryImageInline, ReviewThemeInline, GuestReviewHighlightInline, HouseRuleInline, CalendarFeedInline)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "calendar/",
                self.admin_site.admin_view(self.calendar_view),
                name=self._calendar_url_name(),
            ),
            path(
                "calendar-v2/",
                self.admin_site.admin_view(self.calendar_v2_view),
                name=f"{self._calendar_url_name()}_v2",
            )
        ]
        return custom_urls + urls

    @admin.display(description="Calendar")
    def calendar_link(self, obj):
        if obj.category != BookingCategory.STAY:
            return "-"
        return format_html('<a href="{}">Open calendar</a>', self._calendar_url(item=obj))

    def calendar_view(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        return HttpResponseRedirect(self._calendar_url_from_request(request))

    def calendar_v2_view(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        return HttpResponseRedirect(self._calendar_url_from_request(request))

    def _calendar_url_name(self):
        return f"{self.model._meta.app_label}_{self.model._meta.model_name}_calendar"

    def _calendar_url(self, item=None, month=None, date_value=None):
        params = {}
        if item:
            params["item"] = item.pk if hasattr(item, "pk") else item
        if date_value:
            params["date"] = date_value
        elif month:
            params["date"] = month.strftime("%Y-%m-01") if hasattr(month, "strftime") else self._calendar_month_to_date(month)
        url = reverse("bookings:calendar-ops")
        return f"{url}?{urlencode(params)}" if params else url

    def _calendar_url_from_request(self, request):
        selected_id = (
            request.POST.get("item")
            or request.POST.get("block-item")
            or request.POST.get("price-item")
            or request.GET.get("item")
        )
        item = selected_id if selected_id and str(selected_id).isdigit() else None
        return self._calendar_url(
            item=item,
            date_value=request.POST.get("date") or request.GET.get("date"),
            month=request.POST.get("month") or request.GET.get("month"),
        )

    def _calendar_month_to_date(self, value):
        value = str(value)
        if len(value) == 7:
            return f"{value}-01"
        return value


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


class CustomerProfileFeedbackInline(admin.TabularInline):
    model = CustomerFeedback
    fk_name = "customer_profile"
    extra = 0
    fields = ("guest_name", "source", "item", "rating", "feedback_text", "is_public", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("airbnb_guest_record", "item")


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "segment",
        "source",
        "marketing_consent_status",
        "preferred_language",
        "updated_at",
    )
    list_filter = ("segment", "source", "marketing_consent_status", "preferred_language")
    search_fields = ("name", "email", "phone", "notes")
    autocomplete_fields = ("user",)
    readonly_fields = ("marketing_consent_requested_at", "marketing_consent_at", "created_at", "updated_at")
    inlines = (CustomerProfileFeedbackInline,)
    actions = (
        "mark_marketing_opted_in",
        "mark_marketing_opted_out",
        "mark_marketing_unknown",
        "send_marketing_consent_requests",
        "export_customer_contacts_csv",
    )

    @admin.action(description="Mark selected clients as opted in for promotions")
    def mark_marketing_opted_in(self, request, queryset):
        updated = queryset.update(
            marketing_consent_status=MarketingConsentStatus.OPTED_IN,
            marketing_consent_at=timezone.now(),
            marketing_consent_source="admin",
        )
        self.message_user(request, f"Marked {updated} client(s) as opted in.")

    @admin.action(description="Mark selected clients as opted out of promotions")
    def mark_marketing_opted_out(self, request, queryset):
        updated = queryset.update(
            marketing_consent_status=MarketingConsentStatus.OPTED_OUT,
            marketing_consent_at=timezone.now(),
            marketing_consent_source="admin",
        )
        self.message_user(request, f"Marked {updated} client(s) as opted out.")

    @admin.action(description="Reset selected clients to unknown promotion consent")
    def mark_marketing_unknown(self, request, queryset):
        updated = queryset.update(
            marketing_consent_status=MarketingConsentStatus.UNKNOWN,
            marketing_consent_at=None,
            marketing_consent_source="",
        )
        self.message_user(request, f"Reset consent for {updated} client(s).")

    @admin.action(description="Send permission request email to selected clients")
    def send_marketing_consent_requests(self, request, queryset):
        service = MarketingConsentEmailService()
        sent = 0
        skipped = 0
        for profile in queryset:
            if service.send_request(profile):
                sent += 1
            else:
                skipped += 1
        self.message_user(request, f"Sent {sent} consent request(s). Skipped {skipped} client(s) without email.")

    @admin.action(description="Export selected customer contact list as CSV")
    def export_customer_contacts_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="mladis-customer-contacts.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "name",
                "email",
                "phone",
                "segment",
                "source",
                "marketing_consent_status",
                "marketing_consent_requested_at",
                "marketing_consent_at",
                "preferred_language",
                "notes",
            ]
        )
        for profile in queryset.order_by("email", "name"):
            writer.writerow(
                [
                    profile.name,
                    profile.email,
                    profile.phone,
                    profile.get_segment_display(),
                    profile.get_source_display(),
                    profile.get_marketing_consent_status_display(),
                    profile.marketing_consent_requested_at or "",
                    profile.marketing_consent_at or "",
                    profile.preferred_language,
                    profile.notes,
                ]
            )
        return response


class AirbnbGuestFeedbackInline(admin.StackedInline):
    model = CustomerFeedback
    fk_name = "airbnb_guest_record"
    extra = 0
    max_num = 1
    fields = (
        "customer_profile",
        "item",
        "source",
        "source_label",
        "source_url",
        "rating",
        "feedback_text",
        "feedback_summary",
        "permission_notes",
        "is_public",
        "published_at",
    )
    autocomplete_fields = ("customer_profile", "item")


@admin.register(AirbnbGuestRecord)
class AirbnbGuestRecordAdmin(admin.ModelAdmin):
    change_list_template = "admin/bookings/airbnbguestrecord/change_list.html"
    list_display = (
        "guest_name",
        "listing_title",
        "airbnb_listing_id",
        "stay_dates",
        "guests",
        "email",
        "phone",
        "updated_at",
    )
    list_filter = ("airbnb_listing_id", "check_in", "item")
    search_fields = (
        "guest_name",
        "email",
        "phone",
        "listing_title",
        "airbnb_listing_id",
        "source_email_subject",
        "message_excerpt",
        "feedback_summary",
        "permission_notes",
    )
    autocomplete_fields = ("customer_profile", "item")
    readonly_fields = ("created_at", "updated_at")
    inlines = (AirbnbGuestFeedbackInline,)
    actions = ("export_airbnb_guest_records_csv",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_view),
                name=self._import_url_name(),
            )
        ]
        return custom_urls + urls

    def import_view(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        form = AirbnbGuestImportForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            uploaded = form.cleaned_data["import_file"]
            dry_run = form.cleaned_data["dry_run"]
            suffix = Path(uploaded.name).suffix.lower()
            with NamedTemporaryFile(suffix=suffix) as temporary_file:
                for chunk in uploaded.chunks():
                    temporary_file.write(chunk)
                temporary_file.flush()
                result = AirbnbGuestImportService().import_file(
                    temporary_file.name,
                    dry_run=dry_run,
                )
            verb = "Dry run complete" if dry_run else "Import complete"
            self.message_user(
                request,
                (
                    f"{verb}: {result.created} record(s) to create, "
                    f"{result.updated} to update, {result.skipped} skipped."
                ),
                level=messages.SUCCESS,
            )
            return HttpResponseRedirect(self._changelist_url())

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Import Airbnb guests",
            "form": form,
            "changelist_url": self._changelist_url(),
        }
        return TemplateResponse(request, "admin/bookings/airbnbguestrecord/import.html", context)

    def _import_url_name(self):
        return f"{self.model._meta.app_label}_{self.model._meta.model_name}_import"

    def _import_url(self):
        return reverse(f"admin:{self._import_url_name()}")

    def _changelist_url(self):
        return reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")

    @admin.action(description="Export selected Airbnb guest records as CSV")
    def export_airbnb_guest_records_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="mladis-airbnb-guest-records.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "guest_name",
                "email",
                "phone",
                "listing_title",
                "airbnb_listing_id",
                "check_in",
                "check_out",
                "guests",
                "airbnb_thread_url",
                "message_excerpt",
                "feedback_summary",
                "rating",
                "permission_notes",
            ]
        )
        for record in queryset.order_by("-check_in", "guest_name"):
            writer.writerow(
                [
                    record.guest_name,
                    record.email,
                    record.phone,
                    record.listing_title,
                    record.airbnb_listing_id,
                    record.check_in or "",
                    record.check_out or "",
                    record.guests or "",
                    record.airbnb_thread_url,
                    record.message_excerpt,
                    record.feedback_summary,
                    record.rating or "",
                    record.permission_notes,
                ]
            )
        return response


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "guest_name",
        "item",
        "source",
        "rating",
        "customer_profile",
        "is_public",
        "updated_at",
    )
    list_filter = ("source", "is_public", "item", "rating")
    search_fields = (
        "guest_name",
        "email",
        "phone",
        "feedback_text",
        "feedback_summary",
        "permission_notes",
        "source_url",
    )
    autocomplete_fields = ("customer_profile", "airbnb_guest_record", "item")
    readonly_fields = ("created_at", "updated_at")
    actions = ("mark_public", "mark_private", "export_feedback_csv")

    @admin.action(description="Mark selected feedback as public")
    def mark_public(self, request, queryset):
        updated = queryset.update(is_public=True, published_at=timezone.now())
        self.message_user(request, f"Marked {updated} selected feedback record(s) public.")

    @admin.action(description="Mark selected feedback as private")
    def mark_private(self, request, queryset):
        updated = queryset.update(is_public=False, published_at=None)
        self.message_user(request, f"Marked {updated} selected feedback record(s) private.")

    @admin.action(description="Export selected feedback as CSV")
    def export_feedback_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="mladis-customer-feedback.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "guest_name",
                "email",
                "phone",
                "customer_profile",
                "listing",
                "source",
                "source_url",
                "rating",
                "feedback_text",
                "feedback_summary",
                "permission_notes",
                "is_public",
                "created_at",
                "updated_at",
            ]
        )
        for feedback in queryset.select_related("customer_profile", "item").order_by("-created_at"):
            writer.writerow(
                [
                    feedback.guest_name,
                    feedback.email,
                    feedback.phone,
                    feedback.customer_profile or "",
                    feedback.item or "",
                    feedback.get_source_display(),
                    feedback.source_url,
                    feedback.rating or "",
                    feedback.feedback_text,
                    feedback.feedback_summary,
                    feedback.permission_notes,
                    feedback.is_public,
                    feedback.created_at,
                    feedback.updated_at,
                ]
            )
        return response


@admin.register(DamageDeposit)
class DamageDepositAdmin(admin.ModelAdmin):
    change_form_template = "admin/bookings/damagedeposit/change_form.html"
    list_display = ("guest_name", "item", "payment_provider", "display_amount", "status", "created_at")
    list_filter = ("payment_provider", "status", "currency", "item")
    actions = ("capture_selected_deposits", "release_selected_deposits")
    search_fields = (
        "guest_name",
        "email",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
        "paypal_order_id",
        "paypal_authorization_id",
    )
    readonly_fields = ("created_at", "updated_at", "display_amount")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/deposit-action/<str:operation>/",
                self.admin_site.admin_view(self.confirm_deposit_action_view),
                name=self._deposit_action_url_name(),
            )
        ]
        return custom_urls + urls

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            extra_context["deposit_admin_actions"] = self._detail_actions_for_deposit(
                self.get_object(request, object_id)
            )
        return super().changeform_view(request, object_id, form_url, extra_context)

    @admin.action(description="Capture selected authorized deposits")
    def capture_selected_deposits(self, request, queryset):
        self._run_deposit_action(request, queryset, operation="capture")

    @admin.action(description="Release selected authorized deposits")
    def release_selected_deposits(self, request, queryset):
        self._run_deposit_action(request, queryset, operation="release")

    def confirm_deposit_action_view(self, request, object_id, operation):
        deposit = self.get_object(request, object_id)
        if deposit is None:
            return HttpResponseRedirect(self._changelist_url())
        if not self.has_change_permission(request, deposit):
            raise PermissionDenied

        action = self._get_deposit_action(deposit, operation)
        change_url = self._change_url(deposit)
        if not action:
            self.message_user(
                request,
                "This deposit is not currently eligible for that action.",
                level=messages.WARNING,
            )
            return HttpResponseRedirect(change_url)

        if request.method == "POST":
            try:
                self._run_single_deposit_action(deposit, operation)
            except (PayPalAPIError, requests.RequestException, stripe.StripeError, ValueError) as error:
                self.message_user(
                    request,
                    f"Could not {operation} deposit {deposit.id}. {error}",
                    level=messages.ERROR,
                )
            else:
                self.message_user(request, action["success_message"], level=messages.SUCCESS)
            return HttpResponseRedirect(change_url)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": deposit,
            "title": action["title"],
            "action_label": action["label"],
            "action_summary": action["summary"],
            "action_provider_detail": action["provider_detail"],
            "action_warning": action["warning"],
            "confirm_button_label": action["confirm_label"],
            "cancel_url": change_url,
        }
        return TemplateResponse(
            request,
            "admin/bookings/damagedeposit/confirm_deposit_action.html",
            context,
        )

    def _run_deposit_action(self, request, queryset, operation):
        success_label = "Captured" if operation == "capture" else "Released"
        success_count = 0
        skipped_count = 0
        errors = []

        for deposit in queryset:
            if not self._is_manageable_deposit(deposit):
                skipped_count += 1
                continue

            try:
                self._run_single_deposit_action(deposit, operation)
            except (PayPalAPIError, requests.RequestException, stripe.StripeError, ValueError) as error:
                errors.append(f"Deposit {deposit.id}: {error}")
                continue

            success_count += 1

        if success_count:
            self.message_user(
                request,
                f"{success_label} {success_count} deposit hold(s).",
                level=messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                f"Skipped {skipped_count} deposit(s) that were not active authorized holds.",
                level=messages.WARNING,
            )
        if errors:
            preview = "; ".join(errors[:3])
            if len(errors) > 3:
                preview += "; ..."
            self.message_user(
                request,
                f"Failed to {operation} {len(errors)} deposit hold(s). {preview}",
                level=messages.ERROR,
            )

    def _run_single_deposit_action(self, deposit, operation):
        service = get_damage_deposit_service(deposit.payment_provider)
        if operation == "capture":
            return service.capture_deposit(deposit)
        if operation == "release":
            return service.release_deposit(deposit)
        raise ValueError("Unsupported deposit action.")

    def _detail_actions_for_deposit(self, deposit):
        if not self._is_manageable_deposit(deposit):
            return []

        actions = []
        for operation in ("capture", "release"):
            action = self._get_deposit_action(deposit, operation)
            if not action:
                continue
            actions.append(
                {
                    "label": action["label"],
                    "url": reverse(
                        f"admin:{self._deposit_action_url_name()}",
                        args=[quote(deposit.pk), operation],
                    ),
                }
            )
        return actions

    def _get_deposit_action(self, deposit, operation):
        if not self._is_manageable_deposit(deposit):
            return None

        provider_name = deposit.get_payment_provider_display()
        if deposit.payment_provider == DepositProvider.STRIPE:
            provider_detail = f"Stripe payment intent: {deposit.stripe_payment_intent_id}"
            release_summary = f"This will cancel the Stripe hold for {deposit.display_amount}."
        else:
            provider_detail = f"PayPal authorization: {deposit.paypal_authorization_id}"
            release_summary = f"This will void the PayPal authorization for {deposit.display_amount}."

        if operation == "capture":
            return {
                "title": "Capture deposit",
                "label": "Capture deposit",
                "confirm_label": "Confirm capture",
                "summary": f"This will capture the authorized {provider_name} hold for {deposit.display_amount}.",
                "provider_detail": provider_detail,
                "warning": "Capturing turns the hold into a real charge. Use this only for a valid damage claim.",
                "success_message": f"Captured deposit {deposit.id} via {provider_name}.",
            }
        if operation == "release":
            return {
                "title": "Release deposit hold",
                "label": "Release deposit",
                "confirm_label": "Confirm release",
                "summary": release_summary,
                "provider_detail": provider_detail,
                "warning": "Releasing removes the hold without charging the guest.",
                "success_message": f"Released deposit {deposit.id} via {provider_name}.",
            }
        return None

    def _is_manageable_deposit(self, deposit):
        if not deposit or deposit.status != DepositStatus.REQUIRES_CAPTURE:
            return False
        if deposit.payment_provider == DepositProvider.STRIPE:
            return bool(deposit.stripe_payment_intent_id)
        if deposit.payment_provider == DepositProvider.PAYPAL:
            return bool(deposit.paypal_authorization_id)
        return False

    def _change_url(self, deposit):
        return reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[quote(deposit.pk)],
        )

    def _changelist_url(self):
        return reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist")

    def _deposit_action_url_name(self):
        return f"{self.model._meta.app_label}_{self.model._meta.model_name}_deposit_action"


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


@admin.register(ReservationPaymentHold)
class ReservationPaymentHoldAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "item", "display_amount", "status", "capture_after", "created_at")
    list_filter = ("status", "currency", "item")
    search_fields = ("guest_name", "email", "stripe_checkout_session_id", "stripe_payment_intent_id")
    readonly_fields = ("created_at", "updated_at", "display_amount")


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


@admin.register(AvailabilityBlock)
class AvailabilityBlockAdmin(admin.ModelAdmin):
    list_display = ("item", "start_date", "end_date", "reason", "is_active", "updated_at")
    list_filter = ("item", "is_active")
    search_fields = ("item__name", "reason", "notes")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DailyPriceOverride)
class DailyPriceOverrideAdmin(admin.ModelAdmin):
    list_display = ("item", "start_date", "end_date", "nightly_price", "label", "is_active")
    list_filter = ("item", "is_active")
    search_fields = ("item__name", "label", "notes")
    readonly_fields = ("created_at", "updated_at")


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
    list_display = (
        "site_name",
        "logo_status",
        "agent_question_limit",
        "contact_email",
        "request_notifications_email",
        "request_notifications_sms",
        "request_notifications_whatsapp",
        "updated_at",
    )
    readonly_fields = ("logo_preview", "updated_at")
    fieldsets = (
        ("Branding", {"fields": ("site_name", "logo", "logo_url", "logo_preview")}),
        ("Agent settings", {"fields": ("agent_question_limit",)}),
        (
            "Request notifications",
            {
                "fields": (
                    "contact_email",
                    "request_notifications_email",
                    "request_notifications_sms",
                    "request_notifications_whatsapp",
                )
            },
        ),
        ("Public contact", {"fields": ("public_address_label", "updated_at")}),
    )

    @admin.display(description="Logo")
    def logo_status(self, obj):
        return "Uploaded" if obj.logo_display_url else "Using M fallback"

    @admin.display(description="Current logo preview")
    def logo_preview(self, obj):
        if not obj.logo_display_url:
            return format_html(
                '<div style="display:grid;place-items:center;width:72px;height:72px;color:#fff;background:#10665f;border-radius:10px;font-weight:900;font-size:2rem;">M</div>'
            )
        return format_html(
            '<img src="{}" alt="{} logo" style="width:96px;height:96px;object-fit:cover;border-radius:10px;border:1px solid #dbe4dc;">',
            obj.logo_display_url,
            obj.site_name,
        )


@admin.register(AgentKnowledgeSource)
class AgentKnowledgeSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "source_value", "is_active", "sort_order", "updated_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("title", "source_value", "body")
    ordering = ("sort_order", "title")


@admin.register(AgentFAQ)
class AgentFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "item", "language", "priority", "min_score", "is_active", "updated_at")
    list_filter = ("is_active", "category", "language", "item")
    search_fields = ("question", "answer", "keywords", "category")
    autocomplete_fields = ("item",)
    list_editable = ("priority", "min_score", "is_active")
    readonly_fields = ("created_at", "updated_at")


@admin.register(SiteContentBlock)
class SiteContentBlockAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "is_active", "sort_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("key", "title", "body")


admin.site.register(GuestReviewHighlight)
admin.site.register(HouseRule)
