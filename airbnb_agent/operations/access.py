from django.conf import settings


DEFAULT_OWNER_EMAILS = {
    "garciapiterz@mail.com",
    "garciapiterz@gmail.com",
}
DEFAULT_OWNER_FULL_NAMES = {"piter garcia"}
DEFAULT_OWNER_USERNAMES = {"piter"}


def _normalized_values(values):
    return {str(value).strip().lower() for value in values if str(value).strip()}


def operations_owner_emails():
    configured = getattr(settings, "OPERATIONS_WORKBOARD_OWNER_EMAILS", None)
    if configured is None:
        return DEFAULT_OWNER_EMAILS
    if isinstance(configured, str):
        configured = configured.split(",")
    return _normalized_values(configured)


def operations_owner_full_names():
    configured = getattr(settings, "OPERATIONS_WORKBOARD_OWNER_FULL_NAMES", None)
    if configured is None:
        return DEFAULT_OWNER_FULL_NAMES
    if isinstance(configured, str):
        configured = configured.split(",")
    return _normalized_values(configured)


def operations_owner_usernames():
    configured = getattr(settings, "OPERATIONS_WORKBOARD_OWNER_USERNAMES", None)
    if configured is None:
        return DEFAULT_OWNER_USERNAMES
    if isinstance(configured, str):
        configured = configured.split(",")
    return _normalized_values(configured)


def is_operations_owner(user):
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False

    email = str(getattr(user, "email", "")).strip().lower()
    username = str(getattr(user, "username", "")).strip().lower()
    full_name = str(user.get_full_name()).strip().lower() if hasattr(user, "get_full_name") else ""

    return (
        email in operations_owner_emails()
        or full_name in operations_owner_full_names()
        or username in operations_owner_usernames()
    )
