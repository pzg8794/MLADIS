# Generated manually for the Operations Workboard MVP.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bookings", "0016_agentfaq"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=220)),
                ("description", models.TextField(blank=True)),
                ("neuron", models.CharField(choices=[("operations", "Operations"), ("booking", "Booking"), ("finance", "Finance"), ("research", "Research"), ("education", "Education"), ("fitness", "Fitness"), ("portfolio", "Portfolio"), ("pyramid", "Pyramid"), ("fair_agent", "FairAgent")], default="operations", max_length=32)),
                ("status", models.CharField(choices=[("captured", "Captured"), ("planned", "Planned"), ("in_progress", "In Progress"), ("blocked", "Blocked"), ("paused", "Paused"), ("done", "Done")], default="captured", max_length=32)),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")], default="medium", max_length=16)),
                ("next_action", models.CharField(blank=True, max_length=255)),
                ("source_url", models.URLField(blank=True)),
                ("github_url", models.URLField(blank=True)),
                ("drive_url", models.URLField(blank=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_work_items", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_work_items", to=settings.AUTH_USER_MODEL)),
                ("item", models.ForeignKey(blank=True, help_text="Optional listing/resource this work item affects.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="operations_work_items", to="bookings.bookableitem")),
                ("inquiry", models.ForeignKey(blank=True, help_text="Optional reservation/request this work item supports.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="operations_work_items", to="bookings.bookinginquiry")),
            ],
            options={
                "ordering": ["status", "sort_order", "-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="workitem",
            index=models.Index(fields=["status", "sort_order"], name="operations_status_86f9ca_idx"),
        ),
        migrations.AddIndex(
            model_name="workitem",
            index=models.Index(fields=["neuron", "status"], name="operations_neuron_f914c4_idx"),
        ),
        migrations.AddIndex(
            model_name="workitem",
            index=models.Index(fields=["priority", "status"], name="operations_priorit_b5dcb7_idx"),
        ),
        migrations.AddIndex(
            model_name="workitem",
            index=models.Index(fields=["item", "status"], name="operations_item_9ddb1c_idx"),
        ),
        migrations.AddIndex(
            model_name="workitem",
            index=models.Index(fields=["inquiry", "status"], name="operations_inquiry_8890ae_idx"),
        ),
        migrations.AddIndex(
            model_name="workitem",
            index=models.Index(fields=["-updated_at"], name="operations_updated_72256e_idx"),
        ),
    ]
