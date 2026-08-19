import importlib.util
import json
import sys
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from . import historical_data
from .historical_data import (
    ArchiveIntegrityError,
    CollectRepository,
    CurrentOperationalYearPolicy,
    FilesystemHistoryStorage,
    GuestHistoryIndexRepository,
    HistoricalDataError,
    HistoricalDataPreparationService,
    HistoryLookupService,
    IdempotentHistoryPromotionService,
    NullActiveHistorySource,
    PrivateWorkingSegmentRequired,
    PromotionTarget,
    RollingTwelveMonthPolicy,
)


COLLECTION_PATHS = {
    "customer_profiles": "CUSTOMERS/customer_profiles.jsonl",
    "airbnb_guest_records": "CUSTOMERS/airbnb_guest_records.jsonl",
    "booking_requests": "BOOKINGS/booking_requests.jsonl",
    "reservations": "BOOKINGS/reservations.jsonl",
    "airbnb_reservation_snapshots": "BOOKINGS/airbnb_reservation_snapshots.jsonl",
    "inventory": "STAYS/inventory.jsonl",
    "payments": "TRANSACTIONS/payments.jsonl",
    "reservation_payment_holds": "TRANSACTIONS/reservation_payment_holds.jsonl",
    "damage_deposits": "TRANSACTIONS/damage_deposits.jsonl",
    "invoices": "TRANSACTIONS/invoices.jsonl",
    "messages": "BOOKINGS/messages.jsonl",
    "work_orders": "OPERATIONS/work_orders.jsonl",
    "maintenance_events": "MAINTENANCE/maintenance_events.jsonl",
}


def envelope(collection, record_key, data, *, source_model, occurred_at="2021-01-01T00:00:00+00:00"):
    return {
        "schema_version": "1.0",
        "collection": collection,
        "entity_type": collection.rstrip("s"),
        "record_key": record_key,
        "source_system": "sanitized-fixture",
        "source_model": source_model,
        "source_pk": record_key.rsplit(":", 1)[-1],
        "pii_classification": "private",
        "occurred_at": occurred_at,
        "extracted_at": "2026-08-19T12:00:00+00:00",
        "natural_keys": {},
        "data": data,
    }


def reservation(
    *,
    guest_id=42,
    reservation_id=101,
    check_in="2021-06-01",
    check_out="2021-06-04",
    status="confirmed",
    guest_name="Sanitized Guest",
    record_key=None,
):
    return envelope(
        "reservations",
        record_key or f"reservation:{reservation_id}",
        {
            "booking_inquiry_id": reservation_id,
            "customer_profile_id": guest_id,
            "item_id": 7,
            "guest_name": guest_name,
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2,
            "status": status,
            "total_cents": 48000,
            "currency": "usd",
            "created_at": f"{str(check_in)[:4]}-01-02T10:00:00+00:00",
        },
        source_model="bookings.BookingInquiry",
        occurred_at=f"{str(check_in)[:4]}-01-02T10:00:00+00:00",
    )


class StaticActiveSource:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def lookup(self, guest_identity, year):
        self.calls.append((guest_identity, year))
        return self.result


class TrackingStorage(FilesystemHistoryStorage):
    def __init__(self, root):
        super().__init__(root, private_working_segment=True)
        self.read_paths = []
        self.verified_paths = []

    def read_json(self, relative_path):
        self.read_paths.append(relative_path)
        return super().read_json(relative_path)

    def read_jsonl(self, relative_path):
        self.read_paths.append(relative_path)
        return super().read_jsonl(relative_path)

    def verify_file(self, relative_path, *, sha256, size_bytes=None):
        self.verified_paths.append(relative_path)
        return super().verify_file(relative_path, sha256=sha256, size_bytes=size_bytes)


class MemoryPromotionTarget(PromotionTarget):
    def __init__(self):
        self.records = {}

    def contains(self, promotion_key):
        return promotion_key in self.records

    def promote(self, candidate):
        self.records[candidate["promotion_key"]] = dict(candidate)


