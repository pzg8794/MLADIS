from django.db.utils import OperationalError, ProgrammingError

from .models import SiteSettings
from .social_auth import get_social_login_providers


def site_settings(_request):
    try:
        social_login_providers = get_social_login_providers()
        return {
            "site_settings": SiteSettings.current(),
            "social_login_providers": social_login_providers,
            "social_login_provider_count": sum(1 for provider in social_login_providers if provider["is_configured"]),
        }
    except (OperationalError, ProgrammingError):
        return {"site_settings": None, "social_login_providers": [], "social_login_provider_count": 0}
