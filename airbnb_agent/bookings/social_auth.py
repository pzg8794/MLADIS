import os
from urllib.parse import urlencode

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


def get_provider_spec(provider_id):
    return next((item for item in SOCIAL_LOGIN_PROVIDER_SPECS if item["id"] == provider_id), None)


def is_provider_configured(provider_id):
    provider = get_provider_spec(provider_id)
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


def effective_social_auth_origin(request=None):
    """Return the origin OAuth providers will see for callback generation."""
    canonical_origin = getattr(settings, "SOCIAL_AUTH_CANONICAL_ORIGIN", "").strip().rstrip("/")
    if canonical_origin:
        return canonical_origin
    if request is None:
        return ""
    return request_origin(request)


def request_origin(request):
    return f"{request.scheme}://{request.get_host()}".rstrip("/")


def provider_auth_origin(provider_id, request=None):
    """Return the provider-specific origin used to generate OAuth callbacks."""
    provider_origins = getattr(settings, "SOCIAL_AUTH_PROVIDER_ORIGINS", {}) or {}
    provider_origin = str(provider_origins.get(provider_id, "")).strip().rstrip("/")
    if provider_origin:
        return provider_origin
    return effective_social_auth_origin(request)


def provider_from_oauth_path(path):
    parts = path.strip("/").split("/")
    if len(parts) >= 3 and parts[0] == "oauth" and parts[2] == "login":
        provider_id = parts[1]
        if get_provider_spec(provider_id):
            return provider_id
    return ""


def social_launch_url(provider_id, request=None):
    launch_url = reverse("bookings:social-provider-launch", kwargs={"provider_id": provider_id})
    if request is None:
        return launch_url
    next_url = request.GET.get("next", "")
    if next_url.startswith("/"):
        return f"{launch_url}?{urlencode({'next': next_url})}"
    return launch_url


def provider_needs_origin_bridge(provider_id, request=None):
    if request is None or request.get_host() == "testserver":
        return False
    target_origin = provider_auth_origin(provider_id, request)
    return bool(target_origin and request_origin(request) != target_origin)


def is_secure_social_auth_origin(request=None):
    return effective_social_auth_origin(request).startswith("https://")


def provider_launch_block(provider_id, request=None):
    """Return provider-specific launch blockers.

    Facebook requires a secure callback, but local development now solves that
    by redirecting OAuth traffic to SOCIAL_AUTH_CANONICAL_ORIGIN instead of
    disabling the configured provider in the UI.
    """
    return None


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


def get_social_login_providers(request=None):
    env_configured = set()
    admin_configured = set()
    hidden_providers = set(getattr(settings, "SOCIAL_AUTH_HIDDEN_PROVIDERS", []))
    hidden_unconfigured = set(getattr(settings, "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS", []))
    disabled_providers = set(getattr(settings, "SOCIAL_AUTH_DISABLED_PROVIDERS", []))
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
        if provider["id"] in hidden_providers:
            continue
        try:
            login_url = reverse(provider["url_name"])
            next_url = request.GET.get("next", "") if request else ""
            if next_url.startswith("/"):
                login_url = f"{login_url}?{urlencode({'next': next_url})}"
            launch_url = social_launch_url(provider["id"], request)
        except NoReverseMatch:
            login_url = ""
            launch_url = ""
        is_configured = provider["id"] in env_configured or provider["id"] in admin_configured
        if provider["id"] in hidden_unconfigured and not is_configured:
            continue
        if provider["id"] in disabled_providers:
            block = {
                "reason": "disabled",
                "help_text": "This provider is visible in the login experience but disabled for this runtime.",
            }
        else:
            block = provider_launch_block(provider["id"], request) if is_configured and login_url else None
        is_launchable = is_configured and bool(login_url) and block is None
        providers.append(
            {
                "id": provider["id"],
                "label": provider["label"],
                "button_label": f"Continue with {provider['label']}",
                "login_url": login_url,
                "launch_url": launch_url,
                "auth_origin": provider_auth_origin(provider["id"], request) if login_url else "",
                "needs_origin_bridge": provider_needs_origin_bridge(provider["id"], request) if login_url else False,
                "is_configured": is_configured and bool(login_url),
                "is_launchable": is_launchable,
                "disabled_reason": block["reason"] if block else ("setup needed" if not is_configured else ""),
                "help_text": block["help_text"] if block else "",
                "configured_from_env": provider["id"] in env_configured,
                "configured_from_admin": provider["id"] in admin_configured,
                "client_id_env": provider["client_id_env"],
                "secret_env": provider["secret_env"],
            }
        )
    return providers
