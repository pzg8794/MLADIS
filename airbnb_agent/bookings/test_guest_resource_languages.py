"""Localized public resources preserve language, consent, and safe links."""
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit

from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import AudienceCampaignSettings, AudienceSubscription, CustomerProfile
from .public_guest_resources import AudienceService


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
class GuestResourceLanguageTests(TestCase):
    def setUp(self):
        AudienceCampaignSettings.objects.create(signup_enabled=True)
        self.service = AudienceService()
        self.guide = reverse("bookings:airbnb-stay-guide")
        self.signup = reverse("bookings:offers-signup")
        self.privacy = reverse("bookings:offers-privacy")

    def assert_language(self, response, language):
        self.assertEqual(response.headers.get("Content-Language"), language)
        self.assertContains(response, f'<html lang="{language}"', status_code=response.status_code)
        vary = {part.strip().lower() for part in response.headers.get("Vary", "").split(",")}
        self.assertTrue({"accept-language", "cookie"}.issubset(vary), vary)

    def test_four_languages_work_for_public_resources(self):
        for path in (self.guide, self.signup, self.privacy):
            for lang in ("en", "es", "fr", "pt"):
                with self.subTest(path=path, language=lang):
                    response = self.client.get(path, {"lang": lang})
                    self.assertEqual(response.status_code, 200)
                    self.assert_language(response, lang)

    def test_precedence_invalid_and_weighted_header_fallback(self):
        client = Client()
        self.assert_language(client.get(self.guide, HTTP_ACCEPT_LANGUAGE="es-MX;q=0.4, fr-CA;q=0.9, pt-BR;q=0.7"), "fr")
        self.assert_language(client.get(self.guide, HTTP_ACCEPT_LANGUAGE="fr;q=0, es-MX;q=0.8"), "es")
        self.assert_language(client.get(self.guide, HTTP_ACCEPT_LANGUAGE="de-DE, zh;q=0.9"), "en")
        client.cookies["mladis_guest_language"] = "pt"
        self.assert_language(client.get(self.guide, HTTP_ACCEPT_LANGUAGE="fr"), "pt")
        self.assert_language(client.get(self.guide, {"lang": "es"}, HTTP_ACCEPT_LANGUAGE="fr"), "es")
        self.assert_language(client.get(self.guide, {"lang": "invalid"}, HTTP_ACCEPT_LANGUAGE="fr"), "es")
        client.cookies["mladis_guest_language"] = "invalid"
        self.assert_language(client.get(self.guide, {"lang": "invalid"}, HTTP_ACCEPT_LANGUAGE="fr-CA"), "fr")

    def test_language_cookie_security(self):
        response = self.client.get(self.guide, {"lang": "es"}, secure=True)
        cookie = response.cookies["mladis_guest_language"]
        self.assertEqual(cookie.value, "es")
        self.assertEqual(int(cookie["max-age"]), 365 * 24 * 60 * 60)
        self.assertTrue(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"].lower(), "lax")
        response = Client().get(self.guide, {"lang": "invalid"})
        self.assertNotIn("mladis_guest_language", response.cookies)

    def test_switch_links_keep_signed_path_drop_unrelated_query(self):
        self.service.request_signup(email="lang@example.com", welcome_discount=True, seasonal_offers=False, language="es")
        member = AudienceSubscription.objects.get(email="lang@example.com")
        paths = (
            self.guide,
            reverse("bookings:offers-confirm", kwargs={"token": self.service.confirmation_token(member)}),
            reverse("bookings:offers-unsubscribe", kwargs={"token": self.service.unsubscribe_token(member)}),
        )
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, {"lang": "es", "secret": "do-not-propagate"})
                parser = Links()
                parser.feed(response.content.decode())
                options = response.context["language_options"]
                values = set()
                for option in options:
                    self.assertIn(option["url"], parser.hrefs)
                    target = urlsplit(urljoin("https://mladis.com" + path, option["url"]))
                    query = parse_qs(target.query)
                    self.assertEqual(set(query), {"lang"})
                    self.assertEqual(target.path, path)
                    values.update(query["lang"])
                self.assertEqual(values, {"en", "es", "fr", "pt"})

    def test_localized_signup_confirmation_and_consent_evidence(self):
        for lang in ("en", "es", "fr", "pt"):
            with self.subTest(language=lang):
                email = f"{lang}@example.com"
                form_page = self.client.get(self.signup, {"lang": lang})
                form = form_page.context["form"]
                selected_labels = (form.fields["welcome_discount"].label, form.fields["seasonal_offers"].label)
                response = self.client.post(self.signup + "?lang=" + lang, {"email": email, "welcome_discount": "on", "seasonal_offers": "on"})
                self.assertEqual(response.status_code, 200)
                self.assert_language(response, lang)
                member = AudienceSubscription.objects.get(email=email)
                self.assertEqual(member.preferred_language, lang)
                self.assertIsNone(member.confirmed_at)
                self.assertIn(email, mail.outbox[-1].to)
                self.assertIn("lang=" + lang, mail.outbox[-1].body)
                token = self.service.confirmation_token(member)
                url = reverse("bookings:offers-confirm", kwargs={"token": token})
                # Viewing in another language must not replace the consent originally selected.
                get = self.client.get(url, {"lang": "en"})
                self.assert_language(get, "en")
                response = self.client.post(url + "?lang=en")
                self.assertEqual(response.status_code, 200)
                member.refresh_from_db()
                self.assertEqual(member.preferred_language, lang)
                self.assertEqual(member.consent_language, lang)
                for label in selected_labels:
                    self.assertIn(label, member.consent_text)
                self.assertTrue(member.can_receive_promotions)
                self.assertEqual(member.customer_profile.preferred_language, lang)
                unsub = reverse("bookings:offers-unsubscribe", kwargs={"token": self.service.unsubscribe_token(member)})
                self.assert_language(self.client.get(unsub, {"lang": lang}), lang)
                result = self.client.post(unsub + "?lang=" + lang)
                self.assertEqual(result.status_code, 200)
                self.assert_language(result, lang)
                member.refresh_from_db()
                self.assertFalse(member.can_receive_promotions)
        evidence = {m.preferred_language: m.consent_text for m in AudienceSubscription.objects.filter(email__endswith="@example.com")}
        self.assertEqual(len(set(evidence.values())), 4)

    def test_translated_form_errors_invalid_links_and_disabled_signup(self):
        for lang in ("en", "es", "fr", "pt"):
            with self.subTest(language=lang):
                response = self.client.post(self.signup + "?lang=" + lang, {"email": "bad", "welcome_discount": "on"})
                self.assertEqual(response.status_code, 400)
                self.assert_language(response, lang)
                for route in ("bookings:offers-confirm", "bookings:offers-unsubscribe"):
                    invalid = self.client.get(reverse(route, kwargs={"token": "invalid"}), {"lang": lang})
                    self.assertEqual(invalid.status_code, 400)
                    self.assert_language(invalid, lang)
        config = AudienceCampaignSettings.current()
        config.signup_enabled = False
        config.save()
        response = self.client.post(self.signup + "?lang=es", {"email": "disabled@example.com", "welcome_discount": "on"})
        self.assertEqual(response.status_code, 503)
        self.assert_language(response, "es")
        self.assertFalse(AudienceSubscription.objects.filter(email="disabled@example.com").exists())
        self.assertFalse(CustomerProfile.objects.filter(email="disabled@example.com").exists())

    def test_consent_history_retains_earlier_seasonal_permission_across_later_request(self):
        from datetime import timedelta
        from django.utils import timezone
        from .public_guest_resources import OffersSignupForm

        self.service.request_signup(email="history@example.com", welcome_discount=False, seasonal_offers=True, language="es")
        member = AudienceSubscription.objects.get(email="history@example.com")
        first_token = self.service.confirmation_token(member)
        self.service.confirm(first_token)
        member.refresh_from_db()
        self.assertTrue(member.seasonal_offers)
        self.assertEqual(len(member.consent_history), 1)
        spanish_label = OffersSignupForm(language="es").fields["seasonal_offers"].label
        self.assertEqual(member.consent_history[0]["language"], "es")
        self.assertIn(spanish_label, member.consent_history[0]["text"])
        self.assertTrue(member.consent_history[0]["seasonal_offers"])
        self.assertFalse(member.consent_history[0]["welcome_discount"])
        member.requested_at = timezone.now() - timedelta(minutes=16)
        member.save(update_fields=["requested_at"])
        self.service.request_signup(email=member.email, welcome_discount=True, seasonal_offers=False, language="fr")
        member.refresh_from_db()
        second_token = self.service.confirmation_token(member)
        self.service.confirm(second_token)
        self.service.confirm(second_token)
        member.refresh_from_db()
        self.assertTrue(member.seasonal_offers)
        self.assertEqual(len(member.consent_history), 2)
        self.assertEqual(member.consent_history[0]["language"], "es")
        self.assertIn(spanish_label, member.consent_history[0]["text"])
        self.assertEqual(member.consent_history[1]["language"], "fr")
        self.assertTrue(member.consent_history[1]["welcome_discount"])
        self.assertFalse(member.consent_history[1]["seasonal_offers"])
        self.assertEqual(member.consent_language, "fr")
        self.assertIn(OffersSignupForm(language="fr").fields["welcome_discount"].label, member.consent_text)

    def test_legacy_consent_evidence_survives_new_localized_confirmation(self):
        from datetime import timedelta
        from django.utils import timezone
        from .public_guest_resources import OffersSignupForm

        earlier = timezone.now() - timedelta(days=2)
        member = AudienceSubscription.objects.create(
            email="legacy@example.com", confirmed_at=earlier, seasonal_offers=True,
            consent_text="I agree to receive seasonal offers.",
            consent_version="2026-10-29", consent_language="", consent_history=[],
        )
        self.service.request_signup(email=member.email, welcome_discount=True, seasonal_offers=False, language="fr")
        member.refresh_from_db()
        token = self.service.confirmation_token(member)
        self.service.confirm(token)
        self.service.confirm(token)
        member.refresh_from_db()
        self.assertEqual(len(member.consent_history), 2)
        original, current = member.consent_history
        self.assertEqual(original["text"], "I agree to receive seasonal offers.")
        self.assertEqual(original["version"], "2026-10-29")
        self.assertEqual(original["language"], "en")
        self.assertEqual(original["confirmed_at"], earlier.isoformat())
        self.assertTrue(original["legacy"])
        self.assertEqual(current["language"], "fr")
        self.assertIn(OffersSignupForm(language="fr").fields["welcome_discount"].label, current["text"])
        self.assertTrue(member.seasonal_offers)
