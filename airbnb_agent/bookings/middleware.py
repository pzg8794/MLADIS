from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect

from .marketing import analytics_allowed, record_marketing_event, sanitize_utm
from .models import BookableItem, BookingCategory
from .social_auth import provider_auth_origin, provider_from_oauth_path, request_origin


class SocialAuthCanonicalOriginMiddleware:
    """Keeps provider OAuth callbacks on the host/protocol registered with that provider."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        provider_id = provider_from_oauth_path(request.path)
        if provider_id and request.method in {"GET", "HEAD"}:
            canonical_origin = provider_auth_origin(provider_id, request)
            if request.get_host() == "testserver":
                return self.get_response(request)
            current_origin = request_origin(request)
            if current_origin != canonical_origin:
                return redirect(f"{canonical_origin}{request.get_full_path()}")
        return self.get_response(request)


class PageVisitMiddleware:
    """Lightweight analytics for owner dashboards; skips assets and admin internals."""

    SKIP_PREFIXES = ("/static/", "/media/", "/admin/jsi18n/", "/healthz", "/api/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if self._should_record(request, response) and analytics_allowed(request):
            try:
                path_parts = request.path.strip("/").split("/")
                item_slug = path_parts[1] if len(path_parts) == 2 and path_parts[0] == "stays" else ""
                is_public_stay = bool(item_slug) and BookableItem.objects.filter(
                    slug=item_slug,
                    category=BookingCategory.STAY,
                    is_active=True,
                ).exists()
                if request.path == "/" or is_public_stay:
                    record_marketing_event(
                        request,
                        "landing_visit",
                        path=request.path,
                        item_slug=item_slug,
                        utm_payload=sanitize_utm(request.GET),
                    )
            except (OperationalError, ProgrammingError):
                pass
        return response

    def _should_record(self, request, response):
        if request.method != "GET" or response.status_code >= 400:
            return False
        return not request.path.startswith(self.SKIP_PREFIXES)
