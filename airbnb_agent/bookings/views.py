import csv
import json
from datetime import date, timedelta
from urllib.parse import urlencode
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.templatetags.static import static
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
import requests
import stripe

from .forms import (
    AvailabilityBlockForm,
    BookingInquiryForm,
    DailyPriceOverrideForm,
    DamageDepositForm,
    DonationForm,
    ReservationCancelForm,
    ReservationManageForm,
    SignUpForm,
)
from .models import (
    AgentConversation,
    AgentFAQ,
    AdminAccess,
    AirbnbGuestRecord,
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CalendarFeed,
    ClientSegment,
    CustomerFeedback,
    CustomerProfile,
    DailyPriceOverride,
    DamageDeposit,
    DepositStatus,
    Invoice,
    MarketingConsentStatus,
    MaintenanceEvent,
    MaintenancePaymentStatus,
    MaintenanceStatus,
    MaintenanceWorkType,
    MissionCause,
    PageVisit,
    ReservationPaymentHold,
    SiteSettings,
)
from .ops_finance import DepositHoldOperationsService, PaymentsTransactionsService
from .services import (
    AgentAccessContext,
    AgentIntelligenceOperationsService,
    BookingCalendarService,
    CalendarOperationsService,
    CustomersCRMService,
    MaintenanceOperationsService,
    MaintenanceService,
    OpsReservationProjection,
    ReservationPricingService,
    StayListingService,
)
from .social_auth import SOCIAL_LOGIN_PROVIDER_SPECS, get_social_login_providers
from .social_auth import get_provider_spec, provider_auth_origin, request_origin


ops_staff_required = user_passes_test(
    lambda user: user.is_active and user.is_staff,
    login_url=reverse_lazy("bookings:login"),
)


def _build_openai_client(api_key):
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _accept_payment_documents(request, inquiry):
    if not inquiry:
        return None
    wants_json = (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )
    if request.POST.get("property_rules_accepted") != "1" or request.POST.get("damage_terms_accepted") != "1":
        if wants_json:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "Please accept the property rules and damage deposit terms before continuing.",
                },
                status=400,
            )
        messages.error(request, "Please accept the property rules and damage deposit terms before continuing.")
        return redirect(reverse("bookings:home") + "#booking")

    site_settings = SiteSettings.current()
    now = timezone.now()
    update_fields = ["updated_at"]
    if not inquiry.property_rules_accepted_at:
        inquiry.property_rules_accepted_at = now
        update_fields.append("property_rules_accepted_at")
    if not inquiry.damage_terms_accepted_at:
        inquiry.damage_terms_accepted_at = now
        update_fields.append("damage_terms_accepted_at")
    inquiry.accepted_property_rules_version = site_settings.property_rules_version
    inquiry.accepted_damage_terms_version = site_settings.damage_terms_version
    update_fields.extend(["accepted_property_rules_version", "accepted_damage_terms_version"])
    inquiry.save(update_fields=update_fields)
    return None


class HomePageView(TemplateView):
    template_name = "bookings/home.html"

    @staticmethod
    def booking_context(request, form=None, deposit_form=None):
        selected_item_id = request.GET.get("item", "")
        deposit_inquiry = None
        deposit_for_id = request.GET.get("deposit_for", "")
        if deposit_for_id.isdigit():
            deposit_inquiry = (
                BookingInquiry.objects.filter(pk=deposit_for_id, is_admin_test=False)
                .select_related("item")
                .first()
            )
        if form is None and selected_item_id:
            form = BookingInquiryForm(initial={"item": selected_item_id}, user=request.user)
        featured_items = (
            BookableItem.objects.filter(is_active=True, is_featured=True)
            .prefetch_related("gallery_images", "review_themes")
        )
        deposit_initial = {"item": selected_item_id} if selected_item_id else None
        if deposit_inquiry:
            deposit_initial = {
                "inquiry_id": deposit_inquiry.id,
                "item": deposit_inquiry.item_id,
                "guest_name": deposit_inquiry.guest_name,
                "email": deposit_inquiry.email,
            }
        return {
            "booking_form": form or BookingInquiryForm(user=request.user),
            "deposit_form": deposit_form or DamageDepositForm(initial=deposit_initial),
            "donation_form": DonationForm(),
            "deposit_amount": settings.DEPOSIT_AMOUNT_CENTS / 100,
            "deposit_currency": settings.DEPOSIT_CURRENCY.upper(),
            "deposit_inquiry": deposit_inquiry,
            "show_deposit": bool(deposit_inquiry or request.GET.get("deposit") == "1"),
            "area_tiles": [
                {
                    "title": "Santo Domingo Norte",
                    "caption": "City base near the Jacobo Majluta corridor.",
                    "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/SantoDomingoedit.JPG",
                    "class_name": "is-city",
                },
                {
                    "title": "Malls and restaurants",
                    "caption": "Easy city plans near Embassy-area errands.",
                    "image_url": "https://sambil.do/wp-content/uploads/2024/08/LY2A0949.jpg",
                    "class_name": "is-mall",
                },
                {
                    "title": "Juan Dolio beaches",
                    "caption": "A calmer beach-day escape east of Santo Domingo.",
                    "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/62/Juan_Dolio_Beach_1.jpg",
                    "class_name": "is-beach",
                },
                {
                    "title": "Nightlife and family nights",
                    "caption": "Food, music, and warm evenings close to the city.",
                    "image_url": "https://sambil.do/wp-content/uploads/2024/08/LY2A0977.jpg",
                    "class_name": "is-hosted",
                },
            ],
            "featured_items": featured_items,
            "hero_item": featured_items.filter(airbnb_listing_id="588632365342578374").first()
            or featured_items.first(),
            "service_items": BookableItem.objects.filter(
                is_active=True,
                category__in=[
                    BookingCategory.SERVICE,
                    BookingCategory.EXPERIENCE,
                    BookingCategory.TRANSPORT,
                ],
            ),
            "active_items": BookableItem.objects.filter(is_active=True),
            "mission_causes": MissionCause.objects.filter(is_active=True),
            "selected_item_id": selected_item_id,
            "submitted": request.GET.get("submitted") == "1",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.booking_context(self.request))
        return context


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ModernSiteView(TemplateView):
    template_name = "bookings/modern_site.html"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ModernAccountView(LoginRequiredMixin, TemplateView):
    template_name = "bookings/modern_site.html"


@method_decorator(never_cache, name="dispatch")
class PublicSiteSummaryAPIView(View):
    def get(self, request):
        settings_obj = SiteSettings.current()
        logo_url = settings_obj.logo_display_url or static("bookings/brand/mladis-connected-intelligence.png")
        if settings_obj.logo:
            try:
                if not settings_obj.logo.storage.exists(settings_obj.logo.name):
                    logo_url = settings_obj.logo_url or static("bookings/brand/mladis-connected-intelligence.png")
            except OSError:
                logo_url = settings_obj.logo_url or static("bookings/brand/mladis-connected-intelligence.png")
        if logo_url and logo_url.startswith("/"):
            logo_url = request.build_absolute_uri(logo_url)

        stays = (
            BookableItem.objects.filter(is_active=True, is_featured=True, category=BookingCategory.STAY)
            .prefetch_related("gallery_images", "guest_review_highlights", "house_rules")
            .order_by("-is_featured", "name")
        )
        data = {
            "site_name": settings_obj.site_name,
            "logo_url": logo_url,
            "contact_email": settings_obj.contact_email,
            "public_address_label": settings_obj.public_address_label,
            "deposit_amount": f"${settings.DEPOSIT_AMOUNT_CENTS / 100:,.0f}",
            "stays": [self._stay_payload(request, stay) for stay in stays],
            "area_tiles": self._area_tiles(),
            "mission_causes": [
                {"title": cause.name, "description": cause.description}
                for cause in MissionCause.objects.filter(is_active=True).order_by("sort_order", "name")[:3]
            ],
            "social_providers": [
                {
                    "id": provider["id"],
                    "label": provider["label"],
                    "login_url": provider["login_url"],
                    "is_configured": provider["is_configured"],
                    "is_launchable": provider["is_launchable"],
                    "disabled_reason": provider["disabled_reason"],
                    "help_text": provider["help_text"],
                }
                for provider in get_social_login_providers(request)
            ],
            "agent": AgentAccessContext.from_request(request).to_public_payload(),
            "chatkit": self._chatkit_payload(request),
            "generated_at": timezone.now().isoformat(),
        }
        return JsonResponse(data)

    @staticmethod
    def _area_tiles():
        return [
            {
                "title": "Santo Domingo Norte",
                "caption": "A practical base near Colinas del Arroyo II, Los Guaricanos, and Jacobo Majluta.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/SantoDomingoedit.JPG",
            },
            {
                "title": "Malls and restaurants",
                "caption": "Shopping, dinner plans, and Embassy-corridor errands within the city rhythm.",
                "image_url": "https://sambil.do/wp-content/uploads/2024/08/LY2A0949.jpg",
            },
            {
                "title": "Juan Dolio beach days",
                "caption": "A prettier beach-day escape east of Santo Domingo when guests want island time.",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/62/Juan_Dolio_Beach_1.jpg",
            },
            {
                "title": "Hosted city nights",
                "caption": "Food, music, family plans, and direct host support before and during the stay.",
                "image_url": "https://sambil.do/wp-content/uploads/2024/08/LY2A0977.jpg",
            },
        ]

    def _stay_payload(self, request, stay):
        gallery = list(stay.gallery_images.all())
        image_url = stay.image or (gallery[0].image_url if gallery else "")
        if image_url and image_url.startswith("/"):
            image_url = request.build_absolute_uri(image_url)
        detail_url = request.build_absolute_uri(stay.get_absolute_url())
        return {
            "id": stay.id,
            "name": stay.name,
            "slug": stay.slug,
            "headline": stay.marketing_headline or stay.short_description,
            "description": stay.marketing_description or stay.description or stay.short_description,
            "location": stay.location_label,
            "image_url": image_url,
            "rating": str(stay.airbnb_rating or ""),
            "review_label": stay.review_label,
            "price_label": stay.headline_price,
            "stat_list": stay.stat_list,
            "detail_url": detail_url,
            "airbnb_url": stay.airbnb_embed_url,
            "pricing": ReservationPricingService().preview_payload(stay),
            "gallery": [
                {
                    "image_url": image.image_url,
                    "alt_text": image.alt_text,
                    "caption": image.caption,
                }
                for image in gallery[:8]
            ],
            "highlights": [
                {
                    "title": highlight.title,
                    "body": highlight.body,
                    "source_label": highlight.source_label,
                }
                for highlight in stay.guest_review_highlights.all()[:4]
            ],
            "rules": [
                {
                    "title": rule.title,
                    "description": rule.description,
                }
                for rule in stay.house_rules.filter(is_active=True)[:6]
            ],
        }

    @staticmethod
    def _chatkit_payload(request):
        if settings.OPENAI_CHATKIT_WORKFLOW_ID and settings.OPENAI_API_KEY:
            return {
                "mode": "managed",
                "session_url": request.build_absolute_uri(reverse("bookings:chatkit-session-api")),
            }
        if settings.OPENAI_CHATKIT_API_URL and settings.OPENAI_CHATKIT_DOMAIN_KEY:
            return {
                "mode": "custom",
                "api_url": settings.OPENAI_CHATKIT_API_URL,
                "domain_key": settings.OPENAI_CHATKIT_DOMAIN_KEY,
            }
        return None


@method_decorator(never_cache, name="dispatch")
class ChatKitSessionAPIView(View):
    @staticmethod
    def _chatkit_user(request):
        if request.user.is_authenticated:
            return f"user:{request.user.pk}"

        if request.session.session_key is None:
            request.session.save()
        return f"anon:{request.session.session_key}"

    def post(self, request):
        access = AgentAccessContext.from_request(request)
        if not access.can_ask:
            return JsonResponse(access.denial_payload(), status=access.denial_status)

        if not settings.OPENAI_CHATKIT_WORKFLOW_ID or not settings.OPENAI_API_KEY:
            return JsonResponse({"error": "ChatKit managed sessions are not configured."}, status=503)

        workflow = {"id": settings.OPENAI_CHATKIT_WORKFLOW_ID}
        if settings.OPENAI_CHATKIT_WORKFLOW_VERSION:
            workflow["version"] = settings.OPENAI_CHATKIT_WORKFLOW_VERSION

        session = _build_openai_client(settings.OPENAI_API_KEY).beta.chatkit.sessions.create(
            user=self._chatkit_user(request),
            workflow=workflow,
        )
        return JsonResponse(
            {
                "client_secret": session.client_secret,
                "expires_at": session.expires_at,
                "session_id": session.id,
            }
        )


