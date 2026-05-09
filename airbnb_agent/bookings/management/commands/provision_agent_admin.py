import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from bookings.models import AdminAccess, ClientSegment, CustomerProfile


class Command(BaseCommand):
    help = "Provision a dedicated automation/agent admin user from .env values."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="", help="Agent admin email. Falls back to MLADIS_AGENT_ADMIN_EMAIL.")
        parser.add_argument("--name", default="", help="Display name. Falls back to MLADIS_AGENT_ADMIN_NAME.")
        parser.add_argument("--phone", default="", help="Business phone. Falls back to MLADIS_AGENT_ADMIN_PHONE.")
        parser.add_argument("--username", default="", help="Username. Falls back to MLADIS_AGENT_ADMIN_USERNAME.")
        parser.add_argument(
            "--password",
            default="",
            help="Optional password. Falls back to MLADIS_AGENT_ADMIN_PASSWORD; omitted means social-login only.",
        )

    def handle(self, *args, **options):
        email = self._clean(options["email"] or os.getenv("MLADIS_AGENT_ADMIN_EMAIL", "")).lower()
        if not email:
            self.stdout.write(self.style.WARNING("No MLADIS_AGENT_ADMIN_EMAIL configured; skipped agent admin provisioning."))
            return

        name = self._clean(options["name"] or os.getenv("MLADIS_AGENT_ADMIN_NAME", "MLADIS Automation Agent"))
        phone = self._clean(options["phone"] or os.getenv("MLADIS_AGENT_ADMIN_PHONE", ""))
        username = self._clean(options["username"] or os.getenv("MLADIS_AGENT_ADMIN_USERNAME", ""))
        password = options["password"] or os.getenv("MLADIS_AGENT_ADMIN_PASSWORD", "")

        with transaction.atomic():
            access, _created_access = AdminAccess.objects.update_or_create(
                email=email,
                defaults={
                    "name": name,
                    "phone": phone,
                    "is_active": True,
                    "grant_staff_access": True,
                    "grant_superuser_access": True,
                    "notes": "Dedicated MLADIS automation/agent admin access. Do not use owner credentials for routine automation.",
                },
            )
            user = self._upsert_user(email=email, name=name, username=username, password=password)
            self._sync_customer_profile(user=user, access=access)

        password_mode = "password login enabled" if password else "social-login only"
        self.stdout.write(
            self.style.SUCCESS(
                f"Provisioned agent admin {access.name} <{access.email}> as user {user.username} ({password_mode})."
            )
        )

    def _upsert_user(self, *, email, name, username, password):
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            username = username or self._default_username(email)
            user = User(username=self._unique_username(username), email=email)

        first_name, last_name = self._split_name(name)
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = True
        user.is_superuser = True
        if password:
            user.set_password(password)
        elif not user.pk:
            user.set_unusable_password()
        user.save()
        return user

    def _sync_customer_profile(self, *, user, access):
        profile, _created = CustomerProfile.objects.update_or_create(
            email=access.email,
            defaults={
                "user": user,
                "name": access.name,
                "phone": access.phone,
                "segment": ClientSegment.VIP,
                "preferred_language": "en",
            },
        )
        if profile.user_id != user.id:
            profile.user = user
            profile.save(update_fields=["user", "updated_at"])

    def _default_username(self, email):
        return email.split("@", 1)[0].replace(".", "-").replace("_", "-") or "mladis-agent"

    def _unique_username(self, username):
        User = get_user_model()
        candidate = username[:150]
        if not User.objects.filter(username=candidate).exists():
            return candidate
        suffix = 2
        while True:
            trimmed = username[: 150 - len(str(suffix)) - 1]
            candidate = f"{trimmed}-{suffix}"
            if not User.objects.filter(username=candidate).exists():
                return candidate
            suffix += 1

    def _split_name(self, name):
        parts = name.split()
        if not parts:
            return "", ""
        return parts[0][:150], " ".join(parts[1:])[:150]

    def _clean(self, value):
        return (value or "").strip()
