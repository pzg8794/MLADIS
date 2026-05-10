import csv
import json
from datetime import timedelta
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Count, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
import requests
import stripe

from .forms import (
    BookingInquiryForm,
    DamageDepositForm,
    DonationForm,
    ReservationCancelForm,
    ReservationManageForm,
    SignUpForm,
)
from .models import (
    AgentConversation,
    AirbnbGuestRecord,
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CalendarFeed,
    ClientSegment,
    CustomerProfile,
    DailyPriceOverride,
    DamageDeposit,
    DepositStatus,
    Invoice,
    MarketingConsentStatus,
    MissionCause,
    PageVisit,
    SiteSettings,
)
from .services import (
    AdminAccessService,
    AgentRequest,
    BookingAgentService,
    BookingEmailService,
    DamageDepositService,
    DonationService,
    PayPalAPIError,
    PayPalDamageDepositService,
    ReservationRequestService,
    get_damage_deposit_service,
)
from .social_auth import SOCIAL_LOGIN_PROVIDER_SPECS, get_social_login_providers


ops_staff_required = user_passes_test(
    lambda user: user.is_active and user.is_staff,
    login_url=reverse_lazy("bookings:login"),
)


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


class ModernSiteView(TemplateView):
    template_name = "bookings/modern_site.html"


class ModernAccountView(LoginRequiredMixin, TemplateView):
    template_name = "bookings/modern_site.html"


class PublicSiteSummaryAPIView(View):
    def get(self, request):
        settings_obj = SiteSettings.current()
        logo_url = settings_obj.logo_display_url
        if settings_obj.logo:
            try:
                if not settings_obj.logo.storage.exists(settings_obj.logo.name):
                    logo_url = settings_obj.logo_url
            except OSError:
                logo_url = settings_obj.logo_url
        if logo_url and "test-logo" in logo_url:
            logo_url = settings_obj.logo_url
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


