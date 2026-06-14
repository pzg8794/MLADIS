import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationsWorkItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("slug", models.SlugField(blank=True, max_length=220, unique=True)),
                ("description", models.TextField(blank=True)),
                ("list_name", models.CharField(default="Business tasks", max_length=80)),
                (
                    "neuron",
                    models.CharField(
                        choices=[
                            ("operations", "Operations"),
                            ("booking", "Booking"),
                            ("finance", "Finance"),
                            ("research", "Research"),
                            ("education", "Education"),
                            ("fitness", "Fitness"),
                            ("portfolio", "Portfolio"),
                            ("pyramid", "Pyramid"),
                            ("fair_agent", "FairAgent"),
                        ],
                        default="operations",
                        max_length=24,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("captured", "Captured"),
                            ("planned", "Planned"),
                            ("in_progress", "In progress"),
                            ("blocked", "Blocked"),
                            ("paused", "Paused"),
                            ("done", "Done"),
                        ],
                        default="captured",
                        max_length=24,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("critical", "Critical")],
                        default="medium",
                        max_length=16,
                    ),
                ),
                ("next_action", models.CharField(blank=True, max_length=240)),
                ("source_url", models.URLField(blank=True)),
                ("github_url", models.URLField(blank=True)),
                ("drive_url", models.URLField(blank=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("sort_order", models.PositiveIntegerField(default=100)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_operations_work_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_operations_work_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["list_name", "sort_order", "title"],
            },
        ),
        migrations.AddIndex(
            model_name="operationsworkitem",
            index=models.Index(fields=["list_name", "status"], name="ops_wi_list_status_idx"),
        ),
        migrations.AddIndex(
            model_name="operationsworkitem",
            index=models.Index(fields=["neuron", "priority"], name="ops_wi_neuron_prio_idx"),
        ),
        migrations.AddIndex(
            model_name="operationsworkitem",
            index=models.Index(fields=["updated_at"], name="ops_wi_updated_idx"),
        ),
    ]
