from django import forms
from django.utils import timezone

from django.conf import settings

from .models import BookableItem, BookingInquiry, DamageDeposit, Donation, MissionCause


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
            "message",
        ]
        labels = {
            "item": "Booking",
            "guest_name": "Name",
            "check_in": "Start date",
            "check_out": "End date",
        }
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = BookableItem.objects.filter(is_active=True)
        self.fields["item"].empty_label = "Flexible / help me choose"
        self.fields["phone"].required = False
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
        today = timezone.localdate()

        if check_in and check_in < today:
            self.add_error("check_in", "Choose a future date.")
        if check_in and check_out and check_out <= check_in:
            self.add_error("check_out", "End date must be after start date.")

        return cleaned


class DamageDepositForm(forms.ModelForm):
    class Meta:
        model = DamageDeposit
        fields = ["item", "guest_name", "email"]
        labels = {
            "item": "Booking",
            "guest_name": "Name",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = BookableItem.objects.filter(is_active=True)
        self.fields["item"].empty_label = "Flexible / not sure yet"
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("data-field", f"deposit_{field_name}")
            field.widget.attrs.setdefault("id", f"id_deposit_{field_name}")

    def save(self, commit=True):
        deposit = super().save(commit=False)
        deposit.amount_cents = settings.DEPOSIT_AMOUNT_CENTS
        deposit.currency = settings.DEPOSIT_CURRENCY
        if commit:
            deposit.save()
        return deposit


class DonationForm(forms.ModelForm):
    amount = forms.DecimalField(
        label="Donation amount",
        min_value=5,
        max_digits=8,
        decimal_places=2,
        initial=25,
        help_text="Minimum donation is $5.",
    )

    class Meta:
        model = Donation
        fields = ["cause", "donor_name", "email"]
        labels = {
            "donor_name": "Name",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cause"].queryset = MissionCause.objects.filter(is_active=True)
        self.fields["cause"].empty_label = "MLADIS mission fund"
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
