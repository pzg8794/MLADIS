from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BookableItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(unique=True)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("stay", "Stay"),
                            ("experience", "Experience"),
                            ("service", "Service"),
                            ("transport", "Transport"),
                        ],
                        default="stay",
                        max_length=24,
                    ),
                ),
                ("short_description", models.CharField(max_length=220)),
                ("description", models.TextField(blank=True)),
                ("location_label", models.CharField(blank=True, max_length=160)),
                ("image", models.CharField(blank=True, max_length=240)),
                ("starting_price", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("price_unit", models.CharField(default="night", max_length=40)),
                ("max_guests", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("bedrooms", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("beds", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("bathrooms", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
                ("bathroom_label", models.CharField(blank=True, max_length=80)),
                ("airbnb_listing_id", models.CharField(blank=True, max_length=40)),
                ("airbnb_url", models.URLField(blank=True)),
                ("airbnb_rating", models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True)),
                ("is_featured", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["category", "name"]},
        ),
        migrations.CreateModel(
            name="AgentConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(db_index=True, max_length=80)),
                ("visitor_name", models.CharField(blank=True, max_length=160)),
                ("visitor_email", models.EmailField(blank=True, max_length=254)),
                ("last_user_message", models.TextField()),
                ("last_agent_reply", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="agent_conversations",
                        to="bookings.bookableitem",
                    ),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="BookingInquiry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guest_name", models.CharField(max_length=160)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("check_in", models.DateField()),
                ("check_out", models.DateField()),
                ("guests", models.PositiveSmallIntegerField(default=1)),
                ("message", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("reviewing", "Reviewing"),
                            ("quoted", "Quoted"),
                            ("confirmed", "Confirmed"),
                            ("declined", "Declined"),
                        ],
                        default="new",
                        max_length=24,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inquiries",
                        to="bookings.bookableitem",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