class HistoricalDataTests(SimpleTestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        root = Path(self.temporary.name)
        self.collect_root = root / "collect"
        self.history_root = root / "history"
        self.collect_root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write_collection(self, collection, records):
        path = self.collect_root / COLLECTION_PATHS[collection]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )
        return path

    def storage(self, cls=FilesystemHistoryStorage):
        if cls is FilesystemHistoryStorage:
            return cls(self.history_root, private_working_segment=True)
        return cls(self.history_root)

    def prepare(self, *, policy=None, storage=None, resume=False):
        storage = storage or self.storage()
        policy = policy or CurrentOperationalYearPolicy(as_of=date(2026, 8, 19))
        service = HistoricalDataPreparationService(
            collect_repository=CollectRepository(self.collect_root),
            storage=storage,
            partition_policy=policy,
        )
        return service.prepare(resume=resume), storage

    def index_entry(self, storage, guest_id=42):
        return GuestHistoryIndexRepository(storage).get(f"customer_profile:{guest_id}")

    def archive_path(self, storage, *, guest_id=42, year=2021):
        entry = self.index_entry(storage, guest_id)
        partition = next(
            row for row in entry["archive_locations"] if int(row["year"]) == year
        )
        return partition["archive"]["path"]

    def test_same_customer_multiple_years_has_one_compact_index(self):
        self.write_collection(
            "reservations",
            [
                reservation(reservation_id=101, check_in="2021-06-01", check_out="2021-06-04"),
                reservation(reservation_id=202, check_in="2024-09-10", check_out="2024-09-12"),
            ],
        )

        result, storage = self.prepare()
        entry = self.index_entry(storage)

        self.assertEqual(result.guest_index_count, 1)
        self.assertEqual(
            {(row["tier"], row["year"]) for row in entry["archive_locations"]},
            {("cold", 2021), ("cold", 2024)},
        )
        self.assertEqual(entry["counts"]["reservations"], 2)
        self.assertFalse(entry["full_historical_records_duplicated"])
        self.assertNotIn("facts", entry)

    def test_duplicate_source_observations_are_collapsed_by_identity_and_fingerprint(self):
        row = reservation()
        self.write_collection("reservations", [row, row])

        result, storage = self.prepare()
        records = storage.read_jsonl("partitions/cold/2021/clean_observations.jsonl")

        self.assertEqual(result.source_record_count, 2)
        self.assertEqual(result.clean_observation_count, 1)
        self.assertEqual(result.duplicate_observation_count, 1)
        self.assertEqual(records[0]["duplicate_count"], 2)
        self.assertTrue(records[0]["observation_fingerprint"])

    def test_conflicting_guest_and_reservation_facts_remain_visible(self):
        self.write_collection(
            "reservations",
            [
                reservation(status="confirmed", guest_name="Sanitized Guest", record_key="reservation:shared"),
                reservation(status="canceled", guest_name="Sanitized Guest Revised", record_key="reservation:shared"),
            ],
        )

        result, storage = self.prepare()
        conflicts = storage.read_jsonl("conflicts.jsonl")
        context = storage.read_json(self.archive_path(storage))

        self.assertGreaterEqual(result.conflict_count, 3)
        self.assertIn("guest.name", {row["field"] for row in conflicts})
        self.assertIn("reservation.status", {row["field"] for row in conflicts})
        self.assertTrue(context["conflict_refs"])
        self.assertEqual(
            context["relationships"]["reservations"][0]["reconciliation"]["status"],
            "conflict",
        )

    def test_clean_normalizes_names_dates_amounts_and_preserves_uncertainty(self):
        row = reservation(check_in="01/02/2021", check_out="01/05/2021", guest_name="  Sanitized   Guest ")
        row["data"]["financials"] = {
            "total_amount": "1,234.5",
            "fees": "not-known",
            "currency": "usd",
        }
        self.write_collection("reservations", [row])

        _, storage = self.prepare()
        clean = storage.read_jsonl("partitions/cold/2021/clean_observations.jsonl")[0]

        self.assertEqual(clean["facts"]["guest_name"], "Sanitized Guest")
        self.assertEqual(clean["facts"]["check_in"], "2021-01-02")
        self.assertEqual(clean["facts"]["financials"]["total_amount"], "1234.50")
        self.assertIn("unparseable_amount", {item["reason"] for item in clean["uncertainty"]})

    def test_clean_redacts_secrets_provider_references_and_private_message_text(self):
        row = reservation()
        row["data"].update(
            {
                "api_secret": "sanitized-secret-placeholder",
                "stripe_payment_intent_id": "sanitized-provider-reference",
                "message": "Sanitized private message",
            }
        )
        self.write_collection("reservations", [row])

        _, storage = self.prepare()
        facts = storage.read_jsonl("partitions/cold/2021/clean_observations.jsonl")[0]["facts"]

        self.assertEqual(facts["api_secret"], "[redacted]")
        self.assertEqual(facts["stripe_payment_intent_id"], "[redacted]")
        self.assertEqual(facts["message"], "[redacted]")

    def test_prepare_models_complete_relationship_context_without_writes(self):
        self.write_collection("reservations", [reservation()])
        self.write_collection(
            "inventory",
            [
                envelope(
                    "inventory",
                    "bookable_item:7",
                    {"bookable_item_id": 7, "listing_title": "Sanitized Stay", "created_at": "2020-01-01"},
                    source_model="bookings.BookableItem",
                )
            ],
        )
        self.write_collection(
            "reservation_payment_holds",
            [
                envelope(
                    "reservation_payment_holds",
                    "payment:1",
                    {"reservation_payment_hold_id": 1, "booking_inquiry_id": 101, "amount_cents": 48000, "currency": "usd", "status": "authorized"},
                    source_model="bookings.ReservationPaymentHold",
                )
            ],
        )
        self.write_collection(
            "damage_deposits",
            [
                envelope(
                    "damage_deposits",
                    "deposit:1",
                    {"damage_deposit_id": 1, "booking_inquiry_id": 101, "amount_cents": 20000, "currency": "usd", "status": "authorized"},
                    source_model="bookings.DamageDeposit",
                )
            ],
        )
        self.write_collection(
            "invoices",
            [
                envelope(
                    "invoices",
                    "invoice:1",
                    {"invoice_id": 1, "booking_inquiry_id": 101, "customer_profile_id": 42, "invoice_number": "SAN-001", "total_cents": 48000, "currency": "usd", "status": "paid"},
                    source_model="bookings.Invoice",
                )
            ],
        )
        self.write_collection(
            "messages",
            [
                envelope(
                    "messages",
                    "message:1",
                    {"message_id": 1, "booking_inquiry_id": 101, "message_count": 3, "message": "Sanitized private body"},
                    source_model="bookings.ReservationMessage",
                )
            ],
        )
        self.write_collection(
            "maintenance_events",
            [
                envelope(
                    "maintenance_events",
                    "work_order:1",
                    {"maintenance_event_id": 1, "booking_inquiry_id": 101, "item_id": 7, "title": "Sanitized turnover", "work_type": "cleaning", "status": "completed"},
                    source_model="bookings.MaintenanceEvent",
                )
            ],
        )

        _, storage = self.prepare()
        context = storage.read_json(self.archive_path(storage))
        relationships = context["relationships"]

        self.assertEqual(
            set(relationships),
            {"guest_records", "reservations", "properties", "payments", "deposit_holds", "invoices", "messages", "work_orders"},
        )
        for key in ("reservations", "properties", "payments", "deposit_holds", "invoices", "messages", "work_orders"):
            self.assertEqual(len(relationships[key]), 1, key)
        reservation_links = relationships["reservations"][0]["relationship_refs"]
        self.assertEqual(reservation_links["payments"], ["payment:1"])
        self.assertEqual(reservation_links["deposit_holds"], ["deposit_hold:1"])
        self.assertFalse(context["reconciliation"]["authoritative_writes_performed"])

    def test_active_lookup_returns_without_any_archive_access(self):
        active_context = {
            "guest_identity": {"key": "customer_profile:42"},
            "partition": {"year": 2026},
            "relationships": {"reservations": []},
        }
        active = StaticActiveSource(active_context)
        storage = mock.Mock(spec=historical_data.HistoricalStoragePolicy)
        service = HistoryLookupService(
            active_source=active,
            index_repository=GuestHistoryIndexRepository(storage),
            storage=storage,
        )

        result = service.lookup("customer_profile:42", 2026)

        self.assertEqual(result["lookup"]["source"], "active-transactional-store")
        self.assertFalse(result["lookup"]["archive_accessed"])
        self.assertEqual(active.calls, [("customer_profile:42", 2026)])
        self.assertEqual(storage.method_calls, [])

    def test_historical_lookup_selects_only_the_requested_year(self):
        self.write_collection(
            "reservations",
            [
                reservation(reservation_id=101, check_in="2021-06-01", check_out="2021-06-04"),
                reservation(reservation_id=202, check_in="2024-09-10", check_out="2024-09-12"),
            ],
        )
        _, storage = self.prepare()

        result = HistoryLookupService(
            active_source=NullActiveHistorySource(),
            index_repository=GuestHistoryIndexRepository(storage),
            storage=storage,
        ).lookup("customer_profile:42", 2024)

        self.assertEqual(result["partition"]["year"], 2024)
        self.assertEqual(
            [row["reference"] for row in result["relationships"]["reservations"]],
            ["booking_inquiry:202"],
        )
        self.assertEqual(result["lookup"]["exact_partition_count"], 1)

    def test_rehydration_reads_only_the_targeted_guest_segment(self):
        self.write_collection(
            "reservations",
            [
                reservation(guest_id=42, reservation_id=101),
                reservation(guest_id=77, reservation_id=303, guest_name="Other Sanitized Guest"),
            ],
        )
        tracking = self.storage(TrackingStorage)
        self.prepare(storage=tracking)
        other_archive = self.archive_path(tracking, guest_id=77)
        tracking.read_paths.clear()
        tracking.verified_paths.clear()

        result = HistoryLookupService(
            active_source=NullActiveHistorySource(),
            index_repository=GuestHistoryIndexRepository(tracking),
            storage=tracking,
        ).lookup("customer_profile:42", 2021)

        self.assertEqual(result["guest_identity"]["key"], "customer_profile:42")
        self.assertNotIn(other_archive, tracking.read_paths)
        self.assertNotIn(other_archive, tracking.verified_paths)
        self.assertEqual(result["rehydration"]["state"], "temporary_prepared_context")

    def test_idempotent_promotion_port_does_not_duplicate_active_records(self):
        self.write_collection("reservations", [reservation()])
        _, storage = self.prepare()
        context = HistoryLookupService(
            active_source=NullActiveHistorySource(),
            index_repository=GuestHistoryIndexRepository(storage),
            storage=storage,
        ).lookup("customer_profile:42", 2021)
        promotion_key = context["rehydration"]["promotion_candidates"][0]["promotion_key"]
        target = MemoryPromotionTarget()
        service = IdempotentHistoryPromotionService()

        first = service.promote(context, target=target, approved_keys=[promotion_key])
        second = service.promote(context, target=target, approved_keys=[promotion_key])

        self.assertEqual(first.promoted, 1)
        self.assertEqual(second.already_present, 1)
        self.assertEqual(len(target.records), 1)

    def test_missing_archive_fails_closed(self):
        self.write_collection("reservations", [reservation()])
        _, storage = self.prepare()
        relative_path = self.archive_path(storage)
        (self.history_root / relative_path).unlink()

        with self.assertRaisesRegex(ArchiveIntegrityError, "missing"):
            HistoryLookupService(
                active_source=NullActiveHistorySource(),
                index_repository=GuestHistoryIndexRepository(storage),
                storage=storage,
            ).lookup("customer_profile:42", 2021)

    def test_corrupted_archive_fails_closed_before_read(self):
        self.write_collection("reservations", [reservation()])
        _, storage = self.prepare()
        relative_path = self.archive_path(storage)
        (self.history_root / relative_path).write_text("{broken", encoding="utf-8")

        with self.assertRaisesRegex(ArchiveIntegrityError, "size mismatch"):
            HistoryLookupService(
                active_source=NullActiveHistorySource(),
                index_repository=GuestHistoryIndexRepository(storage),
                storage=storage,
            ).lookup("customer_profile:42", 2021)

    def test_same_size_hash_mismatch_fails_closed(self):
        self.write_collection("reservations", [reservation()])
        _, storage = self.prepare()
        relative_path = self.archive_path(storage)
        path = self.history_root / relative_path
        original = path.read_bytes()
        replacement = bytes([original[0] ^ 1]) + original[1:]
        self.assertEqual(len(original), len(replacement))
        path.write_bytes(replacement)

        with self.assertRaisesRegex(ArchiveIntegrityError, "hash mismatch"):
            HistoryLookupService(
                active_source=NullActiveHistorySource(),
                index_repository=GuestHistoryIndexRepository(storage),
                storage=storage,
            ).lookup("customer_profile:42", 2021)

    def test_import_and_reload_do_not_scan_or_read_archives(self):
        module_name = "bookings._historical_data_import_probe"
        spec = importlib.util.spec_from_file_location(module_name, historical_data.__file__)
        probe = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = probe
        try:
            with (
                mock.patch.object(Path, "rglob", side_effect=AssertionError("archive scan")),
                mock.patch.object(Path, "glob", side_effect=AssertionError("archive scan")),
                mock.patch.object(Path, "iterdir", side_effect=AssertionError("archive scan")),
                mock.patch.object(Path, "read_text", side_effect=AssertionError("archive read")),
                mock.patch.object(Path, "open", side_effect=AssertionError("archive read")),
            ):
                spec.loader.exec_module(probe)
        finally:
            sys.modules.pop(module_name, None)

    def test_private_working_segment_is_explicit_and_manifest_rejects_private_git_dataset(self):
        with self.assertRaises(PrivateWorkingSegmentRequired):
            FilesystemHistoryStorage(self.history_root, private_working_segment=False)
        self.write_collection("reservations", [reservation()])

        _, storage = self.prepare()
        manifest = storage.read_json("manifest.json")

        self.assertEqual(manifest["visibility"], "private-protected")
        self.assertFalse(manifest["private_git_dataset_used"])
        self.assertEqual(manifest["transactional_source_of_truth"], "MLADIS Django transactional store")

    def test_collect_and_output_roots_must_be_disjoint(self):
        self.write_collection("reservations", [reservation()])
        nested_output = self.collect_root / "history"
        storage = FilesystemHistoryStorage(nested_output, private_working_segment=True)

        with self.assertRaisesRegex(HistoricalDataError, "disjoint"):
            HistoricalDataPreparationService(
                collect_repository=CollectRepository(self.collect_root),
                storage=storage,
                partition_policy=CurrentOperationalYearPolicy(as_of=date(2026, 8, 19)),
            )

    def test_resume_is_deterministic_and_integrity_verified(self):
        self.write_collection("reservations", [reservation()])
        first, storage = self.prepare()
        first_manifest = (self.history_root / "manifest.json").read_bytes()

        second, _ = self.prepare(storage=storage, resume=True)
        second_manifest = (self.history_root / "manifest.json").read_bytes()

        self.assertFalse(first.resumed)
        self.assertTrue(second.resumed)
        self.assertEqual(first.input_digest, second.input_digest)
        self.assertEqual(first_manifest, second_manifest)

    def test_hot_policy_can_change_without_changing_relationship_behavior(self):
        self.write_collection(
            "reservations",
            [reservation(check_in="2025-12-01", check_out="2025-12-03")],
        )
        current_result, current_storage = self.prepare(
            policy=CurrentOperationalYearPolicy(as_of=date(2026, 8, 19))
        )
        current_entry = self.index_entry(current_storage)

        rolling_root = Path(self.temporary.name) / "rolling-history"
        rolling_storage = FilesystemHistoryStorage(rolling_root, private_working_segment=True)
        rolling_result, _ = self.prepare(
            policy=RollingTwelveMonthPolicy(as_of=date(2026, 8, 19)),
            storage=rolling_storage,
        )
        rolling_entry = self.index_entry(rolling_storage)

        self.assertEqual(current_result.prepared_context_count, rolling_result.prepared_context_count)
        self.assertEqual(current_entry["references"], rolling_entry["references"])
        self.assertEqual(current_entry["archive_locations"][0]["tier"], "cold")
        self.assertEqual(rolling_entry["archive_locations"][0]["tier"], "hot")

    def test_prepare_command_requires_private_acknowledgement_and_runs_one_command_path(self):
        self.write_collection("reservations", [reservation()])
        with self.assertRaises(CommandError):
            call_command(
                "prepare_airbnb_history",
                collect_root=str(self.collect_root),
                output_root=str(self.history_root),
                as_of="2026-08-19",
            )

        output = mock.Mock()
        call_command(
            "prepare_airbnb_history",
            collect_root=str(self.collect_root),
            output_root=str(self.history_root),
            as_of="2026-08-19",
            private_working_segment=True,
            stdout=output,
        )

        self.assertTrue((self.history_root / "manifest.json").is_file())
