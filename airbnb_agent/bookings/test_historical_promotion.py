import json
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from .historical_data import (
    ArchiveIntegrityError,
    CollectRepository,
    FilesystemHistoryStorage,
    HistoricalDataPreparationService,
    RollingTwelveMonthPolicy,
)
from .historical_promotion import HistoricalPromotionService, PreparedHistoryRepository
from .models import AirbnbGuestRecord, BookableItem, BookingInquiry, CustomerProfile


def envelope(collection, record_key, data, *, source_model, source_pk, occurred_at):
    return {
        "schema_version": "1.0",
        "collection": collection,
        "entity_type": collection.rstrip("s"),
        "record_key": record_key,
        "source_system": "sanitized-test",
        "source_model": source_model,
        "source_pk": str(source_pk),
        "pii_classification": "private",
        "occurred_at": occurred_at,
        "extracted_at": "2026-08-19T12:00:00+00:00",
        "natural_keys": {},
        "data": data,
    }


class HistoricalPromotionTests(TestCase):
    def setUp(self):
        self.item = BookableItem.objects.create(
            name="Sanitized Test Stay",
            slug="sanitized-test-stay",
            short_description="A test stay.",
            airbnb_listing_id="fixture-listing",
        )

    def _prepare(self, collect_root, history_root, rows_by_path):
        for relative_path, rows in rows_by_path.items():
            path = Path(collect_root) / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("".join(f"{json.dumps(row)}\n" for row in rows), encoding="utf-8")
        service = HistoricalDataPreparationService(
            collect_repository=CollectRepository(collect_root),
            storage=FilesystemHistoryStorage(history_root, private_working_segment=True),
            partition_policy=RollingTwelveMonthPolicy(as_of=date(2026, 8, 19)),
        )
        service.prepare()

    def _rows(self):
        occurred_at = "2026-07-01T10:00:00+00:00"
        profile = envelope(
            "customer_profiles",
            "profile:42",
            {
                "profile_id": 42,
                "name": "Sanitized Guest",
                "email": "guest42@example.invalid",
                "phone": "+1 555 010 0042",
                "source": "airbnb",
                "marketing_consent_status": "unknown",
                "preferred_language": "en",
                "created_at": occurred_at,
                "updated_at": occurred_at,
            },
            source_model="bookings.CustomerProfile",
            source_pk=42,
            occurred_at=occurred_at,
        )
        reservation = envelope(
            "booking_requests",
            "inquiry:101",
            {
                "booking_inquiry_id": 101,
                "customer_profile_id": 42,
                "item_id": self.item.pk,
                "item_name": self.item.name,
                "guest_name": "Sanitized Guest",
                "email": "guest42@example.invalid",
                "phone": "+1 555 010 0042",
                "check_in": "2026-09-10",
                "check_out": "2026-09-13",
                "guests": 3,
                "status": "confirmed",
                "total_cents": 72000,
                "currency": "usd",
                "created_at": occurred_at,
                "updated_at": occurred_at,
            },
            source_model="bookings.BookingInquiry",
            source_pk=101,
            occurred_at=occurred_at,
        )
        guest_record = envelope(
            "airbnb_guest_records",
            "guest-record:77",
            {
                "airbnb_guest_record_id": 77,
                "customer_profile_id": 42,
                "item_id": self.item.pk,
                "guest_name": "Sanitized Guest",
                "email": "guest42@example.invalid",
                "check_in": "2026-09-10",
                "check_out": "2026-09-13",
                "guests": 3,
                "rating": "4.90",
                "created_at": occurred_at,
                "updated_at": occurred_at,
            },
            source_model="bookings.AirbnbGuestRecord",
            source_pk=77,
            occurred_at=occurred_at,
        )
        return {
            "CUSTOMERS/customer_profiles.jsonl": [profile],
            "BOOKINGS/booking_requests.jsonl": [reservation],
            "CUSTOMERS/airbnb_guest_records.jsonl": [guest_record],
        }

    def test_promotion_is_dry_run_by_default_and_idempotent_when_applied(self):
        initial_profiles = CustomerProfile.objects.count()
        with TemporaryDirectory() as collect_root, TemporaryDirectory() as history_root:
            self._prepare(collect_root, history_root, self._rows())
            repository = PreparedHistoryRepository(history_root, private_working_segment=True)

            dry_run = HistoricalPromotionService(repository).promote()

            self.assertEqual(dry_run.guests_would_create, 1)
            self.assertEqual(dry_run.reservations_would_create, 1)
            self.assertEqual(dry_run.guest_records_would_create, 1)
            self.assertEqual(CustomerProfile.objects.count(), initial_profiles)
            self.assertEqual(BookingInquiry.objects.count(), 0)

            first = HistoricalPromotionService(repository).promote(apply=True)
            second = HistoricalPromotionService(repository).promote(apply=True)

            self.assertEqual(first.guests_created, 1)
            self.assertEqual(first.reservations_created, 1)
            self.assertEqual(first.guest_records_created, 1)
            self.assertEqual(second.guests_matched, 1)
            self.assertEqual(second.reservations_matched, 1)
            self.assertEqual(second.guest_records_matched, 1)
            self.assertEqual(CustomerProfile.objects.count(), initial_profiles + 1)
            self.assertEqual(BookingInquiry.objects.count(), 1)
            self.assertEqual(AirbnbGuestRecord.objects.count(), 1)

    def test_conflicting_guest_identity_stays_unresolved(self):
        initial_profiles = CustomerProfile.objects.count()
        rows = self._rows()
        conflicting = dict(rows["CUSTOMERS/customer_profiles.jsonl"][0])
        conflicting["record_key"] = "profile:42-conflict"
        conflicting["data"] = dict(conflicting["data"], email="other@example.invalid")
        rows["CUSTOMERS/customer_profiles.jsonl"].append(conflicting)
        with TemporaryDirectory() as collect_root, TemporaryDirectory() as history_root:
            self._prepare(collect_root, history_root, rows)

            result = HistoricalPromotionService(
                PreparedHistoryRepository(history_root, private_working_segment=True)
            ).promote(apply=True)

            self.assertEqual(result.guests_unresolved, 1)
            self.assertEqual(CustomerProfile.objects.count(), initial_profiles)
            self.assertEqual(BookingInquiry.objects.count(), 0)

    def test_hash_mismatch_fails_closed_before_transactional_write(self):
        initial_profiles = CustomerProfile.objects.count()
        with TemporaryDirectory() as collect_root, TemporaryDirectory() as history_root:
            self._prepare(collect_root, history_root, self._rows())
            hot_file = next(Path(history_root).glob("partitions/hot/*/clean_observations.jsonl"))
            hot_file.write_text(hot_file.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

            with self.assertRaises(ArchiveIntegrityError):
                HistoricalPromotionService(
                    PreparedHistoryRepository(history_root, private_working_segment=True)
                ).promote(apply=True)

            self.assertEqual(CustomerProfile.objects.count(), initial_profiles)
