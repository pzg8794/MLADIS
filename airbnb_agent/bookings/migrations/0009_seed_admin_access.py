from django.db import migrations


def seed_admin_access(apps, schema_editor):
    AdminAccess = apps.get_model("bookings", "AdminAccess")
    CustomerProfile = apps.get_model("bookings", "CustomerProfile")
    AdminAccess.objects.update_or_create(
        email="garciapiterz@gmail.com",
        defaults={
            "name": "Piter Garcia",
            "phone": "631-575-4841",
            "is_active": True,
            "grant_staff_access": True,
            "grant_superuser_access": True,
            "notes": "Seeded MLADIS owner/admin access. Matching social or password logins are promoted automatically.",
        },
    )
    CustomerProfile.objects.update_or_create(
        email="garciapiterz@gmail.com",
        defaults={
            "name": "Piter Garcia",
            "phone": "631-575-4841",
            "segment": "vip",
            "preferred_language": "en",
        },
    )


def remove_admin_access(apps, schema_editor):
    AdminAccess = apps.get_model("bookings", "AdminAccess")
    AdminAccess.objects.filter(email="garciapiterz@gmail.com").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0008_adminaccess"),
    ]

    operations = [
        migrations.RunPython(seed_admin_access, remove_admin_access),
    ]
