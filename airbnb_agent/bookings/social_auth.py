import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.utils import OperationalError, ProgrammingError
from django.urls import NoReverseMatch, reverse

from allauth.socialaccount.models import SocialApp


SOCIAL_LOGIN_PROVIDER_SPECS = (
    {
        "id": "google",
        "label": "Google",
        "url_name": "google_login",
        "client_id_env": "GOOGLE_OAUTH_CLIENT_ID",
        "secret_env": "GOOGLE_OAUTH_CLIENT_SECRET",
    },
    {
        "id": "facebook",
        "label": "Facebook",
        "url_name": "facebook_login",
        "client_id_env": "FACEBOOK_OAUTH_CLIENT_ID",
        "secret_env": "FACEBOOK_OAUTH_CLIENT_SECRET",
        "settings": lambda: {"scope": _env_list("FACEBOOK_OAUTH_SCOPE", ["public_profile"])},
    },
    {
        "id": "microsoft",
        "label": "Microsoft",
        "url_name": "microsoft_login",
        "client_id_env": "MICROSOFT_OAUTH_CLIENT_ID",
        "secret_env": "MICROSOFT_OAUTH_CLIENT_SECRET",
        "settings": lambda: {
            "tenant": os.getenv("MICROSOFT_OAUTH_TENANT", "common").strip() or "common",
            "login_url": os.getenv("MICROSOFT_OAUTH_LOGIN_URL", "https://login.microsoftonline.com").strip()
            or "https://login.microsoftonline.com",
            "graph_url": os.getenv("MICROSOFT_GRAPH_URL", "https://graph.microsoft.com").strip()
            or "https://graph.microsoft.com",
        },
    },
    {
        "id": "github",
        "label": "GitHub",
        "url_name": "github_login",
        "client_id_env": "GITHUB_OAUTH_CLIENT_ID",
        "secret_env": "GITHUB_OAUTH_CLIENT_SECRET",
    },
)


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default):
    value = os.getenv(name, "").strip()
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_credentials(provider):
    client_id = os.getenv(provider["client_id_env"], "").strip()
    secret = os.getenv(provider["secret_env"], "").strip()
    return client_id, secret


def is_provider_configured(provider_id):
    provider = next((item for item in SOCIAL_LOGIN_PROVIDER_SPECS if item["id"] == provider_id), None)
    if provider is None:
        return False

    client_id, secret = _env_credentials(provider)
    if client_id and secret:
        return True

    if not _env_bool("SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK", getattr(settings, "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK", False)):
        return False

    try:
        return SocialApp.objects.filter(provider=provider_id, sites__id=settings.SITE_ID).exists()
    except (OperationalError, ProgrammingError):
        return False


def sync_social_apps_from_env():
    try:
        site = Site.objects.get(pk=settings.SITE_ID)
    except (Site.DoesNotExist, OperationalError, ProgrammingError):
        return set()

    site_domain = os.getenv("SITE_DOMAIN", "").strip()
    site_name = os.getenv("SITE_NAME", "").strip()
    site_updates = []
    if site_domain and site.domain != site_domain:
        site.domain = site_domain
        site_updates.append("domain")
    if site_name and site.name != site_name:
        site.name = site_name
        site_updates.append("name")
    if site_updates:
        site.save(update_fields=site_updates)

    configured = set()
    for provider in SOCIAL_LOGIN_PROVIDER_SPECS:
        client_id, secret = _env_credentials(provider)
        if not client_id or not secret:
            continue
        app = SocialApp.objects.filter(provider=provider["id"], sites__id=site.id).first()
        if app is None:
            app = SocialApp.objects.filter(provider=provider["id"], provider_id="").first()
        if app is None:
            app = SocialApp(provider=provider["id"], provider_id="")
        app.name = f"{provider['label']} OAuth"
        app.client_id = client_id
        app.secret = secret
        if provider.get("settings"):
            app.settings = provider["settings"]()
        app.save()
        app.sites.add(site)
        configured.add(provider["id"])
    return configured


def get_social_login_providers():
    env_configured = set()
    admin_configured = set()
    hidden_unconfigured = set(getattr(settings, "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS", []))
    try:
        env_configured |= sync_social_apps_from_env()
        if _env_bool("SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK", getattr(settings, "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK", False)):
            admin_configured |= set(
                SocialApp.objects.filter(sites__id=settings.SITE_ID).values_list("provider", flat=True)
            )
    except (OperationalError, ProgrammingError):
        env_configured = set()
        admin_configured = set()

    providers = []
    for provider in SOCIAL_LOGIN_PROVIDER_SPECS:
        try:
            login_url = reverse(provider["url_name"])
        except NoReverseMatch:
            login_url = ""
        is_configured = provider["id"] in env_configured or provider["id"] in admin_configured
        if provider["id"] in hidden_unconfigured and not is_configured:
            continue
        providers.append(
            {
                "id": provider["id"],
                "label": provider["label"],
                "button_label": f"Continue with {provider['label']}",
                "login_url": login_url,
                "is_configured": is_configured and bool(login_url),
                "configured_from_env": provider["id"] in env_configured,
                "configured_from_admin": provider["id"] in admin_configured,
                "client_id_env": provider["client_id_env"],
                "secret_env": provider["secret_env"],
            }
        )
    return providers
