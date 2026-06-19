from django.db.utils import OperationalError, ProgrammingError

from .models import SiteSettings
from .ops_navigation import OPS_NAV_PUBLIC_ITEMS, ops_nav_items_for_path
from .social_auth import get_social_login_providers


def site_settings(request):
    ops_nav_context = {
        "ops_nav_items": ops_nav_items_for_path(request.path),
        "ops_nav_public_items": OPS_NAV_PUBLIC_ITEMS,
    }
    try:
        social_login_providers = get_social_login_providers(request)
        return {
            **ops_nav_context,
            "site_settings": SiteSettings.current(),
            "social_login_providers": social_login_providers,
            "social_login_provider_count": sum(1 for provider in social_login_providers if provider["is_configured"]),
            "social_login_launchable_count": sum(1 for provider in social_login_providers if provider["is_launchable"]),
        }
    except (OperationalError, ProgrammingError):
        return {
            **ops_nav_context,
            "site_settings": None,
            "social_login_providers": [],
            "social_login_provider_count": 0,
            "social_login_launchable_count": 0,
        }
