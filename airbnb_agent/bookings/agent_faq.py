import re
from dataclasses import dataclass
from decimal import Decimal

from django.db import OperationalError, ProgrammingError, connection


_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class AgentFAQMatch:
    id: int
    answer: str
    category: str
    score: Decimal


class LocalAgentFAQService:
    """Answers common MLADIS booking questions without spending OpenAI API credits.

    The public booking agent should call this before OpenAI. It uses a small local
    database table seeded by migrations and editable with the seed_agent_faqs
    management command. If the table is missing or no match is confident enough,
    it quietly returns None and lets the normal OpenAI flow continue.
    """

    TABLE = "bookings_agentfaq"
    DEFAULT_LIMIT = 80

    def match(self, message, item=None):
        normalized_message = self._normalize(message)
        message_tokens = self._tokens(normalized_message)
        if len(message_tokens) < 2:
            return None

        rows = self._fetch_rows(item=item)
        best = None
        for row in rows:
            score = self._score(normalized_message, message_tokens, row)
            min_score = Decimal(str(row["min_score"] or "0.55"))
            if score < min_score:
                continue
            match = AgentFAQMatch(
                id=row["id"],
                answer=row["answer"],
                category=row["category"] or "general",
                score=score,
            )
            if best is None or (match.score, row["priority"]) > (best.score, best_priority):
                best = match
                best_priority = row["priority"]
        return best

    def _fetch_rows(self, item=None):
        item_id = getattr(item, "id", None)
        sql = f"""
            SELECT id, category, question, answer, keywords, min_score, priority
            FROM {self.TABLE}
            WHERE is_active = TRUE
              AND (item_id IS NULL OR item_id = %s)
            ORDER BY priority DESC, id ASC
            LIMIT %s
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, [item_id, self.DEFAULT_LIMIT])
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except (OperationalError, ProgrammingError):
            return []

    def _score(self, normalized_message, message_tokens, row):
        question = self._normalize(row["question"] or "")
        keywords = self._split_keywords(row["keywords"] or "")
        faq_tokens = self._tokens(" ".join([question, *keywords]))
        if not faq_tokens:
            return Decimal("0")

        overlap = len(message_tokens & faq_tokens) / max(min(len(message_tokens), len(faq_tokens)), 1)
        phrase_hits = sum(1 for phrase in keywords if phrase and phrase in normalized_message)
        phrase_bonus = min(phrase_hits * 0.18, 0.36)
        question_bonus = Decimal("0.12") if question and question in normalized_message else Decimal("0")
        score = Decimal(str(min(overlap + phrase_bonus, 1))) + question_bonus
        return min(score, Decimal("1"))

    def _normalize(self, value):
        return " ".join(_WORD_RE.findall((value or "").lower()))

    def _tokens(self, value):
        return {word for word in _WORD_RE.findall(value or "") if len(word) >= 3}

    def _split_keywords(self, value):
        return [self._normalize(part) for part in (value or "").split(",") if self._normalize(part)]


def install_agent_faq_patch():
    """Patch BookingAgentService.reply so FAQ hits skip OpenAI calls.

    This keeps the existing guardrails and fallback flow intact. Only confident
    local matches are intercepted; everything else uses the current agent logic.
    """
    from .models import AgentConversation
    from .services import AgentResponse, BookingAgentService, QuestionAnalyticsService

    if getattr(BookingAgentService, "_local_faq_installed", False):
        return

    original_reply = BookingAgentService.reply

    def reply_with_local_faq(self, request):
        item = self._get_item(request.item_id)
        topic = QuestionAnalyticsService.classify(request.message)
        metadata = {"topic": topic}

        faq_match = LocalAgentFAQService().match(request.message, item=item)
        if faq_match:
            metadata.update(
                {
                    "agent_mode": "faq",
                    "faq_id": faq_match.id,
                    "faq_category": faq_match.category,
                    "faq_score": str(faq_match.score),
                    "openai_skipped": True,
                }
            )
            conversation = AgentConversation.objects.create(
                session_id=request.session_id,
                item=item,
                visitor_name=request.visitor_name,
                visitor_email=request.visitor_email,
                last_user_message=request.message,
                last_agent_reply=faq_match.answer,
                question_topic=topic,
                metadata=metadata,
            )
            return AgentResponse(reply=faq_match.answer, conversation_id=conversation.id)

        return original_reply(self, request)

    BookingAgentService.reply = reply_with_local_faq
    BookingAgentService._local_faq_installed = True
