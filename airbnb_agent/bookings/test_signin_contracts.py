import os
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.shortcuts import redirect
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from .social_auth import sync_social_apps_from_env


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


SIGNIN_ENV = {
    "SITE_DOMAIN": "127.0.0.1:8000",
    "SITE_NAME": "MLADIS Local",
    "GOOGLE_OAUTH_CLIENT_ID": "google-client",
    "GOOGLE_OAUTH_CLIENT_SECRET": "google-secret",
    "FACEBOOK_OAUTH_CLIENT_ID": "facebook-client",
    "FACEBOOK_OAUTH_CLIENT_SECRET": "facebook-secret",
    "FACEBOOK_OAUTH_SCOPE": "public_profile",
    "GITHUB_OAUTH_CLIENT_ID": "github-client",
    "GITHUB_OAUTH_CLIENT_SECRET": "github-secret",
}


SIGNIN_SETTINGS = {
    "ALLOWED_HOSTS": ["127.0.0.1", "localhost", "testserver", "local.mladis.com"],
    "ACCOUNT_DEFAULT_HTTP_PROTOCOL": "http",
    "SOCIAL_AUTH_CANONICAL_ORIGIN": "",
    "SOCIAL_AUTH_PROVIDER_ORIGINS": {
        "google": "http://127.0.0.1:8000",
        "github": "http://127.0.0.1:8000",
        "facebook": "https://local.mladis.com",
        "microsoft": "",
    },
    "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": ["microsoft"],
    "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": False,
    "STORAGES": TEST_STORAGES,
}


QUEUED_BOOKING_MESSAGE = "Thanks, Piter Garcia. Your booking is started."
QUEUED_PAYMENT_MESSAGE = "Payment confirmed. Your MLADIS reservation authorization is recorded."


def queue_booking_messages_then_login(request):
    messages.success(request, QUEUED_BOOKING_MESSAGE)
    messages.success(request, QUEUED_PAYMENT_MESSAGE)
    return redirect(reverse("bookings:login"))


urlpatterns = [
    path("queue-booking-messages/", queue_booking_messages_then_login),
    path("", include(("bookings.urls", "bookings"), namespace="bookings")),
]


