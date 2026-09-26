import json
import re
from uuid import UUID, uuid5

from django.utils import timezone

from .models import PageVisit


ATTRIBUTION_SESSION_KEY = "mladis_marketing_attribution"
ANONYMOUS_SESSION_KEY = "mladis_marketing_anonymous_id"
CONSENT_COOKIE = "mladis_analytics_consent"
UTM_FIELDS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_content",
    "utm_id",
)
SAFE_UTM_VALUE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


def _safe_utm_value(value):
    if not SAFE_UTM_VALUE.fullmatch(value):
        return False
    if len(re.sub(r"\D", "", value)) >= 7:
        return False
    return not re.fullmatch(r"\d{4}[-_.]?\d{2}[-_.]?\d{2}", value)


def analytics_allowed(request):
    return (
        request.COOKIES.get(CONSENT_COOKIE) == "granted"
        and request.META.get("HTTP_DNT") != "1"
    )


def sanitize_utm(payload):
    result = {}
    for field in UTM_FIELDS:
        value = str((payload or {}).get(field, "")).strip()
        if value and _safe_utm_value(value):
            result[field] = value
    campaign_id = result.get("utm_id") or result.get("utm_campaign")
    if campaign_id:
        result["campaign_id"] = campaign_id
    return result


def capture_attribution(request, payload):
    if not analytics_allowed(request):
        return {}
    values = sanitize_utm(payload)
    if not values:
        return request.session.get(ATTRIBUTION_SESSION_KEY, {})

    now = timezone.now().isoformat()
    touch = {**values, "captured_at": now}
    attribution = request.session.get(ATTRIBUTION_SESSION_KEY, {})
    if not attribution.get("first_touch"):
        attribution["first_touch"] = touch
    if values.get("utm_source") or values.get("utm_medium"):
        attribution["last_non_direct_touch"] = touch
    attribution["latest"] = values
    request.session[ATTRIBUTION_SESSION_KEY] = attribution
    return attribution


def get_anonymous_id(request):
    value = request.session.get(ANONYMOUS_SESSION_KEY)
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        from uuid import uuid4

        value = uuid4()
        request.session[ANONYMOUS_SESSION_KEY] = str(value)
        return value


def record_marketing_event(
    request,
    event_name,
    *,
    path,
    item_slug="",
    utm_payload=None,
    idempotency_key="",
):
    if not analytics_allowed(request):
        return None
    attribution = capture_attribution(request, utm_payload or {})
    anonymous_id = get_anonymous_id(request)
    latest = attribution.get("latest", {})
    event_key = ":".join((event_name, path, item_slug, json.dumps(latest, sort_keys=True), str(idempotency_key)))
    event_id = uuid5(anonymous_id, event_key)
    event_path = path[:500]
    return PageVisit.objects.get_or_create(
        event_id=event_id,
        defaults={
            "path": event_path,
            "event_name": event_name,
            "anonymous_id": anonymous_id,
            "campaign_attribution": attribution,
            "language": (getattr(request, "LANGUAGE_CODE", "en") or "en")[:8],
        },
    )[0]


def request_json(request):
    try:
        payload = json.loads(request.body or "{}")
    except (TypeError, ValueError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None
