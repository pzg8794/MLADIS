import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import OperationsWorkItem, WorkItemStatus


@override_settings(
    MLADIS_WORKBOARD_OWNER_EMAILS=["piter@example.com"],
    MLADIS_WORKBOARD_OWNER_USERNAMES=[],
)
class OperationsWorkboardAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="piter-owner",
            email="piter@example.com",
            password="test-pass",
        )
        self.other_user = User.objects.create_user(
            username="other-staff",
            email="other@example.com",
            password="test-pass",
        )
        self.item = OperationsWorkItem.objects.create(
            title="Verify workboard contract",
            list_name="Business tasks",
            neuron="operations",
            status=WorkItemStatus.PLANNED,
            priority="critical",
            next_action="Keep the owner-only workboard useful.",
        )

    def test_owner_can_load_workboard_api(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("operations:workboard-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        business_list = next(item for item in payload["lists"] if item["name"] == "Business tasks")
        self.assertIn(self.item.title, {item["title"] for item in business_list["items"]})

    def test_non_owner_cannot_load_workboard_api(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("operations:workboard-api"))

        self.assertEqual(response.status_code, 403)

    def test_owner_can_toggle_item_completion(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("operations:workitem-completion-api", args=[self.item.pk]),
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, WorkItemStatus.DONE)
        self.assertIsNotNone(self.item.completed_at)
        self.assertTrue(response.json()["item"]["is_done"])

    def test_non_owner_cannot_toggle_item_completion(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("operations:workitem-completion-api", args=[self.item.pk]),
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, WorkItemStatus.PLANNED)
