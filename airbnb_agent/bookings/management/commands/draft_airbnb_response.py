"""Create a reviewable Airbnb response draft from one private message."""

import json

from django.core.management.base import BaseCommand, CommandError

from bookings.airbnb_response_workflow import AirbnbResponseWorkflow, ResponseWorkflowError


class Command(BaseCommand):
    help = "Create a draft-only, staff-gated Airbnb customer response."

    def add_arguments(self, parser):
        parser.add_argument("--message", required=True, help="One private customer message; never committed or logged.")
        parser.add_argument("--item-id", type=int, default=None)
        parser.add_argument("--session-id", default="")

    def handle(self, *args, **options):
        try:
            draft = AirbnbResponseWorkflow().draft(
                options["message"],
                item_id=options["item_id"],
                session_id=options["session_id"] or None,
            )
        except ResponseWorkflowError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            json.dumps(
                {
                    "topic": draft.topic,
                    "mode": draft.mode,
                    "low_stakes": draft.low_stakes,
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
