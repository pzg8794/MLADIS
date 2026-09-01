import json
import os
import re
from urllib.parse import parse_qs, urlparse
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.socialaccount.internal.flows.signup import process_auto_signup
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.google.provider import GoogleProvider
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import CommandError, call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
import stripe

from .adapters import MLADISAccountAdapter, MLADISSocialAccountAdapter
from .admin import DamageDepositAdmin
from .airbnb_capture_state import AirbnbCaptureState
from .airbnb_response_workflow import CustomerResponseDraft, AirbnbResponseWorkflow, ResponseWorkflowError
from .airbnb_import import AirbnbGuestEmailParser, AirbnbGuestImportService
from .airbnb_reservation_lake import (
    AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION,
    AirbnbReservationSnapshotWriter,
)
from .data_lake import MLADISDataLakeExporter
from .interaction_lake import AnonymousInteractionLakeWriter
from .forms import BookingInquiryForm
from .guest_services import GuestService
from .models import (
    AdminAccess,
    AgentFAQ,
    AgentKnowledgeSource,
    AgentConversation,
    AirbnbGuestRecord,
    AvailabilityBlock,
    BookableItem,
    BookingCategory,
    BookingInquiry,
    BookingStatus,
    CancellationPolicy,
    ClientSegment,
    ContactSource,
    Coupon,
    CustomerFeedback,
    CustomerProfile,
    DailyPriceOverride,
    Donation,
    DonationStatus,
    DamageDeposit,
    DepositProvider,
    DepositStatus,
    EmailDeliveryStatus,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    MarketingConsentStatus,
    MaintenanceEvent,
    MaintenancePhoto,
    PageVisit,
    Promotion,
    PromotionRecipient,
    ReservationPaymentHold,
    SiteSettings,
)
from .ops_navigation import OPS_NAV_ITEMS
from .ops_finance import _item_image_url
from .services import (
    AgentAccessContext,
    AgentRequest,
    BookingAgentService,
    BookingCalendarService,
    BookingEmailService,
    DamageDepositService,
    InvoiceEmailService,
    PaymentAuthorization,
    PromotionEmailService,
    ReservationRequestService,
    ReservationPricingService,
    ReservationPaymentHoldService,
)


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

TINY_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
    b"\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@override_settings(STORAGES=TEST_STORAGES)
