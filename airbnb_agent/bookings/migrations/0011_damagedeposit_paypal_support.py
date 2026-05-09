from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0010_seed_diana_admin_access"),
    ]

    operations = [
        migrations.AddField(
            model_name="damagedeposit",
            name="payment_provider",
            field=models.CharField(
                choices=[("stripe", "Stripe"), ("paypal", "PayPal")],
                default="stripe",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="damagedeposit",
            name="paypal_authorization_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="damagedeposit",
            name="paypal_order_id",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]