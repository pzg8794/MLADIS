from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookings"

    def ready(self):
        from . import signals  # noqa: F401
        from .agent_faq import install_agent_faq_patch

        install_agent_faq_patch()