class OpsNavigationContractTests(TestCase):
    expected_nav = [
        ("Overview", "Command Center", "/ops/dashboard/"),
        ("Operations", "Reservations", "/ops/reservations/"),
        ("Operations", "Calendar", "/ops/calendar/"),
        ("Operations", "Guests", "/ops/customers/"),
        ("Operations", "Maintenance", "/ops/maintenance/"),
        ("Operations", "Payments", "/ops/payments/"),
        ("Operations", "Deposits", "/ops/deposits/"),
        ("Operations", "Reports", "/ops/reports/"),
        ("Operations", "FairAgent", "/ops/agent/"),
        ("Business", "Properties", "/ops/properties/"),
        ("Admin", "Settings", "/ops/settings/"),
        ("Admin", "Admin", "/ops/admin/"),
    ]

    def setUp(self):
        self.staff_user = get_user_model().objects.create_user(
            "piter",
            "garciapiterz@gmail.com",
            "secret",
            is_staff=True,
        )
        self.client.force_login(self.staff_user)
        site_settings = SiteSettings.current()
        site_settings.logo_url = "https://cdn.example.test/mladis-logo.png"
        site_settings.save(update_fields=["logo_url", "updated_at"])

    def test_canonical_nav_has_expected_groups_labels_and_urls(self):
        actual_nav = [(item["group"], item["label"], item["href"]) for item in OPS_NAV_ITEMS]

        self.assertEqual(actual_nav, self.expected_nav)

    def _assert_route(self, href: str, expected_view_name: str, expected_template: str | None = None):
        match = resolve(href)
        self.assertEqual(match.view_name, expected_view_name)
        self.assertEqual(reverse(expected_view_name), href)
        response = self.client.get(href)
        self.assertEqual(response.status_code, 200)
        if expected_template:
            self.assertTemplateUsed(response, expected_template)
            self.assertTemplateNotUsed(response, "bookings/modern_dashboard.html")
        html_content = response.content.decode("utf-8")
        nav_match = re.search(
            r'<script id="mladis-ops-nav-items" type="application/json">(.*?)</script>',
            html_content,
            re.S,
        )
        self.assertIsNotNone(nav_match, "Missing canonical ops nav JSON payload")
        nav_items = json.loads(nav_match.group(1))
        actual_nav = [(item["group"], item["label"], item["href"]) for item in nav_items]
        self.assertEqual(actual_nav, self.expected_nav)
        self.assertNotIn("Business profile", html_content)
    def test_ops_dashboard_routes(self):
        self._assert_route("/ops/dashboard/", "bookings:ops-dashboard")

    def test_ops_reservations_routes(self):
        self._assert_route("/ops/reservations/", "bookings:ops-reservations")

    def test_ops_calendar_routes(self):
        self._assert_route("/ops/calendar/", "bookings:calendar-ops")

    def test_ops_guests_routes(self):
        self._assert_route("/ops/customers/", "bookings:ops-customers")

    def test_ops_guests_alias_route(self):
        self._assert_route("/ops/guests/", "bookings:ops-guests")

    def test_ops_maintenance_routes(self):
        self._assert_route(
            "/ops/maintenance/",
            "bookings:ops-maintenance",
            "bookings/modern_ops_maintenance.html",
        )

    def test_ops_payments_routes(self):
        self._assert_route("/ops/payments/", "bookings:ops-payments")

    def test_ops_deposits_routes(self):
        self._assert_route("/ops/deposits/", "bookings:ops-deposits")

    def test_deposit_fallback_image_uses_collected_static_path(self):
        with patch("bookings.ops_finance.static", side_effect=lambda path: path):
            fallback_path = _item_image_url(None)

        self.assertEqual(
            fallback_path,
            "frontend/modern-dashboard/stays/stay-3br.jpg",
        )
        self.assertTrue(
            (Path(__file__).resolve().parent / "static" / fallback_path).is_file()
        )

    def test_deposit_item_image_preserves_remote_urls(self):
        remote_url = "https://cdn.example.test/stay.jpg"

        self.assertEqual(
            _item_image_url(SimpleNamespace(image=remote_url)),
            remote_url,
        )
        self.assertEqual(
            _item_image_url(SimpleNamespace(image="/im/pictures/stay.jpg")),
            "https://a0.muscache.com/im/pictures/stay.jpg",
        )

    def test_ops_reports_routes(self):
        self._assert_route("/ops/reports/", "bookings:ops-reports")

    def test_ops_fairagent_routes(self):
        self._assert_route(
            "/ops/agent/",
            "bookings:ops-agent",
            "bookings/modern_ops_agent.html",
        )

    def test_replacement_agent_and_maintenance_pages_are_removed(self):
        frontend_pages = Path(__file__).resolve().parents[2] / "frontend" / "src" / "ui" / "pages"
        self.assertFalse((frontend_pages / "OpsAgentPage.tsx").exists())
        self.assertFalse((frontend_pages / "OpsMaintenancePage.tsx").exists())

    def test_ops_properties_routes(self):
        self._assert_route("/ops/properties/", "bookings:ops-properties")

    def test_ops_tasks_routes(self):
        self._assert_route("/ops/workboard/", "operations:workboard")

    def test_ops_settings_routes(self):
        self._assert_route("/ops/settings/", "bookings:ops-settings")

    def test_ops_admin_routes(self):
        self._assert_route("/ops/admin/", "bookings:ops-admin")

    def test_legacy_stays_route_redirects_to_properties(self):
        response = self.client.get("/ops/stays/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/ops/properties/")

    def test_legacy_listings_route_redirects_to_properties(self):
        response = self.client.get("/ops/listings/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/ops/properties/")

    def test_react_fallback_has_no_stale_left_nav_labels(self):
        repo_root = Path(__file__).resolve().parents[2]
        fallback_source = (repo_root / "frontend/src/ui/opsNavigation.ts").read_text(encoding="utf-8")

        for _group, label, href in self.expected_nav:
            with self.subTest(label=label, href=href):
                self.assertIn(f"label: '{label}'", fallback_source)
                self.assertIn(f"href: '{href}'", fallback_source)

        stale_label_patterns = [
            "label: 'Dashboard'",
            "label: 'Stays'",
            "label: 'Agent Intelligence'",
            "label: 'Listings'",
            "label: 'Customers'",
            "label: 'Work Orders'",
        ]
        for pattern in stale_label_patterns:
            with self.subTest(stale_label_pattern=pattern):
                self.assertNotIn(pattern, fallback_source)

    def test_sidebar_overlay_contract_keeps_pages_full_width(self):
        repo_root = Path(__file__).resolve().parents[2]
        styles_source = (repo_root / "frontend/src/styles.css").read_text(encoding="utf-8")

        shell_match = re.search(
            r'\.dashboard-shell\[data-theme-reference="gentelella-v4"\]\s*\{\s*'
            r'grid-template-columns:\s*minmax\(0,\s*1fr\);',
            styles_source,
            re.MULTILINE,
        )
        self.assertIsNotNone(shell_match, "Missing full-width ops shell grid rule")

        sidebar_match = re.search(
            r'\.dashboard-shell\[data-theme-reference="gentelella-v4"\]\s*>\s*\.modern-admin-sidebar\.v4-command-sidebar\s*\{(?P<body>.*?)\n\}',
            styles_source,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(sidebar_match, "Missing v4 sidebar overlay rule")
        sidebar_body = sidebar_match.group("body")
        self.assertIn("position: fixed;", sidebar_body)
        self.assertIn("width: 248px;", sidebar_body)
        self.assertIn("transform: translateX(-102%);", sidebar_body)

        expanded_match = re.search(
            r'\.dashboard-shell\[data-theme-reference="gentelella-v4"\]\s*>\s*\.modern-admin-sidebar\.v4-command-sidebar:hover,\s*\n'
            r'\.dashboard-shell\[data-theme-reference="gentelella-v4"\]\s*>\s*\.modern-admin-sidebar\.v4-command-sidebar:focus-within,\s*\n'
            r'\.dashboard-shell\[data-theme-reference="gentelella-v4"\]\s*>\s*\.modern-admin-sidebar\.v4-command-sidebar\.is-expanded\s*\{(?P<body>.*?)\n\}',
            styles_source,
            re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(expanded_match, "Missing expanded sidebar overlay rule")
        self.assertIn("transform: translateX(0);", expanded_match.group("body"))


# ---------------------------------------------------------------------------
# Ops route permission regression tests
# ---------------------------------------------------------------------------

@override_settings(
    STORAGES=TEST_STORAGES,
    MLADIS_WORKBOARD_OWNER_EMAILS=["staff@example.com"],
    MLADIS_WORKBOARD_OWNER_USERNAMES=[],
)
class OpsRoutePermissionRegressionTests(TestCase):
    """
    Regression suite: every ops page route must return HTTP 200 for any
    active staff member, and must deny anonymous / non-staff users (302 or 403).

    History: the workboard page and API were accidentally restricted to a
    hard-coded owner allow-list, so ordinary staff received a 403.  These
    tests prevent that class of regression across the entire ops surface.
    """

    # All ops page routes (SPA shell served by Django)
    OPS_PAGE_ROUTES = [
        "/ops/dashboard/",
        "/ops/reservations/",
        "/ops/reports/",
        "/ops/guests/",
        "/ops/customers/",
        "/ops/deposits/",
        "/ops/agent/",
        "/ops/maintenance/",
        "/ops/calendar/",
        "/ops/settings/",
        "/ops/admin/",
        "/ops/workboard/",
    ]

    # Parameterless read-only API routes that must be reachable by staff
    OPS_API_ROUTES = [
        "/api/ops/summary/",
        "/api/ops/reports/",
        "/api/ops/reservations/",
        "/api/ops/guests/",
        "/api/ops/customers/",
        "/api/ops/deposits/",
        "/api/ops/agent/",
        "/api/ops/maintenance/",
        "/api/ops/calendar/",
        "/api/ops/workboard/",
    ]

    def setUp(self):
        User = get_user_model()
        # A staff user who is NOT in the owner email allow-list.
        self.staff_user = User.objects.create_user(
            "diana-staff", "diana@example.com", "pass", is_staff=True
        )
        self.regular_user = User.objects.create_user(
            "guest", "guest@example.com", "pass", is_staff=False
        )

    # ---- Page routes: staff access ----------------------------------------

    def test_all_ops_page_routes_return_200_for_staff(self):
        """Every ops page route must serve the SPA shell for any staff user."""
        self.client.force_login(self.staff_user)
        for path in self.OPS_PAGE_ROUTES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Expected 200 for staff on {path}, got {response.status_code}",
                )

    # ---- Page routes: non-staff blocked ------------------------------------

    def test_all_ops_page_routes_deny_anonymous_users(self):
        """Anonymous users must be redirected away from every ops page route."""
        for path in self.OPS_PAGE_ROUTES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(
                    response.status_code,
                    {302, 403},
                    f"Expected redirect/deny for anon on {path}, got {response.status_code}",
                )

    def test_all_ops_page_routes_deny_non_staff_users(self):
        """Non-staff authenticated users must not reach any ops page route."""
        self.client.force_login(self.regular_user)
        for path in self.OPS_PAGE_ROUTES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(
                    response.status_code,
                    {302, 403},
                    f"Expected redirect/deny for non-staff on {path}, got {response.status_code}",
                )

    # ---- API routes: staff access -----------------------------------------

    def test_all_ops_api_routes_return_200_for_staff(self):
        """Every ops API route must return HTTP 200 for any staff user."""
        self.client.force_login(self.staff_user)
        for path in self.OPS_API_ROUTES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Expected 200 for staff on {path}, got {response.status_code}",
                )

    # ---- API routes: non-staff blocked ------------------------------------

    def test_all_ops_api_routes_deny_anonymous_users(self):
        """Anonymous users must be denied every ops API route."""
        for path in self.OPS_API_ROUTES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(
                    response.status_code,
                    {302, 403},
                    f"Expected redirect/deny for anon on {path}, got {response.status_code}",
                )

    def test_all_ops_api_routes_deny_non_staff_users(self):
        """Non-staff authenticated users must not reach any ops API route."""
        self.client.force_login(self.regular_user)
        for path in self.OPS_API_ROUTES:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(
                    response.status_code,
                    {302, 403},
                    f"Expected redirect/deny for non-staff on {path}, got {response.status_code}",
                )

    # ---- Workboard-specific: staff must get JSON, not HTML error ----------

    def test_workboard_api_returns_json_for_non_owner_staff(self):
        """Workboard API must not silently return an HTML error page to staff."""
        self.client.force_login(self.staff_user)
        response = self.client.get("/api/ops/workboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("Content-Type", "").split(";")[0], "application/json")
        payload = response.json()
        self.assertIn("lists", payload)
        self.assertIn("summary_cards", payload)


class BookingInquiryFormTests(TestCase):
    def test_rejects_checkout_before_checkin(self):
        today = timezone.localdate()
        form = BookingInquiryForm(
            data={
                "guest_name": "Alex",
                "email": "alex@example.com",
                "phone": "555-0100",
                "check_in": today + timedelta(days=2),
                "check_out": today + timedelta(days=1),
                "guests": 2,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("check_out", form.errors)


class DataLakeExporterTests(TestCase):
    def test_schema_only_export_creates_simple_catalog_and_placeholders(self):
        with TemporaryDirectory() as temp_dir:
            result = MLADISDataLakeExporter(temp_dir).export(
                schema_only=True,
                include_placeholders=True,
            )
            root = Path(temp_dir)

            self.assertTrue((root / "CATALOG.json").exists())
            self.assertTrue((root / "CUSTOMERS" / "subscriptions-placeholder.jsonl").exists())
            self.assertTrue((root / "EVENTS" / "object_states-placeholder.jsonl").exists())
            self.assertTrue((root / "EXPORTS" / f"export-run-{result.export_run_id}.json").exists())
            self.assertTrue(list(root.rglob("*placeholder.jsonl")))
            catalog = json.loads((root / "CATALOG.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["layout"], "simple-object-folders")
            self.assertIn("object_states", {collection["key"] for collection in catalog["collections"]})

    def test_live_object_state_signal_writes_model_snapshot(self):
        with TemporaryDirectory() as temp_dir, override_settings(
            MLADIS_DATASTORE_ROOT=temp_dir,
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            item = BookableItem.objects.create(
                name="Data Lake Test Stay",
                slug="data-lake-test-stay",
                short_description="State stream test.",
            )

            object_file = Path(temp_dir) / "STAYS" / f"bookableitem-{item.id}.json"
            history_file = Path(temp_dir) / "STAYS" / "_history.jsonl"
            self.assertTrue(object_file.exists())
            self.assertTrue(history_file.exists())
            state_text = object_file.read_text(encoding="utf-8")
            self.assertIn("object.created", state_text)
            self.assertIn("bookings.BookableItem", state_text)
            self.assertIn(str(item.id), state_text)
            self.assertIn("data-lake-test-stay", state_text)

    def test_live_object_state_redacts_auth_password_hash(self):
        User = get_user_model()
        with TemporaryDirectory() as temp_dir, override_settings(
            MLADIS_DATASTORE_ROOT=temp_dir,
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            User.objects.create_user(
                username="lake-user@example.com",
                email="lake-user@example.com",
                password="super-secret-pass",
            )

            state_text = (Path(temp_dir) / "CUSTOMERS" / "_history.jsonl").read_text(encoding="utf-8")
            self.assertIn("auth.User", state_text)
            self.assertIn('"password": "[redacted]"', state_text)
            self.assertNotIn("pbkdf2", state_text)
            self.assertNotIn("super-secret-pass", state_text)

    def test_anonymous_interaction_writer_removes_identity_and_source_references(self):
        with TemporaryDirectory() as temp_dir:
            path = AnonymousInteractionLakeWriter(temp_dir).write_conversation(
                source_system="airbnb",
                channel="host_messages",
                language="en",
                topic="arrival",
                known_names=["Maria Rodriguez"],
                turns=[
                    {
                        "role": "guest",
                        "text": "Hi, I am Maria Rodriguez. Email maria@example.com or call +1 809 555 0100. Ref R-1042.",
                    },
                    {"role": "host", "text": "Maria, here is the arrival guide: https://example.com/guide."},
                ],
            )
            payload = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
            output = json.dumps(payload)

            self.assertEqual(payload["collection"], "anonymous_interactions")
            self.assertEqual(payload["pii_classification"], "anonymized")
            self.assertIn("[person]", output)
            self.assertNotIn("Maria Rodriguez", output)
            self.assertNotIn("maria@example.com", output)
            self.assertNotIn("555 0100", output)
            self.assertNotIn("R-1042", output)
            self.assertNotIn("https://example.com", output)

    def test_anonymous_interaction_writer_is_sink_idempotent(self):
        kwargs = {
            "source_system": "airbnb",
            "channel": "host_messages",
            "language": "en",
            "topic": "arrival",
            "turns": [{"role": "guest", "text": "Can I arrive early?"}],
        }
        with TemporaryDirectory() as temp_dir:
            writer = AnonymousInteractionLakeWriter(temp_dir)
            first_path = writer.write_conversation(**kwargs)
            second_path = writer.write_conversation(**kwargs)
            rows = [line for line in first_path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(first_path, second_path)
        self.assertEqual(len(rows), 1)

    def test_anonymous_interaction_writer_keeps_distinct_source_observations(self):
        kwargs = {
            "source_system": "airbnb",
            "channel": "host_messages",
            "language": "en",
            "topic": "arrival",
            "turns": [{"role": "guest", "text": "Can I arrive early?"}],
        }
        with TemporaryDirectory() as temp_dir:
            writer = AnonymousInteractionLakeWriter(temp_dir)
            path = writer.write_conversation(**kwargs, occurred_at="2026-08-18T12:00:00Z")
            writer.write_conversation(**kwargs, occurred_at="2026-08-18T13:00:00Z")
            rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(len(rows), 2)

    def test_airbnb_capture_state_migrates_scope_keys_and_deduplicates(self):
        with TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "BOOKINGS" / AirbnbCaptureState.FILENAME
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "threads": {
                            "normal:thread-1": {
                                "interactions": True,
                                "fingerprints": {"interactions": ["same", "same"]},
                                "observation_counts": {"interactions": 1},
                            },
                            "archived:thread-1": {
                                "interactions": True,
                                "fingerprints": {"interactions": ["same"]},
                                "observation_counts": {"interactions": 1},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            state = AirbnbCaptureState.load(temp_dir)
            entry = state.entries["thread:thread-1"]

        self.assertEqual(entry["fingerprints"]["interactions"], ["same"])
        self.assertEqual(entry["reconciliation_required"], "interaction_prefix_not_available")

    def test_airbnb_capture_state_does_not_grow_fingerprints_on_reload(self):
        document = {
            "source": {"scope": "normal", "thread_id": "thread-reload"},
            "turns": [{"role": "guest", "text": "Can I arrive early?"}],
        }
        with TemporaryDirectory() as temp_dir:
            state = AirbnbCaptureState(temp_dir)
            state.mark(document, "interactions")
            state.save()
            reloaded = AirbnbCaptureState.load(temp_dir)
            reloaded.save()
            payload = json.loads(reloaded.path.read_text(encoding="utf-8"))

        self.assertEqual(
            len(payload["threads"]["thread:thread-reload"]["fingerprints"]["interactions"]),
            1,
        )

    def test_agent_conversation_signal_writes_only_identity_free_interaction_record(self):
        with TemporaryDirectory() as temp_dir, override_settings(
            MLADIS_DATASTORE_ROOT=temp_dir,
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            AgentConversation.objects.create(
                session_id="private-session-123",
                visitor_name="Guest Person",
                visitor_email="guest@example.com",
                last_user_message="My name is Guest Person and my phone is 555-0100.",
                last_agent_reply="Thanks Guest Person, I can help.",
                question_topic="arrival",
            )

            interaction_path = Path(temp_dir) / "INTERACTIONS" / "anonymous_interactions.jsonl"
            self.assertTrue(interaction_path.exists())
            interaction_text = interaction_path.read_text(encoding="utf-8")
            self.assertNotIn("Guest Person", interaction_text)
            self.assertNotIn("guest@example.com", interaction_text)
            self.assertNotIn("555-0100", interaction_text)
            self.assertNotIn("private-session-123", interaction_text)
            booking_agent_files = list((Path(temp_dir) / "BOOKINGAGENTS").glob("agentconversation-*.json"))
            self.assertFalse(booking_agent_files)

    def test_anonymous_interactions_are_exportable_as_a_dedicated_collection(self):
        AgentConversation.objects.create(
            session_id="export-session",
            visitor_name="Export Guest",
            visitor_email="export@example.com",
            last_user_message="Can I check in early?",
            last_agent_reply="We can review early check-in availability.",
            question_topic="arrival",
        )

        with TemporaryDirectory() as temp_dir:
            MLADISDataLakeExporter(temp_dir).export(collections=["anonymous_interactions"])
            export_path = Path(temp_dir) / "INTERACTIONS" / "anonymous_interactions.jsonl"
            export_text = export_path.read_text(encoding="utf-8")

        self.assertIn("anonymous_interactions", export_text)
        self.assertNotIn("Export Guest", export_text)
        self.assertNotIn("export@example.com", export_text)

    def test_airbnb_reservation_snapshot_has_stable_private_id_and_structured_fields(self):
        snapshot = {
            "scope": "archived",
            "thread_id": "2180129386",
            "thread_url": "https://www.airbnb.com/hosting/messages/2180129386?archived=",
            "confirmation_code": "HM-PRIVATE-001",
            "guest": {
                "name": "Reservation Guest",
                "email": "guest@example.com",
                "phone": "+1 809 555 0100",
            },
            "property": {
                "listing_id": "663340642010263561",
                "listing_title": "Three Bedroom Stay",
                "address": "Private property address",
            },
            "lifecycle": {
                "booking_date": "2026-06-01",
                "check_in": "2026-06-16",
                "check_out": "2026-06-19",
                "status": "confirmed",
                "cancellation_policy": "Flexible",
            },
            "occupancy": {"guests": 2, "nights": 3},
            "financials": {"total_amount": "620.00", "currency": "usd", "payment_status": "paid"},
            "notes": "The guest asked about airport transportation.",
            "raw_message_body": "This conversation must never be stored in a reservation snapshot.",
        }

        with TemporaryDirectory() as temp_dir:
            writer = AirbnbReservationSnapshotWriter(temp_dir)
            first = writer.build_record(snapshot)
            second = writer.build_record(snapshot)

        self.assertEqual(first["record_key"], second["record_key"])
        self.assertTrue(first["data"]["mladis_reservation_key"].startswith("AIRBNB-"))
        self.assertEqual(first["data"]["lifecycle"]["check_in"], "2026-06-16")
        self.assertEqual(first["data"]["financials"]["total_amount"], "620.00")
        self.assertEqual(first["data"]["guest"]["phone"], "+1 809 555 0100")
        self.assertTrue(first["data"]["source"]["needs_reconciliation"])
        self.assertNotIn("raw_message_body", first["data"])
        self.assertNotIn("This conversation must never be stored", json.dumps(first))

    def test_airbnb_reservation_snapshot_upsert_is_idempotent(self):
        snapshot = {
            "source": {"scope": "normal", "thread_id": "thread-1", "confirmation_code": "CONF-1"},
            "guest": {"name": "Guest One", "email": "guest1@example.com"},
            "property": {"listing_id": "listing-1", "listing_title": "Stay One"},
            "lifecycle": {"check_in": "2026-07-01", "check_out": "2026-07-03", "status": "confirmed"},
            "guests": 2,
        }
        with TemporaryDirectory() as temp_dir:
            writer = AirbnbReservationSnapshotWriter(temp_dir)
            self.assertEqual(writer.write_snapshot(snapshot)[1], "created")
            snapshot["guests"] = 3
            self.assertEqual(writer.write_snapshot(snapshot)[1], "updated")
            snapshot["lifecycle"]["status"] = "canceled"
            self.assertEqual(writer.write_snapshot(snapshot)[1], "updated")

            path = Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["data"]["lifecycle"]["status"], "canceled")

    def test_airbnb_reservation_key_ignores_mutable_dates_when_confirmation_exists(self):
        base = {
            "source": {"scope": "normal", "thread_id": "thread-date-change", "confirmation_code": "CONF-DATES"},
            "guest": {"name": "Guest One", "email": "guest1@example.com"},
            "property": {"listing_id": "listing-1", "listing_title": "Stay One"},
            "lifecycle": {"check_in": "2026-07-01", "check_out": "2026-07-03", "status": "confirmed"},
        }
        changed = {**base, "lifecycle": {**base["lifecycle"], "check_in": "2026-07-02", "check_out": "2026-07-04"}}

        writer = AirbnbReservationSnapshotWriter("/tmp/mladis-reservation-key-test")
        self.assertEqual(writer.reservation_key(base), writer.reservation_key(changed))
        archived = {**base, "source": {**base["source"], "scope": "archived"}}
        self.assertEqual(writer.reservation_key(base), writer.reservation_key(archived))

    def test_airbnb_reservation_key_rejects_empty_fallback_identity(self):
        with self.assertRaises(ValueError):
            AirbnbReservationSnapshotWriter("/tmp/mladis-reservation-key-test").reservation_key({})

    def test_airbnb_reservation_writer_heals_legacy_scope_key(self):
        snapshot = {
            "source": {"scope": "normal", "thread_id": "legacy-thread", "confirmation_code": "LEGACY-1"},
            "guest": {"name": "Legacy Guest"},
            "property": {"listing_title": "Legacy Stay"},
            "lifecycle": {"status": "confirmed"},
        }
        with TemporaryDirectory() as temp_dir:
            writer = AirbnbReservationSnapshotWriter(temp_dir)
            writer.layout.initialize()
            legacy_record = writer.build_record(snapshot)
            legacy_record["record_key"] = "reservation_snapshot:AIRBNB-OLD-SCOPE-KEY"
            path = writer.layout.collection_path(AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION)
            path.write_text(json.dumps(legacy_record) + "\n", encoding="utf-8")

            writer.write_snapshot(snapshot)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_key"], writer.build_record(snapshot)["record_key"])

    def test_airbnb_reservation_writer_heals_thread_only_legacy_scope_key(self):
        snapshot = {
            "source": {"scope": "archived", "thread_id": "legacy-thread-only"},
            "guest": {"name": "Legacy Thread Guest"},
            "property": {"listing_title": "Legacy Thread Stay"},
            "lifecycle": {"status": "confirmed"},
        }
        with TemporaryDirectory() as temp_dir:
            writer = AirbnbReservationSnapshotWriter(temp_dir)
            writer.layout.initialize()
            legacy_record = writer.build_record(snapshot)
            legacy_record["record_key"] = "reservation_snapshot:ARCHIVED-OLD-SCOPE-KEY"
            path = writer.layout.collection_path(AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION)
            path.write_text(json.dumps(legacy_record) + "\n", encoding="utf-8")

            writer.write_snapshot(snapshot)
            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_key"], writer.build_record(snapshot)["record_key"])

    def test_airbnb_reservation_snapshot_hashes_contact_after_decline_or_no_response(self):
        base = {
            "source": {"thread_id": "thread-consent", "confirmation_code": "CONF-CONSENT"},
            "guest": {"name": "Guest Consent", "email": "consent@example.com", "phone": "+1 809 555 0101"},
            "property": {"listing_title": "Stay Consent"},
            "lifecycle": {"check_in": "2026-08-01", "check_out": "2026-08-03"},
        }
        writer = AirbnbReservationSnapshotWriter("/tmp/mladis-reservation-consent-test")

        declined = writer.build_record({**base, "marketing_consent_status": "opted_out"})
        no_response = writer.build_record({
            **base,
            "marketing_consent": {"status": "requested", "response_received": False},
        })

        for record in (declined, no_response):
            guest = record["data"]["guest"]
            self.assertEqual(guest["email"], "")
            self.assertEqual(guest["phone"], "")
            self.assertTrue(guest["email_hash"])
            self.assertTrue(guest["phone_hash"])
            self.assertNotIn("consent@example.com", json.dumps(record))
            self.assertNotIn("+1 809 555 0101", json.dumps(record))
            self.assertIn(record["data"]["marketing_consent"]["status"], {"opted_out", "no_response"})

    def test_combined_airbnb_data_lake_command_writes_both_collections(self):
        combined_export = {
            "reservations": [{
                "source": {"scope": "normal", "thread_id": "thread-combined", "confirmation_code": "CONF-COMBINED"},
                "guest": {"name": "Combined Guest", "email": "combined@example.com", "phone": "555-0100"},
                "property": {"listing_id": "listing-combined", "listing_title": "Combined Stay"},
                "lifecycle": {"check_in": "2026-09-01", "check_out": "2026-09-03", "status": "confirmed"},
                "guests": 2,
                "financials": {"total_amount": "200.00", "currency": "usd"},
            }],
            "interactions": [{
                "source_system": "airbnb",
                "channel": "host_messages",
                "known_names": ["Combined Guest"],
                "turns": [{"role": "guest", "text": "I am Combined Guest, combined@example.com, 555-0100."}],
            }],
        }

        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            input_path = Path(input_dir) / "airbnb-combined.json"
            input_path.write_text(json.dumps(combined_export), encoding="utf-8")
            output = StringIO()
            call_command("collect_airbnb_data_lake", input=input_path, root=temp_dir, stdout=output)

            reservation_path = Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
            interaction_path = Path(temp_dir) / "INTERACTIONS" / "anonymous_interactions.jsonl"
            reservation_text = reservation_path.read_text(encoding="utf-8")
            interaction_text = interaction_path.read_text(encoding="utf-8")

        self.assertIn("1 interaction(s)", output.getvalue())
        self.assertIn("CONF-COMBINED", reservation_text)
        self.assertIn("Combined Stay", reservation_text)
        self.assertNotIn("Combined Guest", interaction_text)
        self.assertNotIn("combined@example.com", interaction_text)
        self.assertNotIn("555-0100", interaction_text)

    def test_combined_airbnb_data_lake_new_only_resume_skips_completed_capture(self):
        thread_capture = [{
            "dataset": "normal",
            "thread_id": "resume-thread-1",
            "preview": "Confirmed · Aug 21, 2026 – Aug 24, 2026 · 2 guests",
            "messages": [
                "Private Guest · Booker\nCan we arrive early?",
                "Diana · Host\nWe can review arrival options.",
            ],
            "captured_at": "2026-08-18T12:00:00-04:00",
        }]

        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            input_path = Path(input_dir) / "airbnb-thread-captures.json"
            input_path.write_text(json.dumps(thread_capture), encoding="utf-8")
            first_output = StringIO()
            second_output = StringIO()
            call_command("collect_airbnb_data_lake", input=input_path, root=temp_dir, new_only=True, stdout=first_output)
            call_command("collect_airbnb_data_lake", input=input_path, root=temp_dir, new_only=True, stdout=second_output)

            interaction_path = Path(temp_dir) / "INTERACTIONS" / "anonymous_interactions.jsonl"
            reservation_path = Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
            interaction_rows = [line for line in interaction_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            reservation_rows = [line for line in reservation_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            state_text = (Path(temp_dir) / "BOOKINGS" / ".airbnb_capture_state.json").read_text(encoding="utf-8")

        self.assertEqual(len(interaction_rows), 1)
        self.assertEqual(len(reservation_rows), 1)
        self.assertIn("Skipped existing captures: 1 reservation(s), 1 interaction(s).", second_output.getvalue())
        self.assertIn('"threads"', state_text)

    def test_combined_airbnb_data_lake_new_only_accepts_new_message_in_existing_thread(self):
        first_capture = {
            "dataset": "normal",
            "thread_id": "resume-thread-new-message",
            "preview": "Confirmed · Aug 21, 2026 – Aug 24, 2026 · 2 guests",
            "messages": ["Private Guest · Booker\nCan we arrive early?"],
            "captured_at": "2026-08-18T12:00:00-04:00",
        }
        updated_capture = {
            **first_capture,
            "messages": [
                "Private Guest · Booker\nCan we arrive early?",
                "Diana · Host\nWe can review arrival options.",
            ],
            "captured_at": "2026-08-18T12:05:00-04:00",
        }

        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            first_path = Path(input_dir) / "first-capture.json"
            updated_path = Path(input_dir) / "updated-capture.json"
            first_path.write_text(json.dumps([first_capture]), encoding="utf-8")
            updated_path.write_text(json.dumps([updated_capture]), encoding="utf-8")

            call_command("collect_airbnb_data_lake", input=first_path, root=temp_dir, new_only=True)
            call_command("collect_airbnb_data_lake", input=updated_path, root=temp_dir, new_only=True)
            third_output = StringIO()
            call_command(
                "collect_airbnb_data_lake",
                input=updated_path,
                root=temp_dir,
                new_only=True,
                stdout=third_output,
            )
            (Path(temp_dir) / "BOOKINGS" / AirbnbCaptureState.FILENAME).unlink()
            call_command("collect_airbnb_data_lake", input=updated_path, root=temp_dir, new_only=True)

            interaction_path = Path(temp_dir) / "INTERACTIONS" / "anonymous_interactions.jsonl"
            reservation_path = Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
            interaction_rows = [line for line in interaction_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            reservation_rows = [line for line in reservation_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            interaction_records = [json.loads(line) for line in interaction_rows]

        self.assertEqual(len(interaction_rows), 2)
        self.assertEqual(len(reservation_rows), 1)
        self.assertEqual(interaction_records[1]["data"]["turn_count"], 1)
        self.assertEqual(interaction_records[1]["data"]["observation_semantics"], "delta")
        self.assertIn("We can review arrival options.", json.dumps(interaction_records[1]))
        self.assertIn("Skipped existing captures: 1 reservation(s), 1 interaction(s).", third_output.getvalue())

    def test_combined_airbnb_data_lake_new_only_rejects_non_monotonic_history(self):
        first_capture = {
            "dataset": "normal",
            "thread_id": "resume-thread-non-monotonic",
            "messages": ["Private Guest · Booker\nCan we arrive early?"],
            "captured_at": "2026-08-18T12:00:00-04:00",
        }
        changed_capture = {
            **first_capture,
            "messages": ["Private Guest · Booker\nCan we arrive tomorrow?", "Diana · Host\nLet me check."],
            "captured_at": "2026-08-18T12:05:00-04:00",
        }
        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            first_path = Path(input_dir) / "first-capture.json"
            changed_path = Path(input_dir) / "changed-capture.json"
            first_path.write_text(json.dumps([first_capture]), encoding="utf-8")
            changed_path.write_text(json.dumps([changed_capture]), encoding="utf-8")
            call_command("collect_airbnb_data_lake", input=first_path, root=temp_dir, new_only=True)
            with self.assertRaises(CommandError):
                call_command("collect_airbnb_data_lake", input=changed_path, root=temp_dir, new_only=True)

    def test_airbnb_capture_state_rejects_equal_length_or_truncated_history(self):
        first = {
            "thread_id": "thread-history-shape",
            "turns": [{"role": "guest", "text": "Original"}],
        }
        with TemporaryDirectory() as temp_dir:
            state = AirbnbCaptureState(temp_dir)
            state.mark(first, "interactions")
            with self.assertRaises(ValueError):
                state.prepare_interaction(
                    {"thread_id": "thread-history-shape", "turns": [{"role": "guest", "text": "Changed"}]}
                )
            with self.assertRaises(ValueError):
                state.prepare_interaction({"thread_id": "thread-history-shape", "turns": []})

    def test_combined_airbnb_data_lake_new_only_updates_changed_reservation_snapshot(self):
        first_capture = {
            "dataset": "normal",
            "thread_id": "resume-thread-changed-reservation",
            "source": {"confirmation_code": "CONF-CHANGED"},
            "guest": {"name": "Snapshot Guest", "email": "snapshot@example.com"},
            "property": {"listing_id": "listing-snapshot", "listing_title": "Snapshot Stay"},
            "lifecycle": {
                "check_in": "2026-09-01",
                "check_out": "2026-09-03",
                "status": "confirmed",
            },
            "communication": {"message_count": 2},
            "financials": {"total_amount": "200.00", "currency": "usd"},
        }
        changed_capture = {
            **first_capture,
            "lifecycle": {**first_capture["lifecycle"], "status": "cancelled"},
            "captured_at": "2026-08-18T12:05:00-04:00",
        }

        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            first_path = Path(input_dir) / "first-reservation.json"
            changed_path = Path(input_dir) / "changed-reservation.json"
            first_path.write_text(json.dumps([first_capture]), encoding="utf-8")
            changed_path.write_text(json.dumps([changed_capture]), encoding="utf-8")

            call_command("collect_airbnb_data_lake", input=first_path, root=temp_dir, new_only=True)
            call_command("collect_airbnb_data_lake", input=changed_path, root=temp_dir, new_only=True)
            third_output = StringIO()
            call_command(
                "collect_airbnb_data_lake",
                input=changed_path,
                root=temp_dir,
                new_only=True,
                stdout=third_output,
            )

            reservation_path = Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
            records = [
                json.loads(line)
                for line in reservation_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["data"]["lifecycle"]["status"], "cancelled")
        self.assertIn("Skipped existing captures: 1 reservation(s), 0 interaction(s).", third_output.getvalue())

    def test_airbnb_message_table_capture_composes_reservation_projection(self):
        table_export = {
            "captured_at": "2026-08-18T12:00:00-04:00",
            "normal": [{
                "dataset": "normal",
                "thread_id": "table-thread-1",
                "href": "https://www.airbnb.com/hosting/messages/table-thread-1",
                "text": "Confirmed · Aug 21, 2026 – Aug 24, 2026 · 3 guests · 3 nights · 4 bedrooms · potential earnings $620.00 · rating 4.9",
            }],
            "archived": [],
        }

        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            input_path = Path(input_dir) / "airbnb-thread-index.json"
            input_path.write_text(json.dumps(table_export), encoding="utf-8")
            call_command("collect_airbnb_data_lake", input=input_path, root=temp_dir)

            reservation_path = Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
            record = json.loads(reservation_path.read_text(encoding="utf-8").splitlines()[0])

        data = record["data"]
        self.assertEqual(data["source"]["thread_id"], "table-thread-1")
        self.assertEqual(data["lifecycle"]["check_in"], "2026-08-21")
        self.assertEqual(data["lifecycle"]["check_out"], "2026-08-24")
        self.assertEqual(data["occupancy"]["guests"], 3)
        self.assertEqual(data["occupancy"]["nights"], 3)
        self.assertEqual(data["financials"]["potential_earnings"], "620.00")
        self.assertEqual(data["review"]["rating"], "4.90")
        self.assertEqual(data["review"]["text"], "")

    def test_airbnb_thread_capture_creates_reservation_and_sanitized_interaction(self):
        thread_capture = [{
            "dataset": "archived",
            "thread_id": "capture-thread-1",
            "preview": "Confirmed · Aug 21, 2026 – Aug 24, 2026 · 2 guests",
            "detail_text": "Potential earnings $620.00\n4.9 rating from 12 reviews",
            "messages": [
                "Private Guest · Booker\n10:00 AM\nCan we arrive early?",
                "Diana · Host\n10:05 AM\nWe can review arrival options.",
            ],
            "captured_at": "2026-08-18T12:00:00-04:00",
            "message_count": 2,
            "ok": True,
        }]

        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as input_dir, override_settings(
            MLADIS_DATASTORE_LIVE_SYNC_DRIVE=False,
        ):
            input_path = Path(input_dir) / "airbnb-thread-captures.jsonl"
            input_path.write_text("\n".join(json.dumps(row) for row in thread_capture), encoding="utf-8")
            call_command("collect_airbnb_data_lake", input=input_path, root=temp_dir)

            reservation_text = (Path(temp_dir) / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl").read_text(
                encoding="utf-8"
            )
            interaction_text = (Path(temp_dir) / "INTERACTIONS" / "anonymous_interactions.jsonl").read_text(
                encoding="utf-8"
            )

        self.assertIn("capture-thread-1", reservation_text)
        self.assertIn("2", reservation_text)
        reservation = json.loads(reservation_text.splitlines()[0])
        self.assertEqual(reservation["data"]["financials"]["potential_earnings"], "620.00")
        self.assertEqual(reservation["data"]["review"]["rating"], "4.90")
        self.assertEqual(reservation["data"]["review"]["count"], 12)
        self.assertNotIn("Private Guest", interaction_text)
        self.assertNotIn("Diana", interaction_text)
        self.assertIn("Can we arrive early?", interaction_text)

    def test_redacted_export_removes_direct_contact_and_message_text(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="guest@example.com",
            email="guest@example.com",
            password="test-pass",
        )
        profile = CustomerProfile.objects.create(
            user=user,
            name="Guest Person",
            email="guest@example.com",
            phone="555-0100",
        )
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101",
            short_description="Test stay",
        )
        BookingInquiry.objects.create(
            user=user,
            customer_profile=profile,
            item=item,
            guest_name="Guest Person",
            email="guest@example.com",
            phone="555-0100",
            check_in=timezone.localdate() + timedelta(days=1),
            check_out=timezone.localdate() + timedelta(days=3),
            guests=2,
            message="Private request text",
        )
        AgentConversation.objects.create(
            session_id="session-123",
            item=item,
            visitor_name="Guest Person",
            visitor_email="guest@example.com",
            last_user_message="Private chatbot question",
            last_agent_reply="Private answer echoing the guest",
        )

        with TemporaryDirectory() as temp_dir:
            MLADISDataLakeExporter(temp_dir, redacted=True).export(
                collections=["subscriptions", "booking_requests", "agent_conversations"]
            )
            export_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in Path(temp_dir).rglob("*.jsonl")
            )

        self.assertIn("email_hash", export_text)
        self.assertIn("username_hash", export_text)
        self.assertIn("phone_hash", export_text)
        self.assertNotIn("guest@example.com", export_text)
        self.assertNotIn("555-0100", export_text)
        self.assertNotIn("Private request text", export_text)
        self.assertNotIn("Private chatbot question", export_text)
        self.assertNotIn("Private answer echoing the guest", export_text)


@override_settings(STORAGES=TEST_STORAGES)
class AgentAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="agent-guest@example.com",
            email="agent-guest@example.com",
            password="test-pass",
            first_name="Agent",
            last_name="Guest",
        )
        self.item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )

    def test_agent_api_requires_signed_in_user(self):
        response = self.client.post(
            reverse("bookings:agent-api"),
            data=json.dumps({"message": "Can I book this?", "item_id": self.item.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "authentication_required")
        self.assertEqual(AgentConversation.objects.count(), 0)

    def test_agent_api_persists_conversation_for_signed_in_user(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("bookings:agent-api"),
            data=json.dumps({"message": "Can I book this?", "item_id": self.item.id}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.json())
        self.assertEqual(AgentConversation.objects.count(), 1)
        conversation = AgentConversation.objects.get()
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(response.json()["agent"]["questions_used"], 1)

    def test_agent_api_enforces_configured_question_limit(self):
        self.client.force_login(self.user)
        site_settings = SiteSettings.current()
        site_settings.agent_question_limit = 1
        site_settings.save(update_fields=["agent_question_limit", "updated_at"])

        first_response = self.client.post(
            reverse("bookings:agent-api"),
            data=json.dumps({"message": "Can I book this?", "item_id": self.item.id}),
            content_type="application/json",
        )
        second_response = self.client.post(
            reverse("bookings:agent-api"),
            data=json.dumps({"message": "Can I ask another question?", "item_id": self.item.id}),
            content_type="application/json",
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 429)
        self.assertEqual(second_response.json()["code"], "question_limit_reached")
        self.assertEqual(AgentConversation.objects.count(), 1)

    def test_agent_access_context_attaches_shared_agent_object_to_user_actor(self):
        anonymous_request = SimpleNamespace(user=AnonymousUser())
        anonymous_access = AgentAccessContext.from_request(anonymous_request)

        self.assertFalse(anonymous_access.can_ask)
        self.assertEqual(anonymous_access.agent.key, "public-booking-agent")
        self.assertEqual(anonymous_access.actor.visitor_key, "anon:untracked")
        self.assertIs(anonymous_request.user.mladis_agent, anonymous_access.agent)

        signed_in_request = SimpleNamespace(user=self.user)
        signed_in_access = AgentAccessContext.from_request(signed_in_request)

        self.assertTrue(signed_in_access.can_ask)
        self.assertEqual(signed_in_access.actor.user, self.user)
        self.assertEqual(signed_in_access.actor.visitor_key, f"user:{self.user.pk}")
        self.assertIs(self.user.mladis_agent, signed_in_access.agent)

    def test_site_summary_exposes_agent_access_state(self):
        anonymous_response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(anonymous_response.status_code, 200)
        self.assertIn("no-store", anonymous_response.headers["Cache-Control"])
        self.assertEqual(anonymous_response.json()["agent"]["agent_key"], "public-booking-agent")
        self.assertFalse(anonymous_response.json()["agent"]["is_authenticated"])
        self.assertFalse(anonymous_response.json()["agent"]["can_ask"])
        self.assertEqual(anonymous_response.json()["agent"]["login_url"], "/accounts/login/?next=/accounts/")

        self.client.force_login(self.user)
        signed_in_response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(signed_in_response.status_code, 200)
        self.assertTrue(signed_in_response.json()["agent"]["is_authenticated"])
        self.assertTrue(signed_in_response.json()["agent"]["can_ask"])

    def test_account_summary_is_user_context_controller_payload(self):
        anonymous_response = self.client.get(reverse("bookings:account-summary-api"))

        self.assertEqual(anonymous_response.status_code, 200)
        self.assertIn("no-store", anonymous_response.headers["Cache-Control"])
        self.assertFalse(anonymous_response.json()["authenticated"])
        self.assertFalse(anonymous_response.json()["agent"]["is_authenticated"])
        self.assertFalse(anonymous_response.json()["agent"]["can_ask"])

        self.client.force_login(self.user)
        signed_in_response = self.client.get(reverse("bookings:account-summary-api"))

        self.assertEqual(signed_in_response.status_code, 200)
        self.assertTrue(signed_in_response.json()["authenticated"])
        self.assertTrue(signed_in_response.json()["agent"]["is_authenticated"])
        self.assertTrue(signed_in_response.json()["agent"]["can_ask"])

    @override_settings(OPENAI_AGENT_MODEL="gpt-5.4-nano")
    def test_agent_service_uses_openai_when_key_is_configured(self):
        class FakeResponses:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(output_text="Yes, I can help with those dates.", id="resp_test")

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)

        response = BookingAgentService(api_key="sk-test", client=fake_client).reply(
            AgentRequest(
                message="Is there room for four guests?",
                session_id="session-123",
                item_id=self.item.id,
            )
        )

        conversation = AgentConversation.objects.get()
        self.assertEqual(response.reply, "Yes, I can help with those dates.")
        self.assertEqual(fake_responses.kwargs["model"], "gpt-5.4-nano")
        self.assertEqual(fake_responses.kwargs["max_output_tokens"], 280)
        self.assertIn("admin-confirmed", fake_responses.kwargs["instructions"])
        self.assertIn("secure deposit-hold step", fake_responses.kwargs["instructions"])
        self.assertIn("same language as the guest", fake_responses.kwargs["instructions"])
        self.assertIn("under 120 words", fake_responses.kwargs["instructions"])
        self.assertIn("only for the minimum details", fake_responses.kwargs["instructions"])
        self.assertIn("small, normal gathering may be allowed", fake_responses.kwargs["instructions"])
        self.assertIn("registered overnight guests", fake_responses.kwargs["instructions"])
        self.assertNotIn("Quick steps (English / Español)", fake_responses.kwargs["instructions"])
        self.assertIn("Do not promise discounts", fake_responses.kwargs["instructions"])
        self.assertIn("Is there room for four guests?", fake_responses.kwargs["input"])
        self.assertIn("Booking workflow", fake_responses.kwargs["input"])
        self.assertIn("Concise response guide", fake_responses.kwargs["input"])
        self.assertIn("Custom Booking Concierge", fake_responses.kwargs["input"])
        self.assertIn("Repository-backed guest knowledge", fake_responses.kwargs["input"])
        self.assertIn("Admin and external knowledge sources", fake_responses.kwargs["input"])
        self.assertIn(
            "Submitting an inquiry or deposit request does not guarantee a reservation until MLADIS confirms availability and booking terms.",
            fake_responses.kwargs["input"],
        )
        self.assertIn(
            "Booking and account details such as your name, email address, phone number, stay dates, guest count, and messages you send through the site.",
            fake_responses.kwargs["input"],
        )
        self.assertEqual(conversation.metadata["agent_mode"], "openai")
        self.assertEqual(conversation.metadata["openai_response_id"], "resp_test")

    def test_agent_setup_reply_uses_short_structured_steps(self):
        response = BookingAgentService(api_key="").reply(
            AgentRequest(
                message="Is the place available next week?",
                session_id="session-setup",
                item_id=self.item.id,
            )
        )

        self.assertTrue(response.reply.startswith("Next step\n"))
        self.assertIn("1) Confirm Test Stay", response.reply)
        self.assertIn("3) Submit the request", response.reply)
        self.assertLessEqual(len(response.reply.split()), 90)

    def test_agent_reply_formatter_preserves_markdown_content_without_fragmenting_it(self):
        reply = BookingAgentService._format_reply(
            "You’re welcome! **Custom Booking Concierge** can help. 1) Share your dates. 2) Share your 10 guest count."
        )

        self.assertEqual(
            reply,
            "You’re welcome! Custom Booking Concierge can help.\n1) Share your dates.\n2) Share your 10 guest count.",
        )
        self.assertNotIn("\n*\n*", reply)

    def test_airbnb_response_workflow_is_draft_first_and_fails_closed(self):
        workflow = AirbnbResponseWorkflow(agent_service=BookingAgentService(api_key=""))
        draft = workflow.draft(
            "Is the place available next week?",
            item_id=self.item.id,
            session_id="airbnb-workflow-test",
        )

        self.assertTrue(draft.low_stakes)
        self.assertTrue(draft.requires_staff_confirmation)
        self.assertFalse(draft.approved)
        self.assertFalse(draft.sendable)
        self.assertIn("\n1)", draft.reply)

        approved = workflow.approve(draft)
        self.assertTrue(approved.approved)
        self.assertFalse(approved.sendable)
        with self.assertRaises(ResponseWorkflowError):
            workflow.send(approved)

    def test_airbnb_response_workflow_escalates_financial_questions(self):
        workflow = AirbnbResponseWorkflow(agent_service=BookingAgentService(api_key=""))
        draft = workflow.draft(
            "Can you refund the deposit?",
            item_id=self.item.id,
            session_id="airbnb-workflow-escalation-test",
        )

        self.assertFalse(draft.low_stakes)
        self.assertFalse(workflow.approve(draft).sendable)

    def test_airbnb_response_workflow_escalates_day_use_events_with_overnight_guests(self):
        workflow = AirbnbResponseWorkflow(agent_service=BookingAgentService(api_key=""))
        draft = workflow.draft(
            "Can we use the pool for a birthday with 10 people, but have only 5 sleep overnight?",
            item_id=self.item.id,
            session_id="airbnb-workflow-event-test",
        )

        self.assertFalse(draft.low_stakes)
        self.assertFalse(workflow.approve(draft).sendable)

    def test_airbnb_response_workflow_requires_property_grounding_before_approval(self):
        workflow = AirbnbResponseWorkflow(agent_service=BookingAgentService(api_key=""))
        draft = workflow.draft(
            "Is the place available next week?",
            session_id="airbnb-workflow-no-property",
        )

        self.assertTrue(draft.low_stakes)
        self.assertEqual(draft.grounding_status, "property_unresolved")
        self.assertIn("property_not_resolved", draft.risk_reasons)
        self.assertFalse(workflow.approve(draft).sendable)

    def test_airbnb_response_workflow_requires_durable_authorization(self):
        draft = CustomerResponseDraft(
            reply="The stay is available.",
            topic="availability",
            mode="openai",
            conversation_id=None,
            low_stakes=True,
            grounding_status="property_resolved",
            draft_hash="draft-hash",
            approved=True,
            sendable=True,
        )
        workflow = AirbnbResponseWorkflow(sender=lambda _reply: "sent")
        with self.assertRaisesRegex(ResponseWorkflowError, "Durable outbound authorization"):
            workflow.send(draft)

    @override_settings(OPENAI_AGENT_MODEL="gpt-5.4-nano")
    def test_agent_service_blocks_off_topic_question_before_openai(self):
        class FakeResponses:
            def create(self, **_kwargs):
                raise AssertionError("Off-topic prompts should not reach OpenAI")

        fake_client = SimpleNamespace(responses=FakeResponses())

        response = BookingAgentService(api_key="sk-test", client=fake_client).reply(
            AgentRequest(message="Tell me a joke about cats.", session_id="session-off-topic")
        )

        conversation = AgentConversation.objects.get()
        self.assertIn("I can only help with MLADIS bookings", response.reply)
        self.assertEqual(conversation.metadata["agent_mode"], "guardrail")
        self.assertEqual(conversation.metadata["guardrail_reason"], "off_topic")

    @override_settings(OPENAI_AGENT_MODEL="gpt-5.4-nano")
    def test_agent_service_allows_short_follow_up_in_booking_context(self):
        AgentConversation.objects.create(
            session_id="session-follow-up",
            item=self.item,
            last_user_message="I want to book for four guests next weekend.",
            last_agent_reply="Please tell me which stay you prefer.",
            question_topic="availability",
            metadata={"agent_mode": "openai"},
        )

        class FakeResponses:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(output_text="G-101 works well for that group size.", id="resp_follow_up")

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)

        response = BookingAgentService(api_key="sk-test", client=fake_client).reply(
            AgentRequest(message="John Doe", session_id="session-follow-up")
        )

        self.assertEqual(response.reply, "G-101 works well for that group size.")
        self.assertIn("John Doe", fake_responses.kwargs["input"])

    @override_settings(OPENAI_AGENT_MODEL="gpt-5.4-nano")
    def test_agent_service_includes_inline_knowledge_sources(self):
        AgentKnowledgeSource.objects.create(
            title="Airport support",
            source_type="inline",
            body="Airport pickup is available by request through the Custom Booking Concierge option.",
        )

        class FakeResponses:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(output_text="I can help.", id="resp_inline")

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)

        BookingAgentService(api_key="sk-test", client=fake_client).reply(
            AgentRequest(message="Can you arrange airport pickup?", session_id="session-inline")
        )

        self.assertIn("Admin and external knowledge sources", fake_responses.kwargs["input"])
        self.assertIn(
            "Airport pickup is available by request through the Custom Booking Concierge option.",
            fake_responses.kwargs["input"],
        )

    @override_settings(OPENAI_AGENT_MODEL="gpt-5.4-nano")
    @patch("bookings.services.requests.get")
    def test_agent_service_supports_github_blob_sources(self, mock_get):
        mock_get.return_value = SimpleNamespace(
            text="- Guests can share special requests in the booking form.\n- Use concierge for custom transport.",
            raise_for_status=lambda: None,
        )
        AgentKnowledgeSource.objects.create(
            title="GitHub runbook",
            source_type="url",
            source_value="https://github.com/pzg8794/MLADIS/blob/main/docs/guest-faq.md",
        )

        class FakeResponses:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(output_text="I can help.", id="resp_github")

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)

        BookingAgentService(api_key="sk-test", client=fake_client).reply(
            AgentRequest(message="Can I add special requests?", session_id="session-github")
        )

        self.assertIn("Guests can share special requests in the booking form.", fake_responses.kwargs["input"])
        self.assertEqual(
            mock_get.call_args.args[0],
            "https://raw.githubusercontent.com/pzg8794/MLADIS/main/docs/guest-faq.md",
        )

    def test_agent_panel_includes_panel_scoped_csrf_token(self):
        response = self.client.get(reverse("bookings:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="csrf-token"')
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")


@override_settings(STORAGES=TEST_STORAGES)
class ModernOpsDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff_user = User.objects.create_user(
            username="ops",
            email="ops@example.com",
            password="password",
            is_staff=True,
        )
        self.item = BookableItem.objects.create(
            name="G-101 Comfort Stay",
            slug="g-101-comfort-stay",
            category=BookingCategory.STAY,
            short_description="3 bedrooms near Santo Domingo Norte.",
            is_active=True,
            is_featured=True,
            airbnb_rating=Decimal("4.93"),
        )
        self.inquiry = BookingInquiry.objects.create(
            item=self.item,
            guest_name="Maria R.",
            email="maria@example.com",
            phone="555-0100",
            check_in=date.today() + timedelta(days=3),
            check_out=date.today() + timedelta(days=6),
            guests=4,
            status=BookingStatus.REVIEWING,
            total_cents=48000,
        )
        DamageDeposit.objects.create(
            inquiry=self.inquiry,
            item=self.item,
            guest_name="Maria R.",
            email="maria@example.com",
            amount_cents=20000,
            status=DepositStatus.REQUIRES_CAPTURE,
        )
        AgentConversation.objects.create(
            session_id="ops-summary",
            item=self.item,
            last_user_message="How does the deposit work?",
            last_agent_reply="The deposit is an authorization hold.",
            question_topic="deposit",
            metadata={"agent_mode": "faq"},
        )

    def test_modern_dashboard_replaces_ops_dashboard_route(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("bookings:ops-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mladis-ops-nav-items")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

    def test_modern_dashboard_redirects_anonymous_users_to_social_login(self):
        response = self.client.get(reverse("bookings:ops-dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("bookings:login"), response["Location"])
        self.assertIn("next=/ops/dashboard/", response["Location"])

    def test_ops_summary_api_returns_react_dashboard_payload(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("bookings:ops-summary-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["reservations"][0]["guest_name"], "Maria R.")
        self.assertEqual(payload["reservations"][0]["status"], "reviewing")
        self.assertEqual(payload["deposits"][0]["status"], "authorized")
        self.assertEqual(payload["agent_questions"][0]["mode"], "faq")
        self.assertIn("G-101 Comfort Stay", {stay["name"] for stay in payload["stays"]})
        self.assertEqual(payload["metrics"][0]["id"], "reservations")


class BookingInquiryViewTests(TestCase):
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_inquiry_creates_record(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Casey",
                "email": "casey@example.com",
                "phone": "555-0101",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(BookingInquiry.objects.count(), 1)
        inquiry = BookingInquiry.objects.get()
        self.assertEqual(inquiry.email_delivery_status, "sent")
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(mail.outbox[0].subject.startswith("(TEST) "))
        self.assertTrue(mail.outbox[1].subject.startswith("(TEST) "))
        self.assertIn(inquiry.request_key, mail.outbox[0].subject)
        self.assertIn("MLADIS_RESERVATION_REQUEST_V1", mail.outbox[0].body)
        self.assertIn("mode=TEST", mail.outbox[0].body)
        self.assertIn(f"request_key={inquiry.request_key}", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_inquiry_records_coupon_and_blacklist_flag(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        CustomerProfile.objects.create(
            name="Blocked Guest",
            email="blocked@example.com",
            segment=ClientSegment.BLACKLISTED,
        )
        coupon = Coupon.objects.get(code="WELCOME25")
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Blocked Guest",
                "email": "blocked@example.com",
                "phone": "555-0102",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
                "coupon_code": "welcome25",
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = BookingInquiry.objects.get()
        coupon.refresh_from_db()
        self.assertEqual(inquiry.coupon_code, "WELCOME25")
        self.assertTrue(inquiry.is_blacklist_flagged)
        self.assertEqual(coupon.redemption_count, 1)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_staff_can_submit_admin_test_reservation(self):
        user = get_user_model().objects.create_user("staff", "staff@example.com", "secret", is_staff=True)
        self.client.force_login(user)
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Staff Test",
                "email": "staff@example.com",
                "phone": "555-0103",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
                "is_admin_test": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = BookingInquiry.objects.get()
        self.assertTrue(inquiry.is_admin_test)
        self.assertEqual(inquiry.total_cents, 0)
        self.assertEqual(inquiry.deposit_cents, 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_redirects_to_deposit_hold_step(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Morgan",
                "email": "morgan@example.com",
                "phone": "555-0104",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=6),
                "guests": 2,
            },
        )

        inquiry = BookingInquiry.objects.get()
        self.assertRedirects(
            response,
            f"{reverse('bookings:home')}?submitted=1&deposit_for={inquiry.id}#deposit",
            fetch_redirect_response=False,
        )
        self.assertEqual(DamageDeposit.objects.count(), 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_inquiry_json_flow_returns_deposit_modal_payload_and_logs_object_event(self):
        item = BookableItem.objects.create(
            name="Test Stay JSON",
            slug="test-stay-json",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        with TemporaryDirectory() as temp_dir, override_settings(MLADIS_DATASTORE_ROOT=temp_dir):
            response = self.client.post(
                reverse("bookings:inquiry-create"),
                data={
                    "item": item.id,
                    "guest_name": "Jordan",
                    "email": "jordan@example.com",
                    "check_in": today + timedelta(days=3),
                    "check_out": today + timedelta(days=5),
                    "guests": 2,
                },
                HTTP_ACCEPT="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )

            self.assertEqual(response.status_code, 201)
            payload = response.json()
            inquiry = BookingInquiry.objects.get()
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["inquiry"]["id"], inquiry.id)
            self.assertEqual(payload["inquiry"]["request_key"], inquiry.request_key)
            self.assertEqual(payload["inquiry"]["display_deposit"], "$200.00 USD")
            self.assertEqual(inquiry.phone, "")

            event_file = Path(temp_dir) / "BOOKINGS" / "_events.jsonl"
            self.assertTrue(event_file.exists())
            self.assertIn("reservation_request.created", event_file.read_text(encoding="utf-8"))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_booking_request_email_can_be_disabled_from_site_settings(self):
        settings_obj = SiteSettings.current()
        settings_obj.request_notifications_email = False
        settings_obj.save(update_fields=["request_notifications_email", "updated_at"])
        item = BookableItem.objects.create(
            name="No Email Stay",
            slug="no-email-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "No Mail",
                "email": "nomail@example.com",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=5),
                "guests": 2,
            },
        )

        self.assertEqual(response.status_code, 302)
        inquiry = BookingInquiry.objects.get()
        self.assertEqual(inquiry.email_delivery_status, EmailDeliveryStatus.PENDING)
        self.assertEqual(mail.outbox, [])


class ReservationPricingAndPaymentHoldTests(TestCase):
    def test_payment_hold_amounts_keep_cent_precision(self):
        deposit = DamageDeposit(amount_cents=99, currency="usd")
        hold = ReservationPaymentHold(amount_cents=99, currency="usd")

        self.assertEqual(deposit.display_amount, "$0.99 USD")
        self.assertEqual(hold.display_amount, "$0.99 USD")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        DEPOSIT_AMOUNT_CENTS=20000,
        DEPOSIT_CURRENCY="usd",
    )
    def test_three_bed_pricing_is_visible_in_request_payload(self):
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101-pricing",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Price Guest",
                "email": "price@example.com",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=5),
                "guests": 3,
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 201)
        inquiry = BookingInquiry.objects.get()
        payload = response.json()["inquiry"]
        self.assertEqual(inquiry.subtotal_cents, 14000)
        self.assertEqual(inquiry.reservation_payment_cents, 14000)
        self.assertEqual(inquiry.deposit_cents, 20000)
        self.assertEqual(inquiry.total_cents, 34000)
        self.assertEqual(payload["display_subtotal"], "$140.00 USD")
        self.assertEqual(payload["display_reservation_payment"], "$140.00 USD")
        self.assertEqual(payload["display_total"], "$340.00 USD")

    def test_three_bed_capacity_is_enforced(self):
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-102",
            slug="g-102-capacity",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Too Many",
                "email": "many@example.com",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=5),
                "guests": 8,
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("guests", response.json()["errors"])

    def test_six_bed_pricing_charges_added_guests_after_twelve(self):
        item = BookableItem.objects.create(
            name="6 Bedrooms Vacation Home & Pool G-All",
            slug="g-all-pricing",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=6,
            beds=6,
            max_guests=14,
            is_active=True,
        )

        quote = ReservationPricingService().quote(item, guests=14, nights=2)

        self.assertEqual(quote.policy.included_guests, 12)
        self.assertEqual(quote.extra_guest_count, 2)
        self.assertEqual(quote.nightly_cents, 12000)
        self.assertEqual(quote.subtotal_cents, 24000)
        self.assertEqual(quote.policy.max_guests, 14)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    def test_unsuccessful_payment_object_does_not_send_confirmation_email(self):
        deposit = DamageDeposit.objects.create(
            guest_name="Pending Guest",
            email="pending@example.com",
            stripe_checkout_session_id="cs_test_pending",
            status=DepositStatus.CHECKOUT_CREATED,
        )
        session = SimpleNamespace(
            id="cs_test_pending",
            payment_intent="",
            payment_status="unpaid",
            status="open",
        )

        payment = PaymentAuthorization(deposit, session)
        payment.persist()
        sent = payment.send_confirmation(BookingEmailService())

        deposit.refresh_from_db()
        self.assertFalse(payment.successful)
        self.assertFalse(sent)
        self.assertEqual(deposit.status, DepositStatus.CHECKOUT_CREATED)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        DEPOSIT_AMOUNT_CENTS=20000,
        DEPOSIT_CURRENCY="usd",
        STRIPE_SECRET_KEY="sk_test_contract",
    )
    @patch("bookings.services.stripe.checkout.Session.create")
    def test_reservation_payment_checkout_creates_manual_capture_hold(self, stripe_session_create):
        stripe_session_create.return_value = SimpleNamespace(
            id="cs_test_payment",
            url="https://checkout.stripe.test/session",
            payment_intent="pi_test_payment",
        )
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101-payment",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        today = timezone.localdate()
        inquiry_response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Payment Guest",
                "email": "payment@example.com",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=5),
                "guests": 2,
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        inquiry_id = inquiry_response.json()["inquiry"]["id"]

        response = self.client.post(
            reverse("bookings:reservation-payment-checkout"),
            data={
                "inquiry_id": inquiry_id,
                "property_rules_accepted": "1",
                "damage_terms_accepted": "1",
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 201)
        hold = ReservationPaymentHold.objects.get()
        self.assertEqual(hold.amount_cents, 12000)
        self.assertEqual(hold.status, DepositStatus.CHECKOUT_CREATED)
        self.assertTrue(hold.capture_after)
        kwargs = stripe_session_create.call_args.kwargs
        self.assertEqual(kwargs["payment_intent_data"]["capture_method"], "manual")
        self.assertEqual(kwargs["line_items"][0]["price_data"]["unit_amount"], 12000)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        DEPOSIT_AMOUNT_CENTS=20000,
        DEPOSIT_CURRENCY="usd",
        STRIPE_SECRET_KEY="sk_test_contract",
    )
    @patch("bookings.services.stripe.checkout.Session.create")
    @patch("bookings.services.stripe.Customer.create")
    def test_combined_payment_checkout_opens_one_stripe_setup_checkout(
        self,
        stripe_customer_create,
        stripe_session_create,
    ):
        stripe_customer_create.return_value = SimpleNamespace(id="cus_test_combined")
        stripe_session_create.return_value = SimpleNamespace(
            id="cs_test_combined",
            url="https://checkout.stripe.com/c/setup/cs_test_combined",
        )
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101-combined",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        today = timezone.localdate()
        inquiry_response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Combined Guest",
                "email": "combined@example.com",
                "check_in": today + timedelta(days=3),
                "check_out": today + timedelta(days=5),
                "guests": 2,
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        inquiry_id = inquiry_response.json()["inquiry"]["id"]

        response = self.client.post(
            reverse("bookings:reservation-payment-checkout"),
            data={
                "inquiry_id": inquiry_id,
                "payment_choice": "combined",
                "property_rules_accepted": "1",
                "damage_terms_accepted": "1",
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(stripe_session_create.call_count, 1)
        payload = response.json()
        self.assertEqual(payload["checkout_url"], "https://checkout.stripe.com/c/setup/cs_test_combined")
        deposit = DamageDeposit.objects.get()
        hold = ReservationPaymentHold.objects.get()
        self.assertEqual(deposit.amount_cents, 20000)
        self.assertEqual(deposit.status, DepositStatus.CHECKOUT_CREATED)
        self.assertEqual(deposit.stripe_checkout_session_id, "cs_test_combined")
        self.assertEqual(deposit.stripe_payment_intent_id, "")
        self.assertEqual(hold.amount_cents, 12000)
        self.assertEqual(hold.status, DepositStatus.CHECKOUT_CREATED)
        self.assertEqual(hold.stripe_checkout_session_id, "cs_test_combined")
        self.assertEqual(hold.stripe_payment_intent_id, "")
        kwargs = stripe_session_create.call_args.kwargs
        self.assertEqual(kwargs["mode"], "setup")
        self.assertEqual(kwargs["customer"], "cus_test_combined")
        self.assertEqual(kwargs["payment_method_types"], ["card"])
        self.assertNotIn("phone_number_collection", kwargs)
        self.assertIn("session_id={CHECKOUT_SESSION_ID}", kwargs["success_url"])
        self.assertEqual(kwargs["metadata"]["booking_inquiry_id"], str(inquiry_id))
        self.assertEqual(kwargs["setup_intent_data"]["metadata"]["booking_inquiry_id"], str(inquiry_id))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        DEPOSIT_AMOUNT_CENTS=20000,
        DEPOSIT_CURRENCY="usd",
        STRIPE_SECRET_KEY="sk_test_contract",
    )
    @patch("bookings.services.stripe.PaymentIntent.create")
    @patch("bookings.services.stripe.SetupIntent.retrieve")
    @patch("bookings.services.stripe.checkout.Session.retrieve")
    def test_combined_setup_success_creates_two_holds_and_redirects_confirmation(
        self,
        stripe_session_retrieve,
        stripe_setup_intent_retrieve,
        stripe_payment_intent_create,
    ):
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101-combined-success",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        inquiry = BookingInquiry.objects.create(
            item=item,
            guest_name="Combined Guest",
            email="combined@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
        )
        ReservationRequestService().prepare(inquiry)
        inquiry.save()
        stripe_session_retrieve.return_value = SimpleNamespace(
            id="cs_test_combined",
            status="complete",
            setup_intent="seti_test_combined",
            metadata=stripe.StripeObject.construct_from({"booking_inquiry_id": str(inquiry.id)}, None),
        )
        stripe_setup_intent_retrieve.return_value = SimpleNamespace(
            id="seti_test_combined",
            status="succeeded",
            payment_method="pm_test_combined",
            customer="cus_test_combined",
            metadata=stripe.StripeObject.construct_from({"booking_inquiry_id": str(inquiry.id)}, None),
        )
        stripe_payment_intent_create.side_effect = [
            SimpleNamespace(id="pi_test_deposit_hold", status="requires_capture"),
            SimpleNamespace(id="pi_test_stay_hold", status="requires_capture"),
        ]
        DamageDeposit.objects.create(
            inquiry=inquiry,
            item=item,
            guest_name="Combined Guest",
            email="combined@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            stripe_checkout_session_id="cs_test_combined",
            status=DepositStatus.CHECKOUT_CREATED,
        )
        ReservationPaymentHold.objects.create(
            inquiry=inquiry,
            item=item,
            guest_name="Combined Guest",
            email="combined@example.com",
            amount_cents=inquiry.reservation_payment_cents,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            stripe_checkout_session_id="cs_test_combined",
            status=DepositStatus.CHECKOUT_CREATED,
        )

        response = self.client.get(
            reverse("bookings:combined-payment-success") + "?session_id=cs_test_combined"
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("bookings:payment-confirmation", kwargs={"token": inquiry.payment_confirmation_token}),
            response["Location"],
        )
        deposit = DamageDeposit.objects.get()
        hold = ReservationPaymentHold.objects.get()
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CAPTURE)
        self.assertEqual(deposit.stripe_payment_intent_id, "pi_test_deposit_hold")
        self.assertEqual(deposit.stripe_checkout_session_id, "cs_test_combined")
        self.assertEqual(hold.status, DepositStatus.REQUIRES_CAPTURE)
        self.assertEqual(hold.stripe_checkout_session_id, "cs_test_combined")
        self.assertEqual(hold.stripe_payment_intent_id, "pi_test_stay_hold")
        self.assertEqual(stripe_payment_intent_create.call_count, 2)
        deposit_kwargs = stripe_payment_intent_create.call_args_list[0].kwargs
        hold_kwargs = stripe_payment_intent_create.call_args_list[1].kwargs
        self.assertEqual(deposit_kwargs["amount"], 20000)
        self.assertEqual(hold_kwargs["amount"], 12000)
        self.assertTrue(deposit_kwargs["off_session"])
        self.assertTrue(hold_kwargs["off_session"])
        self.assertEqual(deposit_kwargs["capture_method"], "manual")
        self.assertEqual(hold_kwargs["capture_method"], "manual")
        self.assertEqual(deposit_kwargs["metadata"]["transaction_type"], "security_deposit_hold")
        self.assertEqual(hold_kwargs["metadata"]["transaction_type"], "reservation_payment_hold")
        self.assertEqual(deposit_kwargs["idempotency_key"], f"mladis-combined-deposit-{deposit.id}-cs_test_combined")
        self.assertEqual(hold_kwargs["idempotency_key"], f"mladis-combined-stay-{hold.id}-cs_test_combined")

        response = self.client.get(
            reverse("bookings:combined-payment-success") + "?session_id=cs_test_combined"
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(stripe_payment_intent_create.call_count, 2)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        STRIPE_SECRET_KEY="sk_test_contract",
    )
    @patch("bookings.services.stripe.checkout.Session.retrieve")
    def test_damage_deposit_success_sends_test_confirmation_to_guest_and_admin(self, stripe_session_retrieve):
        stripe_session_retrieve.return_value = SimpleNamespace(
            id="cs_test_deposit_complete",
            payment_intent="pi_test_deposit_complete",
            payment_status="unpaid",
            status="complete",
        )
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101-deposit-email",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        inquiry = BookingInquiry.objects.create(
            item=item,
            guest_name="Deposit Guest",
            email="deposit@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
        )
        deposit = DamageDeposit.objects.create(
            inquiry=inquiry,
            item=item,
            guest_name="Deposit Guest",
            email="deposit@example.com",
            stripe_checkout_session_id="cs_test_deposit_complete",
            status=DepositStatus.CHECKOUT_CREATED,
        )

        DamageDepositService().sync_checkout_session("cs_test_deposit_complete")

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CAPTURE)
        self.assertIn("email_confirmed:damage_deposit_authorized", deposit.notes)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(mail.outbox[0].subject.startswith("(TEST) "))
        self.assertTrue(mail.outbox[1].subject.startswith("(TEST) "))
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertEqual(mail.outbox[1].to, ["deposit@example.com"])
        self.assertIn("MLADIS_DAMAGE_DEPOSIT_CONFIRMATION_V1", mail.outbox[0].body)
        self.assertIn("transaction_type=security_deposit_hold", mail.outbox[0].body)
        self.assertIn("mode=TEST", mail.outbox[0].body)

        DamageDepositService().sync_checkout_session("cs_test_deposit_complete")
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        STRIPE_SECRET_KEY="sk_test_contract",
    )
    @patch("bookings.services.stripe.checkout.Session.retrieve")
    def test_reservation_payment_success_sends_test_confirmation_to_guest_and_admin(self, stripe_session_retrieve):
        stripe_session_retrieve.return_value = SimpleNamespace(
            id="cs_test_payment_complete",
            payment_intent="pi_test_payment_complete",
            payment_status="unpaid",
            status="complete",
        )
        item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="g-101-payment-email",
            category=BookingCategory.STAY,
            short_description="A test stay.",
            bedrooms=3,
            beds=3,
            max_guests=7,
            is_active=True,
        )
        inquiry = BookingInquiry.objects.create(
            item=item,
            guest_name="Payment Guest",
            email="payment@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
        )
        hold = ReservationPaymentHold.objects.create(
            inquiry=inquiry,
            item=item,
            guest_name="Payment Guest",
            email="payment@example.com",
            amount_cents=12000,
            stripe_checkout_session_id="cs_test_payment_complete",
            status=DepositStatus.CHECKOUT_CREATED,
        )

        ReservationPaymentHoldService().sync_checkout_session("cs_test_payment_complete")

        hold.refresh_from_db()
        self.assertEqual(hold.status, DepositStatus.REQUIRES_CAPTURE)
        self.assertIn("email_confirmed:reservation_payment_authorized", hold.notes)
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue(mail.outbox[0].subject.startswith("(TEST) "))
        self.assertTrue(mail.outbox[1].subject.startswith("(TEST) "))
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertEqual(mail.outbox[1].to, ["payment@example.com"])
        self.assertIn("MLADIS_RESERVATION_PAYMENT_CONFIRMATION_V1", mail.outbox[0].body)
        self.assertIn("transaction_type=reservation_payment_hold", mail.outbox[0].body)
        self.assertIn("capture_rule=manual capture 24 hours before check-in", mail.outbox[0].body)

        ReservationPaymentHoldService().sync_checkout_session("cs_test_payment_complete")
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(STRIPE_SECRET_KEY="sk_test_contract")
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    @patch("bookings.services.stripe.PaymentIntent.capture")
    @patch("bookings.services.stripe.PaymentIntent.retrieve")
    def test_due_reservation_payment_hold_is_reconciled_and_captured(self, retrieve, capture):
        retrieve.return_value = SimpleNamespace(id="pi_due", status="requires_capture")
        capture.return_value = SimpleNamespace(id="pi_due", status="succeeded")
        inquiry = BookingInquiry.objects.create(
            guest_name="Due Guest",
            email="due@example.com",
            check_in=timezone.localdate() + timedelta(days=1),
            check_out=timezone.localdate() + timedelta(days=3),
            guests=1,
            status=BookingStatus.CONFIRMED,
        )
        hold = ReservationPaymentHold.objects.create(
            inquiry=inquiry,
            guest_name=inquiry.guest_name,
            email=inquiry.email,
            amount_cents=99,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_due",
            capture_after=timezone.now() - timedelta(minutes=1),
        )

        result = ReservationPaymentHoldService().process_lifecycle()

        hold.refresh_from_db()
        self.assertEqual(hold.status, DepositStatus.CAPTURED)
        self.assertEqual(result["captured"], 1)
        capture.assert_called_once_with(
            "pi_due",
            idempotency_key=f"mladis-scheduled-stay-capture-{hold.pk}",
        )
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertEqual(mail.outbox[1].to, ["due@example.com"])
        self.assertIn("event=reservation_payment_captured", mail.outbox[0].body)

    @override_settings(STRIPE_SECRET_KEY="sk_test_contract")
    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
    )
    @patch("bookings.services.stripe.PaymentIntent.cancel")
    @patch("bookings.services.stripe.PaymentIntent.retrieve")
    def test_canceled_reservation_releases_open_stay_and_damage_holds(self, retrieve, cancel):
        retrieve.return_value = SimpleNamespace(status="requires_capture")
        inquiry = BookingInquiry.objects.create(
            guest_name="Canceled Guest",
            email="canceled@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=1,
            status=BookingStatus.CANCELED,
        )
        hold = ReservationPaymentHold.objects.create(
            inquiry=inquiry,
            guest_name=inquiry.guest_name,
            email=inquiry.email,
            amount_cents=99,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_stay_canceled",
        )
        deposit = DamageDeposit.objects.create(
            inquiry=inquiry,
            guest_name=inquiry.guest_name,
            email=inquiry.email,
            amount_cents=99,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_deposit_canceled",
        )

        hold_result = ReservationPaymentHoldService().process_lifecycle()
        deposit_result = DamageDepositService().process_lifecycle()

        hold.refresh_from_db()
        deposit.refresh_from_db()
        self.assertEqual(hold.status, DepositStatus.CANCELED)
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertEqual(hold_result["released"], 1)
        self.assertEqual(deposit_result["released"], 1)
        self.assertEqual(cancel.call_count, 2)
        self.assertEqual(len(mail.outbox), 4)
        self.assertIn("event=reservation_payment_released", mail.outbox[0].body)
        self.assertIn("event=damage_deposit_released", mail.outbox[2].body)


class BookingCalendarServiceTests(TestCase):
    def test_build_month_merges_bookings_blocks_and_daily_prices(self):
        item = BookableItem.objects.create(
            name="Calendar Stay",
            slug="calendar-stay",
            category=BookingCategory.STAY,
            short_description="A test calendar stay.",
            starting_price=Decimal("120.00"),
            is_active=True,
        )
        BookingInquiry.objects.create(
            item=item,
            guest_name="Booked Guest",
            email="guest@example.com",
            check_in=date(2026, 6, 10),
            check_out=date(2026, 6, 13),
            guests=2,
            status=BookingStatus.CONFIRMED,
        )
        BookingInquiry.objects.create(
            item=item,
            guest_name="Canceled Guest",
            email="canceled@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 17),
            guests=2,
            status=BookingStatus.CANCELED,
        )
        AvailabilityBlock.objects.create(
            item=item,
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 19),
            reason="Owner stay",
        )
        DailyPriceOverride.objects.create(
            item=item,
            start_date=date(2026, 6, 20),
            end_date=date(2026, 6, 21),
            nightly_price=Decimal("175.00"),
            label="Weekend premium",
        )

        result = BookingCalendarService().build_month(item, month_start=date(2026, 6, 1))

        booked_day = self._calendar_cell(result["weeks"], date(2026, 6, 11))
        blocked_day = self._calendar_cell(result["weeks"], date(2026, 6, 18))
        priced_day = self._calendar_cell(result["weeks"], date(2026, 6, 20))
        available_day = self._calendar_cell(result["weeks"], date(2026, 6, 15))

        self.assertEqual(booked_day["status"], "booked")
        self.assertEqual(len(booked_day["reservations"]), 1)
        self.assertEqual(booked_day["price_display"], "$120.00")

        self.assertEqual(blocked_day["status"], "blocked")
        self.assertEqual(blocked_day["blocks"][0].reason, "Owner stay")

        self.assertEqual(priced_day["status"], "available")
        self.assertEqual(priced_day["price_display"], "$175.00")
        self.assertEqual(priced_day["price_source"], "override")

        self.assertEqual(available_day["status"], "available")
        self.assertEqual(available_day["price_display"], "$120.00")
        self.assertEqual(len(result["reservations"]), 1)

    def _calendar_cell(self, weeks, target_day):
        for week in weeks:
            for cell in week:
                if cell["date"] == target_day:
                    return cell
        self.fail(f"Could not find calendar cell for {target_day}.")


@override_settings(STORAGES=TEST_STORAGES)
class BookableItemCalendarAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="calendar-admin",
            email="calendar-admin@example.com",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)
        self.item = BookableItem.objects.create(
            name="Calendar Admin Stay",
            slug="calendar-admin-stay",
            category=BookingCategory.STAY,
            short_description="A stay used for admin calendar tests.",
            starting_price=Decimal("120.00"),
            is_active=True,
        )

    def test_admin_home_surfaces_business_calendar(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business calendar")
        self.assertContains(response, reverse("bookings:calendar-ops"))
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Reports")

    def test_bookable_item_changelist_surfaces_business_calendar(self):
        response = self.client.get(reverse("admin:bookings_bookableitem_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Business calendar")
        self.assertContains(response, reverse("bookings:calendar-ops"))

    def test_booking_inquiry_add_form_handles_empty_dates(self):
        response = self.client.get(reverse("admin:bookings_bookinginquiry_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add booking inquiry")

    def test_legacy_admin_calendar_redirects_to_modern_calendar(self):
        response = self.client.get(
            reverse("admin:bookings_bookableitem_calendar"),
            data={"item": self.item.pk, "month": "2026-06"},
        )

        self.assertRedirects(
            response,
            f"{reverse('bookings:calendar-ops')}?item={self.item.pk}&date=2026-06-01",
            fetch_redirect_response=False,
        )

    def test_calendar_v2_admin_url_redirects_to_modern_calendar(self):
        response = self.client.get(reverse("admin:bookings_bookableitem_calendar_v2"))

        self.assertRedirects(response, reverse("bookings:calendar-ops"), fetch_redirect_response=False)

    def test_agent_faq_admin_is_registered(self):
        faq = AgentFAQ.objects.create(
            category="booking",
            question="How do I reserve?",
            answer="Use the booking form.",
            keywords="reserve, booking",
        )

        response = self.client.get(reverse("admin:bookings_agentfaq_change", args=[faq.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "How do I reserve?")

    def test_legacy_admin_calendar_post_redirects_without_mutating(self):
        response = self.client.post(
            reverse("admin:bookings_bookableitem_calendar"),
            data={
                "calendar_action": "add_block",
                "month": "2026-06",
                "item": self.item.pk,
                "block-start_date": "2026-06-22",
                "block-end_date": "2026-06-24",
                "block-reason": "Maintenance",
                "block-notes": "Paint work",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('bookings:calendar-ops')}?item={self.item.pk}&date=2026-06-01",
            fetch_redirect_response=False,
        )
        self.assertFalse(AvailabilityBlock.objects.exists())

    def test_legacy_admin_calendar_price_post_redirects_without_mutating(self):
        response = self.client.post(
            reverse("admin:bookings_bookableitem_calendar"),
            data={
                "calendar_action": "add_price",
                "month": "2026-06",
                "item": self.item.pk,
                "price-start_date": "2026-06-27",
                "price-end_date": "2026-06-28",
                "price-nightly_price": "210.00",
                "price-label": "Holiday weekend",
                "price-notes": "High demand dates",
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('bookings:calendar-ops')}?item={self.item.pk}&date=2026-06-01",
            fetch_redirect_response=False,
        )
        self.assertFalse(DailyPriceOverride.objects.exists())


@override_settings(STORAGES=TEST_STORAGES)
class PublicMediaRoutingTests(TestCase):
    def test_uploaded_logo_is_served_from_media_route(self):
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/", GCS_MEDIA_BUCKET=""):
                site_settings = SiteSettings.current()
                upload = SimpleUploadedFile(
                    "logo.jpg",
                    TINY_PNG_BYTES,
                    content_type="image/jpeg",
                )
                site_settings.logo.save("logo.jpg", upload, save=True)

                response = self.client.get(site_settings.logo_display_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), TINY_PNG_BYTES)

    def test_site_logo_setting_reaches_modern_shells_and_auth_pages(self):
        site_settings = SiteSettings.current()
        site_settings.logo_url = "https://cdn.example.test/mladis-logo.png"
        site_settings.save(update_fields=["logo_url", "updated_at"])

        public_response = self.client.get(reverse("bookings:home"))
        self.assertContains(public_response, 'name="mladis-logo-url"')
        self.assertContains(public_response, site_settings.logo_url)

        login_response = self.client.get(reverse("bookings:login"))
        self.assertContains(login_response, f'src="{site_settings.logo_url}"')
        self.assertNotContains(login_response, "<span>M</span>")

    def test_public_site_summary_uses_valid_uploaded_logo(self):
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/", GCS_MEDIA_BUCKET=""):
                site_settings = SiteSettings.current()
                upload = SimpleUploadedFile(
                    "mladis-brand-logo.png",
                    TINY_PNG_BYTES,
                    content_type="image/png",
                )
                site_settings.logo.save("mladis-brand-logo.png", upload, save=True)

                response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("/media/site/mladis-brand-logo", response.json()["logo_url"])

    def test_placeholder_uploaded_logo_does_not_replace_real_logo(self):
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/", GCS_MEDIA_BUCKET=""):
                site_settings = SiteSettings.current()
                upload = SimpleUploadedFile(
                    "mladis-test-logo.png",
                    TINY_PNG_BYTES,
                    content_type="image/png",
                )
                site_settings.logo.save("mladis-test-logo.png", upload, save=True)

                response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("mladis-test-logo", response.json()["logo_url"])
        self.assertIn("mladis-connected-intelligence", response.json()["logo_url"])

    def test_bad_uploaded_logo_does_not_replace_real_logo(self):
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/", GCS_MEDIA_BUCKET=""):
                site_settings = SiteSettings.current()
                upload = SimpleUploadedFile(
                    "mladis-test-logo.png",
                    b"fake-logo-bytes",
                    content_type="image/png",
                )
                site_settings.logo.save("mladis-test-logo.png", upload, save=True)

                public_response = self.client.get(reverse("bookings:home"))
                api_response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertNotContains(public_response, "mladis-test-logo.png")
        self.assertNotIn("mladis-test-logo", api_response.json()["logo_url"])
        self.assertIn("mladis-connected-intelligence", api_response.json()["logo_url"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["owner@example.com"],
        STRIPE_SECRET_KEY="sk_test_123",
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    def test_booking_still_redirects_to_deposit_choice_when_payment_providers_are_configured(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay-direct-checkout",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        today = timezone.localdate()

        response = self.client.post(
            reverse("bookings:inquiry-create"),
            data={
                "item": item.id,
                "guest_name": "Jamie",
                "email": "jamie@example.com",
                "phone": "555-0106",
                "check_in": today + timedelta(days=4),
                "check_out": today + timedelta(days=7),
                "guests": 2,
            },
        )

        inquiry = BookingInquiry.objects.get()
        self.assertRedirects(
            response,
            f"{reverse('bookings:home')}?submitted=1&deposit_for={inquiry.id}#deposit",
            fetch_redirect_response=False,
        )
        self.assertEqual(DamageDeposit.objects.count(), 0)


@override_settings(STORAGES=TEST_STORAGES)
class MarketingPageTests(TestCase):
    def test_home_serves_modern_public_site(self):
        response = self.client.get(reverse("bookings:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")
        self.assertContains(response, 'name="available-languages" content="en,es"')

    def test_site_summary_api_keeps_airbnb_images_and_review_proof(self):
        response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["stays"])
        self.assertIn("https://a0.muscache.com/im/pictures/", payload["stays"][0]["image_url"])
        self.assertIn("Airbnb", payload["stays"][0]["review_label"])
        self.assertIsNone(payload["chatkit"])

    @override_settings(
        OPENAI_API_KEY="sk-test-chatkit",
        OPENAI_CHATKIT_WORKFLOW_ID="wf_test_chatkit",
    )
    def test_site_summary_api_exposes_managed_chatkit_when_workflow_is_configured(self):
        response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["chatkit"]["mode"], "managed")
        self.assertEqual(
            payload["chatkit"]["session_url"],
            f"http://testserver{reverse('bookings:chatkit-session-api')}",
        )

    @override_settings(
        OPENAI_CHATKIT_API_URL="https://chatkit-api.mladis.test/chatkit",
        OPENAI_CHATKIT_DOMAIN_KEY="domain_pk_test123",
    )
    def test_site_summary_api_exposes_custom_chatkit_when_domain_key_is_configured(self):
        response = self.client.get(reverse("bookings:site-summary-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["chatkit"], {
            "mode": "custom",
            "api_url": "https://chatkit-api.mladis.test/chatkit",
            "domain_key": "domain_pk_test123",
        })

    @override_settings(
        OPENAI_API_KEY="sk-test-chatkit",
        OPENAI_CHATKIT_WORKFLOW_ID="wf_test_chatkit",
    )
    @patch("bookings.views._build_openai_client")
    def test_chatkit_session_api_returns_client_secret(self, mock_build_openai_client):
        mock_build_openai_client.return_value.beta.chatkit.sessions.create.return_value = SimpleNamespace(
            id="ckt_sess_123",
            client_secret="cks_test_secret",
            expires_at=1_800_000_000,
        )
        user = get_user_model().objects.create_user(
            username="chatkit-user",
            email="chatkit@example.com",
            password="secret",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("bookings:chatkit-session-api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "client_secret": "cks_test_secret",
                "expires_at": 1_800_000_000,
                "session_id": "ckt_sess_123",
            },
        )
        mock_build_openai_client.assert_called_once_with("sk-test-chatkit")
        mock_build_openai_client.return_value.beta.chatkit.sessions.create.assert_called_once()
        kwargs = mock_build_openai_client.return_value.beta.chatkit.sessions.create.call_args.kwargs
        self.assertEqual(kwargs["workflow"], {"id": "wf_test_chatkit"})
        self.assertEqual(kwargs["user"], f"user:{user.pk}")

    @override_settings(
        OPENAI_API_KEY="sk-test-chatkit",
        OPENAI_CHATKIT_WORKFLOW_ID="wf_test_chatkit",
    )
    def test_chatkit_session_api_rejects_anonymous_requests(self):
        response = self.client.post(reverse("bookings:chatkit-session-api"))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], "authentication_required")

    @override_settings(
        OPENAI_API_KEY="",
        OPENAI_CHATKIT_WORKFLOW_ID="",
    )
    def test_chatkit_session_api_rejects_unconfigured_requests(self):
        user = get_user_model().objects.create_user(
            username="chatkit-unconfigured-user",
            email="chatkit-unconfigured@example.com",
            password="secret",
        )
        self.client.force_login(user)

        response = self.client.post(reverse("bookings:chatkit-session-api"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "ChatKit managed sessions are not configured.")

    def test_legacy_home_redirects_to_modern_site(self):
        response = self.client.get(reverse("bookings:legacy-home"))

        self.assertRedirects(response, reverse("bookings:home"))

    def test_stay_detail_displays_gallery_and_booking_form(self):
        stay = BookableItem.objects.get(slug="mladis-santo-domingo-guest-home")

        response = self.client.get(stay.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        legacy_response = self.client.get(reverse("bookings:legacy-stay-detail", kwargs={"slug": stay.slug}))
        self.assertRedirects(legacy_response, stay.get_absolute_url())

    def test_about_serves_modern_public_site(self):
        response = self.client.get(reverse("bookings:about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

    def test_spanish_language_switches_public_copy(self):
        response = self.client.get(reverse("bookings:home"), HTTP_ACCEPT_LANGUAGE="es")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="available-languages" content="en,es"')
        self.assertContains(response, "MLADIS Modern Stays")


@override_settings(STORAGES=TEST_STORAGES)
class LegalPageTests(TestCase):
    def setUp(self):
        site_settings = SiteSettings.current()
        site_settings.contact_email = "privacy@example.com"
        site_settings.save(update_fields=["contact_email", "updated_at"])

    def test_business_page_renders_public_business_details(self):
        response = self.client.get(reverse("bookings:business"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        legacy_response = self.client.get(reverse("bookings:legacy-business"))
        self.assertRedirects(legacy_response, reverse("bookings:business"))

    def test_privacy_policy_page_renders_modern_shell_and_legacy_details(self):
        response = self.client.get(reverse("bookings:privacy-policy"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        legacy_response = self.client.get(reverse("bookings:legacy-privacy-policy"))
        self.assertRedirects(legacy_response, reverse("bookings:privacy-policy"))

    def test_terms_page_renders_modern_shell_and_legacy_rules(self):
        response = self.client.get(reverse("bookings:terms"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        legacy_response = self.client.get(reverse("bookings:legacy-terms"))
        self.assertRedirects(legacy_response, reverse("bookings:terms"))

    def test_data_deletion_page_renders_modern_shell_and_legacy_instructions(self):
        response = self.client.get(reverse("bookings:data-deletion"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Modern Stays")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        legacy_response = self.client.get(reverse("bookings:legacy-data-deletion"))
        self.assertRedirects(legacy_response, reverse("bookings:data-deletion"))

    def test_data_deletion_callback_returns_meta_confirmation_payload(self):
        response = self.client.post(
            reverse("bookings:data-deletion-callback"),
            data={"signed_request": "test"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["url"], f"http://testserver{reverse('bookings:data-deletion')}")
        self.assertEqual(len(payload["confirmation_code"]), 32)

    def test_data_deletion_callback_gets_instruction_metadata(self):
        response = self.client.get(reverse("bookings:data-deletion-callback"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(
            payload["instructions_url"],
            f"http://testserver{reverse('bookings:data-deletion')}",
        )


@override_settings(STORAGES=TEST_STORAGES)
class AccountReservationTests(TestCase):
    def test_signup_reuses_existing_guest_profile_and_links_reservations(self):
        email = "future-guest@example.com"
        profile = CustomerProfile.objects.create(
            name="Future Guest",
            email=email,
            phone="202-555-0186",
        )
        reservation = BookingInquiry.objects.create(
            customer_profile=profile,
            item=BookableItem.objects.get(slug="mladis-santo-domingo-guest-home"),
            guest_name="Future Guest",
            email=email,
            phone="202-555-0186",
            check_in=timezone.localdate() + timedelta(days=10),
            check_out=timezone.localdate() + timedelta(days=12),
            guests=2,
        )

        response = self.client.post(
            reverse("bookings:signup"),
            data={
                "username": "future-guest",
                "email": email,
                "first_name": "Future",
                "last_name": "Guest",
                "phone": "202-555-0186",
                "password1": "A-strong-pass-2026!",
                "password2": "A-strong-pass-2026!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="future-guest")
        profile.refresh_from_db()
        reservation.refresh_from_db()
        self.assertEqual(CustomerProfile.objects.filter(email__iexact=email).count(), 1)
        self.assertEqual(profile.user, user)
        self.assertEqual(reservation.user, user)
        self.assertEqual(reservation.customer_profile, profile)

    def test_agent_admin_command_provisions_dedicated_superuser(self):
        output = StringIO()

        with patch.dict(os.environ, {"MLADIS_AGENT_ADMIN_PASSWORD": ""}):
            call_command(
                "provision_agent_admin",
                email="agent-admin@mladis.com",
                name="MLADIS Agent",
                phone="631-575-4841",
                username="mladis-agent",
                stdout=output,
            )

        user = get_user_model().objects.get(email="agent-admin@mladis.com")
        access = AdminAccess.objects.get(email="agent-admin@mladis.com")
        profile = CustomerProfile.objects.get(email="agent-admin@mladis.com")
        self.assertEqual(user.username, "mladis-agent")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(access.name, "MLADIS Agent")
        self.assertEqual(access.phone, "631-575-4841")
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.segment, ClientSegment.VIP)
        self.assertIn("Provisioned agent admin", output.getvalue())

    def test_seeded_admin_email_gets_staff_access_after_signup(self):
        response = self.client.post(
            reverse("bookings:signup"),
            data={
                "username": "piter-owner",
                "email": "garciapiterz@gmail.com",
                "first_name": "Piter",
                "last_name": "Garcia",
                "phone": "631-575-4841",
                "password1": "A-strong-pass-2026!",
                "password2": "A-strong-pass-2026!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="piter-owner")
        self.assertTrue(AdminAccess.objects.filter(email="garciapiterz@gmail.com", is_active=True).exists())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_seeded_diana_admin_email_gets_staff_access_after_signup(self):
        response = self.client.post(
            reverse("bookings:signup"),
            data={
                "username": "diana-owner",
                "email": "GarciaBDianaS@gmail.com",
                "first_name": "Diana",
                "last_name": "Garcia",
                "phone": "555-0105",
                "password1": "A-strong-pass-2026!",
                "password2": "A-strong-pass-2026!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="diana-owner")
        self.assertTrue(AdminAccess.objects.filter(email="garciabdianas@gmail.com", is_active=True).exists())
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    @override_settings(SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=[])
    def test_login_page_renders_social_account_options(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "",
                "GOOGLE_OAUTH_CLIENT_SECRET": "",
                "FACEBOOK_OAUTH_CLIENT_ID": "",
                "FACEBOOK_OAUTH_CLIENT_SECRET": "",
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "GITHUB_OAUTH_CLIENT_ID": "",
                "GITHUB_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
                "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": "",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Google")
        self.assertContains(response, "Continue with Facebook")
        self.assertContains(response, "Continue with Microsoft")
        self.assertContains(response, "Continue with GitHub")
        self.assertContains(response, "setup needed")
        self.assertNotContains(response, 'action="/oauth/google/login/"')

    @override_settings(SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=["microsoft"])
    def test_unconfigured_microsoft_is_hidden_from_social_options(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "",
                "GOOGLE_OAUTH_CLIENT_SECRET": "",
                "FACEBOOK_OAUTH_CLIENT_ID": "",
                "FACEBOOK_OAUTH_CLIENT_SECRET": "",
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "GITHUB_OAUTH_CLIENT_ID": "",
                "GITHUB_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
                "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": "microsoft",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Continue with Microsoft")

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="http://127.0.0.1:8000",
        SOCIAL_AUTH_PROVIDER_ORIGINS={},
        SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=[],
        ALLOWED_HOSTS=["127.0.0.1", "testserver"],
    )
    def test_configured_facebook_login_remains_launchable_on_local_origin(self):
        with patch.dict(
            os.environ,
            {
                "FACEBOOK_OAUTH_CLIENT_ID": "facebook-client-id",
                "FACEBOOK_OAUTH_CLIENT_SECRET": "facebook-client-secret",
                "SITE_DOMAIN": "127.0.0.1:8000",
                "SITE_NAME": "MLADIS Local",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"), HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Facebook")
        self.assertContains(response, f'action="{reverse("facebook_login")}"')
        self.assertNotContains(response, "HTTPS required")

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="https://mladis.localhost",
        SOCIAL_AUTH_PROVIDER_ORIGINS={},
        SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=[],
        ALLOWED_HOSTS=["mladis.localhost", "testserver"],
    )
    def test_configured_facebook_login_is_launchable_on_https_origin(self):
        with patch.dict(
            os.environ,
            {
                "FACEBOOK_OAUTH_CLIENT_ID": "facebook-client-id",
                "FACEBOOK_OAUTH_CLIENT_SECRET": "facebook-client-secret",
                "SITE_DOMAIN": "mladis.localhost",
                "SITE_NAME": "MLADIS Local",
            },
            clear=False,
        ):
            response = self.client.get(
                reverse("bookings:login"),
                HTTP_HOST="mladis.localhost",
                secure=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("facebook_login")}"')
        self.assertNotContains(response, "HTTPS required")

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="http://127.0.0.1:8000",
        SOCIAL_AUTH_PROVIDER_ORIGINS={},
        ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"],
    )
    def test_social_auth_canonical_origin_does_not_redirect_login_host(self):
        response = self.client.get(reverse("bookings:login"), HTTP_HOST="localhost:8000")

        self.assertEqual(response.status_code, 200)

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="http://127.0.0.1:8000",
        SOCIAL_AUTH_PROVIDER_ORIGINS={},
        ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"],
    )
    def test_social_auth_canonical_origin_redirects_provider_get(self):
        response = self.client.get(reverse("google_login"), HTTP_HOST="localhost:8000")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], f"http://127.0.0.1:8000{reverse('google_login')}")

    @override_settings(
        SOCIAL_AUTH_CANONICAL_ORIGIN="https://gateway.example.test",
        SOCIAL_AUTH_PROVIDER_ORIGINS={"google": "http://127.0.0.1:8000"},
        ALLOWED_HOSTS=["127.0.0.1", "gateway.example.test", "testserver"],
    )
    def test_social_provider_launch_uses_provider_specific_origin(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "google-client-id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "google-client-secret",
            },
            clear=False,
        ):
            response = self.client.get(
                reverse("bookings:social-provider-launch", kwargs={"provider_id": "google"}),
                HTTP_HOST="gateway.example.test",
                secure=True,
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            f"http://127.0.0.1:8000{reverse('bookings:social-provider-launch', kwargs={'provider_id': 'google'})}",
        )

    def test_github_login_uses_provider_account_picker_prompt(self):
        with patch.dict(
            os.environ,
            {
                "GITHUB_OAUTH_CLIENT_ID": "github-client-id",
                "GITHUB_OAUTH_CLIENT_SECRET": "github-client-secret",
            },
            clear=False,
        ):
            response = self.client.post(reverse("github_login"))

        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertEqual(query["prompt"], ["select_account"])

    def test_login_page_auto_configures_google_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "google-client-id",
                "GOOGLE_OAUTH_CLIENT_SECRET": "google-client-secret",
                "SITE_DOMAIN": "127.0.0.1:8000",
                "SITE_NAME": "MLADIS Local",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("google_login")}"')
        self.assertContains(response, "Choose a social provider for a faster sign-in")
        app = SocialApp.objects.get(provider="google")
        self.assertEqual(app.client_id, "google-client-id")
        self.assertEqual(app.secret, "google-client-secret")
        self.assertTrue(app.sites.filter(id=1).exists())
        site = Site.objects.get(id=1)
        self.assertEqual(site.domain, "127.0.0.1:8000")
        self.assertEqual(site.name, "MLADIS Local")

    @override_settings(SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=[])
    def test_stale_microsoft_social_app_is_ignored_when_env_is_empty(self):
        stale_app = SocialApp.objects.create(
            provider="microsoft",
            name="Microsoft OAuth",
            client_id="demo-microsoft-client",
            secret="demo-microsoft-secret",
        )
        stale_app.sites.add(Site.objects.get(id=1))

        with patch.dict(
            os.environ,
            {
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))
            launch_response = self.client.post(reverse("microsoft_login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Microsoft")
        self.assertContains(response, "disabled")
        self.assertNotContains(response, f'action="{reverse("microsoft_login")}"')
        self.assertEqual(launch_response.status_code, 302)
        self.assertEqual(launch_response["Location"], reverse("bookings:login"))

    def test_stale_microsoft_social_app_stays_disabled_by_default(self):
        stale_app = SocialApp.objects.create(
            provider="microsoft",
            name="Microsoft OAuth",
            client_id="demo-microsoft-client",
            secret="demo-microsoft-secret",
        )
        stale_app.sites.add(Site.objects.get(id=1))

        with patch.dict(
            os.environ,
            {
                "MICROSOFT_OAUTH_CLIENT_ID": "",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
                "SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS": "",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Continue with Microsoft")
        self.assertContains(response, "disabled")
        self.assertNotContains(response, f'action="{reverse("microsoft_login")}"')

    @override_settings(SOCIAL_AUTH_DISABLED_PROVIDERS=[])
    def test_login_page_can_enable_microsoft_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "MICROSOFT_OAUTH_CLIENT_ID": "microsoft-client-id",
                "MICROSOFT_OAUTH_CLIENT_SECRET": "microsoft-client-secret",
                "MICROSOFT_OAUTH_TENANT": "organizations",
                "MICROSOFT_OAUTH_LOGIN_URL": "https://login.microsoftonline.com",
                "MICROSOFT_GRAPH_URL": "https://graph.microsoft.com",
                "SITE_DOMAIN": "127.0.0.1:8000",
                "SITE_NAME": "MLADIS Local",
            },
            clear=False,
        ):
            response = self.client.get(reverse("bookings:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{reverse("microsoft_login")}"')
        app = SocialApp.objects.get(provider="microsoft")
        self.assertEqual(app.client_id, "microsoft-client-id")
        self.assertEqual(app.secret, "microsoft-client-secret")
        self.assertEqual(app.settings["tenant"], "organizations")
        self.assertEqual(app.settings["login_url"], "https://login.microsoftonline.com")
        self.assertEqual(app.settings["graph_url"], "https://graph.microsoft.com")

    def test_unconfigured_google_login_redirects_instead_of_erroring(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_OAUTH_CLIENT_ID": "",
                "GOOGLE_OAUTH_CLIENT_SECRET": "",
                "SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK": "",
            },
            clear=False,
        ):
            response = self.client.post(reverse("google_login"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("bookings:login"))


@override_settings(STORAGES=TEST_STORAGES)
class SocialAccountAdapterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_facebook_without_email_auto_signs_up_using_generated_email(self):
        request = self.factory.get("/accounts/login/")
        sociallogin = SocialLogin(
            user=get_user_model()(),
            account=SocialAccount(
                provider="facebook",
                uid="123456789",
                extra_data={"id": "123456789", "name": "Peter Zac"},
            ),
        )

        adapter = MLADISSocialAccountAdapter()
        adapter.populate_user(request, sociallogin, {"name": "Peter Zac"})
        auto_signup, response = process_auto_signup(request, sociallogin)

        self.assertTrue(auto_signup)
        self.assertIsNone(response)
        self.assertEqual(
            sociallogin.user.email,
            "facebook-123456789@users.mladis.invalid",
        )
        self.assertEqual(
            sociallogin.email_addresses[0].email,
            "facebook-123456789@users.mladis.invalid",
        )
        self.assertFalse(sociallogin.email_addresses[0].verified)

    def test_google_verified_email_connects_existing_verified_user(self):
        app = SocialApp.objects.create(
            provider="google",
            name="Google",
            client_id="google-client",
            secret="google-secret",
        )
        existing_user = get_user_model().objects.create_user(
            username="diana",
            email="garciabdianas@gmail.com",
            password="secret",
        )
        EmailAddress.objects.create(
            user=existing_user,
            email="garciabdianas@gmail.com",
            verified=True,
            primary=True,
        )
        request = self.factory.get("/oauth/google/login/callback/")
        sociallogin = SocialLogin(
            user=get_user_model()(),
            account=SocialAccount(
                provider="google",
                uid="google-diana",
                extra_data={
                    "email": "garciabdianas@gmail.com",
                    "email_verified": True,
                    "given_name": "Diana",
                    "family_name": "Garcia",
                },
            ),
            provider=GoogleProvider(request, app=app),
        )

        adapter = MLADISSocialAccountAdapter()
        adapter.populate_user(
            request,
            sociallogin,
            {
                "email": "garciabdianas@gmail.com",
                "first_name": "Diana",
                "last_name": "Garcia",
            },
        )
        sociallogin.lookup()

        self.assertEqual(sociallogin.user.pk, existing_user.pk)
        self.assertTrue(sociallogin.email_addresses[0].verified)
        self.assertEqual(sociallogin._did_authenticate_by_email, "garciabdianas@gmail.com")

    def test_social_signup_generates_safe_username_for_new_google_user(self):
        request = self.factory.get("/oauth/google/login/callback/")
        sociallogin = SocialLogin(
            user=get_user_model()(username="Usuario"),
            account=SocialAccount(
                provider="google",
                uid="google-new-diana",
                extra_data={
                    "email": "new.diana@example.com",
                    "email_verified": True,
                    "given_name": "Diana",
                    "family_name": "Garcia",
                },
            ),
        )

        adapter = MLADISSocialAccountAdapter()
        adapter.populate_user(
            request,
            sociallogin,
            {
                "email": "new.diana@example.com",
                "first_name": "Diana",
                "last_name": "Garcia",
            },
        )

        self.assertNotIn(sociallogin.user.username.lower(), {"", "user", "usuario"})
        self.assertIn("diana", sociallogin.user.username.lower())
        self.assertTrue(sociallogin.email_addresses[0].verified)

    def test_generated_social_email_skips_confirmation_mail(self):
        request = self.factory.get("/accounts/login/")
        user = get_user_model()(username="peter")
        email_address = EmailAddress(
            user=user,
            email="facebook-123456789@users.mladis.invalid",
            verified=False,
            primary=True,
        )

        should_send = MLADISAccountAdapter().should_send_confirmation_mail(
            request,
            email_address,
            signup=True,
        )

        self.assertFalse(should_send)

    def test_account_dashboard_and_cancel_reservation(self):
        user = get_user_model().objects.create_user(
            username="guest",
            email="guest@example.com",
            password="secret",
        )
        policy = CancellationPolicy.objects.get(slug="standard-24-hour")
        item = BookableItem.objects.get(slug="mladis-santo-domingo-guest-home")
        reservation = BookingInquiry.objects.create(
            user=user,
            item=item,
            guest_name="Guest User",
            email="guest@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
            cancellation_policy=policy,
        )
        self.client.force_login(user)

        dashboard = self.client.get(reverse("bookings:dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "MLADIS Modern Stays")

        account_response = self.client.get(reverse("bookings:account-summary-api"))
        self.assertEqual(account_response.status_code, 200)
        reservations = account_response.json()["reservations"]
        self.assertEqual(reservations[0]["guest_name"], "Guest User")
        self.assertTrue(reservations[0]["can_edit"])

        response = self.client.post(
            reverse("bookings:reservation-cancel", kwargs={"pk": reservation.pk}),
            data={"reason": "Plans changed"},
        )

        self.assertEqual(response.status_code, 302)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, BookingStatus.CANCELED)


@override_settings(STORAGES=TEST_STORAGES)
class InvoicePageTests(TestCase):
    def test_invoice_print_page_renders_logo_ready_invoice(self):
        invoice = Invoice.objects.create(
            recipient_name="Guest User",
            recipient_email="guest@example.com",
            subtotal_cents=50000,
            total_cents=50000,
        )
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description="Test reservation",
            quantity=1,
            amount_cents=50000,
        )

        response = self.client.get(reverse("bookings:invoice-print", kwargs={"token": invoice.public_token}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invoice.invoice_number)
        self.assertContains(response, "$500.00 USD")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["operations@mladis.com"],
    )
    def test_invoice_email_delivers_customer_and_mladis_copies(self):
        invoice = Invoice.objects.create(
            recipient_name="Guest User",
            recipient_email="guest@example.com",
            subtotal_cents=50000,
            total_cents=50000,
        )
        request = RequestFactory().get("/ops/payments/")

        sent = InvoiceEmailService().send_invoice(invoice, request=request)

        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["operations@mladis.com"])
        self.assertEqual(mail.outbox[1].to, ["guest@example.com"])
        self.assertIn("MLADIS_INVOICE_DELIVERY_V1", mail.outbox[0].body)
        self.assertIn(invoice.invoice_number, mail.outbox[0].body)
        self.assertIn(invoice.invoice_number, mail.outbox[1].body)
        self.assertIn(reverse("bookings:invoice-print", args=[invoice.public_token]), mail.outbox[1].body)


@override_settings(STORAGES=TEST_STORAGES)
class OpsFinanceObjectTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="finance-ops",
            email="finance-ops@example.com",
            password="secret",
            is_staff=True,
        )
        self.item = BookableItem.objects.create(
            name="3 Beds Apt, Vacation Home & Pool, G-101",
            slug="finance-stay-g101",
            category=BookingCategory.STAY,
            short_description="A finance test stay.",
            is_active=True,
        )
        self.inquiry = BookingInquiry.objects.create(
            item=self.item,
            guest_name="Maria Rodriguez",
            email="maria@example.com",
            phone="+1 809 555 0169",
            check_in=timezone.localdate() + timedelta(days=4),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
            total_cents=42000,
        )
        self.invoice = Invoice.objects.create(
            inquiry=self.inquiry,
            recipient_name="Maria Rodriguez",
            recipient_email="maria@example.com",
            status=InvoiceStatus.DRAFT,
            subtotal_cents=42000,
            deposit_cents=20000,
            total_cents=62000,
        )
        self.deposit = DamageDeposit.objects.create(
            inquiry=self.inquiry,
            item=self.item,
            guest_name="Maria Rodriguez",
            email="maria@example.com",
            amount_cents=20000,
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.CHECKOUT_CREATED,
            stripe_checkout_session_id="cs_test_deposit",
        )
        self.hold = ReservationPaymentHold.objects.create(
            inquiry=self.inquiry,
            item=self.item,
            guest_name="Maria Rodriguez",
            email="maria@example.com",
            amount_cents=42000,
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_test_stay",
        )

    def test_payments_api_exposes_payment_transaction_objects(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("bookings:ops-payments-api"),
            {"transaction": f"invoice-{self.invoice.pk}"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["transactions"][0]["id"], f"invoice-{self.invoice.pk}")
        self.assertEqual(payload["transactions"][0]["type"], "stay_payment")
        self.assertEqual(payload["detail"]["deposit_history"][0]["label"], "Damage deposit hold")
        self.assertEqual(payload["detail"]["quick_actions"][1]["kind"], "post")
        self.assertEqual(payload["detail"]["quick_actions"][1]["icon"], "paid")

    def test_payments_api_uses_real_payment_holds_when_no_invoices_exist(self):
        self.invoice.delete()
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("bookings:ops-payments-api"),
            {"transaction": f"payment-hold-{self.hold.pk}"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "api")
        self.assertEqual(payload["total_results"], 1)
        self.assertEqual(payload["rows"][0]["id"], f"payment-hold-{self.hold.pk}")
        self.assertFalse(payload["rows"][0]["is_mock"])
        self.assertEqual(payload["rows"][0]["status"], "Authorized")
        self.assertEqual(payload["detail"]["reservation"]["id"], self.inquiry.pk)
        self.assertEqual(payload["detail"]["guest_detail"]["email"], self.inquiry.email)
        self.assertEqual(payload["detail"]["deposit_history"][0]["id"], self.deposit.pk)
        self.assertEqual(payload["detail"]["invoice"]["number"], "Not generated")
        self.assertFalse(payload["detail"]["invoice"]["can_download"])
        open_reservation = next(
            action for action in payload["detail"]["quick_actions"] if action["label"] == "Open reservation"
        )
        self.assertEqual(open_reservation["kind"], "link")
        self.assertIn(f"reservation={self.inquiry.pk}", open_reservation["url"])

    def test_payments_api_exposes_structured_invoice_and_reservation_links(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("bookings:ops-payments-api"),
            {"transaction": f"invoice-{self.invoice.pk}"},
        )

        self.assertEqual(response.status_code, 200)
        detail = response.json()["detail"]
        self.assertEqual(
            detail["invoice"]["view_url"],
            reverse("bookings:invoice-print", args=[self.invoice.public_token]),
        )
        self.assertFalse(detail["invoice"]["can_download"])
        self.assertEqual(
            detail["invoice"]["disabled_reason"],
            "Invoice download will be available after invoice document generation is implemented.",
        )
        self.assertEqual(
            detail["reservation"]["view_url"],
            reverse("admin:bookings_bookinginquiry_change", args=[self.inquiry.pk]),
        )
        self.assertIn(f"reservation={self.inquiry.pk}", detail["reservation"]["selectable_url"])
        self.assertEqual(detail["deposit_history"][0]["id"], self.deposit.pk)
        self.assertEqual(detail["deposit_history"][0]["type"], "damage_deposit")
        refund = next(action for action in detail["quick_actions"] if action["label"] == "Issue refund")
        self.assertEqual(refund["kind"], "disabled")
        self.assertEqual(
            refund["disabled_reason"],
            "Refund workflow will be implemented in a dedicated refund-actions pass.",
        )

    def test_payment_invoice_projection_points_to_working_invoice_view(self):
        self.client.force_login(self.staff)
        payload = self.client.get(
            reverse("bookings:ops-payments-api"),
            {"transaction": f"invoice-{self.invoice.pk}"},
        ).json()

        response = self.client.get(payload["detail"]["invoice"]["view_url"])

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invoice.invoice_number)

    def test_payments_api_keeps_transaction_detail_closed_without_selection(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("bookings:ops-payments-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_transaction_id"], "")
        self.assertIsNone(payload["detail"])

    def test_payments_api_opens_transaction_detail_when_selected(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("bookings:ops-payments-api"),
            {"transaction": f"invoice-{self.invoice.pk}"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_transaction_id"], f"invoice-{self.invoice.pk}")
        self.assertEqual(payload["detail"]["id"], f"invoice-{self.invoice.pk}")

    def test_payments_api_search_filters_rows(self):
        Invoice.objects.create(
            recipient_name="John Smith",
            recipient_email="john@example.com",
            status=InvoiceStatus.PAID,
            subtotal_cents=18000,
            total_cents=18000,
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse("bookings:ops-payments-api"), {"search": "John"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_results"], 1)
        self.assertEqual(payload["rows"][0]["guest"], "John Smith")

    def test_payments_api_status_channel_and_method_filters_rows(self):
        Invoice.objects.create(
            recipient_name="John Smith",
            recipient_email="john@example.com",
            status=InvoiceStatus.PAID,
            subtotal_cents=18000,
            total_cents=18000,
        )
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("bookings:ops-payments-api"),
            {"status": "Pending", "channel": "Direct Website", "method": "Card hold"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_results"], 1)
        self.assertEqual(payload["rows"][0]["id"], f"invoice-{self.invoice.pk}")
        self.assertIn("statuses", payload["filter_options"])
        self.assertIn("channels", payload["filter_options"])
        self.assertIn("methods", payload["filter_options"])

    def test_payments_api_pagination_returns_requested_page(self):
        other = Invoice.objects.create(
            recipient_name="Ana Lopez",
            recipient_email="ana@example.com",
            status=InvoiceStatus.PAID,
            subtotal_cents=18000,
            total_cents=18000,
            issue_date=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse("bookings:ops-payments-api"), {"page": 2, "page_size": 1})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pagination"]["page"], 2)
        self.assertEqual(payload["pagination"]["page_size"], 1)
        self.assertEqual(payload["pagination"]["total_pages"], 2)
        self.assertEqual(payload["rows"][0]["id"], f"invoice-{self.invoice.pk}")
        self.assertNotEqual(payload["rows"][0]["id"], f"invoice-{other.pk}")

    def test_payments_api_page_change_clears_stale_selected_transaction(self):
        other = Invoice.objects.create(
            recipient_name="Ana Lopez",
            recipient_email="ana@example.com",
            status=InvoiceStatus.PAID,
            subtotal_cents=18000,
            total_cents=18000,
            issue_date=timezone.localdate() + timedelta(days=1),
        )
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse("bookings:ops-payments-api"),
            {
                "page": 2,
                "page_size": 1,
                "transaction": f"invoice-{other.pk}",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pagination"]["page"], 2)
        self.assertEqual(payload["selected_transaction_id"], "")
        self.assertIsNone(payload["detail"])

    def test_payment_action_mark_paid_updates_invoice_object(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("bookings:ops-payment-action-api", args=[f"invoice-{self.invoice.pk}", "mark-paid"]),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, InvoiceStatus.PAID)
        self.assertEqual(self.invoice.email_status, EmailDeliveryStatus.SENT)
        self.assertEqual(response.json()["transaction"]["status"], InvoiceStatus.PAID)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_INQUIRY_RECIPIENTS=["operations@mladis.com"],
    )
    def test_payment_action_send_invoice_updates_invoice_sent_state(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("bookings:ops-payment-action-api", args=[f"invoice-{self.invoice.pk}", "send-invoice"]),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, InvoiceStatus.SENT)
        self.assertEqual(self.invoice.email_status, EmailDeliveryStatus.SENT)
        self.assertIsNotNone(self.invoice.sent_at)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["operations@mladis.com"])
        self.assertEqual(mail.outbox[1].to, ["maria@example.com"])

    def test_transaction_documents_are_available_to_customer_and_admin_accounts(self):
        customer = get_user_model().objects.create_user(
            username="maria-account",
            email=self.inquiry.email,
            password="secret",
        )
        self.inquiry.user = customer
        self.inquiry.save(update_fields=["user", "updated_at"])
        self.client.force_login(customer)

        account_payload = self.client.get(reverse("bookings:account-summary-api")).json()

        document_ids = {document["id"] for document in account_payload["transaction_documents"]}
        self.assertIn(f"invoice-{self.invoice.pk}", document_ids)
        self.assertIn(f"payment-confirmation-{self.inquiry.pk}", document_ids)
        confirmation = next(
            document
            for document in account_payload["transaction_documents"]
            if document["kind"] == "payment_confirmation"
        )
        self.assertIn(str(self.inquiry.payment_confirmation_token), confirmation["view_url"])
        self.assertTrue(confirmation["download_url"].endswith("?download=1"))
        self.assertEqual(confirmation["display_amount"], "$620.00 USD")

        self.client.force_login(self.staff)
        admin_payload = self.client.get(reverse("bookings:ops-admin-api")).json()
        admin_document_ids = {document["id"] for document in admin_payload["transaction_documents"]}
        self.assertIn(f"invoice-{self.invoice.pk}", admin_document_ids)
        self.assertIn(f"payment-confirmation-{self.inquiry.pk}", admin_document_ids)

    def test_payment_confirmation_uses_transaction_amounts_instead_of_inquiry_estimate(self):
        self.inquiry.total_cents = 0
        self.inquiry.save(update_fields=["total_cents", "updated_at"])
        self.deposit.amount_cents = 0
        self.deposit.status = DepositStatus.REQUIRES_CAPTURE
        self.deposit.save(update_fields=["amount_cents", "status", "updated_at"])
        self.hold.amount_cents = 99
        self.hold.save(update_fields=["amount_cents", "updated_at"])

        response = self.client.get(
            reverse(
                "bookings:payment-confirmation",
                kwargs={"token": self.inquiry.payment_confirmation_token},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "$0.99 USD")
        self.assertContains(response, "Total authorized today")
        self.assertNotContains(response, "Total paid today")

    def test_payment_action_unsupported_returns_400(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("bookings:ops-payment-action-api", args=[f"invoice-{self.invoice.pk}", "capture-now"]),
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_deposits_api_exposes_deposit_hold_objects(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("bookings:ops-deposits-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        row_ids = {row["id"] for row in payload["rows"]}
        self.assertIn(f"damage-{self.deposit.pk}", row_ids)
        self.assertIn(f"stay-{self.hold.pk}", row_ids)
        selected = next(row for row in payload["rows"] if row["id"] == f"damage-{self.deposit.pk}")
        self.assertEqual(selected["guest_name"], "Maria Rodriguez")
        self.assertEqual(selected["reservation"]["key"], self.inquiry.request_key)
        self.assertTrue(selected["timeline"])
        self.assertTrue(selected["payment_attempts"])
        self.assertTrue(selected["actions"]["can_approve"])

    def test_deposits_api_exposes_structured_relationships_and_honest_receipt_state(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("bookings:ops-deposits-api"))

        self.assertEqual(response.status_code, 200)
        selected = next(
            row
            for row in response.json()["rows"]
            if row["id"] == f"damage-{self.deposit.pk}"
        )
        self.assertEqual(selected["reservation"]["id"], self.inquiry.pk)
        self.assertEqual(selected["reservation"]["request_key"], self.inquiry.request_key)
        self.assertIn(
            f"reservation={self.inquiry.pk}",
            selected["reservation"]["selectable_url"],
        )
        self.assertEqual(selected["guest"]["name"], "Maria Rodriguez")
        payment_attempt = selected["payment_attempts"][0]
        self.assertTrue(payment_attempt["can_open_payment"])
        self.assertIn(
            f"transaction=invoice-{self.invoice.pk}",
            payment_attempt["payment_url"],
        )
        self.assertFalse(selected["receipt"]["can_generate"])
        self.assertEqual(
            selected["receipt"]["disabled_reason"],
            "Deposit receipt generation will be implemented in a dedicated receipt-document pass.",
        )

    def test_deposit_action_approve_updates_selected_hold(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("bookings:ops-deposit-hold-action-api", args=[f"damage-{self.deposit.pk}", "approve"])
        )

        self.assertEqual(response.status_code, 200)
        self.deposit.refresh_from_db()
        self.assertEqual(self.deposit.status, DepositStatus.REQUIRES_CAPTURE)
        self.assertEqual(response.json()["hold"]["id"], f"damage-{self.deposit.pk}")
        self.assertEqual(response.json()["hold"]["status"], DepositStatus.REQUIRES_CAPTURE)

    def test_deposit_action_release_updates_selected_hold_without_money_capture(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse(
                "bookings:ops-deposit-hold-action-api",
                args=[f"stay-{self.hold.pk}", "release"],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.hold.refresh_from_db()
        self.assertEqual(self.hold.status, DepositStatus.CANCELED)
        self.assertEqual(response.json()["hold"]["status"], DepositStatus.CANCELED)

    def test_deposit_action_request_guest_action_records_note(self):
        self.deposit.status = DepositStatus.NEW
        self.deposit.save(update_fields=["status", "updated_at"])
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse(
                "bookings:ops-deposit-hold-action-api",
                args=[f"damage-{self.deposit.pk}", "request-guest-action"],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.deposit.refresh_from_db()
        self.assertEqual(self.deposit.status, DepositStatus.REQUIRES_CONFIGURATION)
        self.assertIn("Guest action requested by finance-ops", self.deposit.notes)


@override_settings(STORAGES=TEST_STORAGES)
class OpsDashboardTests(TestCase):
    def test_ops_dashboard_shows_metrics_for_staff(self):
        staff = get_user_model().objects.create_user("ops", "ops@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        PageVisit.objects.create(path="/")
        AgentConversation.objects.create(
            session_id="abc",
            last_user_message="What is the price?",
            last_agent_reply="Setup mode.",
            question_topic="pricing",
        )

        response = self.client.get(reverse("bookings:ops-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mladis-ops-nav-items")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        summary_response = self.client.get(reverse("bookings:ops-summary-api"))
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.json()["agent_questions"][0]["topic"], "pricing")

    def test_legacy_ops_dashboard_redirects_to_modern_staff_dashboard(self):
        staff = get_user_model().objects.create_user("legacy-ops", "legacy@example.com", "secret", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("bookings:ops-legacy-dashboard"))

        self.assertRedirects(response, reverse("bookings:ops-dashboard"))

    def test_ops_reports_show_graphs_for_staff(self):
        staff = get_user_model().objects.create_user("reports", "reports@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        PageVisit.objects.create(path="/stays/test/")
        AgentConversation.objects.create(
            session_id="report-abc",
            last_user_message="Is there parking?",
            last_agent_reply="Setup mode.",
            question_topic="amenities",
        )
        BookingInquiry.objects.create(
            guest_name="Graph Guest",
            email="graph@example.com",
            check_in=timezone.localdate() + timedelta(days=5),
            check_out=timezone.localdate() + timedelta(days=7),
            guests=2,
        )

        response = self.client.get(reverse("bookings:ops-reports"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mladis-ops-nav-items")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        api_response = self.client.get(reverse("bookings:ops-reports-api"))
        self.assertEqual(api_response.status_code, 200)
        payload = api_response.json()
        chart_titles = [chart["title"] for chart in payload["charts"]]
        self.assertIn("Reservations by status", chart_titles)
        self.assertIn("Agent question topics", chart_titles)
        self.assertIn("Feedback by source", chart_titles)
        self.assertIn("Visits by day", chart_titles)

        legacy_response = self.client.get(reverse("bookings:ops-legacy-reports"))
        self.assertRedirects(legacy_response, reverse("bookings:ops-reports"))
        self.assertEqual(payload["calendar_url"], reverse("bookings:calendar-ops"))

    def test_modern_ops_customer_deposit_and_agent_sections_use_react_shell_and_apis(self):
        staff = get_user_model().objects.create_user("ops-tabs", "tabs@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        item = BookableItem.objects.create(
            name="G-101",
            slug="g-101-ops-tabs",
            category=BookingCategory.STAY,
            short_description="Modern ops test stay.",
        )
        profile = CustomerProfile.objects.create(
            name="VIP Guest",
            email="vip-tabs@example.com",
            segment=ClientSegment.VIP,
            marketing_consent_status=MarketingConsentStatus.OPTED_IN,
        )
        inquiry = BookingInquiry.objects.create(
            customer_profile=profile,
            item=item,
            guest_name="VIP Guest",
            email="vip-tabs@example.com",
            check_in=timezone.localdate() + timedelta(days=4),
            check_out=timezone.localdate() + timedelta(days=6),
            guests=2,
        )
        DamageDeposit.objects.create(
            inquiry=inquiry,
            item=item,
            guest_name="VIP Guest",
            email="vip-tabs@example.com",
            status=DepositStatus.REQUIRES_CAPTURE,
        )
        AgentFAQ.objects.create(
            question="How does the deposit work?",
            answer="The deposit is a secure authorization hold.",
            category="deposit",
            keywords="deposit,hold",
        )
        AgentConversation.objects.create(
            session_id="ops-tabs-agent",
            item=item,
            last_user_message="How does the deposit work?",
            last_agent_reply="It is a secure authorization hold.",
            question_topic="deposit",
            metadata={"agent_mode": "faq"},
        )

        AdminAccess.objects.create(
            email=staff.email,
            name="Ops Staff",
            phone="+1 555 0100",
            notes="Primary operations access record.",
            is_active=True,
        )
        site_settings = SiteSettings.current()
        site_settings.request_notifications_email = True
        site_settings.property_rules_body = "Registered guests only.\nNo smoking indoors."
        site_settings.save(update_fields=["request_notifications_email", "property_rules_body", "updated_at"])

        for route_name in ["ops-guests", "ops-customers", "ops-deposits", "ops-agent", "ops-admin", "ops-settings", "ops-reports"]:
            response = self.client.get(reverse(f"bookings:{route_name}"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "mladis-ops-nav-items")
            if route_name in {"ops-deposits", "ops-admin", "ops-settings", "ops-reports"}:
                self.assertContains(response, "frontend/modern-dashboard/assets/app.js")
            if route_name == "ops-agent":
                self.assertTemplateUsed(response, "bookings/modern_ops_agent.html")
                self.assertContains(response, 'class="ops-agent-page"')
                self.assertNotContains(response, "frontend/modern-dashboard/assets/app.js")

        customers_payload = self.client.get(reverse("bookings:ops-customers-api")).json()
        self.assertEqual(customers_payload["rows"][0]["identity"]["name"], "VIP Guest")
        self.assertEqual(customers_payload["rows"][0]["segment"]["value"], "vip")

        guests_payload = self.client.get(reverse("bookings:ops-guests-api")).json()
        self.assertEqual(guests_payload["rows"][0]["identity"]["name"], "VIP Guest")
        self.assertEqual(guests_payload["rows"][0]["segment"]["value"], "vip")
        self.assertEqual(guests_payload["rows"][0]["stays"][0]["reservation_key"], inquiry.request_key)
        self.assertEqual(guests_payload["filter_options"]["statuses"][0]["value"], "active")
        self.assertEqual(guests_payload["filter_options"]["sources"][0]["value"], ContactSource.DIRECT)
        guests_search_payload = self.client.get(reverse("bookings:ops-guests-api"), {"search": "VIP"}).json()
        self.assertEqual(len(guests_search_payload["rows"]), 1)
        guests_blocked_payload = self.client.get(reverse("bookings:ops-guests-api"), {"status": "blocked"}).json()
        self.assertEqual(guests_blocked_payload["rows"], [])
        draft_response = self.client.post(
            reverse("bookings:ops-guest-messages-api", args=[profile.pk]),
            data=json.dumps({"body": "Draft arrival note", "confirmed": False}),
            content_type="application/json",
        )
        self.assertEqual(draft_response.status_code, 200)
        self.assertEqual(draft_response.json()["message"]["status"], "drafted")
        sent_response = self.client.post(
            reverse("bookings:ops-guest-messages-api", args=[profile.pk]),
            data=json.dumps({"body": "Confirmed arrival note", "confirmed": True}),
            content_type="application/json",
        )
        self.assertEqual(sent_response.status_code, 200)
        self.assertEqual(sent_response.json()["message"]["status"], "sent")

        deposits_payload = self.client.get(reverse("bookings:ops-deposits-api")).json()
        self.assertEqual(deposits_payload["rows"][0]["guest_name"], "VIP Guest")
        self.assertEqual(deposits_payload["rows"][0]["status"], DepositStatus.REQUIRES_CAPTURE)

        agent_payload = self.client.get(reverse("bookings:ops-agent-api")).json()
        self.assertEqual(agent_payload["conversations"][0]["topic"], "deposit")
        self.assertIn("How does the deposit work?", [row["question"] for row in agent_payload["faqs"]])

        admin_payload = self.client.get(reverse("bookings:ops-admin-api")).json()
        self.assertEqual(admin_payload["rows"][0]["email"], staff.email)
        self.assertEqual(admin_payload["rows"][0]["access_status"], "Protected")
        self.assertEqual(admin_payload["role_options"][0]["label"], "All")

        settings_payload = self.client.get(reverse("bookings:ops-settings-api")).json()
        section_ids = [section["id"] for section in settings_payload["sections"]]
        self.assertIn("brand", section_ids)
        self.assertIn("documents", section_ids)
        self.assertIn("providers", section_ids)
        self.assertIn("site_settings", settings_payload["admin_urls"])

    def test_guest_workspace_collapses_duplicate_profiles_into_unique_real_guests(self):
        staff = get_user_model().objects.create_user("guest-ops", "guest-ops@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        item = BookableItem.objects.create(
            name="G-101",
            slug="g-101-unique-guests",
            category=BookingCategory.STAY,
            short_description="Unique guest test stay.",
        )
        first_profile = CustomerProfile.objects.create(
            name="Primary Guest",
            email="primary.unique@example.com",
            phone="(201) 555-0123",
            source=ContactSource.DIRECT,
        )
        duplicate_profile = CustomerProfile.objects.create(
            name="Imported Guest",
            email="imported.unique@example.com",
            phone="201-555-0123",
            source=ContactSource.AIRBNB,
        )
        first_inquiry = BookingInquiry.objects.create(
            customer_profile=first_profile,
            item=item,
            guest_name="Primary Guest",
            email=first_profile.email,
            phone=first_profile.phone,
            check_in=timezone.localdate() + timedelta(days=3),
            check_out=timezone.localdate() + timedelta(days=5),
            guests=2,
        )
        duplicate_inquiry = BookingInquiry.objects.create(
            customer_profile=duplicate_profile,
            item=item,
            guest_name="Imported Guest",
            email=duplicate_profile.email,
            phone=duplicate_profile.phone,
            check_in=timezone.localdate() + timedelta(days=8),
            check_out=timezone.localdate() + timedelta(days=10),
            guests=2,
        )

        workspace = GuestService().workspace_payload()
        guest_payload = next(row for row in workspace["rows"] if set(row["source_profile_ids"]) == {first_profile.pk, duplicate_profile.pk})
        self.assertEqual(guest_payload["source_profile_count"], 2)
        self.assertCountEqual(guest_payload["source_profile_ids"], [first_profile.pk, duplicate_profile.pk])
        self.assertEqual(guest_payload["row"]["past_stays"], 2)
        self.assertCountEqual(
            [stay["reservation_key"] for stay in guest_payload["stays"]],
            [first_inquiry.request_key, duplicate_inquiry.request_key],
        )
        self.assertEqual(guest_payload["messages"]["items"], [])

        guests_api_payload = self.client.get(reverse("bookings:ops-guests-api")).json()
        customers_api_payload = self.client.get(reverse("bookings:ops-customers-api")).json()
        api_guest = next(row for row in guests_api_payload["rows"] if set(row["source_profile_ids"]) == {first_profile.pk, duplicate_profile.pk})
        compatibility_guest = next(row for row in customers_api_payload["rows"] if set(row["source_profile_ids"]) == {first_profile.pk, duplicate_profile.pk})
        self.assertEqual(compatibility_guest["source_profile_ids"], api_guest["source_profile_ids"])

    def test_guest_workspace_includes_unlinked_real_reservation_guests(self):
        staff = get_user_model().objects.create_user("reservation-guest-ops", "reservation-guest-ops@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        item = BookableItem.objects.create(
            name="G-102",
            slug="g-102-reservation-guests",
            category=BookingCategory.STAY,
            short_description="Reservation-backed guest test stay.",
        )
        inquiry = BookingInquiry.objects.create(
            customer_profile=None,
            item=item,
            guest_name="Reservation Only Guest",
            email="reservation.only@example.com",
            phone="(809) 555-0188",
            check_in=timezone.localdate() + timedelta(days=6),
            check_out=timezone.localdate() + timedelta(days=8),
            guests=2,
            total_cents=42000,
        )

        workspace = GuestService().workspace_payload()
        guest_payload = next(row for row in workspace["rows"] if row["identity"]["name"] == "Reservation Only Guest")

        self.assertEqual(guest_payload["source_profile_ids"], [])
        self.assertEqual(guest_payload["source_profile_count"], 0)
        self.assertEqual(guest_payload["row"]["past_stays"], 1)
        self.assertEqual(guest_payload["row"]["total_spend"]["amount_cents"], 42000)
        self.assertEqual(guest_payload["stays"][0]["reservation_key"], inquiry.request_key)

        response = self.client.get(reverse("bookings:ops-guests"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reservation Only Guest")
        self.assertNotContains(response, "257")

    def test_modern_guests_page_uses_real_filters_pagination_and_export(self):
        staff = get_user_model().objects.create_user("guest-page-ops", "guest-page-ops@example.com", "secret", is_staff=True)
        self.client.force_login(staff)
        CustomerProfile.objects.create(name="Alpha Guest", email="alpha@example.com", source=ContactSource.DIRECT)
        CustomerProfile.objects.create(name="Beta Guest", email="beta@example.com", source=ContactSource.AIRBNB)
        CustomerProfile.objects.create(name="Blocked Guest", email="blocked@example.com", segment=ClientSegment.BLACKLISTED, source=ContactSource.MANUAL)

        page_two = self.client.get(reverse("bookings:ops-guests"), {"page": "2", "page_size": "2"})
        self.assertEqual(page_two.status_code, 200)
        self.assertContains(page_two, "Showing 3 to 4 of")
        self.assertContains(page_two, "real guests")

        filtered = self.client.get(reverse("bookings:ops-guests"), {"source": ContactSource.AIRBNB})
        self.assertContains(filtered, "Beta Guest")
        self.assertNotContains(filtered, "Alpha Guest")

        blocked = self.client.get(reverse("bookings:ops-guests"), {"status": "blocked"})
        self.assertContains(blocked, "Blocked Guest")
        self.assertNotContains(blocked, "Beta Guest")

        exported = self.client.get(reverse("bookings:ops-guests"), {"export": "csv"})
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported["Content-Type"], "text/csv")
        self.assertIn("Alpha Guest", exported.content.decode())

    @override_settings(SOCIAL_AUTH_CANONICAL_ORIGIN="https://mladis.com", SOCIAL_AUTH_PROVIDER_ORIGINS={})
    def test_oauth_diagnostics_displays_callback_urls(self):
        staff = get_user_model().objects.create_user("oauth", "oauth@example.com", "secret", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("bookings:oauth-diagnostics"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OAuth setup")
        self.assertContains(response, "https://mladis.com/oauth/google/login/callback/")
        self.assertContains(response, "https://mladis.com/oauth/facebook/login/callback/")
        self.assertContains(response, "https://mladis.com/oauth/github/login/callback/")


class DamageDepositTests(TestCase):
    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_mladis")
    @patch("bookings.views.stripe.Webhook.construct_event")
    def test_stripe_webhook_accepts_nested_stripe_objects(self, mock_construct_event):
        deposit = DamageDeposit.objects.create(
            guest_name="Webhook Canary",
            email="webhook@example.com",
            payment_provider=DepositProvider.STRIPE,
            stripe_payment_intent_id="pi_webhook_canary",
            status=DepositStatus.REQUIRES_CAPTURE,
        )
        mock_construct_event.return_value = stripe.StripeObject.construct_from(
            {
                "type": "payment_intent.canceled",
                "data": {"object": {"id": "pi_webhook_canary"}},
            },
            "sk_test_mladis",
        )

        response = self.client.post(
            reverse("bookings:stripe-webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )

        self.assertEqual(response.status_code, 200)
        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CANCELED)

    @override_settings(STRIPE_SECRET_KEY="", STRIPE_TEST_SECRET_KEY="", STRIPE_LIVE_SECRET_KEY="")
    def test_deposit_checkout_without_stripe_key_records_configuration_status(self):
        item = BookableItem.objects.create(
            name="Test Stay",
            slug="test-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Jordan",
                "email": "jordan@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.amount_cents, 20000)
        self.assertEqual(deposit.payment_provider, DepositProvider.STRIPE)
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CONFIGURATION)

    @override_settings(STRIPE_SECRET_KEY="", STRIPE_TEST_SECRET_KEY="", STRIPE_LIVE_SECRET_KEY="")
    def test_deposit_checkout_json_without_stripe_key_returns_modal_error(self):
        item = BookableItem.objects.create(
            name="Test Stay JSON",
            slug="test-stay-json",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Jordan",
                "email": "jordan@example.com",
                "payment_provider": DepositProvider.STRIPE,
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["provider"], DepositProvider.STRIPE)
        self.assertEqual(payload["status"], DepositStatus.REQUIRES_CONFIGURATION)
        self.assertIn("Stripe is not configured", payload["message"])

    @override_settings(STRIPE_SECRET_KEY="sk_test_mladis")
    @patch("bookings.services.stripe.checkout.Session.create")
    def test_deposit_checkout_json_returns_stripe_checkout_url(self, mock_session_create):
        item = BookableItem.objects.create(
            name="Stripe Stay Configured",
            slug="stripe-stay-configured",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        mock_session_create.return_value = SimpleNamespace(
            id="cs_test_123",
            url="https://checkout.stripe.com/c/pay/cs_test_123",
            payment_intent="pi_123",
        )

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Jordan",
                "email": "jordan@example.com",
                "payment_provider": DepositProvider.STRIPE,
            },
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["checkout_url"], "https://checkout.stripe.com/c/pay/cs_test_123")
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.payment_provider, DepositProvider.STRIPE)
        self.assertEqual(deposit.status, DepositStatus.CHECKOUT_CREATED)
        self.assertEqual(deposit.checkout_url, "https://checkout.stripe.com/c/pay/cs_test_123")

    @override_settings(PAYPAL_CLIENT_ID="", PAYPAL_CLIENT_SECRET="")
    def test_paypal_checkout_without_credentials_records_configuration_status(self):
        item = BookableItem.objects.create(
            name="PayPal Stay",
            slug="paypal-stay",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Jordan",
                "email": "jordan@example.com",
                "payment_provider": DepositProvider.PAYPAL,
            },
        )

        self.assertEqual(response.status_code, 302)
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.payment_provider, DepositProvider.PAYPAL)
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CONFIGURATION)

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request")
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_paypal_checkout_redirect_records_order(self, _mock_token, mock_api_request):
        item = BookableItem.objects.create(
            name="PayPal Stay Configured",
            slug="paypal-stay-configured",
            category=BookingCategory.STAY,
            short_description="A test booking item.",
            is_active=True,
        )
        mock_api_request.return_value = {
            "id": "ORDER-123",
            "links": [
                {
                    "rel": "payer-action",
                    "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123",
                }
            ],
        }

        response = self.client.post(
            reverse("bookings:deposit-checkout"),
            data={
                "item": item.id,
                "guest_name": "Taylor",
                "email": "taylor@example.com",
                "payment_provider": DepositProvider.PAYPAL,
            },
        )

        self.assertRedirects(
            response,
            "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123",
            fetch_redirect_response=False,
        )
        deposit = DamageDeposit.objects.get()
        self.assertEqual(deposit.payment_provider, DepositProvider.PAYPAL)
        self.assertEqual(deposit.paypal_order_id, "ORDER-123")
        self.assertEqual(deposit.status, DepositStatus.CHECKOUT_CREATED)

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request")
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_paypal_success_authorizes_deposit(self, _mock_token, mock_api_request):
        deposit = DamageDeposit.objects.create(
            guest_name="Taylor",
            email="taylor@example.com",
            payment_provider=DepositProvider.PAYPAL,
            paypal_order_id="ORDER-123",
        )
        mock_api_request.return_value = {
            "purchase_units": [
                {
                    "payments": {
                        "authorizations": [
                            {
                                "id": "AUTH-123",
                            }
                        ]
                    }
                }
            ]
        }

        response = self.client.get(
            reverse("bookings:deposit-paypal-success"),
            data={"token": "ORDER-123"},
        )

        self.assertRedirects(response, reverse("bookings:home") + "#deposit", fetch_redirect_response=False)
        deposit.refresh_from_db()
        self.assertEqual(deposit.paypal_authorization_id, "AUTH-123")
        self.assertEqual(deposit.status, DepositStatus.REQUIRES_CAPTURE)


@override_settings(STORAGES=TEST_STORAGES)
class DamageDepositAdminTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = DamageDepositAdmin(DamageDeposit, AdminSite())
        self.user = get_user_model().objects.create_user(
            username="deposit-admin",
            email="deposit-admin@example.com",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

    def _request(self):
        request = self.factory.post("/admin/bookings/damagedeposit/")
        request.user = self.user
        return request

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request")
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_capture_selected_deposits_updates_only_authorized_paypal_deposits(
        self,
        _mock_token,
        mock_api_request,
        mock_message_user,
    ):
        paypal_deposit = DamageDeposit.objects.create(
            guest_name="Taylor",
            email="taylor@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.PAYPAL,
            status=DepositStatus.REQUIRES_CAPTURE,
            paypal_order_id="ORDER-123",
            paypal_authorization_id="AUTH-123",
        )
        stripe_deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.CANCELED,
            stripe_payment_intent_id="pi_123",
        )
        mock_api_request.return_value = {"id": "CAPTURE-123"}

        self.admin.capture_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk__in=[paypal_deposit.pk, stripe_deposit.pk]),
        )

        paypal_deposit.refresh_from_db()
        stripe_deposit.refresh_from_db()
        self.assertEqual(paypal_deposit.status, DepositStatus.CAPTURED)
        self.assertEqual(stripe_deposit.status, DepositStatus.CANCELED)
        self.assertIn("CAPTURE-123", paypal_deposit.notes)
        mock_api_request.assert_called_once_with(
            "post",
            "/v2/payments/authorizations/AUTH-123/capture",
            access_token="access-token",
            json_body={
                "amount": {"currency_code": "USD", "value": "200.00"},
                "final_capture": True,
            },
        )

        messages = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Captured 1 deposit hold(s).", messages)
        self.assertIn("Skipped 1 deposit(s) that were not active authorized holds.", messages)

    @override_settings(
        PAYPAL_CLIENT_ID="paypal-client",
        PAYPAL_CLIENT_SECRET="paypal-secret",
    )
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.PayPalDamageDepositService._paypal_api_request", return_value={})
    @patch("bookings.services.PayPalDamageDepositService._create_access_token", return_value="access-token")
    def test_release_selected_deposits_voids_authorized_paypal_deposit(
        self,
        _mock_token,
        mock_api_request,
        mock_message_user,
    ):
        deposit = DamageDeposit.objects.create(
            guest_name="Taylor",
            email="taylor@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.PAYPAL,
            status=DepositStatus.REQUIRES_CAPTURE,
            paypal_order_id="ORDER-123",
            paypal_authorization_id="AUTH-123",
        )

        self.admin.release_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk=deposit.pk),
        )

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertIn("AUTH-123", deposit.notes)
        mock_api_request.assert_called_once_with(
            "post",
            "/v2/payments/authorizations/AUTH-123/void",
            access_token="access-token",
            json_body={},
        )

        messages = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Released 1 deposit hold(s).", messages)

    @override_settings(STRIPE_SECRET_KEY="stripe-secret")
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.stripe.PaymentIntent.capture")
    def test_capture_selected_deposits_updates_authorized_stripe_deposit(
        self,
        mock_capture,
        mock_message_user,
    ):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )
        mock_capture.return_value = {"id": "pi_123", "latest_charge": "ch_123"}

        self.admin.capture_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk=deposit.pk),
        )

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CAPTURED)
        self.assertIn("ch_123", deposit.notes)
        mock_capture.assert_called_once_with("pi_123")

        messages_seen = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Captured 1 deposit hold(s).", messages_seen)

    @override_settings(STRIPE_SECRET_KEY="stripe-secret")
    @patch.object(DamageDepositAdmin, "message_user")
    @patch("bookings.services.stripe.PaymentIntent.cancel")
    def test_release_selected_deposits_cancels_authorized_stripe_deposit(
        self,
        mock_cancel,
        mock_message_user,
    ):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )
        mock_cancel.return_value = {"id": "pi_123"}

        self.admin.release_selected_deposits(
            self._request(),
            DamageDeposit.objects.filter(pk=deposit.pk),
        )

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertIn("pi_123", deposit.notes)
        mock_cancel.assert_called_once_with("pi_123")

        messages_seen = [call.args[1] for call in mock_message_user.call_args_list]
        self.assertIn("Released 1 deposit hold(s).", messages_seen)

    def test_change_view_shows_confirmation_links_for_capturable_deposit(self):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )

        response = self.client.get(reverse("admin:bookings_damagedeposit_change", args=[deposit.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Capture deposit")
        self.assertContains(response, "Release deposit")

    @override_settings(STRIPE_SECRET_KEY="stripe-secret")
    @patch("bookings.services.stripe.PaymentIntent.cancel", return_value={"id": "pi_123"})
    def test_confirm_release_view_posts_and_redirects(self, _mock_cancel):
        deposit = DamageDeposit.objects.create(
            guest_name="Jordan",
            email="jordan@example.com",
            amount_cents=20000,
            currency="usd",
            payment_provider=DepositProvider.STRIPE,
            status=DepositStatus.REQUIRES_CAPTURE,
            stripe_payment_intent_id="pi_123",
        )

        response = self.client.post(
            reverse("admin:bookings_damagedeposit_deposit_action", args=[deposit.pk, "release"]),
            follow=True,
        )

        deposit.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(deposit.status, DepositStatus.CANCELED)
        self.assertContains(response, "Released deposit")
        message_levels = [message.level for message in response.context["messages"]]
        self.assertIn(messages.SUCCESS, message_levels)


class DonationTests(TestCase):
    @override_settings(STRIPE_SECRET_KEY="")
    def test_donation_checkout_without_stripe_key_records_configuration_status(self):
        response = self.client.post(
            reverse("bookings:donation-checkout"),
            data={
                "amount": "25.00",
                "donor_name": "Riley",
                "email": "riley@example.com",
                "cause": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        donation = Donation.objects.get()
        self.assertEqual(donation.amount_cents, 2500)
        self.assertEqual(donation.status, DonationStatus.REQUIRES_CONFIGURATION)


@override_settings(STORAGES=TEST_STORAGES)
class CustomerMarketingConsentTests(TestCase):
    AIRBNB_SAMPLE_BODY = """
RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024

Remember: Airbnb will never ask you to wire money. Learn more.

Diana

It will be a pleasure

[Pre-approve / Decline](https://www.airbnb.com/hosting/thread/1773535134?thread_type=home_booking)

Respond to Diana by replying directly to this email.

[6 Bedrooms Vacation Home & Pool (Apartment G-102)](https://www.airbnb.com/rooms/588632365342578374)

Reservation details

6 Bedrooms Vacation Home & Pool (Apartment G-102)

Guests

10 guests

Check-In

Thursday

August 22, 2024

Check-out

Sunday

September 1, 2024
"""
    AIRBNB_INITIAL_INQUIRY_BODY = """
Respond to Ana’s inquiry

[Ana](https://www.airbnb.com/hosting/thread/1773535134?thread_type=home_booking)

Identity verified · 1 review

US

Hello Diana, my name is Ana im planning a trip to DR on August 22 to sept 1 with my volleyball team.

[6 Bedrooms Vacation Home & Pool (Apartment G-102)](https://www.airbnb.com/rooms/588632365342578374)

Check-in

Thu, Aug 22

3:00 PM

Checkout

Sun, Sep 1

11:00 AM

Guests

10 adults
"""
    AIRBNB_SPANISH_REPLY_BODY = """
Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may

Por tu seguridad y protección, comunícate siempre a través de la plataforma de Airbnb.

Yoel

Responsable de reservación

Hola dia a que hora es la salida?

Diana

Anfitrión

Saludos Yoel, es un apartamento de tres habitaciones.

[Revisar consulta](https://es-l.airbnb.com/hosting/thread/2520797227?thread_type=home_booking)

[3 Bedrooms Vacation Home & Pool (Apartment G-101)](https://es-l.airbnb.com/rooms/582161420407543691)

3 Bedrooms Vacation Home & Pool (Apartment G-101)

Alojamiento vacacional - Vivienda o apartamento entero, anfitrión: Piter

Check-in

lunes

4 de mayo de 2026

15:00

Check-out

martes

5 de mayo de 2026

11:00

Viajeros

7 adultos
"""

    def test_airbnb_email_parser_extracts_guest_stay_and_thread_data(self):
        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-123",
                "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                "body": self.AIRBNB_SAMPLE_BODY,
                "email_ts": "2024-04-04T16:18:54",
            }
        )

        self.assertEqual(payload.source_message_id, "gmail-123")
        self.assertEqual(payload.guest_name, "Diana")
        self.assertEqual(payload.airbnb_listing_id, "588632365342578374")
        self.assertEqual(payload.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/1773535134")
        self.assertEqual(payload.guests, 10)
        self.assertEqual(payload.check_in, date(2024, 8, 22))
        self.assertEqual(payload.check_out, date(2024, 9, 1))
        self.assertIn("It will be a pleasure", payload.message_excerpt)

    def test_airbnb_email_parser_extracts_guest_from_initial_inquiry(self):
        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-initial-123",
                "subject": "Inquiry for 6 Bedrooms Vacation Home & Pool (Apartment G-102) for Aug 22 – Sep 1, 2024",
                "body": self.AIRBNB_INITIAL_INQUIRY_BODY,
                "email_ts": "2024-04-04T15:44:13",
            }
        )

        self.assertEqual(payload.guest_name, "Ana")
        self.assertEqual(payload.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/1773535134")
        self.assertEqual(payload.airbnb_listing_id, "588632365342578374")

    def test_airbnb_email_parser_extracts_spanish_airbnb_reply(self):
        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-spanish-123",
                "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                "body": self.AIRBNB_SPANISH_REPLY_BODY,
                "email_ts": "2026-05-03T15:40:25",
            }
        )

        self.assertEqual(payload.guest_name, "Yoel")
        self.assertEqual(payload.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/2520797227")
        self.assertEqual(payload.airbnb_listing_id, "582161420407543691")
        self.assertEqual(payload.check_in, date(2026, 5, 4))
        self.assertEqual(payload.check_out, date(2026, 5, 5))
        self.assertEqual(payload.guests, 7)
        self.assertIn("Hola dia", payload.message_excerpt)

    def test_airbnb_email_parser_counts_spanish_children_as_travelers(self):
        body = self.AIRBNB_SPANISH_REPLY_BODY.replace("7 adultos", "5 adultos, 2 niños")

        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-spanish-family-123",
                "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                "body": body,
                "email_ts": "2026-05-03T15:40:25",
            }
        )

        self.assertEqual(payload.guests, 7)

    def test_airbnb_email_parser_counts_spanish_babies_as_travelers(self):
        body = self.AIRBNB_SPANISH_REPLY_BODY.replace("7 adultos", "1 adulto, 1 bebé")

        payload = AirbnbGuestEmailParser().parse_message(
            {
                "id": "gmail-spanish-baby-123",
                "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                "body": body,
                "email_ts": "2026-05-03T15:40:25",
            }
        )

        self.assertEqual(payload.guests, 2)

    def test_airbnb_import_service_upserts_guest_records_from_json_file(self):
        item = BookableItem.objects.create(
            name="Six bedroom stay",
            slug="six-bedroom-stay",
            category=BookingCategory.STAY,
            short_description="A stay from Airbnb.",
            airbnb_listing_id="999999999999999999",
            is_active=True,
        )
        body = self.AIRBNB_SAMPLE_BODY.replace("588632365342578374", "999999999999999999")
        data = {
            "responses": [
                {
                    "id": "gmail-123",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": body,
                    "email_ts": "2024-04-04T16:18:54",
                }
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            service = AirbnbGuestImportService()

            first = service.import_file(path)
            second = service.import_file(path)

        self.assertEqual(first.created, 1)
        self.assertEqual(second.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.item, item)
        self.assertEqual(record.customer_profile.source, ContactSource.AIRBNB)
        self.assertEqual(record.customer_profile.marketing_consent_status, MarketingConsentStatus.UNKNOWN)
        feedback = CustomerFeedback.objects.get()
        self.assertEqual(feedback.airbnb_guest_record, record)
        self.assertEqual(feedback.customer_profile, record.customer_profile)
        self.assertEqual(feedback.item, item)
        self.assertIn("It will be a pleasure", feedback.feedback_text)

    def test_airbnb_import_service_imports_structured_guest_contact_list(self):
        data = {
            "guest_contact_list": [
                {
                    "guest_name": "Jessica",
                    "email": "",
                    "phone_number": "",
                    "airbnb_profile_name_or_id": "airbnb-profile-123",
                    "airbnb_thread_url": "https://www.airbnb.com/hosting/messages/2423037932",
                    "listing_apartment": "6 Bedrooms Vacation Home & Pool (Apartment G-102)",
                    "check_in_date": "Apr 17",
                    "check_out_date": "Apr 19",
                    "number_of_guests": "",
                    "message_summary": "Template message: discount offer + feedback request.",
                    "feedback_or_review_summary": "Feedback requested; review not shown.",
                    "permission_to_contact_outside_airbnb": "unknown",
                    "consent_status": "unknown",
                    "promotion_permission_notes": "Opt-in required before marketing.",
                }
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-contacts.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        current_year = timezone.localdate().year
        self.assertEqual(result.created, 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.guest_name, "Jessica")
        self.assertEqual(record.airbnb_listing_id, "588632365342578374")
        self.assertEqual(record.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/2423037932")
        self.assertEqual(record.check_in, date(current_year, 4, 17))
        self.assertEqual(record.check_out, date(current_year, 4, 19))
        self.assertIsNone(record.guests)
        self.assertIn("discount offer", record.message_excerpt)
        self.assertIn("Feedback requested", record.feedback_summary)
        self.assertIn("airbnb-profile-123", record.permission_notes)
        self.assertEqual(record.customer_profile.marketing_consent_status, MarketingConsentStatus.UNKNOWN)
        feedback = CustomerFeedback.objects.get()
        self.assertEqual(feedback.airbnb_guest_record, record)
        self.assertEqual(feedback.customer_profile, record.customer_profile)
        self.assertIn("Feedback requested", feedback.feedback_text)
        self.assertIn("airbnb-profile-123", feedback.permission_notes)

    def test_airbnb_import_service_coalesces_messages_from_same_thread(self):
        first_body = self.AIRBNB_SAMPLE_BODY
        second_body = self.AIRBNB_SAMPLE_BODY.replace("It will be a pleasure", "Can we use the pool?")
        data = {
            "responses": [
                {
                    "id": "gmail-thread-1",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": first_body,
                    "email_ts": "2024-04-04T16:18:54",
                },
                {
                    "id": "gmail-thread-2",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": second_body,
                    "email_ts": "2024-04-04T16:19:33",
                },
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/1773535134")
        self.assertIn("Can we use the pool?", record.message_excerpt)
        self.assertEqual(CustomerFeedback.objects.count(), 1)
        self.assertIn("Can we use the pool?", record.customer_feedback.feedback_text)

    def test_airbnb_import_service_coalesces_same_guest_listing_and_dates(self):
        first_body = self.AIRBNB_SPANISH_REPLY_BODY.replace("2520797227", "2520797000")
        second_body = self.AIRBNB_SPANISH_REPLY_BODY.replace("2520797227", "2520797999").replace(
            "Hola dia a que hora es la salida?",
            "Vamos otra vez y queremos confirmar la piscina.",
        )
        data = {
            "responses": [
                {
                    "id": "gmail-same-stay-1",
                    "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                    "body": first_body,
                    "email_ts": "2026-05-03T15:40:25",
                },
                {
                    "id": "gmail-same-stay-2",
                    "subject": "RE: Consulta sobre 3 Bedrooms Vacation Home & Pool (Apartment G-101), para 4 – 5 de may",
                    "body": second_body,
                    "email_ts": "2026-05-03T15:42:25",
                },
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.airbnb_thread_url, "https://www.airbnb.com/hosting/thread/2520797000")
        self.assertIn("confirmar la piscina", record.message_excerpt)
        self.assertEqual(CustomerFeedback.objects.count(), 1)
        self.assertIn("confirmar la piscina", record.customer_feedback.feedback_text)

    def test_airbnb_import_service_preserves_initial_inquiry_guest_identity(self):
        data = {
            "responses": [
                {
                    "id": "gmail-reply-first",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": self.AIRBNB_SAMPLE_BODY,
                    "email_ts": "2024-04-04T16:18:54",
                },
                {
                    "id": "gmail-initial-second",
                    "subject": "Inquiry for 6 Bedrooms Vacation Home & Pool (Apartment G-102) for Aug 22 – Sep 1, 2024",
                    "body": self.AIRBNB_INITIAL_INQUIRY_BODY,
                    "email_ts": "2024-04-04T15:44:13",
                },
            ]
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "airbnb-guests.json"
            path.write_text(json.dumps(data))
            result = AirbnbGuestImportService().import_file(path)

        self.assertEqual(result.created, 1)
        self.assertEqual(result.updated, 1)
        self.assertEqual(AirbnbGuestRecord.objects.count(), 1)
        self.assertEqual(AirbnbGuestRecord.objects.get().guest_name, "Ana")

    def test_airbnb_guest_record_tracks_stay_feedback_and_permission_notes(self):
        item = BookableItem.objects.create(
            name="Airbnb Stay",
            slug="airbnb-stay",
            category=BookingCategory.STAY,
            short_description="A stay from Airbnb.",
            is_active=True,
        )
        profile = CustomerProfile.objects.create(
            name="Diana",
            source=ContactSource.AIRBNB,
            marketing_consent_status=MarketingConsentStatus.UNKNOWN,
        )

        record = AirbnbGuestRecord.objects.create(
            customer_profile=profile,
            item=item,
            guest_name="Diana",
            listing_title="6 Bedrooms Vacation Home & Pool",
            airbnb_listing_id="588632365342578374",
            check_in=date(2024, 8, 22),
            check_out=date(2024, 9, 1),
            guests=10,
            feedback_summary="Positive Airbnb message thread.",
            permission_notes="Contact through Airbnb thread; no marketing opt-in yet.",
        )

        self.assertEqual(record.stay_dates, "2024-08-22 to 2024-09-01")
        self.assertFalse(profile.can_receive_promotions)
        feedback = CustomerFeedback.sync_from_airbnb_record(record)
        self.assertEqual(feedback.customer_profile, profile)
        self.assertEqual(feedback.item, item)
        self.assertEqual(feedback.feedback_text, "Positive Airbnb message thread.")

    def test_promotion_recipients_are_limited_to_opted_in_profiles(self):
        opted_in = CustomerProfile.objects.create(
            name="Opted In",
            email="opted@example.com",
            marketing_consent_status=MarketingConsentStatus.OPTED_IN,
        )
        CustomerProfile.objects.create(
            name="Unknown",
            email="unknown@example.com",
            marketing_consent_status=MarketingConsentStatus.UNKNOWN,
        )
        CustomerProfile.objects.create(
            name="Opted Out",
            email="out@example.com",
            marketing_consent_status=MarketingConsentStatus.OPTED_OUT,
        )
        promotion = Promotion.objects.create(
            title="Future Stay",
            subject="MLADIS future stay offer",
            message="A small thank-you offer.",
        )

        recipients = PromotionEmailService().build_recipients(promotion)

        self.assertEqual(len(recipients), 1)
        self.assertEqual(recipients[0].customer_profile, opted_in)
        self.assertEqual(recipients[0].email, "opted@example.com")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_manual_promotion_recipient_without_opt_in_is_not_sent(self):
        promotion = Promotion.objects.create(
            title="Manual recipient",
            subject="MLADIS future stay offer",
            message="A small thank-you offer.",
        )
        recipient = PromotionRecipient.objects.create(
            promotion=promotion,
            email="manual@example.com",
            name="Manual",
        )

        sent = PromotionEmailService().send_promotion(promotion)

        self.assertEqual(sent, 0)
        self.assertEqual(len(mail.outbox), 0)
        recipient.refresh_from_db()
        self.assertIn("not opted in", recipient.error)

    def test_admin_airbnb_guest_import_page_loads(self):
        user = get_user_model().objects.create_user(
            username="airbnb-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:bookings_airbnbguestrecord_import"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Import Airbnb guests")

    def test_admin_airbnb_guest_import_dry_run_does_not_write_records(self):
        user = get_user_model().objects.create_user(
            username="airbnb-dry-run-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        upload = SimpleUploadedFile(
            "airbnb-guests.json",
            self._airbnb_import_json("999999999999999998"),
            content_type="application/json",
        )

        response = self.client.post(
            reverse("admin:bookings_airbnbguestrecord_import"),
            {"import_file": upload, "dry_run": "on"},
        )

        self.assertRedirects(response, reverse("admin:bookings_airbnbguestrecord_changelist"))
        self.assertEqual(AirbnbGuestRecord.objects.count(), 0)

    def test_admin_airbnb_guest_import_creates_records(self):
        user = get_user_model().objects.create_user(
            username="airbnb-import-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        item = BookableItem.objects.create(
            name="Admin imported stay",
            slug="admin-imported-stay",
            category=BookingCategory.STAY,
            short_description="A stay from Airbnb.",
            airbnb_listing_id="999999999999999997",
            is_active=True,
        )
        upload = SimpleUploadedFile(
            "airbnb-guests.json",
            self._airbnb_import_json("999999999999999997"),
            content_type="application/json",
        )

        response = self.client.post(
            reverse("admin:bookings_airbnbguestrecord_import"),
            {"import_file": upload},
        )

        self.assertRedirects(response, reverse("admin:bookings_airbnbguestrecord_changelist"))
        record = AirbnbGuestRecord.objects.get()
        self.assertEqual(record.item, item)
        self.assertEqual(record.guest_name, "Diana")
        self.assertEqual(record.customer_profile.source, ContactSource.AIRBNB)
        self.assertEqual(CustomerFeedback.objects.get().airbnb_guest_record, record)

    def _airbnb_import_json(self, listing_id):
        body = self.AIRBNB_SAMPLE_BODY.replace("588632365342578374", listing_id)
        data = {
            "responses": [
                {
                    "id": f"gmail-{listing_id}",
                    "subject": "RE: Inquiry at 6 Bedrooms Vacation Home & Pool (Apartment G-102) for August 22, 2024 - September 1, 2024",
                    "body": body,
                    "email_ts": "2024-04-04T16:18:54",
                }
            ]
        }
        return json.dumps(data).encode()

    def test_ops_reservations_requires_staff_login(self):
        response = self.client.get(reverse("bookings:ops-reservations"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("bookings:login"), response["Location"])
        self.assertIn("next=/ops/reservations/", response["Location"])

    def test_ops_reservations_lists_customer_groups_feedback_and_contact(self):
        user = get_user_model().objects.create_user(
            username="reservation-ops",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(user)
        profile = CustomerProfile.objects.create(
            name="Diana",
            email="diana@example.com",
            phone="631-555-0100",
            segment=ClientSegment.VIP,
            source=ContactSource.AIRBNB,
            marketing_consent_status=MarketingConsentStatus.REQUESTED,
        )
        record = AirbnbGuestRecord.objects.create(
            customer_profile=profile,
            guest_name="Diana",
            email="",
            phone="",
            listing_title="6 Bedrooms Vacation Home & Pool",
            airbnb_listing_id="588632365342578374",
            check_in=date(2024, 8, 22),
            check_out=date(2024, 9, 1),
            guests=10,
            feedback_summary="Loved the pool and the host support.",
            airbnb_thread_url="https://www.airbnb.com/hosting/thread/1773535134",
        )
        CustomerFeedback.sync_from_airbnb_record(record)

        response = self.client.get(reverse("bookings:ops-reservations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MLADIS Command Center")
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

        api_response = self.client.get(reverse("bookings:ops-reservations-api"))
        self.assertEqual(api_response.status_code, 200)
        payload = api_response.json()
        self.assertEqual(payload["rows"][0]["name"], "Diana")
        self.assertEqual(payload["rows"][0]["segment"], "VIP")
        self.assertEqual(payload["rows"][0]["email"], "diana@example.com")
        self.assertIn("Loved the pool", payload["rows"][0]["feedback"])
        self.assertTrue(payload["rows"][0]["feedback_admin_url"])
        self.assertIn("VIP", [option["label"] for option in payload["segment_options"]])
        self.assertEqual(payload["reservations"][0]["key"], f"airbnb-{record.pk}")
        self.assertEqual(payload["reservations"][0]["guest"]["name"], "Diana")
        self.assertEqual(payload["reservations"][0]["stay"]["name"], "6 Bedrooms Vacation Home & Pool")
        self.assertEqual(payload["reservations"][0]["dates"]["nights"], 10)
        self.assertEqual(payload["reservations"][0]["status"]["tab"], "completed")
        self.assertEqual(payload["reservations"][0]["agent"]["risk_level"], "low")

    def test_ops_reservation_status_api_returns_updated_reservation_object(self):
        user = get_user_model().objects.create_user(
            username="reservation-status-ops",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(user)
        item = BookableItem.objects.create(
            name="3 Beds Apt, Vacation Home & Pool, G-101",
            slug="reservation-status-stay",
            category=BookingCategory.STAY,
            short_description="Direct reservation stay.",
            starting_price=Decimal("120.00"),
            is_active=True,
        )
        reservation = BookingInquiry.objects.create(
            item=item,
            guest_name="Direct Guest",
            email="direct@example.com",
            phone="201-555-0101",
            check_in=date(2026, 6, 20),
            check_out=date(2026, 6, 22),
            guests=2,
            status=BookingStatus.REVIEWING,
        )

        response = self.client.post(
            reverse("bookings:ops-reservation-status-api", args=[reservation.pk]),
            data=json.dumps({"status": "confirmed"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["reservation"]["key"], f"direct-{reservation.pk}")
        self.assertEqual(payload["reservation"]["guest"]["name"], "Direct Guest")
        self.assertEqual(payload["reservation"]["status"]["tab"], "confirmed")
        self.assertTrue(payload["reservation"]["admin"]["can_transition_status"])

    def test_ops_reservations_filters_by_customer_group_and_exports_csv(self):
        user = get_user_model().objects.create_user(
            username="reservation-export-ops",
            password="secret",
            is_staff=True,
        )
        self.client.force_login(user)
        vip_profile = CustomerProfile.objects.create(
            name="VIP Guest",
            email="vip@example.com",
            segment=ClientSegment.VIP,
            source=ContactSource.AIRBNB,
        )
        favorite_profile = CustomerProfile.objects.create(
            name="Favorite Guest",
            email="favorite@example.com",
            segment=ClientSegment.FAVORITE,
            source=ContactSource.AIRBNB,
        )
        AirbnbGuestRecord.objects.create(
            customer_profile=vip_profile,
            guest_name="VIP Guest",
            listing_title="VIP Stay",
            check_in=date(2024, 8, 22),
            check_out=date(2024, 8, 24),
        )
        AirbnbGuestRecord.objects.create(
            customer_profile=favorite_profile,
            guest_name="Favorite Guest",
            listing_title="Favorite Stay",
            check_in=date(2024, 9, 2),
            check_out=date(2024, 9, 4),
        )

        response = self.client.get(reverse("bookings:ops-reservations-api"), {"segment": ClientSegment.VIP})

        rows = response.json()["rows"]
        self.assertEqual([row["name"] for row in rows], ["VIP Guest"])

        csv_response = self.client.get(
            reverse("bookings:ops-reservations"),
            {"segment": ClientSegment.VIP, "format": "csv"},
        )

        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        content = csv_response.content.decode()
        self.assertIn("VIP Guest", content)
        self.assertNotIn("Favorite Guest", content)


@override_settings(STORAGES=TEST_STORAGES)
class CalendarOpsTests(TestCase):
    def test_calendar_ops_requires_staff_login(self):
        response = self.client.get(reverse("bookings:calendar-ops"))

        self.assertRedirects(
            response,
            f"{reverse('bookings:login')}?next={reverse('bookings:calendar-ops')}",
            fetch_redirect_response=False,
        )

    def test_calendar_ops_loads_for_staff(self):
        user = get_user_model().objects.create_user(
            username="ops",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("bookings:calendar-ops"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/modern_dashboard.html")
        self.assertContains(response, 'id="root"')
        self.assertContains(response, "frontend/modern-dashboard/assets/app.js")
        self.assertContains(response, 'id="mladis-ops-nav-items"')
        self.assertNotContains(response, "frontend/modern-dashboard/assets/ops-calendar.css")
        self.assertNotContains(response, "data-calendar-cell")

    def test_calendar_ops_route_uses_react_shell_with_query_controls(self):
        user = get_user_model().objects.create_user(
            username="ops-calendar-controls",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        week_response = self.client.get(
            reverse("bookings:calendar-ops"),
            {"view": "week", "date": "2026-06-17", "status": "blocked"},
        )

        self.assertEqual(week_response.status_code, 200)
        self.assertTemplateUsed(week_response, "bookings/modern_dashboard.html")
        self.assertContains(week_response, "frontend/modern-dashboard/assets/app.js")

        day_response = self.client.get(
            reverse("bookings:calendar-ops"),
            {"view": "day", "date": "2026-06-17"},
        )

        self.assertEqual(day_response.status_code, 200)
        self.assertTemplateUsed(day_response, "bookings/modern_dashboard.html")

    def test_calendar_workspace_subroutes_load_for_staff(self):
        user = get_user_model().objects.create_user(
            username="ops-calendar-tabs",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        for route_name in ("calendar-ops-list", "calendar-ops-rooms", "calendar-ops-analytics"):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(f"bookings:{route_name}"))

                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "bookings/modern_dashboard.html")
                self.assertContains(response, "frontend/modern-dashboard/assets/app.js")

    def test_calendar_ops_api_returns_snapshot_and_mutates_manual_records(self):
        user = get_user_model().objects.create_user(
            username="ops-api",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)
        item = BookableItem.objects.create(
            name="Ops Calendar Stay",
            slug="ops-calendar-stay",
            category=BookingCategory.STAY,
            short_description="Modern calendar API stay.",
            starting_price=Decimal("120.00"),
            is_active=True,
        )
        BookingInquiry.objects.create(
            item=item,
            guest_name="Calendar Guest",
            email="calendar@example.com",
            check_in=date(2026, 6, 10),
            check_out=date(2026, 6, 13),
            guests=2,
            status=BookingStatus.CONFIRMED,
        )
        AvailabilityBlock.objects.create(
            item=item,
            start_date=date(2026, 6, 18),
            end_date=date(2026, 6, 19),
            reason="Owner stay",
        )
        DailyPriceOverride.objects.create(
            item=item,
            start_date=date(2026, 6, 20),
            end_date=date(2026, 6, 21),
            nightly_price=Decimal("175.00"),
            label="Weekend premium",
        )

        response = self.client.get(
            reverse("bookings:ops-calendar-api"),
            {"item": item.pk, "date": "2026-06-10", "view": "week"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["selected_item_id"], item.pk)
        self.assertEqual(payload["view"], "week")
        self.assertEqual(payload["month_label"], "June 2026")
        self.assertEqual(len(payload["week_days"]), 7)
        self.assertEqual(payload["admin_records_url"], reverse("admin:bookings_bookableitem_changelist"))
        self.assertIn("reservation", {event["type"] for event in payload["events"]})
        self.assertIn("block", {event["type"] for event in payload["events"]})
        self.assertIn("price", {event["type"] for event in payload["events"]})

        block_response = self.client.post(
            reverse("bookings:ops-calendar-blocks-api"),
            data=json.dumps(
                {
                    "item": item.pk,
                    "start_date": "2026-06-22",
                    "end_date": "2026-06-23",
                    "reason": "Maintenance",
                    "notes": "Pool filter work",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(block_response.status_code, 201)
        block = AvailabilityBlock.objects.get(reason="Maintenance")
        self.assertEqual(block.notes, "Pool filter work")

        price_response = self.client.post(
            reverse("bookings:ops-calendar-prices-api"),
            data=json.dumps(
                {
                    "item": item.pk,
                    "start_date": "2026-06-24",
                    "end_date": "2026-06-24",
                    "nightly_price": "210.00",
                    "label": "Summer demand",
                    "notes": "Modern calendar test",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(price_response.status_code, 201)
        override = DailyPriceOverride.objects.get(label="Summer demand")
        self.assertEqual(override.nightly_price, Decimal("210.00"))

        delete_block_response = self.client.delete(
            reverse("bookings:ops-calendar-blocks-api"),
            data=json.dumps({"id": block.pk}),
            content_type="application/json",
        )
        delete_price_response = self.client.delete(
            reverse("bookings:ops-calendar-prices-api"),
            data=json.dumps({"id": override.pk}),
            content_type="application/json",
        )

        self.assertEqual(delete_block_response.status_code, 200)
        self.assertEqual(delete_price_response.status_code, 200)
        self.assertFalse(AvailabilityBlock.objects.filter(pk=block.pk).exists())
        self.assertFalse(DailyPriceOverride.objects.filter(pk=override.pk).exists())


@override_settings(STORAGES=TEST_STORAGES)
class MaintenanceOpsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="maintenance-admin",
            password="secret",
            is_staff=True,
            is_superuser=True,
        )
        self.item = BookableItem.objects.create(
            name="3 Bedrooms Vacation Home & Pool G-101",
            slug="maintenance-g-101",
            category=BookingCategory.STAY,
            short_description="Maintenance test stay.",
            is_active=True,
        )
        self.other_item = BookableItem.objects.create(
            name="6 Bedrooms Vacation Home & Pool G-102",
            slug="maintenance-g-102",
            category=BookingCategory.STAY,
            short_description="Second maintenance test stay.",
            is_active=True,
        )
        self.booking = BookingInquiry.objects.create(
            item=self.item,
            guest_name="Maintenance Guest",
            email="guest@example.com",
            check_in=date(2026, 6, 10),
            check_out=date(2026, 6, 12),
            guests=2,
            status=BookingStatus.CONFIRMED,
        )

    def test_maintenance_ops_requires_staff_login(self):
        response = self.client.get(reverse("bookings:ops-maintenance"))

        self.assertRedirects(
            response,
            f"{reverse('bookings:login')}?next={reverse('bookings:ops-maintenance')}",
            fetch_redirect_response=False,
        )

    def test_maintenance_ops_loads_for_staff(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("bookings:ops-maintenance"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookings/modern_ops_maintenance.html")
        self.assertContains(response, 'class="ops-mnt-page"')
        self.assertContains(response, "frontend/modern-dashboard/assets/ops-maintenance.css")
        self.assertNotContains(response, "frontend/modern-dashboard/assets/app.js")
        self.assertNotContains(response, "WO-2026-0104")

    def test_maintenance_api_rejects_completed_event_without_photo(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("bookings:ops-maintenance-api"),
            {
                "item": self.item.pk,
                "title": "Post-stay cleaning",
                "work_type": "cleaning",
                "status": "completed",
                "cost_amount": "55.00",
                "cost_currency": "USD",
                "reported_at": "2026-06-07T10:30",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("photos", response.json()["errors"])
        self.assertFalse(MaintenanceEvent.objects.exists())

    def test_maintenance_api_creates_event_photo_and_agent_payload(self):
        self.client.force_login(self.user)
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
                response = self.client.post(
                    reverse("bookings:ops-maintenance-api"),
                    {
                        "item": self.item.pk,
                        "title": "Replace pool filter",
                        "work_type": "repair",
                        "status": "completed",
                        "cost_amount": "75.50",
                        "cost_currency": "USD",
                        "reported_at": "2026-06-07T11:00",
                        "started_at": "2026-06-07T10:00",
                        "completed_at": "2026-06-07T10:45",
                        "vendor_name": "Local maintenance",
                        "payment_status": "paid",
                        "proof_of_payment_ref": "cash receipt 102",
                        "description": "Replaced pool filter cartridge after inspection.",
                        "photos": SimpleUploadedFile("filter.png", TINY_PNG_BYTES, content_type="image/png"),
                    },
                )

                self.assertEqual(response.status_code, 201)
                event = MaintenanceEvent.objects.get()
                photo = MaintenancePhoto.objects.get(event=event)
                self.assertEqual(event.title, "Replace pool filter")
                self.assertEqual(event.cost_amount, Decimal("75.50"))
                self.assertEqual(event.created_by, self.user)
                self.assertEqual(event.photo_count, 1)
                self.assertTrue(photo.checksum_sha256)

                payload_response = self.client.get(
                    reverse("bookings:ops-maintenance-agent-payload-api", args=[event.pk])
                )

        self.assertEqual(payload_response.status_code, 200)
        payload = payload_response.json()
        self.assertEqual(payload["title"], "Replace pool filter")
        self.assertEqual(payload["cost"]["amount"], "75.50")
        self.assertEqual(payload["time"]["duration_minutes"], 45)
        self.assertEqual(len(payload["pictures"]), 1)

    def test_maintenance_event_can_link_to_reservation_for_billing_payload(self):
        self.client.force_login(self.user)
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/"):
                response = self.client.post(
                    reverse("bookings:ops-maintenance-api"),
                    {
                        "item": self.item.pk,
                        "booking": self.booking.pk,
                        "title": "Post-checkout cleaning",
                        "work_type": "cleaning",
                        "status": "completed",
                        "cost_amount": "60.00",
                        "cost_currency": "USD",
                        "reported_at": "2026-06-12T10:00",
                        "payment_status": "pending",
                        "description": "Cleaning after guest checkout.",
                        "photos": SimpleUploadedFile("cleaning.png", TINY_PNG_BYTES, content_type="image/png"),
                    },
                )
                event = MaintenanceEvent.objects.get(title="Post-checkout cleaning")
                payload_response = self.client.get(
                    reverse("bookings:ops-maintenance-agent-payload-api", args=[event.pk])
                )

        self.assertEqual(response.status_code, 201)
        event_payload = response.json()["event"]
        self.assertEqual(event_payload["booking_id"], self.booking.pk)
        self.assertEqual(event_payload["booking_request_key"], self.booking.request_key)
        self.assertIn("Maintenance Guest", event_payload["booking_label"])
        event.refresh_from_db()
        self.assertEqual(event.booking, self.booking)
        report_payload = payload_response.json()
        self.assertEqual(report_payload["reservation"]["request_key"], self.booking.request_key)
        self.assertEqual(report_payload["reservation"]["guest_name"], "Maintenance Guest")
        self.assertEqual(report_payload["reservation"]["nights"], 2)

    def test_maintenance_event_rejects_reservation_for_different_listing(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("bookings:ops-maintenance-api"),
            {
                "item": self.other_item.pk,
                "booking": self.booking.pk,
                "title": "Wrong stay assignment",
                "work_type": "inspection",
                "status": "draft",
                "cost_amount": "0.00",
                "cost_currency": "USD",
                "reported_at": "2026-06-12T10:00",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("booking", response.json()["errors"])

    def test_maintenance_ai_description_requires_openai_configuration(self):
        self.client.force_login(self.user)
        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root, MEDIA_URL="/media/", OPENAI_API_KEY=""):
                event = MaintenanceEvent.objects.create(
                    item=self.item,
                    title="Document ceiling stain",
                    work_type="inspection",
                    status="completed",
                    cost_amount=Decimal("0.00"),
                    cost_currency="USD",
                    created_by=self.user,
                )
                MaintenancePhoto.objects.create(
                    event=event,
                    image=SimpleUploadedFile("stain.png", TINY_PNG_BYTES, content_type="image/png"),
                    caption="Ceiling stain",
                    mime_type="image/png",
                )

                response = self.client.post(
                    reverse("bookings:ops-maintenance-ai-description-api", args=[event.pk])
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ai_description", response.json()["errors"])

    def test_maintenance_draft_ai_description_requires_click_and_does_not_create_event(self):
        self.client.force_login(self.user)
        fake_response = SimpleNamespace(
            output_text=json.dumps(
                {
                    "description": "Photo evidence shows post-stay cleaning work with surfaces ready for review.",
                    "observations": ["Cleaning evidence visible"],
                    "confidence": "medium",
                }
            )
        )
        fake_client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: fake_response))

        with self.settings(OPENAI_API_KEY="sk-test", OPENAI_MAINTENANCE_VISION_MODEL="gpt-vision-test"):
            with patch("bookings.services._build_openai_client", return_value=fake_client):
                response = self.client.post(
                    reverse("bookings:ops-maintenance-ai-description-draft-api"),
                    data={
                        "item": str(self.item.pk),
                        "title": "Post-stay cleaning",
                        "work_type": "cleaning",
                        "status": "completed",
                        "cost_amount": "50.00",
                        "cost_currency": "USD",
                        "photos": SimpleUploadedFile("cleaning.png", TINY_PNG_BYTES, content_type="image/png"),
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertIn("post-stay cleaning", response.json()["description"].lower())
        self.assertEqual(response.json()["model"], "gpt-vision-test")
        self.assertEqual(MaintenanceEvent.objects.count(), 0)

    def test_maintenance_ai_description_persists_and_updates_agent_payload(self):
        self.client.force_login(self.user)
        fake_response = SimpleNamespace(
            output_text=json.dumps(
                {
                    "description": "Photo evidence shows a replaced pool filter cartridge and a clean equipment area. The record is suitable for repair documentation after staff review.",
                    "observations": ["Pool filter cartridge visible", "Equipment area appears clean"],
                    "confidence": "high",
                }
            )
        )
        fake_client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: fake_response))

        with TemporaryDirectory() as media_root:
            with self.settings(
                MEDIA_ROOT=media_root,
                MEDIA_URL="/media/",
                OPENAI_API_KEY="sk-test",
                OPENAI_MAINTENANCE_VISION_MODEL="gpt-vision-test",
            ):
                event = MaintenanceEvent.objects.create(
                    item=self.item,
                    title="Replace pool filter",
                    work_type="repair",
                    status="completed",
                    cost_amount=Decimal("75.50"),
                    cost_currency="USD",
                    created_by=self.user,
                )
                MaintenancePhoto.objects.create(
                    event=event,
                    image=SimpleUploadedFile("filter.png", TINY_PNG_BYTES, content_type="image/png"),
                    caption="Pool filter",
                    mime_type="image/png",
                )

                with patch("bookings.services._build_openai_client", return_value=fake_client):
                    response = self.client.post(
                        reverse("bookings:ops-maintenance-ai-description-api", args=[event.pk])
                    )
                payload_response = self.client.get(
                    reverse("bookings:ops-maintenance-agent-payload-api", args=[event.pk])
                )

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertTrue(event.use_ai_description)
        self.assertIn("replaced pool filter", event.ai_description.lower())
        self.assertEqual(event.ai_description_model, "gpt-vision-test")
        self.assertEqual(event.ai_description_metadata["confidence"], "high")
        self.assertEqual(payload_response.json()["description"], event.ai_description)
        self.assertEqual(payload_response.json()["work_description"]["active"], "ai")

    def test_maintenance_api_snapshot_includes_filter_options_and_rows(self):
        self.client.force_login(self.user)
        MaintenanceEvent.objects.create(
            item=self.item,
            title="Inventory count",
            work_type="inspection",
            status="draft",
            cost_amount=Decimal("0.00"),
            cost_currency="USD",
            created_by=self.user,
        )

        response = self.client.get(reverse("bookings:ops-maintenance-api"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["rows"][0]["title"], "Inventory count")
        self.assertIn("Cleaning", [option["label"] for option in payload["work_type_options"]])
        self.assertIn("3 Beds Apt", payload["stays"][0]["name"])
        self.assertEqual(payload["reservations"][0]["request_key"], self.booking.request_key)
