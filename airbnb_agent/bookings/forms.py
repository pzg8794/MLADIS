from django import forms
from django.utils import timezone

from django.conf import settings

from .models import BookableItem, BookingInquiry, DamageDeposit


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

    def save(self, commit=True):
        deposit = super().save(commit=False)
        deposit.amount_cents = settings.DEPOSIT_AMOUNT_CENTS
        deposit.currency = settings.DEPOSIT_CURRENCY
        if commit:
            deposit.save()
        return deposit
