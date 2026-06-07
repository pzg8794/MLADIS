from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0021_agent_access_limits"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="request_notifications_email",
            field=models.BooleanField(
                default=True,
                help_text="Send new reservation requests to admin email recipients.",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="request_notifications_sms",
            field=models.BooleanField(
                default=False,
                help_text="Future channel flag. Requires an SMS provider before messages can be sent.",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="request_notifications_whatsapp",
            field=models.BooleanField(
                default=False,
                help_text="Future channel flag. Requires a WhatsApp provider before messages can be sent.",
            ),
        ),
    ]
