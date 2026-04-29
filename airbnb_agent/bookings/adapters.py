from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import CustomerProfile
from .services import AdminAccessService


class MLADISAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=commit)
        AdminAccessService().apply_to_user(user)
        self._sync_profile(user)
        return user

    def _sync_profile(self, user):
        if not user.email:
            return
        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "email": user.email,
                "name": user.get_full_name() or user.username,
            },
        )


class MLADISSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        extra_data = getattr(sociallogin.account, "extra_data", {}) or {}
        if not user.email:
            user.email = data.get("email") or extra_data.get("email") or ""
        if not user.first_name:
            user.first_name = data.get("first_name") or extra_data.get("given_name") or ""
        if not user.last_name:
            user.last_name = data.get("last_name") or extra_data.get("family_name") or ""
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        AdminAccessService().apply_to_user(user)
        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "email": user.email,
                "name": user.get_full_name() or user.username,
            },
        )
        return user
