"""Promote verified hot Airbnb history into MLADIS transactional objects."""

import json

from django.core.management.base import BaseCommand, CommandError

from bookings.historical_data import ArchiveIntegrityError, PrivateWorkingSegmentRequired, write_private_json
from bookings.historical_promotion import (
    HistoricalPromotionError,
    HistoricalPromotionService,
    PreparedHistoryRepository,
)


class Command(BaseCommand):
    help = "Reconcile verified hot PREPARE history into CustomerProfile and BookingInquiry objects."

    def add_arguments(self, parser):
        parser.add_argument("--history-root", required=True)
        parser.add_argument(
            "--private-working-segment",
            action="store_true",
            help="Acknowledge that the history root is a protected, non-Git working segment.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write reconciled objects. Without this flag the command is a dry run.",
        )
        parser.add_argument("--limit-guests", type=int, default=None)
        parser.add_argument(
            "--report",
            default="",
            help="Optional protected JSON path for a count-only promotion report.",
        )

    def handle(self, *args, **options):
        try:
            repository = PreparedHistoryRepository(
                options["history_root"],
                private_working_segment=options["private_working_segment"],
            )
            result = HistoricalPromotionService(repository).promote(
                apply=options["apply"],
                limit_guests=options["limit_guests"],
            )
        except (ArchiveIntegrityError, HistoricalPromotionError, PrivateWorkingSegmentRequired) as error:
            raise CommandError(str(error)) from error

        payload = result.to_record()
        if options["report"]:
            write_private_json(options["report"], payload)
        self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        if options["apply"]:
            self.stdout.write(self.style.SUCCESS("Verified hot-history promotion completed."))
        else:
            self.stdout.write(self.style.WARNING("Dry run only; no transactional records were written."))
