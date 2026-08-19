import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase, override_settings

from .airbnb_outbound import (
    OutboundAuthorizationError,
    OutboundAuthorizationRepository,
    OutboundAuthorizationService,
)
from .airbnb_response_workflow import AirbnbResponseWorkflow, ResponseWorkflowError
from .models import AgentConversation, BookableItem, HouseRule
from .services import AgentResponse


class FakeAgentService:
    def __init__(self, reply="The property includes on-site parking for registered guests."):
        self.reply_text = reply

    def reply(self, request):
        conversation = AgentConversation.objects.create(
            session_id=request.session_id,
            item_id=request.item_id,
            last_user_message=request.message,
            last_agent_reply=self.reply_text,
            question_topic="amenities",
            metadata={"agent_mode": "openai"},
        )
        return AgentResponse(reply=self.reply_text, conversation_id=conversation.pk)


class AirbnbOutboundAuthorizationTests(TestCase):
    def setUp(self):
        self.item = BookableItem.objects.create(
            name="Rules Grounded Stay",
            slug="rules-grounded-stay",
            short_description="A test stay.",
            location_label="Santo Domingo Norte",
        )
        self.rule = HouseRule.objects.create(
            item=self.item,
            title="Parking",
            description="Parking is available for registered guests.",
        )

    def _workflow(self, root, *, sender=None, reply=None):
        repository = OutboundAuthorizationRepository(root)
        authorization_service = OutboundAuthorizationService(repository=repository)
        return AirbnbResponseWorkflow(
            agent_service=FakeAgentService(reply=reply or "The property includes on-site parking for registered guests."),
            sender=sender,
            authorization_service=authorization_service,
        )

    def test_authorized_low_stakes_send_is_idempotent(self):
        deliveries = []

        def sender(reply, *, thread_key, authorization_id):
            deliveries.append((reply, thread_key, authorization_id))
            return {"provider_message_id": "provider-message-1"}

        with TemporaryDirectory() as root:
            workflow = self._workflow(root, sender=sender)
            inbound = "Does the property have parking?"
            draft = workflow.draft(inbound, item_id=self.item.pk)
            authorization = workflow.authorize_automatic(
                draft,
                thread_key="private-thread-key",
                latest_message=inbound,
            )

            completed = workflow.send(
                draft,
                authorization=authorization,
                thread_key="private-thread-key",
                latest_message=inbound,
            )

            self.assertEqual(completed.status, "sent")
            self.assertEqual(len(deliveries), 1)
            with self.assertRaisesRegex(ResponseWorkflowError, "duplicate or uncertain"):
                workflow.send(
                    draft,
                    authorization=authorization,
                    thread_key="private-thread-key",
                    latest_message=inbound,
                )
            self.assertEqual(len(deliveries), 1)

    def test_new_customer_message_invalidates_authorization(self):
        with TemporaryDirectory() as root:
            workflow = self._workflow(root, sender=lambda *_args, **_kwargs: "should-not-send")
            inbound = "Does the property have parking?"
            draft = workflow.draft(inbound, item_id=self.item.pk)
            authorization = workflow.authorize_automatic(
                draft,
                thread_key="private-thread-key",
                latest_message=inbound,
            )

            with self.assertRaisesRegex(ResponseWorkflowError, "inbound_message_hash"):
                workflow.send(
                    draft,
                    authorization=authorization,
                    thread_key="private-thread-key",
                    latest_message="Does it also have a private pool?",
                )

    def test_changed_house_rule_invalidates_authorization(self):
        with TemporaryDirectory() as root:
            workflow = self._workflow(root, sender=lambda *_args, **_kwargs: "should-not-send")
            inbound = "Does the property have parking?"
            draft = workflow.draft(inbound, item_id=self.item.pk)
            authorization = workflow.authorize_automatic(
                draft,
                thread_key="private-thread-key",
                latest_message=inbound,
            )
            self.rule.description = "Parking now requires staff confirmation."
            self.rule.save(update_fields=["description"])

            with self.assertRaisesRegex(ResponseWorkflowError, "rules_digest"):
                workflow.send(
                    draft,
                    authorization=authorization,
                    thread_key="private-thread-key",
                    latest_message=inbound,
                )

    def test_expired_authorization_cannot_be_claimed(self):
        with TemporaryDirectory() as root:
            workflow = self._workflow(root)
            inbound = "Does the property have parking?"
            draft = workflow.draft(inbound, item_id=self.item.pk)
            created_at = datetime(2026, 8, 19, tzinfo=timezone.utc)
            authorization = workflow.authorization_service.authorize(
                draft,
                thread_key="private-thread-key",
                latest_message=inbound,
                now=created_at,
            )

            with self.assertRaisesRegex(OutboundAuthorizationError, "expired"):
                workflow.authorization_service.claim(
                    authorization.authorization_id,
                    thread_key="private-thread-key",
                    latest_message=inbound,
                    draft_hash=draft.draft_hash,
                    now=created_at + timedelta(minutes=11),
                )

    def test_availability_is_drafted_but_not_auto_authorized(self):
        with TemporaryDirectory() as root:
            workflow = self._workflow(root)
            inbound = "Is the property available next weekend?"
            draft = workflow.draft(inbound, item_id=self.item.pk)

            with self.assertRaisesRegex(ResponseWorkflowError, "topic_not_auto_send_eligible"):
                workflow.authorize_automatic(
                    draft,
                    thread_key="private-thread-key",
                    latest_message=inbound,
                )

    def test_financial_or_visitor_questions_never_auto_authorize(self):
        with TemporaryDirectory() as root:
            workflow = self._workflow(root)
            for inbound in (
                "Can you refund the deposit?",
                "Can I bring extra visitors to a birthday gathering?",
            ):
                draft = workflow.draft(inbound, item_id=self.item.pk)
                with self.assertRaises(ResponseWorkflowError):
                    workflow.authorize_automatic(
                        draft,
                        thread_key="private-thread-key",
                        latest_message=inbound,
                    )

    @override_settings(OPENAI_API_KEY="")
    def test_private_command_holds_setup_mode_without_exposing_message(self):
        with TemporaryDirectory() as root:
            input_path = Path(root) / "input.json"
            output_path = Path(root) / "output.json"
            input_path.write_text(
                json.dumps(
                    {
                        "thread_key": "private-thread-key",
                        "latest_message": "Does the property have parking?",
                        "item_id": self.item.pk,
                    }
                ),
                encoding="utf-8",
            )
            os.chmod(input_path, 0o600)

            call_command(
                "process_airbnb_auto_response",
                "prepare",
                input=str(input_path),
                output=str(output_path),
                authorize_low_stakes=True,
                verbosity=0,
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "held")
            self.assertIn("live_model_not_available", payload["hold_reason"])
            self.assertEqual(output_path.stat().st_mode & 0o777, 0o600)
