"""Guarded, draft-first workflow for future Airbnb guest responses."""

import hashlib
import re
from dataclasses import dataclass, replace
from uuid import uuid4

from .models import AgentConversation, BookableItem
from .services import AgentRequest, BookingAgentService, QuestionAnalyticsService


class ResponseWorkflowError(RuntimeError):
    """Raised when an outbound response cannot pass the safety contract."""


@dataclass(frozen=True)
class CustomerResponseDraft:
    reply: str
    topic: str
    mode: str
    conversation_id: int | None
    low_stakes: bool
    grounding_status: str = "property_unresolved"
    risk_reasons: tuple[str, ...] = ()
    draft_hash: str = ""
    requires_staff_confirmation: bool = True
    approved: bool = False
    sendable: bool = False


class AirbnbResponseWorkflow:
    """Create reviewable responses without silently sending to Airbnb."""

    # Only narrow, factual intents may reach the approval gate. Broad
    # "general" and rules questions require staff review because the answer
    # depends on property-specific facts and applicable policy.
    LOW_STAKES_TOPICS = {"availability", "location", "amenities", "services"}
    ESCALATION_TERMS = {
        "payment",
        "deposit",
        "refund",
        "cancel",
        "cancellation",
        "complaint",
        "damage",
        "safety",
        "legal",
        "discrimination",
        "discount",
        "special exception",
        "guarantee",
        "party",
        "parties",
        "event",
        "events",
        "birthday",
        "day-only",
        "day use",
        "day-use",
        "non-overnight",
        "without an overnight stay",
        "common area",
        "extra visitor",
        "extra guest",
        "gathering",
    }

    def __init__(self, *, agent_service=None, sender=None):
        self.agent_service = agent_service or BookingAgentService()
        self.sender = sender

    def draft(self, message, *, item_id=None, session_id=None):
        message = str(message or "").strip()
        if not message:
            raise ResponseWorkflowError("A customer message is required to create a draft.")
        session_id = session_id or f"airbnb-draft-{uuid4().hex}"
        response = self.agent_service.reply(
            AgentRequest(message=message, session_id=session_id, item_id=item_id)
        )
        conversation = AgentConversation.objects.filter(id=response.conversation_id).first()
        metadata = conversation.metadata if conversation else {}
        item = BookableItem.objects.filter(id=item_id).first() if item_id else None
        topic = QuestionAnalyticsService.classify(message)
        low_stakes = self._is_low_stakes(message, topic)
        grounding_status = "property_resolved" if item else "property_unresolved"
        risk_reasons = self._risk_reasons(message, topic, item)
        reply = self.format_reply(response.reply)
        return CustomerResponseDraft(
            reply=reply,
            topic=topic,
            mode=str((metadata or {}).get("agent_mode") or "unknown"),
            conversation_id=response.conversation_id,
            low_stakes=low_stakes,
            grounding_status=grounding_status,
            risk_reasons=risk_reasons,
            draft_hash=hashlib.sha256(reply.encode("utf-8")).hexdigest(),
        )

    def approve(self, draft):
        if not draft.requires_staff_confirmation:
            raise ResponseWorkflowError("This draft cannot be approved through the staff gate.")
        sendable = (
            draft.low_stakes
            and draft.grounding_status == "property_resolved"
            and not draft.risk_reasons
            and draft.mode == "openai"
        )
        return replace(draft, approved=True, sendable=sendable)

    def send(self, draft):
        """Fail closed until durable outbound authorization exists."""
        if not draft.approved:
            raise ResponseWorkflowError("Staff confirmation is required before sending.")
        if not draft.sendable:
            raise ResponseWorkflowError("This response requires manual review and cannot be auto-sent.")
        raise ResponseWorkflowError(
            "Live Airbnb sending is disabled until durable ResponseReview or "
            "OutboundResponseAuthorization is implemented."
        )

    @classmethod
    def _is_low_stakes(cls, message, topic):
        lowered = message.casefold()
        return topic in cls.LOW_STAKES_TOPICS and not any(term in lowered for term in cls.ESCALATION_TERMS)

    @classmethod
    def _risk_reasons(cls, message, topic, item):
        reasons = []
        if topic not in cls.LOW_STAKES_TOPICS:
            reasons.append("topic_requires_manual_review")
        if any(term in str(message or "").casefold() for term in cls.ESCALATION_TERMS):
            reasons.append("escalation_signal_detected")
        if item is None:
            reasons.append("property_not_resolved")
        return tuple(reasons)

    @staticmethod
    def format_reply(reply):
        """Make model output readable without changing its meaning."""
        return BookingAgentService._format_reply(reply)
