# Generated migration for MaintenanceEvent and MaintenancePhoto
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Adjust these to your actual app labels / migration names
        ("bookings", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenanceEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=200)),
                ("category", models.CharField(
                    choices=[("CLEANING","Cleaning"),("REPAIR","Repair"),("INSPECTION","Inspection"),("OTHER","Other")],
                    default="CLEANING", max_length=20)),
                ("cost_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cost_currency", models.CharField(default="USD", max_length=3)),
                ("start_at", models.DateTimeField()),
                ("end_at", models.DateTimeField(blank=True, null=True)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(
                    choices=[("SCHEDULED","Scheduled"),("IN_PROGRESS","In Progress"),("DONE","Done"),("INVOICED","Invoiced")],
                    default="DONE", max_length=20)),
                ("tax_category_code", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("property", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="maintenance_events",
                    to="bookings.bookableitem")),
                ("booking", models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="maintenance_events",
                    to="bookings.bookinginquiry")),
                ("created_by", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="created_maintenance_events",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-start_at",), "verbose_name": "Maintenance Event", "verbose_name_plural": "Maintenance Events"},
        ),
        migrations.CreateModel(
            name="MaintenancePhoto",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("image", models.ImageField(upload_to="maintenance_photos/")),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("event", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="photos",
                    to="maintenance.maintenanceevent")),
            ],
            options={"ordering": ("created_at",)},
        ),
    ]
