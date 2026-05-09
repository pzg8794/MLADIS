from django.db import migrations


ADMIN_EMAIL = "garciabdianas@gmail.com"


def seed_admin_access(apps, schema_editor):
    AdminAccess = apps.get_model("bookings", "AdminAccess")
    CustomerProfile = apps.get_model("bookings", "CustomerProfile")
    AdminAccess.objects.update_or_create(
        email=ADMIN_EMAIL,
        defaults={
            "name": "Diana Garcia",
            "phone": "",
            "is_active": True,
            "grant_staff_access": True,
            "grant_superuser_access": True,
            "notes": "Seeded MLADIS admin access for Diana Garcia. Matching social or password logins are promoted automatically.",
        },
    )
    CustomerProfile.objects.update_or_create(
        email=ADMIN_EMAIL,
        defaults={
            "name": "Diana Garcia",
            "phone": "",
            "segment": "vip",
            "preferred_language": "en",
        },
    )


def remove_admin_access(apps, schema_editor):
    AdminAccess = apps.get_model("bookings", "AdminAccess")
    AdminAccess.objects.filter(email=ADMIN_EMAIL).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0009_seed_admin_access"),
    ]

    operations = [
        migrations.RunPython(seed_admin_access, remove_admin_access),
    ]