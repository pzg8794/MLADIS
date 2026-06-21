import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import OperationsWorkItem, WorkItemStatus
from .services import WorkboardAccessPolicy

# Use non-manifest static storage to avoid "Missing staticfiles manifest" errors
# when template rendering calls `staticfiles_storage.url()` during page tests.
_TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_workitem(**kwargs):
    defaults = dict(
        title="Test work item",
        list_name="Business tasks",
        neuron="operations",
        status=WorkItemStatus.PLANNED,
        priority="medium",
        next_action="Write tests.",
    )
    defaults.update(kwargs)
    return OperationsWorkItem.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Unit tests for WorkboardAccessPolicy
# ---------------------------------------------------------------------------

@override_settings(
    MLADIS_WORKBOARD_OWNER_EMAILS=["owner@example.com"],
    MLADIS_WORKBOARD_OWNER_USERNAMES=["the-owner"],
)
class WorkboardAccessPolicyTests(TestCase):
    """Unit tests for WorkboardAccessPolicy.can_manage() rules."""

    def _policy(self):
        return WorkboardAccessPolicy()

    def _user(self, **attrs):
        """Return a lightweight mock-like object."""
        from types import SimpleNamespace
        defaults = dict(is_authenticated=True, is_active=True, is_staff=False, email="", username="")
        defaults.update(attrs)
        return SimpleNamespace(**defaults)

    def test_unauthenticated_user_cannot_manage(self):
        u = self._user(is_authenticated=False)
        self.assertFalse(self._policy().can_manage(u))

    def test_inactive_user_cannot_manage(self):
        u = self._user(is_active=False, is_staff=True)
        self.assertFalse(self._policy().can_manage(u))

    def test_staff_user_can_manage(self):
        u = self._user(is_staff=True)
        self.assertTrue(self._policy().can_manage(u))

    def test_owner_email_can_manage(self):
        u = self._user(email="owner@example.com")
        self.assertTrue(self._policy().can_manage(u))

    def test_owner_email_is_case_insensitive(self):
        u = self._user(email="OWNER@EXAMPLE.COM")
        self.assertTrue(self._policy().can_manage(u))

    def test_owner_username_can_manage(self):
        u = self._user(username="the-owner")
        self.assertTrue(self._policy().can_manage(u))

    def test_non_staff_non_owner_cannot_manage(self):
        u = self._user(email="stranger@example.com", username="stranger")
        self.assertFalse(self._policy().can_manage(u))


# ---------------------------------------------------------------------------
# Integration tests: workboard page view
# ---------------------------------------------------------------------------