@override_settings(**SIGNIN_SETTINGS)
class SignInContractTests(TestCase):
    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={"domain": "127.0.0.1:8000", "name": "MLADIS Local"},
        )

    def _sync_env_apps(self):
        with patch.dict(os.environ, SIGNIN_ENV, clear=False):
            sync_social_apps_from_env()

    def _oauth_redirect_query(self, provider_url_name, host="127.0.0.1:8000", secure=False):
        self._sync_env_apps()
        with patch.dict(os.environ, SIGNIN_ENV, clear=False):
            response = self.client.post(
                reverse(provider_url_name),
                HTTP_HOST=host,
                secure=secure,
            )
        self.assertEqual(response.status_code, 302)
        location = response["Location"]
        self.assertTrue(
            location.startswith("http"),
            msg=f"Expected an external OAuth redirect, got {location}",
        )
        return parse_qs(urlparse(location).query)

    def test_login_page_uses_direct_local_posts_and_facebook_https_bridge(self):
        with patch.dict(os.environ, SIGNIN_ENV, clear=False):
            response = self.client.get(
                f"{reverse('bookings:login')}?next=/accounts/",
                HTTP_HOST="127.0.0.1:8000",
            )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('action="/oauth/google/login/?next=%2Faccounts%2F"', html)
        self.assertIn('action="/oauth/github/login/?next=%2Faccounts%2F"', html)
        self.assertIn('href="/accounts/social/facebook/?next=%2Faccounts%2F"', html)
        self.assertNotIn('href="/accounts/social/github/', html)
        self.assertNotIn("Continue with Microsoft", html)
        self.assertNotIn("modern-social-button--microsoft", html)

    @override_settings(ROOT_URLCONF=__name__)
    def test_login_page_omits_queued_booking_messages(self):
        response = self.client.get("/queue-booking-messages/", HTTP_HOST="127.0.0.1:8000", follow=True)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Log in to your account", html)
        self.assertNotIn(QUEUED_BOOKING_MESSAGE, html)
        self.assertNotIn(QUEUED_PAYMENT_MESSAGE, html)

    def test_google_oauth_keeps_local_callback_and_provider_account_picker(self):
        query = self._oauth_redirect_query("google_login")

        self.assertEqual(query["redirect_uri"], ["http://127.0.0.1:8000/oauth/google/login/callback/"])
        self.assertEqual(query["prompt"], ["select_account"])

    def test_github_oauth_keeps_local_callback_and_provider_account_picker(self):
        query = self._oauth_redirect_query("github_login")

        self.assertEqual(query["redirect_uri"], ["http://127.0.0.1:8000/oauth/github/login/callback/"])
        self.assertEqual(query["prompt"], ["select_account"])

    def test_facebook_local_launch_redirects_to_https_provider_origin(self):
        self._sync_env_apps()
        with patch.dict(os.environ, SIGNIN_ENV, clear=False):
            response = self.client.get(
                f"{reverse('bookings:social-provider-launch', kwargs={'provider_id': 'facebook'})}?next=/accounts/",
                HTTP_HOST="127.0.0.1:8000",
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "https://local.mladis.com/accounts/social/facebook/?next=%2Faccounts%2F",
        )

    def test_facebook_stable_local_oauth_uses_https_callback(self):
        query = self._oauth_redirect_query(
            "facebook_login",
            host="local.mladis.com",
            secure=True,
        )

        self.assertEqual(
            query["redirect_uri"],
            ["https://local.mladis.com/oauth/facebook/login/callback/"],
        )

    @override_settings(
        ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver", ".trycloudflare.com"],
        SOCIAL_AUTH_PROVIDER_ORIGINS={
            "google": "http://127.0.0.1:8000",
            "github": "http://127.0.0.1:8000",
            "facebook": "",
            "microsoft": "",
        }
    )
    def test_facebook_tunnel_request_origin_can_drive_callback(self):
        query = self._oauth_redirect_query(
            "facebook_login",
            host="active-facebook-tunnel.trycloudflare.com",
            secure=True,
        )

        self.assertEqual(
            query["redirect_uri"],
            ["https://active-facebook-tunnel.trycloudflare.com/oauth/facebook/login/callback/"],
        )

    def test_oauth_diagnostics_route_shows_provider_callback_urls(self):
        self._sync_env_apps()
        staff = get_user_model().objects.create_user("oauth", "oauth@example.com", "secret", is_staff=True)
        self.client.force_login(staff)

        with patch.dict(os.environ, SIGNIN_ENV, clear=False):
            response = self.client.get(reverse("bookings:oauth-diagnostics"), HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/oauth_diagnostics.html")
        self.assertContains(response, "http://127.0.0.1:8000/oauth/google/login/callback/")
        self.assertContains(response, "http://127.0.0.1:8000/oauth/github/login/callback/")
        self.assertContains(response, "https://local.mladis.com/oauth/facebook/login/callback/")

    @override_settings(
        ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver", "mladis.com"],
        ACCOUNT_DEFAULT_HTTP_PROTOCOL="https",
        SOCIAL_AUTH_CANONICAL_ORIGIN="https://mladis.com",
        SOCIAL_AUTH_PROVIDER_ORIGINS={
            "google": "",
            "github": "",
            "facebook": "",
            "microsoft": "",
        },
    )
    def test_production_oauth_contract_uses_mladis_domain(self):
        self._sync_env_apps()
        staff = get_user_model().objects.create_user("prod-oauth", "prod-oauth@example.com", "secret", is_staff=True)
        self.client.force_login(staff)

        with patch.dict(os.environ, SIGNIN_ENV, clear=False):
            response = self.client.get(reverse("bookings:oauth-diagnostics"), HTTP_HOST="mladis.com", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://mladis.com/oauth/google/login/callback/")
        self.assertContains(response, "https://mladis.com/oauth/facebook/login/callback/")
        self.assertContains(response, "https://mladis.com/oauth/github/login/callback/")
