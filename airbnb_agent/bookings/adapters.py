from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .models import CustomerProfile
from .social_auth import is_provider_configured, sync_social_apps_from_env


GENERATED_SOCIAL_EMAIL_DOMAIN = "users.mladis.invalid"


def _apply_admin_access(user):
    from .services import AdminAccessService

    AdminAccessService().apply_to_user(user)


class MLADISAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=commit)
        _apply_admin_access(user)
        self._sync_profile(user)
        return user

    def should_send_confirmation_mail(self, request, email_address, signup):
        if email_address.email.endswith(f"@{GENERATED_SOCIAL_EMAIL_DOMAIN}"):
            return False
        return super().should_send_confirmation_mail(request, email_address, signup)

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
    def get_app(self, request, provider, client_id=None):
        try:
            sync_social_apps_from_env()
            provider_id = getattr(provider, "id", provider)
            if not is_provider_configured(str(provider_id)):
                raise SocialApp.DoesNotExist()
            return super().get_app(request, provider, client_id=client_id)
        except SocialApp.DoesNotExist:
            provider_name = getattr(provider, "name", None) or str(provider).title()
            messages.warning(
                request,
                _("%(provider)s sign-in is not configured yet. Add OAuth credentials in the environment or admin, then try again.")
                % {"provider": provider_name},
            )
            raise ImmediateHttpResponse(redirect("bookings:login"))

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        extra_data = getattr(sociallogin.account, "extra_data", {}) or {}
        provider_email = (data.get("email") or extra_data.get("email") or "").strip().lower()
        if provider_email and (not user.email or self._is_generated_social_email(user.email)):
            user.email = provider_email
        if not user.first_name:
            user.first_name = data.get("first_name") or extra_data.get("given_name") or ""
        if not user.last_name:
            user.last_name = data.get("last_name") or extra_data.get("family_name") or ""
        self._sync_sociallogin_email(sociallogin, provider_email=provider_email)
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        self._sync_sociallogin_email(sociallogin)
        return super().is_auto_signup_allowed(request, sociallogin)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        _apply_admin_access(user)
        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={
                "email": user.email,
                "name": user.get_full_name() or user.username,
            },
        )
        return user

    def _sync_sociallogin_email(self, sociallogin, provider_email=""):
        user = getattr(sociallogin, "user", None)
        account = getattr(sociallogin, "account", None)
        if user is None or account is None:
            return

        extra_data = getattr(account, "extra_data", {}) or {}
        provider_email = (provider_email or extra_data.get("email") or "").strip().lower()
        if provider_email:
            user.email = provider_email
            self._set_sociallogin_email(sociallogin, provider_email, verified=False)
            return

        if account.provider != "facebook":
            return

        generated_email = self._build_generated_social_email(account.provider, account.uid)
        if not generated_email:
            return

        if not user.email or self._is_generated_social_email(user.email):
            user.email = generated_email
        self._set_sociallogin_email(sociallogin, user.email, verified=False)

    def _set_sociallogin_email(self, sociallogin, email, verified):
        user = getattr(sociallogin, "user", None)
        if user is None or not email:
            return
        sociallogin.email_addresses = [
            EmailAddress(user=user, email=email, verified=verified, primary=True)
        ]

    def _build_generated_social_email(self, provider_id, uid):
        safe_uid = "".join(character for character in str(uid).lower() if character.isalnum())
        if not safe_uid:
            return ""
        return f"{provider_id}-{safe_uid}@{GENERATED_SOCIAL_EMAIL_DOMAIN}"

    def _is_generated_social_email(self, email):
        return email.endswith(f"@{GENERATED_SOCIAL_EMAIL_DOMAIN}")