@override_settings(
    STORAGES=_TEST_STORAGES,
    MLADIS_WORKBOARD_OWNER_EMAILS=["owner@example.com"],
    MLADIS_WORKBOARD_OWNER_USERNAMES=[],
)
class WorkboardPageAccessTests(TestCase):
    """
    Every is_staff user must reach the workboard page (HTTP 200).
    Non-staff users must be denied (403 or redirect).

    Regression: previously the access policy checked only configured
    owner emails/usernames, so any other staff member received a 403.
    """

    def setUp(self):
        User = get_user_model()
        self.owner_staff = User.objects.create_user(
            "owner-staff", "owner@example.com", "pass", is_staff=True
        )
        # Staff user who is NOT in the owner allow-list.
        self.other_staff = User.objects.create_user(
            "diana-staff", "diana@example.com", "pass", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "guest", "guest@example.com", "pass", is_staff=False
        )

    def test_owner_staff_can_load_workboard_page(self):
        self.client.force_login(self.owner_staff)
        response = self.client.get(reverse("operations:workboard"))
        self.assertEqual(response.status_code, 200)

    def test_non_owner_staff_can_load_workboard_page(self):
        """Any active staff member must be able to reach the workboard page."""
        self.client.force_login(self.other_staff)
        response = self.client.get(reverse("operations:workboard"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_load_workboard_page(self):
        response = self.client.get(reverse("operations:workboard"))
        self.assertIn(response.status_code, {302, 403})

    def test_non_staff_authenticated_user_cannot_load_workboard_page(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("operations:workboard"))
        self.assertIn(response.status_code, {302, 403})


# ---------------------------------------------------------------------------
# Integration tests: workboard API
# ---------------------------------------------------------------------------

@override_settings(
    MLADIS_WORKBOARD_OWNER_EMAILS=["owner@example.com"],
    MLADIS_WORKBOARD_OWNER_USERNAMES=[],
)
class WorkboardAPIAccessTests(TestCase):
    """
    Every is_staff user must be able to call the workboard snapshot API.

    Regression: previously only configured owner emails/usernames could
    call GET /api/ops/workboard/ — all other staff received a 403.
    """

    def setUp(self):
        User = get_user_model()
        self.owner_staff = User.objects.create_user(
            "owner-staff", "owner@example.com", "pass", is_staff=True
        )
        self.other_staff = User.objects.create_user(
            "diana-staff", "diana@example.com", "pass", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "guest", "guest@example.com", "pass", is_staff=False
        )
        self.item = _make_workitem(title="Verify workboard contract")

    def test_owner_staff_can_load_workboard_api(self):
        self.client.force_login(self.owner_staff)
        response = self.client.get(reverse("operations:workboard-api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        all_titles = {i["title"] for lst in payload["lists"] for i in lst["items"]}
        self.assertIn(self.item.title, all_titles)

    def test_non_owner_staff_can_load_workboard_api(self):
        """Any active staff member must receive a 200 from the workboard API."""
        self.client.force_login(self.other_staff)
        response = self.client.get(reverse("operations:workboard-api"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_load_workboard_api(self):
        response = self.client.get(reverse("operations:workboard-api"))
        self.assertIn(response.status_code, {302, 403})

    def test_non_staff_authenticated_user_cannot_load_workboard_api(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse("operations:workboard-api"))
        self.assertIn(response.status_code, {302, 403})

    def test_workboard_api_returns_json_with_expected_structure(self):
        self.client.force_login(self.owner_staff)
        response = self.client.get(reverse("operations:workboard-api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in ("summary_cards", "lists", "status_columns", "focus_items", "generated_at"):
            self.assertIn(key, payload, f"Missing key '{key}' in workboard API response")


# ---------------------------------------------------------------------------
# Integration tests: work-item completion API
# ---------------------------------------------------------------------------

@override_settings(
    MLADIS_WORKBOARD_OWNER_EMAILS=["owner@example.com"],
    MLADIS_WORKBOARD_OWNER_USERNAMES=[],
)
class WorkItemCompletionAPITests(TestCase):
    """
    Staff users must be able to toggle work-item completion.
    Non-staff users must be denied.
    """

    def setUp(self):
        User = get_user_model()
        self.owner_staff = User.objects.create_user(
            "owner-staff", "owner@example.com", "pass", is_staff=True
        )
        self.other_staff = User.objects.create_user(
            "diana-staff", "diana@example.com", "pass", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "guest", "guest@example.com", "pass", is_staff=False
        )
        self.item = _make_workitem(title="Complete me")

    def _completion_url(self):
        return reverse("operations:workitem-completion-api", args=[self.item.pk])

    def _post(self, completed=True):
        return self.client.post(
            self._completion_url(),
            data=json.dumps({"completed": completed}),
            content_type="application/json",
        )

    def test_owner_staff_can_mark_item_done(self):
        self.client.force_login(self.owner_staff)
        response = self._post(completed=True)
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, WorkItemStatus.DONE)
        self.assertIsNotNone(self.item.completed_at)
        self.assertTrue(response.json()["item"]["is_done"])

    def test_non_owner_staff_can_mark_item_done(self):
        """Any active staff member must be able to mark work items done."""
        self.client.force_login(self.other_staff)
        response = self._post(completed=True)
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, WorkItemStatus.DONE)

    def test_owner_staff_can_reopen_item(self):
        self.item.mark_done()
        self.item.save()
        self.client.force_login(self.owner_staff)
        response = self._post(completed=False)
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertNotEqual(self.item.status, WorkItemStatus.DONE)
        self.assertFalse(response.json()["item"]["is_done"])

    def test_non_owner_staff_can_reopen_item(self):
        self.item.mark_done()
        self.item.save()
        self.client.force_login(self.other_staff)
        response = self._post(completed=False)
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertNotEqual(self.item.status, WorkItemStatus.DONE)

    def test_anonymous_cannot_toggle_item_completion(self):
        response = self._post()
        self.assertIn(response.status_code, {302, 403})
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, WorkItemStatus.PLANNED)

    def test_non_staff_user_cannot_toggle_item_completion(self):
        self.client.force_login(self.regular_user)
        response = self._post()
        self.assertIn(response.status_code, {302, 403})
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, WorkItemStatus.PLANNED)

    def test_invalid_json_body_returns_400(self):
        self.client.force_login(self.owner_staff)
        response = self.client.post(
            self._completion_url(),
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
