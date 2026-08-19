import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.test import TestCase, override_settings

from .interaction_lake import AnonymousInteractionLakeWriter
from .interaction_learning import (
    AnonymousInteractionRepository,
    InteractionLearningError,
    InteractionLearningService,
    LearnedInteractionKnowledgeRepository,
)
from .models import BookableItem, HouseRule
from .services import AgentRequest, BookingAgentService


class InteractionLearningTests(TestCase):
    def _artifact(self, root):
        source = Path(root) / "INTERACTIONS" / "anonymous_interactions.jsonl"
        writer = AnonymousInteractionLakeWriter(root)
        writer.write_conversation(
            source_system="airbnb",
            channel="host_messages",
            language="en",
            topic="amenities",
            outcome="resolved",
            turns=[
                {"role": "guest", "text": "Is parking available?"},
                {"role": "host", "text": "Parking is free."},
            ],
            occurred_at="2026-06-01T10:00:00+00:00",
        )
        output = Path(root) / "LEARN" / "interaction_knowledge.json"
        InteractionLearningService().learn(AnonymousInteractionRepository(source), output)
        return output

    def test_learning_artifact_keeps_aggregates_not_raw_factual_answers(self):
        with TemporaryDirectory() as root:
            output = self._artifact(root)
            payload = json.loads(output.read_text(encoding="utf-8"))
            serialized = output.read_text(encoding="utf-8")

            self.assertEqual(payload["authority"]["kind"], "experience_not_facts")
            self.assertFalse(payload["privacy"]["raw_turn_text_retained"])
            self.assertEqual(payload["intents"][0]["name"], "amenities")
            self.assertNotIn("Parking is free", serialized)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_learning_rejects_a_record_without_redaction_evidence(self):
        with TemporaryDirectory() as root:
            source = Path(root) / "interactions.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "collection": "anonymous_interactions",
                        "pii_classification": "anonymized",
                        "record_key": "conversation:test",
                        "data": {"turns": []},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(InteractionLearningError):
                InteractionLearningService().learn(
                    AnonymousInteractionRepository(source),
                    Path(root) / "learn.json",
                )

    @override_settings(OPENAI_AGENT_MODEL="gpt-5.4-nano")
    def test_current_house_rule_overrides_stale_conversation_experience(self):
        with TemporaryDirectory() as root:
            output = self._artifact(root)
            item = BookableItem.objects.create(
                name="Current Facts Stay",
                slug="current-facts-stay",
                short_description="A current-facts test stay.",
            )
            HouseRule.objects.create(
                item=item,
                title="Parking",
                description="Parking is $15 per day.",
            )

            class FakeResponses:
                def __init__(self):
                    self.kwargs = None

                def create(self, **kwargs):
                    self.kwargs = kwargs
                    return SimpleNamespace(output_text="Parking is $15 per day.", id="resp-learn")

            responses = FakeResponses()
            service = BookingAgentService(
                api_key="sk-test",
                client=SimpleNamespace(responses=responses),
                learned_repository=LearnedInteractionKnowledgeRepository(output),
            )
            reply, response_id = service._openai_reply(
                AgentRequest(
                    message="Is parking available?",
                    session_id="learned-context-test",
                    item_id=item.pk,
                ),
                item,
            )

            self.assertEqual(reply, "Parking is $15 per day.")
            self.assertEqual(response_id, "resp-learn")
            self.assertIn("Parking: Parking is $15 per day.", responses.kwargs["input"])
            self.assertIn("EXPERIENCE ONLY", responses.kwargs["input"])
            self.assertNotIn("Parking is free", responses.kwargs["input"])
            self.assertIn("always override conversation-derived experience", responses.kwargs["instructions"])
