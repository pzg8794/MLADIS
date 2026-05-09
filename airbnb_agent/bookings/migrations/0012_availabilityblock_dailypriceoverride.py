from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0011_damagedeposit_paypal_support"),
    ]

    operations = [
        migrations.CreateModel(
            name="AvailabilityBlock",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("reason", models.CharField(blank=True, max_length=160)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "item",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="availability_blocks", to="bookings.bookableitem"),
                ),
            ],
            options={
                "ordering": ["item__name", "start_date", "end_date", "id"],
            },
        ),
        migrations.CreateModel(
            name="DailyPriceOverride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("nightly_price", models.DecimalField(decimal_places=2, max_digits=8)),
                ("label", models.CharField(blank=True, max_length=120)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "item",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="daily_price_overrides", to="bookings.bookableitem"),
                ),
            ],
            options={
                "ordering": ["item__name", "start_date", "end_date", "id"],
            },
        ),
    ]