from django.test import TestCase
from django.urls import reverse


class SaNDAIShowcaseRouteTests(TestCase):
    def test_showcase_route_serves_modern_react_shell(self):
        self.assertEqual(reverse("bookings:sandai-showcase"), "/sandai/")
        response = self.client.get("/sandai/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/modern_site.html")
        self.assertContains(response, 'id="root"')
