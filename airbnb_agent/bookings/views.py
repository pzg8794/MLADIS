import json
from datetime import timedelta
from uuid import uuid4

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Count, Q
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
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CalendarFeed,
    CustomerProfile,
    Invoice,
    MissionCause,
    PageVisit,
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


@method_decorator(staff_member_required, name="dispatch")
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


@method_decorator(staff_member_required, name="dispatch")
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


@method_decorator(staff_member_required, name="dispatch")
class OpsDashboardView(TemplateView):
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
