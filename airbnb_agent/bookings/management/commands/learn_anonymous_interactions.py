"""Build the private aggregate LEARN artifact from anonymous interactions."""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bookings.interaction_learning import (
    AnonymousInteractionRepository,
    InteractionLearningError,
    InteractionLearningService,
    INTERACTION_RELATIVE_PATH,
    LEARNED_ARTIFACT_RELATIVE_PATH,
)


class Command(BaseCommand):
    help = "Derive aggregate intent and response-shape experience from anonymous interactions."

    def add_arguments(self, parser):
        parser.add_argument("--input", default="")
        parser.add_argument("--output", default="")
        parser.add_argument(
            "--private-working-segment",
            action="store_true",
            help="Acknowledge that input and output are protected non-Git data-store files.",
        )

    def handle(self, *args, **options):
        if not options["private_working_segment"]:
            raise CommandError("Learning requires --private-working-segment.")
        configured_root = str(getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        root = Path(configured_root) if configured_root else Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"
        input_path = Path(options["input"]).expanduser() if options["input"] else root / INTERACTION_RELATIVE_PATH
        output_path = Path(options["output"]).expanduser() if options["output"] else root / LEARNED_ARTIFACT_RELATIVE_PATH
        try:
            result = InteractionLearningService().learn(
                AnonymousInteractionRepository(input_path),
                output_path,
            )
        except InteractionLearningError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            json.dumps(
                {
                    "input_records": result.input_records,
                    "accepted_records": result.accepted_records,
                    "rejected_records": result.rejected_records,
                    "artifact_path": result.artifact_path,
                    "input_sha256": result.input_sha256,
                },
                indent=2,
                sort_keys=True,
            )
        )
        self.stdout.write(self.style.SUCCESS("Anonymous interaction LEARN artifact created."))