@method_decorator(never_cache, name="dispatch")
class AccountSummaryAPIView(View):
    def get(self, request):
        agent_access = AgentAccessContext.from_request(request)
        if not request.user.is_authenticated:
            return JsonResponse(
                {
                    "profile": None,
                    "authenticated": False,
                    "agent": agent_access.to_public_payload(),
                    "generated_at": timezone.now().isoformat(),
                },
                status=200,
            )
        reservations = (
            BookingInquiry.objects.filter(Q(user=request.user) | Q(email__iexact=request.user.email))
            .select_related("item", "coupon", "cancellation_policy")
            .order_by("-created_at")
        )
        invoices = (
            Invoice.objects.filter(Q(recipient_email__iexact=request.user.email) | Q(customer_profile__user=request.user))
            .select_related("inquiry", "customer_profile")
            .order_by("-created_at")
        )
        profile = getattr(request.user, "customer_profile", None)
        return JsonResponse(
            {
                "profile": {
                    "name": request.user.get_full_name() or request.user.username or request.user.email,
                    "email": request.user.email,
                    "phone": profile.phone if profile else "",
                    "is_staff": request.user.is_staff or request.user.is_superuser,
                    "is_superuser": request.user.is_superuser,
                },
                "authenticated": True,
                "is_staff": request.user.is_staff or request.user.is_superuser,
                "is_superuser": request.user.is_superuser,
                "agent": agent_access.to_public_payload(),
                "reservations": [self._reservation_payload(request, reservation) for reservation in reservations],
                "invoices": [self._invoice_payload(request, invoice) for invoice in invoices],
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _reservation_payload(request, reservation):
        item = reservation.item
        return {
            "id": reservation.id,
            "guest_name": reservation.guest_name,
            "stay_name": item.business_display_name if item else "Flexible stay",
            "check_in": reservation.check_in.isoformat(),
            "check_out": reservation.check_out.isoformat(),
            "guests": reservation.guests,
            "phone": reservation.phone,
            "status": reservation.get_status_display(),
            "can_cancel": reservation.can_customer_cancel,
            "display_subtotal": reservation.display_subtotal,
            "display_discount": reservation.display_discount,
            "display_reservation_payment": reservation.display_reservation_payment,
            "display_total": reservation.display_total,
            "display_deposit": reservation._display_money(reservation.deposit_cents),
            "reservation_payment_cents": reservation.reservation_payment_cents,
            "pricing": ReservationPricingService().preview_payload(item),
            "coupon_code": reservation.coupon_code,
            "message": reservation.message,
            "detail_url": request.build_absolute_uri(reverse("bookings:reservation-detail", kwargs={"pk": reservation.pk})),
            "edit_url": request.build_absolute_uri(reverse("bookings:reservation-edit", kwargs={"pk": reservation.pk})),
            "cancel_url": request.build_absolute_uri(reverse("bookings:reservation-cancel", kwargs={"pk": reservation.pk})),
            "airbnb_url": item.airbnb_embed_url if item else "",
            "created_at": reservation.created_at.isoformat(),
        }

    @staticmethod
    def _invoice_payload(request, invoice):
        return {
            "id": invoice.id,
            "title": invoice.title,
            "status": invoice.get_status_display(),
            "display_total": invoice.display_total,
            "print_url": request.build_absolute_uri(reverse("bookings:invoice-print", kwargs={"token": invoice.public_token})),
            "created_at": invoice.created_at.isoformat(),
        }


class StayDetailView(DetailView):
    model = BookableItem
    template_name = "bookings/stay_detail.html"
    context_object_name = "stay"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            BookableItem.objects.filter(is_active=True, category=BookingCategory.STAY)
            .prefetch_related("gallery_images", "review_themes", "guest_review_highlights", "house_rules")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "booking_form": BookingInquiryForm(initial={"item": self.object.id}, user=self.request.user),
                "deposit_form": DamageDepositForm(initial={"item": self.object.id}),
                "deposit_amount": settings.DEPOSIT_AMOUNT_CENTS / 100,
                "deposit_currency": settings.DEPOSIT_CURRENCY.upper(),
                "other_stays": BookableItem.objects.filter(
                    is_active=True,
                    is_featured=True,
                    category=BookingCategory.STAY,
                )
                .exclude(id=self.object.id)
                .prefetch_related("gallery_images"),
                "active_items": BookableItem.objects.filter(is_active=True),
            }
        )
        return context


class AboutPageView(TemplateView):
    template_name = "bookings/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "donation_form": DonationForm(),
                "mission_causes": MissionCause.objects.filter(is_active=True),
                "featured_items": BookableItem.objects.filter(is_active=True, is_featured=True),
                "active_items": BookableItem.objects.filter(is_active=True),
                "gallery_tiles": [
                    {
                        "title": "Santo Domingo Norte",
                        "text": "A practical home base near Colinas del Arroyo II, Los Guaricanos, and the Jacobo Majluta corridor.",
                        "class_name": "is-city",
                        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/SantoDomingoedit.JPG",
                    },
                    {
                        "title": "Embassy and malls corridor",
                        "text": "Easy positioning for Embassy-area errands, shopping, restaurants, and family plans in the city.",
                        "class_name": "is-mall",
                        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/SantoDomingoedit.JPG",
                    },
                    {
                        "title": "Juan Dolio day trips",
                        "text": "A beach-day option east of Santo Domingo for guests who want more island in the itinerary.",
                        "class_name": "is-beach",
                        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/62/Juan_Dolio_Beach_1.jpg",
                    },
                    {
                        "title": "Hosted with care",
                        "text": "Direct support before, during, and after your stay.",
                        "class_name": "is-hosted",
                        "image_url": "https://a0.muscache.com/im/pictures/miso/Hosting-582161420407543691/original/c097c0de-d8eb-45da-be8a-644065f20ab8.jpeg?im_w=1200&quality=80&auto=webp",
                    },
                ],
            }
        )
        return context


class PrivacyPolicyPageView(TemplateView):
    template_name = "bookings/privacy_policy.html"


class BusinessPageView(TemplateView):
    template_name = "bookings/business.html"


class TermsPageView(TemplateView):
    template_name = "bookings/terms.html"


class DataDeletionPageView(TemplateView):
    template_name = "bookings/data_deletion.html"


@method_decorator(csrf_exempt, name="dispatch")
class DataDeletionCallbackView(View):
    def get(self, request):
        return JsonResponse(
            {
                "instructions_url": request.build_absolute_uri(reverse("bookings:data-deletion")),
                "message": "Send Meta data deletion callbacks to this endpoint with POST.",
            }
        )

    def post(self, request):
        confirmation_code = uuid4().hex
        return JsonResponse(
            {
                "url": request.build_absolute_uri(reverse("bookings:data-deletion")),
                "confirmation_code": confirmation_code,
            }
        )


class BookingInquiryCreateView(View):
    def post(self, request):
        form = BookingInquiryForm(request.POST, user=request.user)
        if form.is_valid():
            from .services import BookingEmailService, ReservationRequestService

            inquiry = ReservationRequestService().create_from_form(form, request)
            request.session["payment_inquiry_id"] = inquiry.id
            BookingEmailService().send_inquiry_notifications(inquiry, request=request)
            messages.success(
                request,
                f"Thanks, {inquiry.guest_name}. Your booking is started.",
            )
            if self._wants_json(request):
                return JsonResponse(
                    {
                        "ok": True,
                        "message": "Request received. Continue with the secure deposit hold.",
                        "inquiry": self._inquiry_payload(request, inquiry),
                    },
                    status=201,
                )
            if inquiry.is_admin_test:
                return redirect(reverse("bookings:dashboard"))
            return redirect(reverse("bookings:home") + f"?submitted=1&deposit_for={inquiry.id}#deposit")

        if self._wants_json(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return render(
            request,
            "bookings/home.html",
            HomePageView.booking_context(request, form=form),
            status=400,
        )

    @staticmethod
    def _wants_json(request):
        return (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or "application/json" in request.headers.get("accept", "")
        )

    @staticmethod
    def _inquiry_payload(request, inquiry):
        site_settings = SiteSettings.current()
        item = inquiry.item
        return {
            "id": inquiry.id,
            "request_key": inquiry.request_key,
            "guest_name": inquiry.guest_name,
            "email": inquiry.email,
            "phone": inquiry.phone,
            "item_id": inquiry.item_id,
            "stay_name": item.business_display_name if item else "Flexible / help me choose",
            "check_in": inquiry.check_in.isoformat(),
            "check_out": inquiry.check_out.isoformat(),
            "nights": inquiry.nights,
            "guests": inquiry.guests,
            "coupon_code": inquiry.coupon_code,
            "display_subtotal": inquiry.display_subtotal,
            "display_discount": inquiry.display_discount,
            "display_deposit": inquiry._display_money(inquiry.deposit_cents),
            "display_reservation_payment": inquiry.display_reservation_payment,
            "display_total": inquiry.display_total,
            "reservation_payment_cents": inquiry.reservation_payment_cents,
            "deposit_checkout_url": request.build_absolute_uri(reverse("bookings:deposit-checkout")),
            "reservation_payment_checkout_url": request.build_absolute_uri(
                reverse("bookings:reservation-payment-checkout")
            ),
            "payment_confirmation_url": request.build_absolute_uri(
                reverse("bookings:payment-confirmation", kwargs={"token": inquiry.payment_confirmation_token})
            ),
            "property_rules_url": request.build_absolute_uri(reverse("bookings:property-rules")),
            "damage_terms_url": request.build_absolute_uri(reverse("bookings:damage-deposit-terms")),
            "documents_accepted": inquiry.required_documents_accepted,
            "property_rules_title": site_settings.property_rules_title,
            "property_rules_version": site_settings.property_rules_version,
            "property_rules_body": site_settings.property_rules_body,
            "damage_terms_title": site_settings.damage_terms_title,
            "damage_terms_version": site_settings.damage_terms_version,
            "damage_terms_body": site_settings.damage_terms_body,
            "admin_test": inquiry.is_admin_test,
        }


class PolicyDocumentView(View):
    document_kind = "property_rules"
    template_name = "bookings/policy_document.html"

    def get(self, request):
        site_settings = SiteSettings.current()
        if self.document_kind == "damage_terms":
            title = site_settings.damage_terms_title
            body = site_settings.damage_terms_body
            version = site_settings.damage_terms_version
        else:
            title = site_settings.property_rules_title
            body = site_settings.property_rules_body
            version = site_settings.property_rules_version
        return render(
            request,
            self.template_name,
            {
                "title": title,
                "body": body,
                "version": version,
                "document_kind": self.document_kind,
                "site_settings": site_settings,
            },
        )


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("bookings:dashboard")

    def form_valid(self, form):
        from .services import AdminAccessService

        response = super().form_valid(form)
        CustomerProfile.objects.get_or_create(
            user=self.object,
            defaults={
                "email": self.object.email,
                "name": self.object.get_full_name() or self.object.username,
                "phone": form.cleaned_data.get("phone", ""),
            },
        )
        AdminAccessService().apply_to_user(self.object)
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        return response


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "bookings/account_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "reservations": self._reservation_queryset(),
                "invoices": Invoice.objects.filter(
                    Q(recipient_email__iexact=self.request.user.email)
                    | Q(customer_profile__user=self.request.user)
                ).select_related("inquiry", "customer_profile"),
            }
        )
        return context

    def _reservation_queryset(self):
        return BookingInquiry.objects.filter(
            Q(user=self.request.user) | Q(email__iexact=self.request.user.email)
        ).select_related("item", "coupon", "cancellation_policy")


class OwnedReservationMixin(LoginRequiredMixin):
    model = BookingInquiry
    context_object_name = "reservation"

    def get_queryset(self):
        return BookingInquiry.objects.filter(
            Q(user=self.request.user) | Q(email__iexact=self.request.user.email)
        ).select_related("item", "coupon", "cancellation_policy")


class ReservationDetailView(OwnedReservationMixin, DetailView):
    template_name = "bookings/reservation_detail.html"


class ModernReservationDetailView(OwnedReservationMixin, TemplateView):
    template_name = "bookings/modern_site.html"

    def get(self, request, pk):
        get_object_or_404(self.get_queryset(), pk=pk)
        return super().get(request, pk=pk)


