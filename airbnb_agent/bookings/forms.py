from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.conf import settings

from .models import (
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    Coupon,
    DailyPriceOverride,
    DamageDeposit,
    DepositProvider,
    Donation,
    MissionCause,
)


class BookingInquiryForm(forms.ModelForm):
    class Meta:
        model = BookingInquiry
        fields = [
            "item",
            "guest_name",
            "email",
            "phone",
            "check_in",
            "check_out",
            "guests",
            "coupon_code",
            "is_admin_test",
            "message",
        ]
        labels = {
            "item": _("Booking"),
            "guest_name": _("Name"),
            "check_in": _("Start date"),
            "check_out": _("End date"),
            "coupon_code": _("Coupon code"),
            "is_admin_test": _("Admin test reservation"),
        }
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.coupon = None
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = BookableItem.objects.filter(is_active=True)
        self.fields["item"].empty_label = _("Flexible / help me choose")
        self.fields["phone"].required = True
        self.fields["phone"].label = _("Phone number")
        self.fields["message"].required = False
        self.fields["coupon_code"].required = False
        self.fields["guests"].min_value = 1
        self.fields["guests"].widget.attrs["min"] = "1"
        if self.user and self.user.is_authenticated:
            full_name = self.user.get_full_name()
            self.fields["guest_name"].initial = self.fields["guest_name"].initial or full_name or self.user.username
            self.fields["email"].initial = self.fields["email"].initial or self.user.email
            profile = getattr(self.user, "customer_profile", None)
            if profile:
                self.fields["phone"].initial = self.fields["phone"].initial or profile.phone
        if not (self.user and self.user.is_staff):
            self.fields.pop("is_admin_test")
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("data-field", field_name)

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        today = timezone.localdate()

        if check_in and check_in < today:
            self.add_error("check_in", _("Choose a future date."))
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", _("End date must be after start date."))

        coupon_code = (cleaned.get("coupon_code") or "").strip().upper()
        if coupon_code:
            coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
            if not coupon or not coupon.is_valid():
                self.add_error("coupon_code", _("This coupon is not active or has expired."))
            else:
                self.coupon = coupon
                cleaned["coupon_code"] = coupon.code

        return cleaned


class DamageDepositForm(forms.ModelForm):
    inquiry_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    payment_provider = forms.ChoiceField(
        label=_("Payment method"),
        choices=DepositProvider.choices,
        required=False,
        initial=DepositProvider.STRIPE,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = DamageDeposit
        fields = ["item", "guest_name", "email"]
        labels = {
            "item": _("Booking"),
            "guest_name": _("Name"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = BookableItem.objects.filter(is_active=True)
        self.fields["item"].empty_label = _("Flexible / not sure yet")
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("data-field", f"deposit_{field_name}")
            field.widget.attrs.setdefault("id", f"id_deposit_{field_name}")
        self.fields["payment_provider"].widget.attrs.setdefault("data-field", "deposit_payment_provider")
        self.order_fields(["item", "guest_name", "email", "payment_provider", "inquiry_id"])

    def save(self, commit=True):
        deposit = super().save(commit=False)
        inquiry_id = self.cleaned_data.get("inquiry_id")
        if inquiry_id:
            inquiry = BookingInquiry.objects.filter(pk=inquiry_id).select_related("item").first()
            if inquiry:
                deposit.inquiry = inquiry
                deposit.item = deposit.item or inquiry.item
                deposit.guest_name = deposit.guest_name or inquiry.guest_name
                deposit.email = deposit.email or inquiry.email
        deposit.payment_provider = self.cleaned_data.get("payment_provider") or DepositProvider.STRIPE
        deposit.amount_cents = settings.DEPOSIT_AMOUNT_CENTS
        deposit.currency = settings.DEPOSIT_CURRENCY
        if commit:
            deposit.save()
        return deposit


class DonationForm(forms.ModelForm):
    amount = forms.DecimalField(
        label=_("Donation amount"),
        min_value=5,
        max_digits=8,
        decimal_places=2,
        initial=25,
        help_text=_("Minimum donation is $5."),
    )

    class Meta:
        model = Donation
        fields = ["cause", "donor_name", "email"]
        labels = {
            "donor_name": _("Name"),
            "email": _("Email"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cause"].queryset = MissionCause.objects.filter(is_active=True)
        self.fields["cause"].empty_label = _("MLADIS mission fund")
        self.fields["donor_name"].required = False
        self.fields["email"].required = False
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("data-field", f"donation_{field_name}")
            field.widget.attrs.setdefault("id", f"id_donation_{field_name}")
        self.fields["amount"].widget.attrs.setdefault("class", "form-control")
        self.fields["amount"].widget.attrs.setdefault("data-field", "donation_amount")
        self.fields["amount"].widget.attrs.setdefault("id", "id_donation_amount")
        self.order_fields(["cause", "amount", "donor_name", "email"])

    def save(self, commit=True):
        donation = super().save(commit=False)
        donation.amount_cents = int(self.cleaned_data["amount"] * 100)
        donation.currency = settings.DONATION_CURRENCY
        if commit:
            donation.save()
        return donation


class AvailabilityBlockForm(forms.ModelForm):
    class Meta:
        model = AvailabilityBlock
        fields = ["item", "start_date", "end_date", "reason", "notes"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = BookableItem.objects.filter(
            is_active=True,
            category=BookingCategory.STAY,
        )
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "vTextField")
            field.widget.attrs.setdefault("data-field", f"availability_block_{field_name}")


class DailyPriceOverrideForm(forms.ModelForm):
    class Meta:
        model = DailyPriceOverride
        fields = ["item", "start_date", "end_date", "nightly_price", "label", "notes"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "nightly_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = BookableItem.objects.filter(
            is_active=True,
            category=BookingCategory.STAY,
        )
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "vTextField")
            field.widget.attrs.setdefault("data-field", f"daily_price_override_{field_name}")


class AirbnbGuestImportForm(forms.Form):
    import_file = forms.FileField(
        label=_("Airbnb export file"),
        help_text=_("Upload a .json or .csv export from Airbnb/Gmail reservation messages."),
    )
    dry_run = forms.BooleanField(
        label=_("Dry run only"),
        required=False,
        initial=True,
        help_text=_("Preview how many records would be created or updated before writing anything."),
    )

    def clean_import_file(self):
        uploaded = self.cleaned_data["import_file"]
        filename = (uploaded.name or "").lower()
        if not filename.endswith((".json", ".csv")):
            raise forms.ValidationError(_("Upload a .json or .csv file."))
        if uploaded.size > 10 * 1024 * 1024:
            raise forms.ValidationError(_("Keep Airbnb import files under 10 MB."))
        return uploaded


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(label=_("First name"), max_length=150, required=False)
    last_name = forms.CharField(label=_("Last name"), max_length=150, required=False)
    phone = forms.CharField(label=_("Phone number"), max_length=40, required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("data-field", field_name)


class ReservationManageForm(forms.ModelForm):
    class Meta:
        model = BookingInquiry
        fields = ["phone", "check_in", "check_out", "guests", "message"]
        labels = {
            "check_in": _("Start date"),
            "check_out": _("End date"),
        }
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = True
        self.fields["message"].required = False
        self.fields["guests"].min_value = 1
        self.fields["guests"].widget.attrs["min"] = "1"
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("data-field", field_name)

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", _("End date must be after start date."))
        return cleaned


class ReservationCancelForm(forms.Form):
    reason = forms.CharField(
        label=_("Cancellation reason"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
