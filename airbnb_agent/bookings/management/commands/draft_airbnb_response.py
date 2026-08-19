"""Create a reviewable Airbnb response draft from one private message."""

import json
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from bookings.airbnb_response_workflow import AirbnbResponseWorkflow, ResponseWorkflowError


class Command(BaseCommand):
    help = "Create a draft-only, staff-gated Airbnb customer response."

    def add_arguments(self, parser):
        parser.add_argument(
            "--message-file",
            default="-",
            help="Read one private customer message from a protected file; '-' reads stdin.",
        )
        parser.add_argument("--item-id", type=int, default=None)

    def handle(self, *args, **options):
        try:
            message = self._read_message(options["message_file"])
            draft = AirbnbResponseWorkflow().draft(
                message,
                item_id=options["item_id"],
            )
        except (OSError, ResponseWorkflowError) as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            json.dumps(
                {
                    "topic": draft.topic,
                    "mode": draft.mode,
                    "low_stakes": draft.low_stakes,
                    "grounding_status": draft.grounding_status,
                    "risk_reasons": list(draft.risk_reasons),
                    "draft_hash": draft.draft_hash,
                    "requires_staff_confirmation": draft.requires_staff_confirmation,
                    "approved": draft.approved,
                    "sendable": draft.sendable,
                    "conversation_id": draft.conversation_id,
                    "reply": draft.reply,
                    "send_status": "draft_only",
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    @staticmethod
    def _read_message(message_file):
        if message_file == "-":
            return sys.stdin.read()
        return Path(message_file).expanduser().read_text(encoding="utf-8")
