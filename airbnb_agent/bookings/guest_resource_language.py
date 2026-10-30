"""Language preferences limited to public guest resources, without global locale changes."""
from urllib.parse import urlencode

from django.urls import reverse
from django.utils.cache import patch_vary_headers
from django.utils.translation.trans_real import parse_accept_lang_header

from .guest_resource_content import LANGUAGE_NAMES, get_content


LANGUAGE_COOKIE = "mladis_guest_language"


def supported_language(value):
    """Accept a supported language or its regional variant; never arbitrary input."""
    language = (value or "").lower().split("-", 1)[0]
    return language if language in LANGUAGE_NAMES else None


def resolve_language(request):
    explicit = supported_language(request.GET.get("lang"))
    saved = supported_language(request.COOKIES.get(LANGUAGE_COOKIE))
    if explicit or saved:
        return explicit or saved
    for tag, quality in parse_accept_lang_header(request.META.get("HTTP_ACCEPT_LANGUAGE", "")):
        language = supported_language(tag)
        if quality > 0 and language:
            return language
    return "en"


def localized_url(path, language):
    return path + "?" + urlencode({"lang": supported_language(language) or "en"})


def translated(text, language):
    return get_content(language)["messages"].get(text, text)


class GuestResourceLanguageMixin:
    """One request preference shared by content, forms, links and HTTP metadata."""

    def dispatch(self, request, *args, **kwargs):
        self.resource_language = resolve_language(request)
        response = super().dispatch(request, *args, **kwargs)
        response["Content-Language"] = self.resource_language
        patch_vary_headers(response, ("Accept-Language", "Cookie"))
        if supported_language(request.GET.get("lang")):
            response.set_cookie(
                LANGUAGE_COOKIE, self.resource_language, max_age=365 * 24 * 60 * 60,
                secure=request.is_secure(), httponly=True, samesite="Lax",
            )
        return response

    def language_context(self):
        language = self.resource_language
        return {
            "language": language,
            "copy": get_content(language),
            "language_options": [
                {"code": code, "label": label, "url": localized_url(self.request.path, code), "active": code == language}
                for code, label in LANGUAGE_NAMES.items()
            ],
            "privacy_url": localized_url(reverse("bookings:offers-privacy"), language),
            "offers_url": localized_url(reverse("bookings:offers-signup"), language),
        }

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), **self.language_context()}

    def tr(self, text):
        return translated(text, self.resource_language)