class AccountSummaryAPIView(LoginRequiredMixin, View):
    def get(self, request):
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
        return JsonResponse(
            {
                "profile": {
                    "name": request.user.get_full_name() or request.user.username or request.user.email,
                    "email": request.user.email,
                },
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
            "stay_name": item.name if item else "Flexible stay",
            "check_in": reservation.check_in.isoformat(),
            "check_out": reservation.check_out.isoformat(),
            "guests": reservation.guests,
            "phone": reservation.phone,
            "status": reservation.get_status_display(),
            "can_cancel": reservation.can_customer_cancel,
            "display_total": reservation.display_total,
            "display_deposit": reservation._display_money(reservation.deposit_cents),
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
            inquiry = form.save(commit=False)
            if request.user.is_authenticated:
                inquiry.user = request.user
            ReservationRequestService().prepare(inquiry, coupon=form.coupon)
            inquiry.save()
            BookingEmailService().send_inquiry_notifications(inquiry, request=request)
            messages.success(
                request,
                f"Thanks, {inquiry.guest_name}. Your booking is started.",
            )
            if inquiry.is_admin_test:
                return redirect(reverse("bookings:dashboard"))
            return redirect(reverse("bookings:home") + f"?submitted=1&deposit_for={inquiry.id}#deposit")

        return render(
            request,
            "bookings/home.html",
            HomePageView.booking_context(request, form=form),
            status=400,
        )


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("bookings:dashboard")

    def form_valid(self, form):
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
            messages.error(request, "Please add your name, email, and listing before starting the deposit hold.")
            context = HomePageView.booking_context(request, deposit_form=form)
            context["show_deposit"] = True
            return render(request, "bookings/home.html", context, status=400)

        deposit = form.save()
        service = get_damage_deposit_service(form.cleaned_data.get("payment_provider"))
        result = service.create_checkout_session(deposit, request)
        if result.success:
            return redirect(result.checkout_url)

        messages.warning(request, result.message)
        deposit_for = f"?deposit_for={deposit.inquiry_id}" if deposit.inquiry_id else "?deposit=1"
        return redirect(reverse("bookings:home") + f"{deposit_for}#deposit")


class DonationCheckoutView(View):
    service_class = DonationService

    def post(self, request):
        form = DonationForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please choose a valid donation amount and mission cause.")
            context = AboutPageView().get_context_data()
            context["donation_form"] = form
            return render(request, "bookings/about.html", context, status=400)

        donation = form.save()
        result = self.service_class().create_checkout_session(donation, request)
        if result.success:
            return redirect(result.checkout_url)

        messages.warning(request, result.message)
        return redirect(reverse("bookings:about") + "#mission")


class DonationSuccessView(View):
    service_class = DonationService

    def get(self, request):
        session_id = request.GET.get("session_id", "")
        donation = None
        if session_id:
            try:
                donation = self.service_class().sync_checkout_session(session_id)
            except stripe.StripeError:
                donation = None

        if donation:
            messages.success(request, f"Thank you for your {donation.display_amount} donation.")
        else:
            messages.success(request, "Thank you. Your donation checkout was completed.")
        return redirect(reverse("bookings:about") + "#mission")


class DamageDepositSuccessView(View):
    service_class = DamageDepositService

    def get(self, request):
        session_id = request.GET.get("session_id", "")
        deposit = None
        if session_id:
            try:
                deposit = self.service_class().sync_checkout_session(session_id)
            except stripe.StripeError:
                deposit = None

        if deposit:
            messages.success(
                request,
                f"Your {deposit.display_amount} damage deposit authorization is recorded.",
            )
        else:
            messages.success(request, "Thanks. Your deposit checkout was completed.")
        return redirect(reverse("bookings:home") + "#deposit")


class PayPalDamageDepositSuccessView(View):
    service_class = PayPalDamageDepositService

    def get(self, request):
        order_id = request.GET.get("token", "")
        deposit = None
        if order_id:
            try:
                deposit = self.service_class().authorize_order(order_id)
            except (PayPalAPIError, requests.RequestException):
                deposit = None

        if deposit:
            messages.success(
                request,
                f"Your {deposit.display_amount} damage deposit authorization is recorded.",
            )
        else:
            messages.warning(
                request,
                "We could not confirm the PayPal deposit authorization. Please try again.",
            )
        return redirect(reverse("bookings:home") + "#deposit")


class PayPalDamageDepositCancelView(View):
    service_class = PayPalDamageDepositService

    def get(self, request):
        order_id = request.GET.get("token", "")
        self.service_class().cancel_order(order_id)
        messages.warning(request, "The PayPal deposit authorization was canceled.")
        return redirect(reverse("bookings:home") + "#deposit")


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    service_class = DamageDepositService

    def post(self, request):
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

        self.service_class().handle_event(event)
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
class OAuthDiagnosticsView(TemplateView):
    template_name = "bookings/oauth_diagnostics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        origin = getattr(settings, "SOCIAL_AUTH_CANONICAL_ORIGIN", "") or self.request.build_absolute_uri("/")[:-1]
        callback_rows = []
        provider_status = {provider["id"]: provider for provider in get_social_login_providers()}
        for provider in SOCIAL_LOGIN_PROVIDER_SPECS:
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
                "origin": origin,
                "site": Site.objects.get(pk=settings.SITE_ID),
                "callback_rows": callback_rows,
                "account_protocol": settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
            }
        )
        return context


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
            AirbnbGuestRecord.objects.select_related("customer_profile", "item", "customer_feedback")
            .order_by("-check_in", "guest_name", "-updated_at")
        )
        for record in records:
            profile = record.customer_profile
            email = record.email or (profile.email if profile else "")
            phone = record.phone or (profile.phone if profile else "")
            feedback_entry = getattr(record, "customer_feedback", None)
            feedback = (
                feedback_entry.feedback_text
                if feedback_entry
                else record.feedback_summary or record.message_excerpt
            )
            consent_status = (
                profile.get_marketing_consent_status_display()
                if profile
                else MarketingConsentStatus.UNKNOWN.label
            )
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
                    "feedback_admin_url": reverse("admin:bookings_customerfeedback_change", args=[feedback_entry.pk])
                    if feedback_entry
                    else "",
                    "item": record.item,
                    "listing": record.item.name if record.item else record.listing_title or record.airbnb_listing_id,
                    "listing_id": record.airbnb_listing_id,
                    "stay_dates": record.stay_dates,
                    "guests": record.guests,
                    "rating": record.rating,
                    "feedback": feedback,
                    "source_subject": record.source_email_subject,
                    "thread_url": record.airbnb_thread_url,
                    "consent_status": consent_status,
                    "segment": profile.get_segment_display() if profile else "",
                    "updated_at": record.updated_at,
                }
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
            {"label": "Airbnb reservations", "value": len(rows), "caption": "Booked Airbnb stays linked to guests."},
            {"label": "With email", "value": with_email, "caption": "Direct email found in imported data."},
            {"label": "With phone", "value": with_phone, "caption": "Phone number found in imported data."},
            {"label": "With feedback", "value": with_feedback, "caption": "Feedback, rating, or message context attached."},
            {"label": "Promotion-ready", "value": opted_in, "caption": "Customers marked opted in for offers."},
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
class ModernOpsDashboardView(TemplateView):
    template_name = "bookings/modern_dashboard.html"


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
                    "Open and upcoming requests",
                    progress=min(reservations.filter(created_at__gte=since).count() * 8, 100),
                    trend_label=f"+{reservations.filter(created_at__gte=since).count()} in 30 days",
                    accent="teal",
                ),
                self._metric(
                    "deposits",
                    "Deposit holds",
                    self._money(active_deposits.aggregate(total=Sum("amount_cents"))["total"]),
                    "Authorized or pending holds",
                    progress=min(active_deposits.count() * 12, 100),
                    trend_label=f"{active_deposits.count()} active holds",
                    accent="blue",
                ),
                self._metric(
                    "customers",
                    "Guest CRM",
                    str(customers.count()),
                    "Customer profiles and imported Airbnb contacts",
                    progress=min(customers.count(), 100),
                    trend_label=f"{customers.filter(updated_at__gte=since).count()} updated",
                    accent="amber",
                ),
                self._metric(
                    "agent",
                    "Agent coverage",
                    f"{agent_coverage}%",
                    "Questions answered by the FAQ layer",
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
                }
            )
        return rows

    @staticmethod
    def _stay_image_url(stay):
        gallery_image = stay.gallery_images.first()
        if gallery_image:
            return gallery_image.image_url
        return stay.image

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


class AgentAPIView(View):
    service_class = BookingAgentService

    def post(self, request):
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
            visitor_name=str(payload.get("visitor_name", "")).strip(),
            visitor_email=str(payload.get("visitor_email", "")).strip(),
        )
        response = self.service_class().reply(agent_request)
        return JsonResponse(
            {
                "reply": response.reply,
                "session_id": session_id,
                "conversation_id": response.conversation_id,
            }
        )
