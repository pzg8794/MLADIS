from datetime import date, datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from bookings.historical_data import (
    ArchiveIntegrityError,
    FilesystemHistoryStorage,
    GuestHistoryIndexRepository,
    HistoricalDataError,
    HistoryLookupService,
    HistoryNotFoundError,
    write_private_json,
)


def _iso(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value


class DjangoActiveHistorySource:
    """Read-only adapter over current transactional records."""

    def lookup(self, guest_identity: str, year: int) -> dict[str, Any] | None:
        if not guest_identity.startswith("customer_profile:"):
            return None
        raw_profile_id = guest_identity.partition(":")[2]
        try:
            profile_id = int(raw_profile_id)
        except ValueError:
            return None

        from bookings.models import (  # Imported only for an explicit command run.
            AirbnbGuestRecord,
            BookingInquiry,
            CustomerProfile,
            DamageDeposit,
            Invoice,
            MaintenanceEvent,
            ReservationPaymentHold,
        )

        if not CustomerProfile.objects.filter(pk=profile_id).exists():
            return None
        reservations = list(
            BookingInquiry.objects.filter(customer_profile_id=profile_id, check_in__year=year)
            .values("id", "item_id", "status", "check_in", "check_out", "guests")
            .order_by("id")
        )
        guest_records = list(
            AirbnbGuestRecord.objects.filter(customer_profile_id=profile_id, check_in__year=year)
            .values("id", "item_id", "check_in", "check_out", "guests", "rating")
            .order_by("id")
        )
        if not reservations and not guest_records:
            return None

        reservation_ids = [row["id"] for row in reservations]
        payment_rows = list(
            ReservationPaymentHold.objects.filter(inquiry_id__in=reservation_ids)
            .values("id", "inquiry_id", "item_id", "amount_cents", "currency", "status")
            .order_by("id")
        )
        deposit_rows = list(
            DamageDeposit.objects.filter(inquiry_id__in=reservation_ids)
            .values("id", "inquiry_id", "item_id", "amount_cents", "currency", "status")
            .order_by("id")
        )
        invoice_rows = list(
            Invoice.objects.filter(customer_profile_id=profile_id, inquiry_id__in=reservation_ids)
            .values("id", "inquiry_id", "invoice_number", "total_cents", "currency", "status")
            .order_by("id")
        )
        work_order_rows = list(
            MaintenanceEvent.objects.filter(booking_id__in=reservation_ids)
            .values("id", "booking_id", "item_id", "work_type", "status", "reported_at")
            .order_by("id")
        )

        properties = {
            f"bookable_item:{row['item_id']}"
            for row in (*reservations, *guest_records)
            if row.get("item_id")
        }
        relationships = {
            "guest_records": [
                self._relation(
                    f"airbnb_guest_record:{row['id']}",
                    row,
                    summary_fields=("check_in", "check_out", "guests", "rating"),
                )
                for row in guest_records
            ],
            "reservations": [self._active_reservation(row) for row in reservations],
            "properties": [
                {
                    "reference": reference,
                    "observation_refs": [],
                    "source_models": ["bookings.BookableItem"],
                    "conflict_refs": [],
                    "observations": [],
                }
                for reference in sorted(properties)
            ],
            "payments": [
                self._dependent_relation("reservation_payment_hold", row, "inquiry_id")
                for row in payment_rows
            ],
            "deposit_holds": [
                self._dependent_relation("damage_deposit", row, "inquiry_id")
                for row in deposit_rows
            ],
            "invoices": [
                self._dependent_relation("invoice", row, "inquiry_id")
                for row in invoice_rows
            ],
            "messages": [],
            "work_orders": [
                self._dependent_relation("work_order", row, "booking_id")
                for row in work_order_rows
            ],
        }
        latest_activity = max(
            [
                _iso(row.get("check_in")) or ""
                for row in (*reservations, *guest_records)
            ],
            default="",
        )
        return {
            "schema_version": "1.0",
            "projection_type": "active_guest_history_context",
            "guest_identity": {
                "key": guest_identity,
                "kind": "CustomerProfile",
                "resolution": {
                    "status": "confirmed",
                    "authoritative_write": False,
                },
            },
            "partition": {"tier": "active", "year": year},
            "latest_activity_at": latest_activity,
            "relationships": relationships,
            "reconciliation": {
                "source": "MLADIS transactional store",
                "authoritative_writes_performed": False,
            },
        }

    @staticmethod
    def _relation(reference, row, *, summary_fields):
        return {
            "reference": reference,
            "observation_refs": [],
            "source_models": [],
            "conflict_refs": [],
            "observations": [
                {
                    "observation_ref": "active-transactional-store",
                    "summary": {
                        field: _iso(row.get(field))
                        for field in summary_fields
                        if row.get(field) not in (None, "")
                    },
                }
            ],
        }

    def _active_reservation(self, row):
        relation = self._relation(
            f"booking_inquiry:{row['id']}",
            row,
            summary_fields=("status", "check_in", "check_out", "guests"),
        )
        relation["source_models"] = ["bookings.BookingInquiry"]
        relation["property_refs"] = (
            [f"bookable_item:{row['item_id']}"] if row.get("item_id") else []
        )
        relation["reconciliation"] = {
            "status": "active",
            "authoritative_write": False,
        }
        return relation

    def _dependent_relation(self, prefix, row, reservation_field):
        relation = self._relation(
            f"{prefix}:{row['id']}",
            row,
            summary_fields=("amount_cents", "total_cents", "currency", "status", "work_type", "reported_at"),
        )
        relation["reservation_ref"] = f"booking_inquiry:{row[reservation_field]}"
        return relation


class Command(BaseCommand):
    help = "Lookup current history first, then rehydrate one verified guest/year archive context."

    def add_arguments(self, parser):
        parser.add_argument("--history-root", required=True, help="Protected historical sidecar root.")
        parser.add_argument(
            "--guest-id",
            required=True,
            help="Stable CustomerProfile ID or customer_profile:<id> identity.",
        )
        parser.add_argument("--year", required=True, type=int, help="Exact activity year to request.")
        parser.add_argument(
            "--temporary-output",
            default="",
            help="Optional protected path for the temporary prepared context (written mode 0600).",
        )
        parser.add_argument(
            "--private-working-segment",
            action="store_true",
            help="Required acknowledgement that the archive and any output are protected and outside public Git.",
        )

    def handle(self, *args, **options):
        guest_identity = self._guest_identity(options["guest_id"])
        try:
            storage = FilesystemHistoryStorage(
                options["history_root"],
                private_working_segment=options["private_working_segment"],
            )
            context = HistoryLookupService(
                active_source=DjangoActiveHistorySource(),
                index_repository=GuestHistoryIndexRepository(storage),
                storage=storage,
            ).lookup(guest_identity, options["year"])
            if options["temporary_output"]:
                write_private_json(options["temporary_output"], context)
        except (ArchiveIntegrityError, HistoricalDataError, HistoryNotFoundError, OSError, ValueError) as error:
            raise CommandError(str(error)) from error

        relationships = context.get("relationships") or {}
        source = (context.get("lookup") or {}).get("source", "unknown")
        self.stdout.write(self.style.SUCCESS(f"Historical lookup complete from {source}."))
        self.stdout.write(
            "Context references: "
            + ", ".join(
                f"{key}={len(value)}"
                for key, value in sorted(relationships.items())
                if isinstance(value, list)
            )
        )
        self.stdout.write("No transactional records were created or changed.")

    @staticmethod
    def _guest_identity(value: str) -> str:
        normalized = str(value).strip()
        if normalized.startswith("customer_profile:"):
            return normalized
        try:
            return f"customer_profile:{int(normalized)}"
        except ValueError as error:
            raise CommandError("--guest-id must be a CustomerProfile integer ID.") from error
