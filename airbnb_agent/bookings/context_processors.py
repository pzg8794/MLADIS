from django.db.utils import OperationalError, ProgrammingError

from .models import SiteSettings


def site_settings(_request):
    try:
        return {"site_settings": SiteSettings.current()}
    except (OperationalError, ProgrammingError):
        return {"site_settings": None}
