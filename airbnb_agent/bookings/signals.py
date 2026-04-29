from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .services import AdminAccessService


@receiver(user_logged_in)
def promote_known_admin_email(sender, request, user, **kwargs):
    AdminAccessService().apply_to_user(user)
