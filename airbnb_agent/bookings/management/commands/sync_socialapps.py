from django.core.management.base import BaseCommand

from bookings.social_auth import get_social_login_providers, sync_social_apps_from_env


class Command(BaseCommand):
    help = "Create or update django-allauth SocialApp rows from OAuth .env credentials."

    def handle(self, *args, **options):
        synced = sync_social_apps_from_env()
        providers = get_social_login_providers()

        if synced:
            self.stdout.write(self.style.SUCCESS(f"Synced from .env: {', '.join(sorted(synced))}"))
        else:
            self.stdout.write(self.style.WARNING("No complete OAuth .env credentials were found."))

        for provider in providers:
            status = "ready" if provider["is_configured"] else "needs setup"
            source = "env" if provider["configured_from_env"] else "admin" if provider["configured_from_admin"] else "none"
            self.stdout.write(f"- {provider['label']}: {status} ({source})")