class ReservationUpdateView(OwnedReservationMixin, UpdateView):
    form_class = ReservationManageForm
    template_name = "bookings/reservation_form.html"

    def dispatch(self, request, *args, **kwargs):
        reservation = self.get_object()
        if reservation.status not in {BookingStatus.NEW, BookingStatus.REVIEWING, BookingStatus.QUOTED}:
            messages.warning(request, "This reservation can no longer be edited. Please contact MLADIS.")
            return redirect(reverse("bookings:reservation-detail", kwargs={"pk": reservation.pk}))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("bookings:reservation-detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        from .services import ReservationRequestService

        self.object = form.save(commit=False)
        ReservationRequestService().prepare(self.object, coupon=self.object.coupon, redeem_coupon=False)
        self.object.save()
        messages.success(self.request, "Reservation request updated with the latest price.")
        return redirect(self.get_success_url())


class ModernReservationUpdateView(ReservationUpdateView):
    template_name = "bookings/modern_site.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return render(request, self.template_name)


class ReservationCancelView(OwnedReservationMixin, View):
    template_name = "bookings/reservation_cancel.html"

    def get(self, request, pk):
        reservation = get_object_or_404(self.get_queryset(), pk=pk)
        return render(request, self.template_name, {"reservation": reservation, "form": ReservationCancelForm()})

    def post(self, request, pk):
        reservation = get_object_or_404(self.get_queryset(), pk=pk)
        form = ReservationCancelForm(request.POST)
        if not reservation.can_customer_cancel:
            messages.error(request, "This reservation is outside the current cancellation window.")
            return redirect(reverse("bookings:reservation-detail", kwargs={"pk": reservation.pk}))
        if form.is_valid():
            reservation.cancel(reason=form.cleaned_data.get("reason", ""), by_user=request.user)
            messages.success(request, "Your cancellation request was recorded.")
            return redirect(reverse("bookings:dashboard"))
        return render(request, self.template_name, {"reservation": reservation, "form": form}, status=400)


class ModernReservationCancelView(ReservationCancelView):
    template_name = "bookings/modern_site.html"

    def get(self, request, pk):
        get_object_or_404(self.get_queryset(), pk=pk)
        return render(request, self.template_name)


class InvoicePrintView(DetailView):
    model = Invoice
    template_name = "bookings/invoice_print.html"
    context_object_name = "invoice"
    slug_field = "public_token"
    slug_url_kwarg = "token"

    def get_queryset(self):
        return Invoice.objects.prefetch_related("line_items").select_related("inquiry", "customer_profile")


class DamageDepositCheckoutView(View):
    def post(self, request):
        form = DamageDepositForm(request.POST)
        if not form.is_valid():
            if self._wants_json(request):
                return JsonResponse(
                    {
                        "ok": False,
                        "message": "Please add your name, email, and stay before starting the deposit hold.",
                        "errors": form.errors,
                    },
                    status=400,
                )
            messages.error(request, "Please add your name, email, and listing before starting the deposit hold.")
            context = HomePageView.booking_context(request, deposit_form=form)
            context["show_deposit"] = True
            return render(request, "bookings/home.html", context, status=400)

        deposit = form.save(commit=False)
        document_error = _accept_payment_documents(request, deposit.inquiry)
        if document_error:
            return document_error
        deposit.save()
        from .services import get_damage_deposit_service

        service = get_damage_deposit_service(form.cleaned_data.get("payment_provider"))
        result = service.create_checkout_session(deposit, request)
        if result.success:
            if deposit.inquiry_id:
                request.session["payment_inquiry_id"] = deposit.inquiry_id
            if self._wants_json(request):
                return JsonResponse(
                    {
                        "ok": True,
                        "message": result.message,
                        "checkout_url": result.checkout_url,
                        "deposit_id": deposit.id,
                        "provider": deposit.payment_provider,
                        "status": deposit.status,
                    },
                    status=201,
                )
            return redirect(result.checkout_url)

        if self._wants_json(request):
            return JsonResponse(
                {
                    "ok": False,
                    "message": result.message,
                    "deposit_id": deposit.id,
                    "provider": deposit.payment_provider,
                    "status": deposit.status,
                },
                status=400,
            )
        messages.warning(request, result.message)
        deposit_for = f"?deposit_for={deposit.inquiry_id}" if deposit.inquiry_id else "?deposit=1"
        return redirect(reverse("bookings:home") + f"{deposit_for}#deposit")

    @staticmethod
    def _wants_json(request):
        return (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or "application/json" in request.headers.get("accept", "")
        )


class DonationCheckoutView(View):
    def post(self, request):
        from .services import DonationService

        form = DonationForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please choose a valid donation amount and mission cause.")
            context = AboutPageView().get_context_data()
            context["donation_form"] = form
            return render(request, "bookings/about.html", context, status=400)

        donation = form.save()
        result = DonationService().create_checkout_session(donation, request)
        if result.success:
            return redirect(result.checkout_url)

        messages.warning(request, result.message)
        return redirect(reverse("bookings:about") + "#mission")


class DonationSuccessView(View):
    def get(self, request):
        from .services import DonationService

        session_id = request.GET.get("session_id", "")
        donation = None
        if session_id:
            try:
                donation = DonationService().sync_checkout_session(session_id)
            except stripe.StripeError:
                donation = None

        if donation:
            messages.success(request, f"Thank you for your {donation.display_amount} donation.")
        else:
            messages.success(request, "Thank you. Your donation checkout was completed.")
        return redirect(reverse("bookings:about") + "#mission")


class DamageDepositSuccessView(View):
    def get(self, request):
        from .services import DamageDepositService

        session_id = request.GET.get("session_id", "")
        deposit = None
        if session_id:
            try:
                deposit = DamageDepositService().sync_checkout_session(session_id, request=request)
            except stripe.StripeError:
                deposit = None

        if deposit:
            messages.success(
                request,
                f"Your {deposit.display_amount} damage deposit authorization is recorded.",
            )
            if deposit.inquiry_id:
                request.session["payment_inquiry_id"] = deposit.inquiry_id
                return redirect(
                    reverse(
                        "bookings:payment-confirmation",
                        kwargs={"token": deposit.inquiry.payment_confirmation_token},
                    )
                )
        else:
            messages.success(request, "Thanks. Your deposit checkout was completed.")
        return redirect(reverse("bookings:home") + "#deposit")


class ReservationPaymentContextAPIView(View):
    def get(self, request):
        inquiry = self._inquiry(request)
        if not inquiry:
            return JsonResponse({"ok": False, "message": "Reservation request not found."}, status=404)
        if not self._can_access(request, inquiry):
            return JsonResponse({"ok": False, "message": "This payment window is not available."}, status=403)

        from .services import ReservationRequestService

        ReservationRequestService().prepare(inquiry, coupon=inquiry.coupon, redeem_coupon=False)
        inquiry.save(
            update_fields=[
                "subtotal_cents",
                "discount_cents",
                "deposit_cents",
                "total_cents",
                "currency",
                "updated_at",
            ]
        )
        request.session["payment_inquiry_id"] = inquiry.id
        return JsonResponse({"ok": True, "inquiry": BookingInquiryCreateView._inquiry_payload(request, inquiry)})

    def _inquiry(self, request):
        inquiry_id = request.GET.get("inquiry_id") or request.session.get("payment_inquiry_id")
        if not inquiry_id:
            return None
        return (
            BookingInquiry.objects.select_related("item", "coupon", "customer_profile", "user")
            .filter(pk=inquiry_id)
            .first()
        )

    @staticmethod
    def _can_access(request, inquiry):
        if request.session.get("payment_inquiry_id") == inquiry.id:
            return True
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return True
            if inquiry.user_id == request.user.id:
                return True
            if request.user.email and inquiry.email.lower() == request.user.email.lower():
                return True
        return False


class ReservationPaymentCheckoutView(View):
    def post(self, request):
        inquiry = self._inquiry(request)
        if not inquiry:
            return JsonResponse({"ok": False, "message": "Reservation request not found."}, status=404)
        if not ReservationPaymentContextAPIView._can_access(request, inquiry):
            return JsonResponse({"ok": False, "message": "This payment hold is not available."}, status=403)

        from .services import ReservationPaymentHoldService

        document_error = _accept_payment_documents(request, inquiry)
        if document_error:
            return document_error
        service = ReservationPaymentHoldService()
        if request.POST.get("payment_choice") == "combined":
            result = service.create_combined_checkout_for_inquiry(inquiry, request)
        else:
            result = service.create_checkout_for_inquiry(inquiry, request)
        request.session["payment_inquiry_id"] = inquiry.id
        hold = inquiry.payment_holds.order_by("-created_at").first()
        if result.success:
            return JsonResponse(
                {
                    "ok": True,
                    "message": result.message,
                    "checkout_url": result.checkout_url,
                    "payment_hold_id": hold.id if hold else None,
                    "status": hold.status if hold else "",
                },
                status=201,
            )
        return JsonResponse(
            {
                "ok": False,
                "message": result.message,
                "payment_hold_id": hold.id if hold else None,
                "status": hold.status if hold else "",
            },
            status=400,
        )

    @staticmethod
    def _inquiry(request):
        inquiry_id = request.POST.get("inquiry_id") or request.session.get("payment_inquiry_id")
        if not inquiry_id:
            return None
        return (
            BookingInquiry.objects.select_related("item", "coupon", "customer_profile", "user")
            .filter(pk=inquiry_id)
            .first()
        )


class ReservationPaymentSuccessView(View):
    def get(self, request):
        from .services import ReservationPaymentHoldService

        session_id = request.GET.get("session_id", "")
        hold = None
        if session_id:
            try:
                hold = ReservationPaymentHoldService().sync_checkout_session(session_id, request=request)
            except stripe.StripeError:
                hold = None

        if hold:
            messages.success(
                request,
                f"Your {hold.display_amount} reservation payment authorization is recorded.",
            )
            if hold.inquiry_id:
                request.session["payment_inquiry_id"] = hold.inquiry_id
                return redirect(
                    reverse(
                        "bookings:payment-confirmation",
                        kwargs={"token": hold.inquiry.payment_confirmation_token},
                    )
                )
        messages.success(request, "Thanks. Your reservation payment checkout was completed.")
        return redirect(reverse("bookings:home") + "#booking")


class CombinedPaymentCheckoutView(View):
    def get(self, request, token):
        from .services import ReservationPaymentHoldService

        inquiry = get_object_or_404(
            BookingInquiry.objects.select_related("item"),
            payment_confirmation_token=token,
        )
        checkout_url = (
            inquiry.payment_holds.exclude(checkout_url="")
            .order_by("-created_at")
            .values_list("checkout_url", flat=True)
            .first()
            or ""
        )
        if checkout_url.startswith("http") and "/payments/combined-checkout/" not in checkout_url:
            return redirect(checkout_url)
        service = ReservationPaymentHoldService()
        result = service.create_combined_checkout_for_inquiry(inquiry, request)
        if result.success and result.checkout_url:
            return redirect(result.checkout_url)
        messages.error(request, result.message or "The combined checkout could not be restarted.")
        return redirect(reverse("bookings:home") + "#booking")


class CombinedPaymentSuccessView(View):
    def get(self, request):
        from .services import ReservationPaymentHoldService

        session_id = request.GET.get("session_id", "")
        setup_intent_id = request.GET.get("setup_intent", "")
        deposit = None
        hold = None
        service = ReservationPaymentHoldService()
        if session_id:
            try:
                deposit, hold = service.finalize_combined_checkout_session(session_id, request=request)
            except stripe.StripeError as error:
                messages.error(request, f"Stripe could not finish the combined authorization: {error}")
        elif setup_intent_id:
            try:
                deposit, hold = service.finalize_combined_setup_intent(setup_intent_id, request=request)
            except stripe.StripeError as error:
                messages.error(request, f"Stripe could not finish the combined authorization: {error}")

        record = hold or deposit
        if record and record.inquiry_id:
            request.session["payment_inquiry_id"] = record.inquiry_id
            messages.success(request, "Payment confirmed. Your MLADIS reservation authorization is recorded.")
            return redirect(
                reverse(
                    "bookings:payment-confirmation",
                    kwargs={"token": record.inquiry.payment_confirmation_token},
                )
            )
        messages.error(request, "We could not confirm the combined payment authorization. Please contact MLADIS.")
        return redirect(reverse("bookings:home") + "#booking")


class PaymentConfirmationView(View):
    template_name = "bookings/payment_confirmation.html"

    def get(self, request, token):
        inquiry = get_object_or_404(
            BookingInquiry.objects.select_related("item").prefetch_related("damage_deposits", "payment_holds"),
            payment_confirmation_token=token,
        )
        context = self._context(request, inquiry)
        if request.GET.get("download") == "1":
            response = HttpResponse(self._download_body(context), content_type="text/plain; charset=utf-8")
            response["Content-Disposition"] = (
                f'attachment; filename="{inquiry.request_key.lower()}-payment-confirmation.txt"'
            )
            return response
        return render(request, self.template_name, context)

    def _context(self, request, inquiry):
        deposit = self._preferred_record(inquiry.damage_deposits.all())
        hold = self._preferred_record(inquiry.payment_holds.all())
        confirmation_url = request.build_absolute_uri(
            reverse("bookings:payment-confirmation", kwargs={"token": inquiry.payment_confirmation_token})
        )
        share_text = (
            f"{inquiry.request_key} payment confirmation for "
            f"{inquiry.item.business_display_name if inquiry.item else 'MLADIS reservation'}: {confirmation_url}"
        )
        return {
            "inquiry": inquiry,
            "deposit": deposit,
            "hold": hold,
            "confirmation_url": confirmation_url,
            "download_url": f"{confirmation_url}?download=1",
            "mailto_url": "mailto:?" + urlencode(
                {
                    "subject": f"{inquiry.request_key} MLADIS payment confirmation",
                    "body": share_text,
                }
            ),
            "whatsapp_url": "https://wa.me/?" + urlencode({"text": share_text}),
            "sms_url": "sms:?" + urlencode({"body": share_text}),
            "site_settings": SiteSettings.current(),
        }

    @staticmethod
    def _preferred_record(records):
        ordered = sorted(records, key=lambda record: record.created_at, reverse=True)
        for status in (DepositStatus.REQUIRES_CAPTURE, DepositStatus.CAPTURED, DepositStatus.CHECKOUT_CREATED):
            for record in ordered:
                if record.status == status:
                    return record
        return ordered[0] if ordered else None

    @staticmethod
    def _download_body(context):
        inquiry = context["inquiry"]
        deposit = context["deposit"]
        hold = context["hold"]
        lines = [
            "MLADIS payment confirmation",
            "",
            f"Reference: {inquiry.request_key}",
            f"Guest: {inquiry.guest_name}",
            f"Email: {inquiry.email}",
            f"Stay: {inquiry.item.business_display_name if inquiry.item else 'Flexible / help me choose'}",
            f"Dates: {inquiry.check_in} to {inquiry.check_out}",
            f"Guests: {inquiry.guests}",
            f"Reservation payment hold: {hold.display_amount if hold else inquiry.display_reservation_payment}",
            f"Reservation payment status: {hold.get_status_display() if hold else 'Pending'}",
            f"Damage deposit hold: {deposit.display_amount if deposit else inquiry.display_deposit}",
            f"Damage deposit status: {deposit.get_status_display() if deposit else 'Pending'}",
            "",
            f"Confirmation URL: {context['confirmation_url']}",
        ]
        return "\n".join(lines)


class PayPalDamageDepositSuccessView(View):
    def get(self, request):
        from .services import PayPalAPIError, PayPalDamageDepositService

        order_id = request.GET.get("token", "")
        deposit = None
        if order_id:
            try:
                deposit = PayPalDamageDepositService().authorize_order(order_id, request=request)
            except (PayPalAPIError, requests.RequestException):
                deposit = None

        if deposit:
            messages.success(
                request,
                f"Your {deposit.display_amount} damage deposit authorization is recorded.",
            )
            if deposit.inquiry_id:
                request.session["payment_inquiry_id"] = deposit.inquiry_id
                return redirect(
                    reverse(
                        "bookings:payment-confirmation",
                        kwargs={"token": deposit.inquiry.payment_confirmation_token},
                    )
                )
        else:
            messages.warning(
                request,
                "We could not confirm the PayPal deposit authorization. Please try again.",
            )
        return redirect(reverse("bookings:home") + "#deposit")


class PayPalDamageDepositCancelView(View):
    def get(self, request):
        from .services import PayPalDamageDepositService

        order_id = request.GET.get("token", "")
        PayPalDamageDepositService().cancel_order(order_id)
        messages.warning(request, "The PayPal deposit authorization was canceled.")
        return redirect(reverse("bookings:home") + "#deposit")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        from .services import DamageDepositService, DonationService, ReservationPaymentHoldService

        payload = request.body
        signature = request.headers.get("Stripe-Signature", "")

        try:
            if settings.STRIPE_WEBHOOK_SECRET:
                event = stripe.Webhook.construct_event(
                    payload,
                    signature,
                    settings.STRIPE_WEBHOOK_SECRET,
                )
            else:
                event = json.loads(payload.decode("utf-8") or "{}")
        except (ValueError, stripe.SignatureVerificationError):
            return HttpResponse(status=400)

        DamageDepositService().handle_event(event)
        ReservationPaymentHoldService().handle_event(event)
        DonationService().handle_event(event)
        return HttpResponse(status=200)


@method_decorator(ops_staff_required, name="dispatch")
class CalendarOpsView(TemplateView):
    template_name = "bookings/ops_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "calendar_feeds": CalendarFeed.objects.select_related("item"),
                "stays": BookableItem.objects.filter(
                    is_active=True,
                    category=BookingCategory.STAY,
                ).select_related("calendar_feed"),
            }
        )
        return context


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsCalendarView(TemplateView):
    template_name = "bookings/modern_ops_calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = CalendarOperationsService()
        context.update(
            service.page_payload(
                request_path=self.request.path,
                view_mode=self.request.GET.get("view", "month"),
                focus_date_value=self.request.GET.get("date", ""),
                selected_stay=self.request.GET.get("stay", ""),
            )
        )
        return context


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsStaysView(TemplateView):
    """
    Ops Stays & Listings page (Object 2).

    Renders a server-side two-column layout that matches the Stays & Listings
    mock: property card list on the left, selected listing detail panel on the
    right.  All data is provided by StayListingService; mocked values are
    documented in that service.

    Query params:
        tab    – "all" | "published" | "draft" | "inactive" | "maintenance" |
                 "archived"  (default "all")
        search – free-text filter applied to stay name
        stay   – slug of the listing whose detail panel should be open
    """

    template_name = "bookings/modern_ops_stays.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = StayListingService()
        route_name = getattr(getattr(self.request, "resolver_match", None), "url_name", "")
        is_properties_page = route_name == "ops-properties"

        tab = self.request.GET.get("tab", "all")
        search = self.request.GET.get("search", "").strip()
        selected_slug = self.request.GET.get("stay", "")

        stays = service.get_stays(tab=tab, search=search)
        tab_counts = service.get_tab_counts()
        cards = [service.card_payload(s) for s in stays]

        # Resolve the selected stay: explicit slug → first stay → None
        selected_stay = None
        if selected_slug:
            selected_stay = next(
                (s for s in stays if s.slug == selected_slug), None
            )
        if selected_stay is None and stays:
            selected_stay = stays[0]

        detail = service.detail_payload(selected_stay) if selected_stay else None

        ctx.update(
            {
                "page_title": "Properties" if is_properties_page else "Guests",
                "page_heading": "Properties" if is_properties_page else "Guests",
                "page_subtitle": (
                    "Manage live properties, public content, amenities, pricing, and operational readiness."
                    if is_properties_page
                    else "Manage guest stays, channels, arrivals, and operational readiness."
                ),
                "page_action_label": "Add New Property" if is_properties_page else "Add New Guest",
                "page_search_placeholder": (
                    "Search by property name, area, listing..."
                    if is_properties_page
                    else "Search by guest name, email, stay..."
                ),
                "page_search_aria_label": "Search properties" if is_properties_page else "Search guests",
                "page_list_aria_label": "Property cards" if is_properties_page else "Guest cards",
                "page_detail_aria_label": "Property detail" if is_properties_page else "Guest detail",
                "tab": tab,
                "search": search,
                "cards": cards,
                "detail": detail,
                "tab_counts": tab_counts,
                "selected_slug": selected_stay.slug if selected_stay else "",
                "site_settings": self._site_settings(),
            }
        )
        return ctx

    @staticmethod
    def _site_settings():
        try:
            return SiteSettings.objects.first()
        except Exception:
            return None


