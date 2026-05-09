from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0012_availabilityblock_dailypriceoverride"),
    ]

    operations = [
        migrations.AlterField(
            model_name="damagedeposit",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "New"),
                    ("requires_configuration", "Requires payment configuration"),
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
    ]