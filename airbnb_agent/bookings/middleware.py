from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect
from django.utils.translation import get_language

from .models import PageVisit
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
        if self._should_record(request, response):
            try:
                PageVisit.objects.create(
                    path=request.path[:500],
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key or "",
                    language=(get_language() or "en")[:8],
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
                )
            except (OperationalError, ProgrammingError):
                pass
        return response

    def _should_record(self, request, response):
        if request.method != "GET" or response.status_code >= 400:
            return False
        return not request.path.startswith(self.SKIP_PREFIXES)