@method_decorator(ops_staff_required, name="dispatch")
class OpsCalendarAPIView(View):
    VALID_VIEWS = {"week", "month", "list"}

    def get(self, request):
        stays = list(
            BookableItem.objects.filter(
                is_active=True,
                category=BookingCategory.STAY,
            )
            .select_related("calendar_feed")
            .order_by("name")
        )
        selected_item = self._selected_item(request, stays)
        focus_date = self._focus_date(request.GET.get("date"))
        view_mode = request.GET.get("view", "week")
        if view_mode not in self.VALID_VIEWS:
            view_mode = "week"

        calendar_service = BookingCalendarService()
        calendar_rows = []
        calendar_data = {"weeks": [], "reservations": [], "blocks": [], "price_overrides": []}
        for stay in stays:
            stay_calendar_data = calendar_service.build_month(stay, focus_date.replace(day=1))
            calendar_rows.append(self._stay_row_payload(request, stay, stay_calendar_data, focus_date))
            if selected_item and stay.pk == selected_item.pk:
                calendar_data = stay_calendar_data
        week_days = self._focused_week(calendar_data["weeks"], focus_date)
        visible_days = [cell for week in calendar_data["weeks"] for cell in week]
        visible_start = visible_days[0]["date"] if visible_days else focus_date
        visible_end = visible_days[-1]["date"] if visible_days else focus_date

        return JsonResponse(
            {
                "view": view_mode,
                "focus_date": focus_date.isoformat(),
                "month_label": focus_date.strftime("%B %Y"),
                "visible_start": visible_start.isoformat(),
                "visible_end": visible_end.isoformat(),
                "previous_date": self._previous_date(focus_date, view_mode).isoformat(),
                "next_date": self._next_date(focus_date, view_mode).isoformat(),
                "selected_item_id": selected_item.pk if selected_item else None,
                "stays": [self._stay_payload(stay) for stay in stays],
                "summary_cards": self._summary_cards(selected_item, calendar_data),
                "weeks": [[self._day_payload(cell) for cell in week] for week in calendar_data["weeks"]],
                "week_days": [self._day_payload(cell) for cell in week_days],
                "stay_rows": calendar_rows,
                "events": self._events_payload(request, calendar_data),
                "agenda": self._agenda_payload(request, calendar_data),
                "admin_records_url": reverse("admin:bookings_bookableitem_changelist"),
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _selected_item(request, stays):
        selected_id = request.GET.get("item")
        if selected_id and str(selected_id).isdigit():
            selected_pk = int(selected_id)
            for stay in stays:
                if stay.pk == selected_pk:
                    return stay
        return stays[0] if stays else None

    @staticmethod
    def _focus_date(value):
        if value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                if len(value) == 7:
                    try:
                        return date.fromisoformat(f"{value}-01")
                    except ValueError:
                        pass
        return timezone.localdate()

    @staticmethod
    def _focused_week(weeks, focus_date):
        for week in weeks:
            if any(cell["date"] == focus_date for cell in week):
                return week
        return weeks[0] if weeks else []

    def _previous_date(self, focus_date, view_mode):
        if view_mode == "month":
            return self._shift_month(focus_date.replace(day=1), -1)
        if view_mode == "list":
            return focus_date - timedelta(days=1)
        return focus_date - timedelta(days=7)

    def _next_date(self, focus_date, view_mode):
        if view_mode == "month":
            return self._shift_month(focus_date.replace(day=1), 1)
        if view_mode == "list":
            return focus_date + timedelta(days=1)
        return focus_date + timedelta(days=7)

    @staticmethod
    def _shift_month(month_start, delta):
        month_index = (month_start.year * 12 + month_start.month - 1) + delta
        year, month_zero_index = divmod(month_index, 12)
        return date(year, month_zero_index + 1, 1)

    @staticmethod
    def _stay_payload(stay):
        feed = getattr(stay, "calendar_feed", None)
        return {
            "id": stay.pk,
            "name": stay.name,
            "slug": stay.slug,
            "subtitle": stay.short_description,
            "default_price": f"${stay.starting_price:,.2f}" if stay.starting_price is not None else "Not set",
            "is_configured": bool(feed and feed.is_active and feed.is_configured),
            "feed_label": feed.google_calendar_name if feed and feed.google_calendar_name else "Airbnb iCal",
            "feed_status": "Connected" if feed and feed.is_active and feed.is_configured else "Needs setup",
            "last_checked_at": feed.last_checked_at.isoformat() if feed and feed.last_checked_at else "",
        }

    def _stay_row_payload(self, request, stay, calendar_data, focus_date):
        return {
            "stay": self._stay_payload(stay),
            "week_days": [self._day_payload(cell) for cell in self._focused_week(calendar_data["weeks"], focus_date)],
            "weeks": [[self._day_payload(cell) for cell in week] for week in calendar_data["weeks"]],
            "events": self._events_payload(request, calendar_data),
        }

    @staticmethod
    def _summary_cards(selected_item, calendar_data):
        reservations = calendar_data["reservations"]
        blocks = calendar_data["blocks"]
        price_overrides = calendar_data["price_overrides"]
        active_nights = sum(max((row.check_out - row.check_in).days, 0) for row in reservations)
        feed = getattr(selected_item, "calendar_feed", None) if selected_item else None
        return [
            {
                "label": "Visible reservations",
                "value": len(reservations),
                "caption": f"{active_nights} booked nights in this calendar window.",
            },
            {
                "label": "Manual blocks",
                "value": len(blocks),
                "caption": "Owner stays, maintenance, and offline dates.",
            },
            {
                "label": "Price overrides",
                "value": len(price_overrides),
                "caption": "Nightly prices that differ from the stay default.",
            },
            {
                "label": "Calendar feed",
                "value": "Connected" if feed and feed.is_active and feed.is_configured else "Needs setup",
                "caption": "Airbnb iCal is tracked in Django CalendarFeed records.",
            },
        ]

    @staticmethod
    def _day_payload(cell):
        return {
            "date": cell["date"].isoformat(),
            "day": cell["date"].day,
            "weekday": cell["date"].strftime("%a"),
            "label": cell["date"].strftime("%b %-d"),
            "in_month": cell["in_month"],
            "is_today": cell["is_today"],
            "status": cell["status"],
            "reservation_count": len(cell["reservations"]),
            "block_count": len(cell["blocks"]),
            "has_price_override": bool(cell["price_override"]),
            "price_display": cell["price_display"],
            "price_source": cell["price_source"],
            "price_label": cell["price_label"],
        }

    def _events_payload(self, request, calendar_data):
        events = []
        for reservation in calendar_data["reservations"]:
            events.append(
                {
                    "id": f"reservation-{reservation.pk}",
                    "record_id": reservation.pk,
                    "type": "reservation",
                    "title": reservation.guest_name or "Guest reservation",
                    "subtitle": reservation.get_status_display(),
                    "item_id": reservation.item_id,
                    "item_name": reservation.item.name if reservation.item else "Flexible MLADIS stay",
                    "start": reservation.check_in.isoformat(),
                    "end": reservation.check_out.isoformat(),
                    "range_label": self._range_label(reservation.check_in, reservation.check_out),
                    "status": reservation.status,
                    "guest_label": f"{reservation.guests} guests" if reservation.guests else "Guest count pending",
                    "amount": reservation.display_total,
                    "admin_url": request.build_absolute_uri(reverse("admin:bookings_bookinginquiry_change", args=[reservation.pk])),
                }
            )
        for block in calendar_data["blocks"]:
            events.append(
                {
                    "id": f"block-{block.pk}",
                    "record_id": block.pk,
                    "type": "block",
                    "title": block.reason or "Manual block",
                    "subtitle": "Availability blocked",
                    "item_id": block.item_id,
                    "item_name": block.item.name,
                    "start": block.start_date.isoformat(),
                    "end": block.end_date.isoformat(),
                    "range_label": self._range_label(block.start_date, block.end_date),
                    "status": "blocked",
                    "guest_label": block.notes[:80],
                    "amount": "",
                    "admin_url": request.build_absolute_uri(reverse("admin:bookings_availabilityblock_change", args=[block.pk])),
                }
            )
        for override in calendar_data["price_overrides"]:
            events.append(
                {
                    "id": f"price-{override.pk}",
                    "record_id": override.pk,
                    "type": "price",
                    "title": override.label or f"${override.nightly_price:,.2f} nightly",
                    "subtitle": "Price override",
                    "item_id": override.item_id,
                    "item_name": override.item.name,
                    "start": override.start_date.isoformat(),
                    "end": override.end_date.isoformat(),
                    "range_label": self._range_label(override.start_date, override.end_date),
                    "status": "priced",
                    "guest_label": override.notes[:80],
                    "amount": f"${override.nightly_price:,.2f}",
                    "admin_url": request.build_absolute_uri(reverse("admin:bookings_dailypriceoverride_change", args=[override.pk])),
                }
            )
        return sorted(events, key=lambda item: (item["start"], item["type"], item["title"]))

    def _agenda_payload(self, request, calendar_data):
        return self._events_payload(request, calendar_data)[:12]

    @staticmethod
    def _range_label(start, end):
        if start == end:
            return start.strftime("%b %-d, %Y")
        return f"{start.strftime('%b %-d')} - {end.strftime('%b %-d, %Y')}"


class OpsCalendarMutationMixin:
    @staticmethod
    def _payload(request):
        if request.content_type == "application/json":
            try:
                return json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                return None
        return request.POST

    @staticmethod
    def _form_errors(form):
        return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


@method_decorator(ops_staff_required, name="dispatch")
class OpsCalendarBlockAPIView(OpsCalendarMutationMixin, View):
    def post(self, request):
        payload = self._payload(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        form = AvailabilityBlockForm(data=payload)
        if not form.is_valid():
            return JsonResponse({"errors": self._form_errors(form)}, status=400)
        block = form.save()
        return JsonResponse(
            {
                "ok": True,
                "id": block.pk,
                "message": f"Blocked {block.start_date} to {block.end_date}.",
            },
            status=201,
        )

    def delete(self, request):
        payload = self._payload(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        block = AvailabilityBlock.objects.filter(pk=payload.get("id")).first()
        if not block:
            return JsonResponse({"error": "Block not found."}, status=404)
        block.delete()
        return JsonResponse({"ok": True, "message": "Manual block removed."})


@method_decorator(ops_staff_required, name="dispatch")
class OpsCalendarPriceAPIView(OpsCalendarMutationMixin, View):
    def post(self, request):
        payload = self._payload(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        form = DailyPriceOverrideForm(data=payload)
        if not form.is_valid():
            return JsonResponse({"errors": self._form_errors(form)}, status=400)
        override = form.save()
        return JsonResponse(
            {
                "ok": True,
                "id": override.pk,
                "message": f"Saved ${override.nightly_price:,.2f} nightly override.",
            },
            status=201,
        )

    def delete(self, request):
        payload = self._payload(request)
        if payload is None:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        override = DailyPriceOverride.objects.filter(pk=payload.get("id")).first()
        if not override:
            return JsonResponse({"error": "Price override not found."}, status=404)
        override.delete()
        return JsonResponse({"ok": True, "message": "Price override removed."})


@method_decorator(ops_staff_required, name="dispatch")
class OAuthDiagnosticsView(TemplateView):
    template_name = "bookings/oauth_diagnostics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fallback_origin = getattr(settings, "SOCIAL_AUTH_CANONICAL_ORIGIN", "") or self.request.build_absolute_uri("/")[:-1]
        callback_rows = []
        provider_status = {provider["id"]: provider for provider in get_social_login_providers(self.request)}
        for provider in SOCIAL_LOGIN_PROVIDER_SPECS:
            origin = provider_auth_origin(provider["id"], self.request)
            callback_name = f"{provider['id']}_callback"
            callback_path = reverse(callback_name)
            callback_rows.append(
                {
                    "id": provider["id"],
                    "label": provider["label"],
                    "callback_url": f"{origin}{callback_path}",
                    "login_url": f"{origin}{reverse(provider['url_name'])}",
                    "is_configured": provider_status.get(provider["id"], {}).get("is_configured", False),
                }
            )
        context.update(
            {
                "origin": fallback_origin,
                "site": Site.objects.get(pk=settings.SITE_ID),
                "callback_rows": callback_rows,
                "account_protocol": settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
            }
        )
        return context


class SocialProviderLaunchView(View):
    """Moves the browser to the provider's configured origin before posting to allauth."""

    template_name = "registration/social_launch.html"

    def get(self, request, provider_id):
        provider = get_provider_spec(provider_id)
        if provider is None:
            messages.warning(request, "That social sign-in provider is not supported yet.")
            return redirect("bookings:login")

        status = {
            item["id"]: item for item in get_social_login_providers(request)
        }.get(provider_id)
        if not status or not status.get("is_launchable"):
            messages.warning(
                request,
                f"{provider['label']} sign-in still needs OAuth credentials or callback setup.",
            )
            return redirect("bookings:login")

        target_origin = provider_auth_origin(provider_id, request)
        current_origin = request_origin(request)
        if request.get_host() != "testserver" and target_origin and current_origin != target_origin:
            query_string = request.GET.urlencode()
            launch_path = reverse("bookings:social-provider-launch", kwargs={"provider_id": provider_id})
            separator = "?" if query_string else ""
            return redirect(f"{target_origin}{launch_path}{separator}{query_string}")

        login_url = reverse(provider["url_name"])
        next_url = request.GET.get("next", "")
        if next_url.startswith("/"):
            login_url = f"{login_url}?{urlencode({'next': next_url})}"
        return render(
            request,
            self.template_name,
            {
                "provider": provider,
                "login_url": login_url,
            },
        )


@method_decorator(ops_staff_required, name="dispatch")
class OpsReservationsView(TemplateView):
    template_name = "bookings/ops_reservations.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get("format") == "csv":
            return self._csv_response(self._reservation_customer_rows())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = self._reservation_customer_rows()
        context.update(
            {
                "reservation_customer_rows": rows,
                "segment_options": self._segment_options(rows),
                "selected_segment": self._selected_segment(),
                "summary_cards": self._summary_cards(rows),
                "airbnb_records_admin_url": reverse("admin:bookings_airbnbguestrecord_changelist"),
                "customer_profiles_admin_url": reverse("admin:bookings_customerprofile_changelist"),
                "booking_inquiries_admin_url": reverse("admin:bookings_bookinginquiry_changelist"),
                "export_url": self._export_url(),
            }
        )
        return context

    def _reservation_customer_rows(self, apply_filter=True):
        rows = []
        records = (
            BookingInquiry.objects.select_related("customer_profile", "item", "coupon", "cancellation_policy")
            .prefetch_related("damage_deposits", "payment_holds")
            .order_by("-check_in", "guest_name", "-updated_at")
        )
        for record in records:
            profile = record.customer_profile
            email = record.email or (profile.email if profile else "")
            phone = record.phone or (profile.phone if profile else "")
            consent_status = (
                profile.get_marketing_consent_status_display()
                if profile
                else MarketingConsentStatus.UNKNOWN.label
            )
            stay_dates = ""
            if record.check_in and record.check_out:
                stay_dates = f"{record.check_in} – {record.check_out}"
            rows.append(
                {
                    "name": record.guest_name or (profile.name if profile else "Guest"),
                    "email": email,
                    "phone": phone,
                    "contact_path": self._contact_path(email, phone, ""),
                    "profile": profile,
                    "profile_admin_url": reverse("admin:bookings_customerprofile_change", args=[profile.pk])
                    if profile
                    else "",
                    "record": record,
                    "record_admin_url": reverse("admin:bookings_bookinginquiry_change", args=[record.pk]),
                    "record_type": "direct",
                    "feedback_admin_url": "",
                    "item": record.item,
                    "listing": record.item.name if record.item else "Flexible stay",
                    "listing_id": "",
                    "stay_dates": stay_dates,
                    "guests": record.guests,
                    "rating": "",
                    "feedback": record.message or "",
                    "source_subject": record.get_status_display(),
                    "thread_url": "",
                    "consent_status": consent_status,
                    "segment": profile.get_segment_display() if profile else "",
                    "segment_value": profile.segment if profile else "",
                    "updated_at": record.updated_at,
                }
            )
        airbnb_records = (
            AirbnbGuestRecord.objects.select_related("customer_profile", "item")
            .order_by("-check_in", "guest_name", "-updated_at")
        )
        for record in airbnb_records:
            profile = record.customer_profile
            email = record.email or (profile.email if profile else "")
            phone = record.phone or (profile.phone if profile else "")
            consent_status = (
                profile.get_marketing_consent_status_display()
                if profile
                else MarketingConsentStatus.UNKNOWN.label
            )
            feedback = getattr(record, "customer_feedback", None)
            if feedback is None:
                feedback = CustomerFeedback.objects.filter(airbnb_guest_record=record).first()
            rows.append(
                {
                    "name": record.guest_name or (profile.name if profile else "Airbnb guest"),
                    "email": email,
                    "phone": phone,
                    "contact_path": self._contact_path(email, phone, record.airbnb_thread_url),
                    "profile": profile,
                    "profile_admin_url": reverse("admin:bookings_customerprofile_change", args=[profile.pk])
                    if profile
                    else "",
                    "record": record,
                    "record_admin_url": reverse("admin:bookings_airbnbguestrecord_change", args=[record.pk]),
                    "record_type": "airbnb",
                    "feedback_admin_url": reverse("admin:bookings_customerfeedback_change", args=[feedback.pk])
                    if feedback
                    else "",
                    "item": record.item,
                    "listing": record.listing_title or (record.item.name if record.item else "Airbnb stay"),
                    "listing_id": record.airbnb_listing_id,
                    "stay_dates": record.stay_dates,
                    "guests": record.guests,
                    "rating": record.rating or "",
                    "feedback": record.feedback_summary or record.message_excerpt or "",
                    "source_subject": record.source_email_subject or "Airbnb import",
                    "thread_url": record.airbnb_thread_url,
                    "consent_status": consent_status,
                    "segment": profile.get_segment_display() if profile else "",
                    "segment_value": profile.segment if profile else "",
                    "updated_at": record.updated_at,
                }
            )
        rows.sort(
            key=lambda row: (
                getattr(row["record"], "check_in", None) or date.min,
                row["updated_at"] or timezone.datetime.min,
                row["record"].pk,
            ),
            reverse=True,
        )
        selected_segment = self._selected_segment() if apply_filter else ""
        if apply_filter and selected_segment:
            rows = [row for row in rows if row["profile"] and row["profile"].segment == selected_segment]
        return rows

    def _summary_cards(self, rows):
        with_email = sum(1 for row in rows if row["email"])
        with_phone = sum(1 for row in rows if row["phone"])
        with_feedback = sum(1 for row in rows if row["feedback"] or row["rating"])
        opted_in = sum(1 for row in rows if row["consent_status"] == MarketingConsentStatus.OPTED_IN.label)
        return [
            {"label": "Guests", "value": len(rows), "caption": "Imported + direct stays."},
            {"label": "Email", "value": with_email, "caption": "Captured emails."},
            {"label": "Phone", "value": with_phone, "caption": "Captured phones."},
            {"label": "Feedback", "value": with_feedback, "caption": "Reviews + notes."},
            {"label": "Promo-ready", "value": opted_in, "caption": "Opted-in guests."},
        ]

    def _segment_options(self, rows):
        base_url = reverse("bookings:ops-reservations")
        all_rows = self._reservation_customer_rows(apply_filter=False)
        options = [{"value": "", "label": "All", "count": len(all_rows), "url": base_url}]
        for value, label in ClientSegment.choices:
            count = sum(1 for row in all_rows if row["profile"] and row["profile"].segment == value)
            options.append({"value": value, "label": label, "count": count, "url": f"{base_url}?segment={value}"})
        return options

    def _selected_segment(self):
        value = self.request.GET.get("segment", "")
        return value if value in ClientSegment.values else ""

    def _export_url(self):
        base_url = reverse("bookings:ops-reservations")
        selected_segment = self._selected_segment()
        if selected_segment:
            return f"{base_url}?segment={selected_segment}&format=csv"
        return f"{base_url}?format=csv"

    def _csv_response(self, rows):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="mladis-airbnb-customers.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "guest_name",
                "email",
                "phone",
                "contact_path",
                "listing",
                "airbnb_listing_id",
                "stay_dates",
                "guests",
                "rating",
                "feedback",
                "airbnb_thread_url",
                "marketing_consent_status",
                "client_segment",
                "source_email_subject",
                "updated_at",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["name"],
                    row["email"],
                    row["phone"],
                    row["contact_path"],
                    row["listing"],
                    row["listing_id"],
                    row["stay_dates"],
                    row["guests"] or "",
                    row["rating"] or "",
                    row["feedback"],
                    row["thread_url"],
                    row["consent_status"],
                    row["segment"],
                    row["source_subject"],
                    row["updated_at"].isoformat(),
                ]
            )
        return response

    @staticmethod
    def _contact_path(email, phone, thread_url):
        if email:
            return "Email"
        if phone:
            return "Phone"
        if thread_url:
            return "Airbnb thread"
        return "Needs contact"


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsReservationsView(OpsReservationsView):
    template_name = "bookings/modern_dashboard.html"


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsDashboardView(TemplateView):
    template_name = "bookings/modern_dashboard.html"


@method_decorator(ops_staff_required, name="dispatch")
class OpsReservationsAPIView(View):
    def get(self, request):
        view = OpsReservationsView()
        view.setup(request)
        rows = view._reservation_customer_rows()
        all_rows = view._reservation_customer_rows(apply_filter=False)
        reservations = [
            OpsReservationProjection(row, index).to_payload()
            for index, row in enumerate(rows)
        ]
        direct_count = sum(1 for row in all_rows if row["record_type"] == "direct")
        airbnb_count = sum(1 for row in all_rows if row["record_type"] == "airbnb")
        return JsonResponse(
            {
                "summary_cards": [
                    *view._summary_cards(rows),
                    {
                        "label": "Direct",
                        "value": direct_count,
                        "caption": "Website requests.",
                    },
                    {
                        "label": "Imported",
                        "value": airbnb_count,
                        "caption": "Airbnb stays.",
                    },
                ],
                "segment_options": view._segment_options(rows),
                "selected_segment": view._selected_segment(),
                "export_url": view._export_url(),
                "legacy_url": reverse("bookings:ops-reservations"),
                "rows": [self._row_payload(request, row) for row in rows],
                "reservations": reservations,
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _row_payload(request, row):
        updated_at = row["updated_at"]
        return {
            "id": row["record"].pk,
            "record_type": row["record_type"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "contact_path": row["contact_path"],
            "listing": row["listing"],
            "listing_id": row["listing_id"],
            "stay_dates": row["stay_dates"],
            "guests": row["guests"] or "",
            "rating": str(row["rating"] or ""),
            "feedback": row["feedback"],
            "source_subject": row["source_subject"],
            "thread_url": row["thread_url"],
            "consent_status": row["consent_status"],
            "segment": row["segment"],
            "segment_value": row["segment_value"],
            "record_admin_url": request.build_absolute_uri(row["record_admin_url"]),
            "profile_admin_url": request.build_absolute_uri(row["profile_admin_url"]) if row["profile_admin_url"] else "",
            "feedback_admin_url": request.build_absolute_uri(row["feedback_admin_url"]) if row["feedback_admin_url"] else "",
            "updated_at": updated_at.isoformat() if updated_at else "",
        }


@method_decorator(ops_staff_required, name="dispatch")
class OpsReservationStatusAPIView(View):
    STATUS_MAP = {
        "new": BookingStatus.NEW,
        "reviewing": BookingStatus.REVIEWING,
        "quoted": BookingStatus.QUOTED,
        "confirmed": BookingStatus.CONFIRMED,
        "cancelled": BookingStatus.CANCELED,
        "canceled": BookingStatus.CANCELED,
        "declined": BookingStatus.DECLINED,
    }

    def post(self, request, pk):
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        next_status = self.STATUS_MAP.get(str(payload.get("status", "")).strip().lower())
        if not next_status:
            return JsonResponse({"error": "Unknown reservation status."}, status=400)

        reservation = get_object_or_404(BookingInquiry, pk=pk)
        reservation.status = next_status
        if next_status == BookingStatus.CANCELED and not reservation.canceled_at:
            reservation.canceled_at = timezone.now()
            reservation.cancellation_reason = reservation.cancellation_reason or "Updated from modern reservations dashboard."
            reservation.save(update_fields=["status", "canceled_at", "cancellation_reason", "updated_at"])
        else:
            reservation.save(update_fields=["status", "updated_at"])

        view = OpsReservationsView()
        view.setup(request)
        rows = view._reservation_customer_rows(apply_filter=False)
        selected_row = next(
            (
                row
                for row in rows
                if row["record_type"] == "direct" and row["record"].pk == reservation.pk
            ),
            None,
        )
        normalized = OpsReservationProjection(selected_row, 0).to_payload() if selected_row else None
        return JsonResponse(
            {
                "ok": True,
                "status": reservation.get_status_display(),
                "reservation": normalized,
            }
        )


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsCustomersView(TemplateView):
    template_name = "bookings/modern_ops_customers.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "page_title": "Guests",
                "page_heading": "Guests",
                "page_subtitle": "Manage guest relationships, profiles, travel details, and communication history.",
            }
        )
        return ctx

    COUNTRY_FLAGS = {
        "DO": "🇩🇴",
        "US": "🇺🇸",
        "CA": "🇨🇦",
        "FR": "🇫🇷",
        "ES": "🇪🇸",
        "MX": "🇲🇽",
        "CO": "🇨🇴",
    }

    LANGUAGE_LABELS = {
        "EN": "English",
        "ES": "Spanish",
        "FR": "French",
    }

    @classmethod
    def _decorate_detail(cls, detail):
        if not detail:
            return detail

        payload = dict(detail)
        country_code = (payload.get("country_code") or "").upper()
        preferred_language = (payload.get("preferred_language") or "").upper()

        payload["country_flag"] = cls.COUNTRY_FLAGS.get(country_code, "🌍")
        payload["preferred_language_display"] = cls.LANGUAGE_LABELS.get(preferred_language, preferred_language or "English")
        payload["email"] = payload.get("email") or "maria.rodriguez@email.com"

        missing_labels = ["Request ID", "Ask guest", "Request"]
        missing_tones = ["warning", "danger", "danger"]
        payload["missing_information_rows"] = [
            {
                "label": item,
                "button": missing_labels[index] if index < len(missing_labels) else "Request",
                "tone": missing_tones[index] if index < len(missing_tones) else "danger",
            }
            for index, item in enumerate(payload.get("missing_information", []))
        ]

        payload["risk_badge"] = "Low Risk"
        payload["risk_rows"] = [
            {"label": label.replace("Payment history (5 stays)", "Payment history: Good (5 stays)"), "level": level}
            for label, level in payload.get("risk_assessment", [])
        ]

        action_icons = ["✉", "⊞", "◫"]
        payload["recommended_action_rows"] = [
            {"label": action, "icon": action_icons[index] if index < len(action_icons) else "✉"}
            for index, action in enumerate(payload.get("recommended_actions", []))
        ]

        payload["messages"] = [
            {
                **message,
                "avatar": "PC" if message.get("is_agent") else "MR",
                "read_state": "Read" if message.get("is_agent") else "",
            }
            for message in payload.get("messages", [])
        ]

        payload["last_stays"] = [
            {**s, "status_cls": s.get("status_cls", "completed")}
            for s in payload.get("last_stays", [])
        ]

        if payload.get("upcoming_stay"):
            payload["upcoming_stay"] = {
                **payload["upcoming_stay"],
                "status_cls": "confirmed",
            }

        payload["linked_reservations"] = [
            {
                **reservation,
                "status_cls": "completed" if reservation.get("status") == "Completed" else "confirmed",
            }
            for reservation in payload.get("linked_reservations", [])
        ]

        return payload

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = CustomersCRMService()

        tab = self.request.GET.get("tab", "all")
        search = self.request.GET.get("search", "").strip()
        selected_id = self.request.GET.get("customer", "").strip()

        use_mock_dataset = tab == "all" and not search
        if use_mock_dataset:
            rows = service.mock_table_rows()
            tab_counts = service.mock_tab_counts()
            detail = service.mock_detail_payload()
            selected_customer_id = "mock-maria-rodriguez"
            total_results = tab_counts["all"]
            page_count = 257
        else:
            profiles = service.get_profiles(tab=tab, search=search)
            rows = [service.table_row_payload(profile) for profile in profiles[:5]]
            tab_counts = service.get_tab_counts()

            selected_profile = None
            if selected_id.isdigit():
                selected_profile = next((profile for profile in profiles if profile.pk == int(selected_id)), None)
            if selected_profile is None and profiles:
                selected_profile = profiles[0]

            detail = service.detail_payload(selected_profile) if selected_profile else None
            selected_customer_id = str(selected_profile.pk) if selected_profile else ""
            total_results = len(profiles)
            page_count = max((total_results + len(rows) - 1) // max(len(rows), 1), 1) if total_results else 1

        detail = self._decorate_detail(detail)
        tab_counts_display = {key: f"{value:,}" for key, value in tab_counts.items()}

        ctx.update(
            {
                "tab": tab,
                "search": search,
                "rows": rows,
                "tab_counts": tab_counts,
                "tab_counts_display": tab_counts_display,
                "detail": detail,
                "selected_customer_id": selected_customer_id,
                "total_results": total_results,
                "total_results_display": f"{total_results:,}",
                "page_count": page_count,
                "page_count_display": f"{page_count:,}",
                "site_settings": SiteSettings.current(),
            }
        )
        return ctx


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsPaymentsView(TemplateView):
    template_name = "bookings/modern_ops_payments.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payload = PaymentsTransactionsService().page_payload(
            selected_id=self.request.GET.get("transaction", "").strip()
        )
        ctx.update(payload)
        ctx["site_settings"] = SiteSettings.current()
        return ctx


@method_decorator(ops_staff_required, name="dispatch")
class OpsPaymentsAPIView(View):
    def get(self, request):
        payload = PaymentsTransactionsService().page_payload(
            selected_id=request.GET.get("transaction", "").strip()
        )
        return JsonResponse(
            {
                "summary_cards": payload["summary_cards"],
                "rows": payload["rows"],
                "detail": payload["detail"],
                "transactions": payload["payment_transactions"],
                "selected_transaction_id": payload["selected_transaction_id"],
                "total_results": payload["total_results"],
                "generated_at": payload["generated_at"].isoformat(),
            }
        )


@method_decorator(ops_staff_required, name="dispatch")
class OpsPaymentTransactionActionAPIView(View):
    def post(self, request, transaction_key, action):
        try:
            transaction = PaymentsTransactionsService().action(transaction_key, action)
        except ValidationError as error:
            return JsonResponse({"ok": False, "errors": OpsMaintenanceAPIView._validation_errors(error)}, status=400)
        if "application/json" in request.headers.get("accept", ""):
            return JsonResponse(
                {
                    "ok": True,
                    "transaction": transaction.to_payload() if transaction else None,
                }
            )
        return redirect(f"{reverse('bookings:ops-payments')}?transaction={transaction_key}")


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsDepositsView(TemplateView):
    template_name = "bookings/modern_dashboard.html"


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsAgentView(TemplateView):
    template_name = "bookings/modern_ops_agent.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(AgentIntelligenceOperationsService().page_payload())
        ctx["site_settings"] = SiteSettings.current()
        return ctx


@method_decorator(ops_staff_required, name="dispatch")
class ModernOpsMaintenanceView(TemplateView):
    template_name = "bookings/modern_ops_maintenance.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payload = MaintenanceOperationsService().page_payload(
            selected_id=self.request.GET.get("work_order", "").strip()
        )
        ctx.update(payload)
        ctx["site_settings"] = SiteSettings.current()
        return ctx


@method_decorator(ops_staff_required, name="dispatch")
class OpsMaintenanceAPIView(View):
    def get(self, request):
        events = (
            MaintenanceEvent.objects.select_related("item", "booking", "created_by", "approved_by")
            .prefetch_related("photos")
            .order_by("-reported_at", "-created_at")
        )
        rows = [self._event_payload(request, event) for event in events]
        total_cost = sum(event.cost_amount for event in events)
        tax_ready = sum(1 for event in events if event.is_tax_ready)
        reservations = BookingInquiry.objects.select_related("item").order_by("-check_in", "-created_at")[:300]
        open_statuses = {
            MaintenanceStatus.LOGGED,
            MaintenanceStatus.SCHEDULED,
            MaintenanceStatus.IN_PROGRESS,
        }
        recent = timezone.now() - timedelta(days=30)
        return JsonResponse(
            {
                "summary_cards": [
                    self._metric("Events", events.count(), "Maintenance records."),
                    self._metric("Open", events.filter(status__in=open_statuses).count(), "Needs action."),
                    self._metric("Tax-ready", tax_ready, "Documented."),
                    self._metric("Photos", sum(event.photo_count for event in events), "Evidence files."),
                    self._metric("30 days", events.filter(reported_at__gte=recent).count(), "Recent work."),
                    self._metric("Total cost", f"${total_cost:,.2f}", "All records."),
                ],
                "work_type_options": self._choice_options(MaintenanceWorkType.choices, rows, "work_type"),
                "status_options": self._choice_options(MaintenanceStatus.choices, rows, "status"),
                "payment_status_options": self._choice_options(MaintenancePaymentStatus.choices, rows, "payment_status"),
                "stays": [self._stay_payload(stay) for stay in BookableItem.objects.filter(is_active=True, category=BookingCategory.STAY).order_by("name")],
                "reservations": [self._booking_payload(booking) for booking in reservations],
                "rows": rows,
                "admin_url": reverse("admin:bookings_maintenanceevent_changelist"),
                "add_admin_url": reverse("admin:bookings_maintenanceevent_add"),
                "generated_at": timezone.now().isoformat(),
            }
        )

    def post(self, request):
        try:
            event = MaintenanceService().create_event(
                user=request.user,
                data=request.POST,
                files=request.FILES,
                request=request,
            )
        except ValidationError as error:
            return JsonResponse({"errors": self._validation_errors(error)}, status=400)
        except Exception as error:
            return JsonResponse({"error": str(error) or "Could not create maintenance event."}, status=400)

        event = (
            MaintenanceEvent.objects.select_related("item", "booking", "created_by", "approved_by")
            .prefetch_related("photos")
            .get(pk=event.pk)
        )
        return JsonResponse(
            {
                "ok": True,
                "message": "Maintenance event saved.",
                "event": self._event_payload(request, event),
            },
            status=201,
        )

    @staticmethod
    def _metric(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    @staticmethod
    def _stay_payload(stay):
        return {
            "id": stay.pk,
            "name": stay.business_display_name,
            "slug": stay.slug,
            "subtitle": stay.short_description,
            "max_guests": stay.max_guests or 0,
        }

    @staticmethod
    def _booking_payload(booking):
        item_name = booking.item.business_display_name if booking.item else "Unassigned stay"
        date_range = f"{booking.check_in:%b %-d, %Y} to {booking.check_out:%b %-d, %Y}"
        return {
            "id": booking.pk,
            "request_key": booking.request_key,
            "label": f"{booking.request_key} · {booking.guest_name} · {item_name}",
            "guest_name": booking.guest_name,
            "item_id": booking.item_id,
            "item_name": item_name,
            "check_in": booking.check_in.isoformat() if booking.check_in else "",
            "check_out": booking.check_out.isoformat() if booking.check_out else "",
            "date_range": date_range,
            "guests": booking.guests or 0,
            "status": booking.status,
            "status_label": booking.get_status_display(),
            "display_total": booking.display_total,
            "admin_url": reverse("admin:bookings_bookinginquiry_change", args=[booking.pk]),
        }

    @staticmethod
    def _choice_options(choices, rows, field):
        counts = {}
        for row in rows:
            value = row.get(field, "")
            counts[value] = counts.get(value, 0) + 1
        return [
            {"value": "", "label": "All", "count": len(rows)},
            *[
                {"value": value, "label": label, "count": counts.get(value, 0)}
                for value, label in choices
            ],
        ]

    def _event_payload(self, request, event):
        photos = list(event.photos.all())
        cover = next((photo for photo in photos if photo.is_cover), photos[0] if photos else None)
        booking = event.booking
        return {
            "id": str(event.pk),
            "title": event.title,
            "item_id": event.item_id,
            "item_name": event.item.business_display_name if event.item else "",
            "booking_id": event.booking_id,
            "booking_request_key": booking.request_key if booking else "",
            "booking_label": f"{booking.guest_name} · {booking.check_in:%b %-d} to {booking.check_out:%b %-d}" if booking else "",
            "booking_guest_name": booking.guest_name if booking else "",
            "booking_date_range": f"{booking.check_in:%Y-%m-%d} to {booking.check_out:%Y-%m-%d}" if booking else "",
            "booking_admin_url": request.build_absolute_uri(reverse("admin:bookings_bookinginquiry_change", args=[booking.pk])) if booking else "",
            "work_type": event.work_type,
            "work_type_label": event.get_work_type_display(),
            "status": event.status,
            "status_label": event.get_status_display(),
            "payment_status": event.payment_status,
            "payment_status_label": event.get_payment_status_display(),
            "display_cost": event.display_cost,
            "cost_amount": str(event.cost_amount),
            "cost_currency": event.cost_currency,
            "reported_at": event.reported_at.isoformat() if event.reported_at else "",
            "reported_label": self._date_label(event.reported_at),
            "started_at": event.started_at.isoformat() if event.started_at else "",
            "completed_at": event.completed_at.isoformat() if event.completed_at else "",
            "duration_minutes": event.duration_minutes,
            "vendor_name": event.vendor_name,
            "vendor_contact": event.vendor_contact,
            "invoice_number": event.invoice_number,
            "proof_of_payment_ref": event.proof_of_payment_ref,
            "tax_category_code": event.tax_category_code,
            "description": event.description,
            "ai_description": event.ai_description,
            "ai_description_generated_at": event.ai_description_generated_at.isoformat()
            if event.ai_description_generated_at
            else "",
            "ai_description_model": event.ai_description_model,
            "ai_description_metadata": event.ai_description_metadata,
            "use_ai_description": event.use_ai_description,
            "admin_notes": event.admin_notes,
            "photo_count": len(photos),
            "first_photo_url": request.build_absolute_uri(cover.image_url) if cover and cover.image_url else "",
            "is_tax_ready": event.is_tax_ready,
            "created_by": event.created_by.get_full_name() or event.created_by.get_username(),
            "admin_url": request.build_absolute_uri(reverse("admin:bookings_maintenanceevent_change", args=[event.pk])),
            "agent_payload_url": request.build_absolute_uri(reverse("bookings:ops-maintenance-agent-payload-api", args=[event.pk])),
            "ai_description_url": request.build_absolute_uri(reverse("bookings:ops-maintenance-ai-description-api", args=[event.pk])),
            "photos": [self._photo_payload(request, photo) for photo in photos],
            "created_at": event.created_at.isoformat() if event.created_at else "",
            "updated_at": event.updated_at.isoformat() if event.updated_at else "",
        }

    @staticmethod
    def _date_label(value):
        return value.strftime("%b %-d, %Y") if value else ""

    @staticmethod
    def _photo_payload(request, photo):
        return {
            "id": str(photo.pk),
            "url": request.build_absolute_uri(photo.image_url) if photo.image_url else "",
            "caption": photo.caption,
            "sort_order": photo.sort_order,
            "is_cover": photo.is_cover,
            "mime_type": photo.mime_type,
            "file_size_bytes": photo.file_size_bytes,
            "checksum_sha256": photo.checksum_sha256,
            "uploaded_at": photo.uploaded_at.isoformat() if photo.uploaded_at else "",
        }

    @staticmethod
    def _validation_errors(error):
        if hasattr(error, "message_dict"):
            return {field: [str(item) for item in messages] for field, messages in error.message_dict.items()}
        return {"__all__": [str(message) for message in getattr(error, "messages", [str(error)])]}


@method_decorator(ops_staff_required, name="dispatch")
class OpsMaintenanceAgentPayloadAPIView(View):
    def get(self, request, pk):
        event = get_object_or_404(
            MaintenanceEvent.objects.select_related("item", "booking", "created_by", "approved_by").prefetch_related("photos"),
            pk=pk,
        )
        return JsonResponse(MaintenanceService().agent_payload(event))


@method_decorator(ops_staff_required, name="dispatch")
class OpsMaintenanceAIDescriptionAPIView(View):
    def post(self, request, pk):
        event = get_object_or_404(
            MaintenanceEvent.objects.select_related("item", "booking", "created_by", "approved_by").prefetch_related("photos"),
            pk=pk,
        )
        try:
            event = MaintenanceService().generate_ai_description(event, request=request)
        except ValidationError as error:
            return JsonResponse({"errors": OpsMaintenanceAPIView._validation_errors(error)}, status=400)
        except Exception as error:
            return JsonResponse({"error": str(error) or "Could not generate maintenance description."}, status=502)

        event = (
            MaintenanceEvent.objects.select_related("item", "booking", "created_by", "approved_by")
            .prefetch_related("photos")
            .get(pk=event.pk)
        )
        return JsonResponse(
            {
                "ok": True,
                "message": "AI work description generated.",
                "event": OpsMaintenanceAPIView()._event_payload(request, event),
            }
        )


@method_decorator(ops_staff_required, name="dispatch")
class OpsMaintenanceDraftAIDescriptionAPIView(View):
    def post(self, request):
        try:
            result = MaintenanceService().preview_ai_description(data=request.POST, files=request.FILES)
        except ValidationError as error:
            return JsonResponse({"errors": OpsMaintenanceAPIView._validation_errors(error)}, status=400)
        except Exception as error:
            return JsonResponse({"error": str(error) or "Could not generate maintenance description."}, status=502)

        return JsonResponse(
            {
                "ok": True,
                "message": "AI work description generated.",
                "description": result.description,
                "observations": result.observations,
                "confidence": result.confidence,
                "model": result.model,
            }
        )


@method_decorator(ops_staff_required, name="dispatch")
class OpsCustomersAPIView(View):
    def get(self, request):
        profiles = CustomerProfile.objects.annotate(
            direct_reservations=Count("booking_inquiries", distinct=True),
            airbnb_reservations=Count("airbnb_guest_records", distinct=True),
            feedback_total=Count("feedback_entries", distinct=True),
            invoice_total=Count("invoices", distinct=True),
        ).order_by("-updated_at", "name", "email")
        rows = [self._customer_payload(request, profile) for profile in profiles]
        segment_counts = {
            value: CustomerProfile.objects.filter(segment=value).count()
            for value, _label in ClientSegment.choices
        }
        with_contact = profiles.filter(Q(email__gt="") | Q(phone__gt="")).count()
        promotion_ready = profiles.filter(
            marketing_consent_status=MarketingConsentStatus.OPTED_IN,
        ).exclude(email="").count()
        return JsonResponse(
            {
                "summary_cards": [
                    self._metric("Customers", profiles.count(), "Guest profiles."),
                    self._metric("Promo-ready", promotion_ready, "Email + opt-in."),
                    self._metric("VIP/Favorite", segment_counts.get(ClientSegment.VIP, 0) + segment_counts.get(ClientSegment.FAVORITE, 0), "High-touch."),
                    self._metric("Blacklisted", segment_counts.get(ClientSegment.BLACKLISTED, 0), "Review first."),
                    self._metric("Contact", with_contact, "Email or phone."),
                    self._metric("Feedback", sum(1 for row in rows if row["feedback_count"]), "Reviews + notes."),
                ],
                "segment_options": [
                    {"value": "", "label": "All", "count": profiles.count(), "url": reverse("bookings:ops-customers")},
                    *[
                        {
                            "value": value,
                            "label": label,
                            "count": segment_counts.get(value, 0),
                            "url": f"{reverse('bookings:ops-customers')}?segment={value}",
                        }
                        for value, label in ClientSegment.choices
                    ],
                ],
                "rows": rows,
                "admin_url": reverse("admin:bookings_customerprofile_changelist"),
                "legacy_url": reverse("admin:bookings_customerprofile_changelist"),
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _metric(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    def _customer_payload(self, request, profile):
        last_direct = profile.booking_inquiries.order_by("-check_in", "-updated_at").first()
        last_airbnb = profile.airbnb_guest_records.order_by("-check_in", "-updated_at").first()
        last_stay = self._latest_stay(last_direct, last_airbnb)
        return {
            "id": profile.pk,
            "name": profile.name or profile.email or f"Customer {profile.pk}",
            "email": profile.email,
            "phone": profile.phone,
            "segment": profile.get_segment_display(),
            "segment_value": profile.segment,
            "source": profile.get_source_display(),
            "marketing_consent": profile.get_marketing_consent_status_display(),
            "can_receive_promotions": profile.can_receive_promotions,
            "direct_reservations": profile.direct_reservations,
            "airbnb_reservations": profile.airbnb_reservations,
            "feedback_count": profile.feedback_total,
            "invoice_count": profile.invoice_total,
            "last_stay": last_stay["label"],
            "last_stay_sort": last_stay["sort"],
            "notes": profile.notes[:180],
            "admin_url": request.build_absolute_uri(reverse("admin:bookings_customerprofile_change", args=[profile.pk])),
            "updated_at": profile.updated_at.isoformat(),
        }

    @staticmethod
    def _latest_stay(last_direct, last_airbnb):
        candidates = []
        if last_direct:
            label = last_direct.item.name if last_direct.item else "Direct MLADIS reservation"
            date_label = f"{last_direct.check_in} to {last_direct.check_out}" if last_direct.check_in and last_direct.check_out else ""
            candidates.append((last_direct.check_in or date.min, f"{label} · {date_label}".strip(" ·")))
        if last_airbnb:
            label = last_airbnb.listing_title or (last_airbnb.item.name if last_airbnb.item else "Airbnb stay")
            candidates.append((last_airbnb.check_in or date.min, f"{label} · {last_airbnb.stay_dates}".strip(" ·")))
        if not candidates:
            return {"label": "No stay linked yet", "sort": ""}
        sort_date, label = max(candidates, key=lambda item: item[0])
        return {"label": label, "sort": sort_date.isoformat() if sort_date else ""}


@method_decorator(ops_staff_required, name="dispatch")
class OpsDepositsAPIView(View):
    def get(self, request):
        return JsonResponse(DepositHoldOperationsService().snapshot_payload(request))

    @staticmethod
    def _metric(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    @staticmethod
    def _money(cents):
        return f"${(cents or 0) / 100:,.2f}"

    @staticmethod
    def _date_label(value):
        return value.strftime("%b %-d, %Y") if value else ""

    def _deposit_payload(self, request, deposit):
        return {
            "id": deposit.pk,
            "guest_name": deposit.guest_name,
            "email": deposit.email,
            "stay_name": deposit.item.name if deposit.item else "Flexible MLADIS stay",
            "amount": deposit.display_amount,
            "amount_cents": deposit.amount_cents,
            "currency": deposit.currency.upper(),
            "provider": deposit.get_payment_provider_display(),
            "status": deposit.status,
            "status_label": deposit.get_status_display(),
            "checkout_url": deposit.checkout_url,
            "notes": deposit.notes[:180],
            "admin_url": request.build_absolute_uri(reverse("admin:bookings_damagedeposit_change", args=[deposit.pk])),
            "inquiry_admin_url": request.build_absolute_uri(reverse("admin:bookings_bookinginquiry_change", args=[deposit.inquiry_id])) if deposit.inquiry_id else "",
            "created_at": deposit.created_at.isoformat(),
            "created_label": self._date_label(deposit.created_at),
            "updated_at": deposit.updated_at.isoformat(),
        }


@method_decorator(ops_staff_required, name="dispatch")
class OpsDepositHoldActionAPIView(View):
    def post(self, request, hold_key, action):
        service = DepositHoldOperationsService()
        try:
            hold = service.apply_action(hold_key, action, actor=request.user)
        except ValidationError as error:
            return JsonResponse({"ok": False, "errors": OpsMaintenanceAPIView._validation_errors(error)}, status=400)
        return JsonResponse(
            {
                "ok": True,
                "hold": hold.to_row_payload(request),
                "snapshot": service.snapshot_payload(request),
            }
        )


@method_decorator(ops_staff_required, name="dispatch")
class OpsAgentAPIView(View):
    def get(self, request):
        conversations = AgentConversation.objects.select_related("item").order_by("-updated_at")
        faqs = AgentFAQ.objects.select_related("item").order_by("-priority", "category", "question")
        faq_conversations = conversations.filter(metadata__agent_mode="faq").count()
        openai_conversations = conversations.filter(metadata__agent_mode="openai").count()
        fallback_conversations = conversations.exclude(metadata__agent_mode__in=["faq", "openai"]).count()
        coverage = round((faq_conversations / conversations.count()) * 100) if conversations.count() else 0
        topic_rows = list(
            conversations.values("question_topic")
            .annotate(total=Count("id"))
            .order_by("-total", "question_topic")[:12]
        )
        max_topic_total = max([row["total"] for row in topic_rows] or [0])
        return JsonResponse(
            {
                "summary_cards": [
                    self._metric("Conversations", conversations.count(), "Website chats."),
                    self._metric("FAQ coverage", f"{coverage}%", "FAQ-first answers."),
                    self._metric("OpenAI assists", openai_conversations, "Model-routed."),
                    self._metric("Fallback/guardrail", fallback_conversations, "Needs review."),
                    self._metric("Active FAQs", faqs.filter(is_active=True).count(), "Live answers."),
                    self._metric("Inactive FAQs", faqs.filter(is_active=False).count(), "Draft or disabled answers."),
                ],
                "topics": [
                    {
                        "label": (row["question_topic"] or "general").replace("_", " ").title(),
                        "value": row["question_topic"] or "general",
                        "total": row["total"],
                        "width": int((row["total"] / max_topic_total) * 100) if max_topic_total else 0,
                    }
                    for row in topic_rows
                ],
                "conversations": [self._conversation_payload(request, row) for row in conversations[:30]],
                "faqs": [self._faq_payload(request, row) for row in faqs[:80]],
                "faq_admin_url": reverse("admin:bookings_agentfaq_changelist"),
                "conversation_admin_url": reverse("admin:bookings_agentconversation_changelist"),
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _metric(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    @staticmethod
    def _mode(row):
        mode = (row.metadata or {}).get("agent_mode", "fallback")
        if mode not in {"faq", "openai", "guardrail"}:
            return "fallback"
        return mode

    def _conversation_payload(self, request, row):
        return {
            "id": row.pk,
            "topic": row.question_topic or "general",
            "mode": self._mode(row),
            "item": row.item.name if row.item else "General MLADIS",
            "visitor": row.visitor_name or row.visitor_email or "Website visitor",
            "last_question": row.last_user_message[:220],
            "last_reply": row.last_agent_reply[:220],
            "language": row.language,
            "admin_url": request.build_absolute_uri(reverse("admin:bookings_agentconversation_change", args=[row.pk])),
            "updated_at": row.updated_at.isoformat(),
        }

    @staticmethod
    def _faq_payload(request, row):
        return {
            "id": row.pk,
            "question": row.question,
            "answer": row.answer[:260],
            "category": row.get_category_display(),
            "keywords": row.keywords,
            "item": row.item.name if row.item else "All stays",
            "language": row.language,
            "min_score": str(row.min_score),
            "priority": row.priority,
            "is_active": row.is_active,
            "admin_url": request.build_absolute_uri(reverse("admin:bookings_agentfaq_change", args=[row.pk])),
            "updated_at": row.updated_at.isoformat(),
        }


@method_decorator(ops_staff_required, name="dispatch")
class OpsAdminAPIView(View):
    def get(self, request):
        User = get_user_model()
        users = list(User.objects.order_by("-is_superuser", "-is_staff", "username")[:100])
        access_records = {
            access.email.lower(): access
            for access in AdminAccess.objects.order_by("email")
            if access.email
        }
        rows = [self._user_payload(request, user, access_records.get((user.email or "").lower())) for user in users]
        role_counts = {
            "owner": sum(1 for row in rows if row["role_value"] == "owner"),
            "staff": sum(1 for row in rows if row["role_value"] == "staff"),
            "active": sum(1 for row in rows if row["status_value"] == "active"),
            "invited": sum(1 for row in rows if row["access_status_value"] == "invited"),
        }
        return JsonResponse(
            {
                "summary_cards": [
                    self._metric("Admin users", len(rows), "Django accounts."),
                    self._metric("Staff", role_counts["staff"] + role_counts["owner"], "Can enter ops."),
                    self._metric("Owners", role_counts["owner"], "Superuser access."),
                    self._metric("Active", role_counts["active"], "Enabled accounts."),
                    self._metric("Access records", AdminAccess.objects.count(), "Provisioning rules."),
                    self._metric("Invited", role_counts["invited"], "Access waiting on account."),
                ],
                "role_options": [
                    {"value": "", "label": "All", "count": len(rows)},
                    {"value": "owner", "label": "Owners", "count": role_counts["owner"]},
                    {"value": "staff", "label": "Staff", "count": role_counts["staff"]},
                    {"value": "guest", "label": "Guests", "count": sum(1 for row in rows if row["role_value"] == "guest")},
                    {"value": "inactive", "label": "Inactive", "count": sum(1 for row in rows if row["status_value"] == "inactive")},
                ],
                "rows": rows,
                "admin_url": reverse("admin:auth_user_changelist"),
                "access_admin_url": reverse("admin:bookings_adminaccess_changelist"),
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _metric(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    def _user_payload(self, request, user, access):
        role_value = "owner" if user.is_superuser else "staff" if user.is_staff else "guest"
        role_label = "Owner" if role_value == "owner" else "Staff" if role_value == "staff" else "Guest"
        access_active = bool(access and access.is_active)
        access_status_value = "protected" if user.is_staff and access_active else "invited" if access_active else "standard"
        access_status = "Protected" if access_status_value == "protected" else "Invited" if access_status_value == "invited" else "Standard"
        full_name = user.get_full_name().strip()
        display_name = full_name or user.username or user.email or f"User {user.pk}"
        return {
            "id": user.pk,
            "name": display_name,
            "username": user.username,
            "email": user.email,
            "phone": access.phone if access else "",
            "role": role_label,
            "role_value": role_value,
            "status": "Active" if user.is_active else "Inactive",
            "status_value": "active" if user.is_active else "inactive",
            "access_status": access_status,
            "access_status_value": access_status_value,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "last_login": self._date_label(user.last_login),
            "joined": self._date_label(user.date_joined),
            "notes": (access.notes if access else "")[:220],
            "admin_url": request.build_absolute_uri(reverse("admin:auth_user_change", args=[user.pk])),
            "access_admin_url": request.build_absolute_uri(reverse("admin:bookings_adminaccess_change", args=[access.pk])) if access else reverse("admin:bookings_adminaccess_add"),
        }

    @staticmethod
    def _date_label(value):
        return timezone.localtime(value).strftime("%b %-d, %Y %-I:%M %p") if value else "Never"


@method_decorator(ops_staff_required, name="dispatch")
class OpsSettingsAPIView(View):
    def get(self, request):
        site_settings = SiteSettings.current()
        property_rules = self._body_lines(site_settings.property_rules_body)
        damage_terms = self._body_lines(site_settings.damage_terms_body)
        notification_enabled = sum(
            [
                site_settings.request_notifications_email,
                site_settings.request_notifications_sms,
                site_settings.request_notifications_whatsapp,
            ]
        )
        provider_flags = self._provider_flags()
        return JsonResponse(
            {
                "summary_cards": [
                    self._metric("Site profile", site_settings.site_name, "Public brand object."),
                    self._metric("Notifications", f"{notification_enabled}/3", "Enabled channels."),
                    self._metric("House rules", len(property_rules), f"Version {site_settings.property_rules_version}."),
                    self._metric("Damage terms", len(damage_terms), f"Version {site_settings.damage_terms_version}."),
                    self._metric("Agent limit", site_settings.agent_question_limit, "Questions per user."),
                    self._metric("Providers", f"{sum(provider_flags.values())}/4", "Configured locally."),
                ],
                "sections": [
                    {
                        "id": "brand",
                        "label": "Brand & Public Site",
                        "status": "Ready",
                        "status_tone": "green",
                        "description": "Customer-facing identity and contact information from SiteSettings.",
                        "fields": [
                            self._field("site_name", "Site name", site_settings.site_name, "text"),
                            self._field("contact_email", "Contact email", site_settings.contact_email, "email"),
                            self._field("public_address_label", "Public address label", site_settings.public_address_label, "text"),
                            self._field("logo_url", "Logo URL", site_settings.logo_url, "url"),
                        ],
                    },
                    {
                        "id": "documents",
                        "label": "Rules & Guest Documents",
                        "status": "Published",
                        "status_tone": "blue",
                        "description": "Property rules and damage-hold terms that gate checkout.",
                        "fields": [
                            self._field("property_rules_title", "Property rules title", site_settings.property_rules_title, "text"),
                            self._field("property_rules_version", "Property rules version", site_settings.property_rules_version, "text"),
                            self._field("property_rules_body", "Property rules body", "\n".join(property_rules), "textarea"),
                            self._field("damage_terms_title", "Damage terms title", site_settings.damage_terms_title, "text"),
                            self._field("damage_terms_version", "Damage terms version", site_settings.damage_terms_version, "text"),
                            self._field("damage_terms_body", "Damage terms body", "\n".join(damage_terms), "textarea"),
                        ],
                    },
                    {
                        "id": "notifications",
                        "label": "Notifications",
                        "status": "Partial" if notification_enabled < 3 else "Ready",
                        "status_tone": "orange" if notification_enabled < 3 else "green",
                        "description": "Admin request notification channels. SMS and WhatsApp stay off until providers exist.",
                        "fields": [
                            self._field("request_notifications_email", "Email notifications", site_settings.request_notifications_email, "boolean"),
                            self._field("request_notifications_sms", "SMS notifications", site_settings.request_notifications_sms, "boolean"),
                            self._field("request_notifications_whatsapp", "WhatsApp notifications", site_settings.request_notifications_whatsapp, "boolean"),
                        ],
                    },
                    {
                        "id": "providers",
                        "label": "Providers & Access",
                        "status": "Operational",
                        "status_tone": "violet",
                        "description": "Safe boolean status only. Secrets are never exposed in the page payload.",
                        "fields": [
                            self._field("stripe", "Stripe", provider_flags["stripe"], "boolean"),
                            self._field("paypal", "PayPal", provider_flags["paypal"], "boolean"),
                            self._field("email", "Email backend", provider_flags["email"], "boolean"),
                            self._field("openai", "OpenAI", provider_flags["openai"], "boolean"),
                        ],
                    },
                ],
                "admin_urls": {
                    "site_settings": reverse("admin:bookings_sitesettings_changelist"),
                    "oauth": reverse("bookings:oauth-diagnostics"),
                    "agent_faq": reverse("admin:bookings_agentfaq_changelist"),
                    "users": reverse("bookings:ops-admin"),
                },
                "generated_at": timezone.now().isoformat(),
            }
        )

    @staticmethod
    def _metric(label, value, caption):
        return {"label": label, "value": value, "caption": caption}

    @staticmethod
    def _field(key, label, value, field_type):
        return {"key": key, "label": label, "value": value, "type": field_type}

    @staticmethod
    def _body_lines(body):
        return [line.strip() for line in (body or "").splitlines() if line.strip()]

    @staticmethod
    def _provider_flags():
        return {
            "stripe": bool(getattr(settings, "STRIPE_SECRET_KEY", "") or getattr(settings, "STRIPE_TEST_SECRET_KEY", "")),
            "paypal": bool(getattr(settings, "PAYPAL_CLIENT_ID", "")),
            "email": bool(getattr(settings, "EMAIL_BACKEND", "")),
            "openai": bool(getattr(settings, "OPENAI_API_KEY", "")),
        }


@method_decorator(ops_staff_required, name="dispatch")
class OpsSummaryAPIView(View):
    def get(self, request):
        now = timezone.now()
        since = now - timedelta(days=30)
        reservations = BookingInquiry.objects.select_related("item", "customer_profile")
        deposits = DamageDeposit.objects.select_related("item", "inquiry")
        conversations = AgentConversation.objects.select_related("item")
        customers = CustomerProfile.objects.all()
        visits = PageVisit.objects.filter(created_at__gte=since)

        active_hold_statuses = [
            DepositStatus.NEW,
            DepositStatus.REQUIRES_CONFIGURATION,
            DepositStatus.CHECKOUT_CREATED,
            DepositStatus.REQUIRES_CAPTURE,
        ]
        active_deposits = deposits.filter(status__in=active_hold_statuses)
        faq_total = conversations.filter(metadata__agent_mode="faq").count()
        conversation_total = conversations.count()
        agent_coverage = round((faq_total / conversation_total) * 100) if conversation_total else 0

        data = {
            "metrics": [
                self._metric(
                    "reservations",
                    "Reservations",
                    str(reservations.count()),
                    "Open requests",
                    progress=min(reservations.filter(created_at__gte=since).count() * 8, 100),
                    trend_label=f"+{reservations.filter(created_at__gte=since).count()} in 30 days",
                    accent="teal",
                ),
                self._metric(
                    "deposits",
                    "Active deposits",
                    self._money(active_deposits.aggregate(total=Sum("amount_cents"))["total"]),
                    "Open security workflows",
                    progress=min(active_deposits.count() * 12, 100),
                    trend_label=f"{active_deposits.count()} active holds",
                    accent="blue",
                ),
                self._metric(
                    "customers",
                    "Guest CRM",
                    str(customers.count()),
                    "Guest profiles",
                    progress=min(customers.count(), 100),
                    trend_label=f"{customers.filter(updated_at__gte=since).count()} updated",
                    accent="amber",
                ),
                self._metric(
                    "agent",
                    "Agent coverage",
                    f"{agent_coverage}%",
                    "FAQ-handled questions",
                    progress=agent_coverage,
                    trend_label="FAQ layer active" if agent_coverage else "Needs more FAQ data",
                    accent="violet",
                ),
            ],
            "reservations": [self._reservation(row) for row in reservations.order_by("-created_at")[:8]],
            "deposits": [self._deposit(row) for row in deposits.order_by("-created_at")[:6]],
            "agent_questions": [self._agent_question(row) for row in conversations.order_by("-updated_at")[:6]],
            "calendar_alerts": self._calendar_alerts(),
            "stays": self._stays(),
            "generated_at": now.isoformat(),
            "signals": {
                "visits_30_days": visits.count(),
                "cancellations": reservations.filter(status=BookingStatus.CANCELED).count(),
                "inquiries": reservations.filter(status=BookingStatus.NEW).count(),
            },
        }
        return JsonResponse(data)

    @staticmethod
    def _metric(id_, label, value, caption, *, progress, trend_label, accent):
        return {
            "id": id_,
            "label": label,
            "value": value,
            "caption": caption,
            "trend": "up" if progress else "neutral",
            "trend_label": trend_label,
            "accent": accent,
            "progress": progress,
        }

    @staticmethod
    def _money(cents):
        return f"${(cents or 0) / 100:,.0f}"

    @staticmethod
    def _date_label(value):
        return value.strftime("%b %-d") if value else ""

    def _reservation(self, row):
        return {
            "id": row.pk,
            "guest_name": row.guest_name,
            "stay_name": row.item.name if row.item else "Flexible MLADIS stay",
            "check_in": self._date_label(row.check_in),
            "check_out": self._date_label(row.check_out),
            "guests": row.guests,
            "status": self._reservation_status(row.status),
            "admin_url": reverse("admin:bookings_bookinginquiry_change", args=[row.pk]),
            "action_required": row.status in {BookingStatus.NEW, BookingStatus.REVIEWING, BookingStatus.QUOTED}
            or row.is_blacklist_flagged
            or row.email_delivery_status == "failed",
        }

    @staticmethod
    def _reservation_status(status):
        if status == BookingStatus.CONFIRMED:
            return "confirmed"
        if status in {BookingStatus.CANCELED, BookingStatus.DECLINED}:
            return "cancelled"
        if status in {BookingStatus.REVIEWING, BookingStatus.QUOTED}:
            return "reviewing"
        return "new"

    def _deposit(self, row):
        return {
            "id": row.pk,
            "guest_name": row.guest_name,
            "stay_name": row.item.name if row.item else "Flexible MLADIS stay",
            "amount_cents": row.amount_cents,
            "currency": row.currency.upper(),
            "provider": "PayPal" if row.payment_provider == "paypal" else "Stripe",
            "status": self._deposit_status(row.status),
        }

    @staticmethod
    def _deposit_status(status):
        if status == DepositStatus.REQUIRES_CAPTURE:
            return "authorized"
        if status == DepositStatus.CAPTURED:
            return "captured"
        if status == DepositStatus.CANCELED:
            return "released"
        if status == DepositStatus.FAILED:
            return "failed"
        return "pending"

    @staticmethod
    def _agent_question(row):
        mode = (row.metadata or {}).get("agent_mode", "fallback")
        if mode not in {"faq", "openai"}:
            mode = "fallback"
        return {
            "id": row.pk,
            "topic": row.question_topic or "general",
            "last_question": row.last_user_message[:140],
            "mode": mode,
            "created_at": row.updated_at.isoformat(),
        }

    def _calendar_alerts(self):
        alerts = []
        today = timezone.localdate()
        blocks = (
            AvailabilityBlock.objects.filter(is_active=True, end_date__gte=today)
            .select_related("item")
            .order_by("start_date")[:4]
        )
        for block in blocks:
            alerts.append(
                {
                    "id": f"block-{block.pk}",
                    "label": block.reason or "Manual block active",
                    "stay_name": block.item.name,
                    "date_range": self._range_label(block.start_date, block.end_date),
                    "severity": "warning",
                }
            )
        overrides = (
            DailyPriceOverride.objects.filter(is_active=True, end_date__gte=today)
            .select_related("item")
            .order_by("start_date")[:4]
        )
        for override in overrides:
            alerts.append(
                {
                    "id": f"price-{override.pk}",
                    "label": override.label or f"${override.nightly_price:,.0f} nightly override",
                    "stay_name": override.item.name,
                    "date_range": self._range_label(override.start_date, override.end_date),
                    "severity": "info",
                }
            )
        if not alerts:
            needs_setup = BookableItem.objects.filter(
                is_active=True,
                category=BookingCategory.STAY,
            ).filter(Q(calendar_feed__isnull=True) | Q(calendar_feed__airbnb_ical_url=""))
            for stay in needs_setup[:3]:
                alerts.append(
                    {
                        "id": f"feed-{stay.pk}",
                        "label": "Calendar feed needs setup",
                        "stay_name": stay.name,
                        "date_range": "Airbnb iCal not connected",
                        "severity": "danger",
                    }
                )
        return alerts[:6]

    def _stays(self):
        rows = []
        today = timezone.localdate()
        for stay in (
            BookableItem.objects.filter(is_active=True, category=BookingCategory.STAY)
            .prefetch_related("gallery_images")
            .order_by("-is_featured", "name")[:6]
        ):
            reservations = BookingInquiry.objects.filter(
                item=stay,
                status__in=[BookingStatus.CONFIRMED, BookingStatus.REVIEWING, BookingStatus.QUOTED],
                check_out__gte=today,
            )
            booked_nights = sum(min((row.check_out - row.check_in).days, 30) for row in reservations[:20])
            occupancy = min(round((booked_nights / 30) * 100), 100)
            revenue_cents = reservations.aggregate(total=Sum("total_cents"))["total"] or 0
            rows.append(
                {
                    "id": stay.slug,
                    "name": stay.name,
                    "subtitle": stay.short_description,
                    "image_url": self._stay_image_url(stay),
                    "rating": str(stay.airbnb_rating or ""),
                    "occupancy_label": f"{occupancy}% occupied",
                    "revenue_label": self._money(revenue_cents),
            "status": "review" if not getattr(stay, "calendar_feed", None) else "live",
            "detail_url": reverse("bookings:stay-detail", args=[stay.slug]),
        }
            )
        return rows

    @staticmethod
    def _stay_image_url(stay):
        gallery_image = stay.gallery_images.first()
        if gallery_image:
            return gallery_image.image_url
        if stay.image:
            return stay.image
        return (
            "https://a0.muscache.com/im/pictures/miso/Hosting-582161420407543691/"
            "original/c097c0de-d8eb-45da-be8a-644065f20ab8.jpeg?im_w=1200&quality=80&auto=webp"
        )

    def _range_label(self, start, end):
        if start == end:
            return self._date_label(start)
        return f"{self._date_label(start)} - {self._date_label(end)}"


@method_decorator(ops_staff_required, name="dispatch")
class LegacyOpsDashboardView(TemplateView):
    template_name = "bookings/ops_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        reservations = BookingInquiry.objects.all()
        visits = PageVisit.objects.filter(created_at__gte=thirty_days_ago)
        context.update(
            {
                "reservation_count": reservations.count(),
                "cancellation_count": reservations.filter(status=BookingStatus.CANCELED).count(),
                "inquiry_count": reservations.filter(status=BookingStatus.NEW).count(),
                "visit_count": visits.count(),
                "recent_reservations": reservations.select_related("item", "customer_profile")[:8],
                "top_questions": AgentConversation.objects.values("question_topic")
                .annotate(total=Count("id"))
                .order_by("-total", "question_topic")[:8],
                "popular_pages": visits.values("path").annotate(total=Count("id")).order_by("-total", "path")[:8],
            }
        )
        return context


@method_decorator(never_cache, name="dispatch")
class AgentAPIView(View):
    def post(self, request):
        from .services import AgentRequest, BookingAgentService

        access = AgentAccessContext.from_request(request)
        if not access.can_ask:
            return JsonResponse(access.denial_payload(), status=access.denial_status)

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        message = str(payload.get("message", "")).strip()
        if not message:
            return JsonResponse({"error": "No message provided."}, status=400)

        session_id = str(payload.get("session_id") or uuid4())
        item_id = payload.get("item_id") or None

        agent_request = AgentRequest(
            message=message,
            session_id=session_id,
            item_id=item_id,
            user_id=request.user.pk,
            visitor_name=str(payload.get("visitor_name", "")).strip()
            or request.user.get_full_name()
            or request.user.get_username(),
            visitor_email=str(payload.get("visitor_email", "")).strip() or request.user.email,
        )
        response = BookingAgentService().reply(agent_request)
        return JsonResponse(
            {
                "reply": response.reply,
                "session_id": session_id,
                "conversation_id": response.conversation_id,
                "agent": AgentAccessContext.from_request(request).to_public_payload(),
            }
        )
