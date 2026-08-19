from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from bookings.historical_data import (
    CollectRepository,
    FilesystemHistoryStorage,
    HistoricalDataError,
    HistoricalDataPreparationService,
    build_partition_policy,
)


class Command(BaseCommand):
    help = "Run deterministic CLEAN and PREPARE for protected Airbnb historical data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--collect-root",
            required=True,
            help="Read-only root of an existing MLADIS Object Lake COLLECT segment.",
        )
        parser.add_argument(
            "--output-root",
            required=True,
            help="Disjoint protected output root for the historical Pyramid sidecar.",
        )
        parser.add_argument(
            "--hot-policy",
            choices=("current-year", "rolling-12-months"),
            default="current-year",
            help="Hot partition policy; guest and reservation behavior is policy-independent.",
        )
        parser.add_argument(
            "--as-of",
            default="",
            help="Policy reference date in YYYY-MM-DD form; defaults to the current local date.",
        )
        parser.add_argument(
            "--resume",
            action="store_true",
            help="Reuse a complete integrity-verified result when source hashes and policy match.",
        )
        parser.add_argument(
            "--private-working-segment",
            action="store_true",
            help="Required acknowledgement that both roots are protected and excluded from public Git.",
        )

    def handle(self, *args, **options):
        try:
            as_of = self._as_of(options["as_of"])
            storage = FilesystemHistoryStorage(
                options["output_root"],
                private_working_segment=options["private_working_segment"],
            )
            service = HistoricalDataPreparationService(
                collect_repository=CollectRepository(options["collect_root"]),
                storage=storage,
                partition_policy=build_partition_policy(options["hot_policy"], as_of=as_of),
            )
            result = service.prepare(resume=options["resume"])
        except (HistoricalDataError, OSError, ValueError) as error:
            raise CommandError(str(error)) from error

        mode = "Resumed verified" if result.resumed else "Prepared"
        self.stdout.write(self.style.SUCCESS(f"{mode} Airbnb historical sidecar."))
        self.stdout.write(
            "CLEAN: "
            f"{result.clean_observation_count} observation(s), "
            f"{result.duplicate_observation_count} duplicate(s), "
            f"{result.conflict_count} conflict set(s)."
        )
        self.stdout.write(
            "PREPARE: "
            f"{result.prepared_context_count} guest/year context(s), "
            f"{result.guest_index_count} GuestHistoryIndex entry/entries."
        )
        self.stdout.write("No transactional records were created or changed.")

    @staticmethod
    def _as_of(value: str) -> date:
        if not value:
            return timezone.localdate()
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise CommandError("--as-of must use YYYY-MM-DD.") from error
