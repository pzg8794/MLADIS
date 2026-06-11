from django import forms

from .models import WorkItem


class WorkItemForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = [
            "title",
            "description",
            "neuron",
            "status",
            "priority",
            "next_action",
            "item",
            "inquiry",
            "source_url",
            "github_url",
            "drive_url",
            "assigned_to",
            "due_date",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "next_action": forms.TextInput(attrs={"placeholder": "What is the next tiny action?"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get("item")
        inquiry = cleaned_data.get("inquiry")

        if inquiry and not item and inquiry.item_id:
            cleaned_data["item"] = inquiry.item
        return cleaned_data
