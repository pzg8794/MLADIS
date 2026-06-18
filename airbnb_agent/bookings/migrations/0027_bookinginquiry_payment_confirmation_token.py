from uuid import uuid4

from django.db import migrations, models


def populate_confirmation_tokens(apps, schema_editor):
    BookingInquiry = apps.get_model("bookings", "BookingInquiry")
    for inquiry in BookingInquiry.objects.filter(payment_confirmation_token__isnull=True):
        inquiry.payment_confirmation_token = uuid4()
        inquiry.save(update_fields=["payment_confirmation_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0026_bookinginquiry_accepted_damage_terms_version_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookinginquiry",
            name="payment_confirmation_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(populate_confirmation_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="bookinginquiry",
            name="payment_confirmation_token",
            field=models.UUIDField(default=uuid4, editable=False, unique=True),
        ),
    ]
