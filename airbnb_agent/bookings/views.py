import json
from uuid import uuid4

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, TemplateView
import stripe

from .forms import BookingInquiryForm, DamageDepositForm, DonationForm
from .models import BookableItem, BookingCategory, CalendarFeed, MissionCause
from .services import AgentRequest, BookingAgentService, DamageDepositService, DonationService


class HomePageView(TemplateView):
    template_name = "bookings/home.html"

    @staticmethod
    def booking_context(request, form=None):
        selected_item_id = request.GET.get("item", "")
        if form is None and selected_item_id:
            form = BookingInquiryForm(initial={"item": selected_item_id})
        featured_items = (
            BookableItem.objects.filter(is_active=True, is_featured=True)
            .prefetch_related("gallery_images", "review_themes")
        )
        return {
            "booking_form": form or BookingInquiryForm(),
            "deposit_form": DamageDepositForm(initial={"item": selected_item_id} if selected_item_id else None),
            "donation_form": DonationForm(),
            "deposit_amount": settings.DEPOSIT_AMOUNT_CENTS / 100,
            "deposit_currency": settings.DEPOSIT_CURRENCY.upper(),
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
            .prefetch_related("gallery_images", "review_themes")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "booking_form": BookingInquiryForm(initial={"item": self.object.id}),
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
                "gallery_tiles": [
                    {
                        "title": "Santo Domingo",
                        "text": "Colonial streets, modern restaurants, and easy local access.",
                        "class_name": "is-city",
                        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e3/SantoDomingoedit.JPG",
                    },
                    {
                        "title": "Tropical days",
                        "text": "Beach energy, warm weather, and room for family memories.",
                        "class_name": "is-beach",
                        "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/78/Bavaro.jpg",
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


class BookingInquiryCreateView(View):
    def post(self, request):
        form = BookingInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save()
            messages.success(
                request,
                f"Thanks, {inquiry.guest_name}. We received your request and will follow up soon.",
            )
            return redirect(reverse("bookings:home") + "?submitted=1#booking")

        return render(
            request,
            "bookings/home.html",
            HomePageView.booking_context(request, form=form),
            status=400,
        )


class DamageDepositCheckoutView(View):
    service_class = DamageDepositService

    def post(self, request):
        form = DamageDepositForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Please add your name, email, and listing before starting the deposit hold.")
            context = HomePageView.booking_context(request)
            context["deposit_form"] = form
            return render(request, "bookings/home.html", context, status=400)

        deposit = form.save()
        result = self.service_class().create_checkout_session(deposit, request)
        if result.success:
            return redirect(result.checkout_url)

        messages.warning(request, result.message)
        return redirect(reverse("bookings:home") + "#deposit")


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
