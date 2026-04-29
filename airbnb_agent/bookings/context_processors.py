from django.db.utils import OperationalError, ProgrammingError
from django.conf import settings
from django.urls import NoReverseMatch, reverse

from .models import SiteSettings


def site_settings(_request):
    try:
        return {
            "site_settings": SiteSettings.current(),
            "social_login_providers": _social_login_providers(),
        }
    except (OperationalError, ProgrammingError):
        return {"site_settings": None, "social_login_providers": []}


def _social_login_providers():
    provider_specs = [
        ("google", "Google", "google_login"),
        ("facebook", "Facebook", "facebook_login"),
        ("microsoft", "Microsoft", "microsoft_login"),
        ("github", "GitHub", "github_login"),
    ]
    configured = set()
    try:
        from allauth.socialaccount.models import SocialApp

        configured = set(
            SocialApp.objects.filter(sites__id=settings.SITE_ID).values_list("provider", flat=True)
        )
    except (OperationalError, ProgrammingError):
        configured = set()

    providers = []
    for provider_id, label, url_name in provider_specs:
        try:
            login_url = reverse(url_name)
        except NoReverseMatch:
            login_url = ""
        providers.append(
            {
                "id": provider_id,
                "label": label,
                "login_url": login_url,
                "is_configured": provider_id in configured and bool(login_url),
            }
        )
    return providers
