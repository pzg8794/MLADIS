from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0002_seed_bookable_items"),
    ]

    operations = [
        migrations.CreateModel(
            name="DamageDeposit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guest_name", models.CharField(max_length=160)),
                ("email", models.EmailField(max_length=254)),
                ("amount_cents", models.PositiveIntegerField(default=20000)),
                ("currency", models.CharField(default="usd", max_length=3)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("requires_configuration", "Requires Stripe configuration"),
                            ("checkout_created", "Checkout created"),
                            ("requires_capture", "Authorized"),
                            ("captured", "Captured"),
                            ("canceled", "Canceled"),
                            ("failed", "Failed"),
                        ],
                        default="new",
                        max_length=32,
                    ),
                ),
                ("stripe_checkout_session_id", models.CharField(blank=True, max_length=255)),
                ("stripe_payment_intent_id", models.CharField(blank=True, max_length=255)),
                ("checkout_url", models.URLField(blank=True, max_length=1000)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "inquiry",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="damage_deposits",
                        to="bookings.bookinginquiry",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="damage_deposits",
                        to="bookings.bookableitem",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
