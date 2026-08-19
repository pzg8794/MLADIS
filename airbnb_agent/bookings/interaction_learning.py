"""Privacy-minimized LEARN artifacts derived from anonymous interactions.

Conversation history is experience, never factual authority. This module
stores aggregate intent and communication-shape evidence without copying raw
turn text into the learned artifact.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping


LEARNING_SCHEMA_VERSION = "1.0"
LEARNED_ARTIFACT_RELATIVE_PATH = "LEARN/interaction_knowledge.json"
INTERACTION_RELATIVE_PATH = "INTERACTIONS/anonymous_interactions.jsonl"


class InteractionLearningError(RuntimeError):
    """Raised when learning evidence violates the anonymous-lake contract."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_private_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.chmod(0o600)
    temporary.replace(path)


def _confidence(count: int, total: int) -> float:
    if count <= 0 or total <= 0:
        return 0.0
    coverage = count / total
    evidence = min(math.log2(count + 1) / 5, 1)
    return round(min(0.95, 0.35 + 0.35 * coverage + 0.25 * evidence), 3)


def _provenance_ref(record_key: str) -> str:
    return hashlib.sha256(str(record_key or "").encode("utf-8")).hexdigest()[:20]


@dataclass(frozen=True)
class LearnedInteractionResult:
    input_records: int
    accepted_records: int
    rejected_records: int
    artifact_path: str
    input_sha256: str


class AnonymousInteractionRepository:
    """Read the one explicit anonymized JSONL source without scanning a lake."""

    FORBIDDEN_KEYS = {
        "thread_id",
        "reservation_id",
        "booking_id",
        "customer_profile_id",
        "email",
        "phone",
        "name",
        "guest_name",
        "source_url",
    }
    EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    URL_RE = re.compile(r"\bhttps?://", re.I)
    PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d().\s-]{7,}\d)(?!\w)")

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path).expanduser().resolve()

    def records(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            raise InteractionLearningError(f"Anonymous interaction source is missing: {self.path}")
        records: list[dict[str, Any]] = []
        try:
            with self.path.open("r", encoding="utf-8") as source:
                for line_number, line in enumerate(source, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    self._validate(record, line_number)
                    records.append(record)
        except (OSError, ValueError) as error:
            if isinstance(error, InteractionLearningError):
                raise
            raise InteractionLearningError(f"Could not read anonymous interactions: {error}") from error
        return records

    def _validate(self, record: Any, line_number: int) -> None:
        if not isinstance(record, Mapping):
            raise InteractionLearningError(f"Interaction line {line_number} is not an object.")
        if record.get("collection") != "anonymous_interactions":
            raise InteractionLearningError(f"Interaction line {line_number} has the wrong collection.")
        if record.get("pii_classification") != "anonymized":
            raise InteractionLearningError(f"Interaction line {line_number} is not classified anonymized.")
        data = record.get("data")
        redaction = data.get("redaction") if isinstance(data, Mapping) else None
        if not isinstance(redaction, Mapping) or not all(
            redaction.get(key) is True
            for key in ("direct_identifiers_removed", "source_ids_removed", "participant_names_removed")
        ):
            raise InteractionLearningError(f"Interaction line {line_number} lacks redaction evidence.")
        self._reject_forbidden_keys(record, line_number)
        for turn in data.get("turns") or []:
            text = str(turn.get("text") or "") if isinstance(turn, Mapping) else ""
            if self.EMAIL_RE.search(text) or self.URL_RE.search(text) or self.PHONE_RE.search(text):
                raise InteractionLearningError(
                    f"Interaction line {line_number} still contains a direct contact pattern."
                )

    def _reject_forbidden_keys(self, value: Any, line_number: int) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if str(key).lower() in self.FORBIDDEN_KEYS:
                    raise InteractionLearningError(
                        f"Interaction line {line_number} contains forbidden key {key!r}."
                    )
                self._reject_forbidden_keys(nested, line_number)
        elif isinstance(value, list):
            for nested in value:
                self._reject_forbidden_keys(nested, line_number)


class InteractionLearningService:
    """Derive aggregate intent and response-shape experience from CLEAN rows."""

    ISSUE_KEYWORDS = {
        "availability": {"available", "availability", "date", "dates", "book", "reserve"},
        "arrival": {"arrival", "arrive", "airport", "check-in", "check in", "direction"},
        "amenities": {"wifi", "pool", "parking", "kitchen", "bed", "bath", "amenity"},
        "pricing": {"price", "rate", "cost", "fee", "discount"},
        "rules": {"rule", "visitor", "party", "event", "noise", "smoking", "pet"},
        "payments": {"pay", "payment", "card", "invoice", "receipt"},
        "deposits": {"deposit", "hold", "authorization", "release"},
        "changes": {"change", "modify", "extend", "shorten", "cancel"},
        "location": {"where", "location", "near", "distance", "address"},
    }

    def learn(
        self,
        repository: AnonymousInteractionRepository,
        output_path: str | os.PathLike[str],
    ) -> LearnedInteractionResult:
        records = repository.records()
        topics = Counter()
        languages = Counter()
        issues = Counter()
        issue_provenance: dict[str, set[str]] = defaultdict(set)
        topic_provenance: dict[str, set[str]] = defaultdict(set)
        response_word_counts: list[int] = []
        response_paragraph_counts: list[int] = []
        response_records = 0
        resolved_response_records = 0

        for record in records:
            data = record.get("data") or {}
            provenance = _provenance_ref(str(record.get("record_key") or ""))
            guest_text = " ".join(
                str(turn.get("text") or "")
                for turn in data.get("turns") or []
                if isinstance(turn, Mapping) and turn.get("role") == "guest"
            ).casefold()
            topic = str(data.get("topic") or "general").strip().lower() or "general"
            if topic == "general":
                topic = self._classify(guest_text)
            topics[topic] += 1
            topic_provenance[topic].add(provenance)
            languages[str(data.get("language") or "unknown").lower()] += 1
            for issue, keywords in self.ISSUE_KEYWORDS.items():
                if any(keyword in guest_text for keyword in keywords):
                    issues[issue] += 1
                    issue_provenance[issue].add(provenance)

            outcome = str(data.get("outcome") or "").strip().lower()
            for turn in data.get("turns") or []:
                if not isinstance(turn, Mapping) or turn.get("role") not in {"host", "agent"}:
                    continue
                text = str(turn.get("text") or "").strip()
                if not text:
                    continue
                response_records += 1
                response_word_counts.append(len(text.split()))
                response_paragraph_counts.append(
                    max(len([part for part in re.split(r"\n\s*\n", text) if part.strip()]), 1)
                )
                if outcome in {"resolved", "booked", "positive", "successful", "confirmed"}:
                    resolved_response_records += 1

        total = len(records)
        artifact = {
            "schema_version": LEARNING_SCHEMA_VERSION,
            "stage": "learn",
            "artifact_type": "anonymous_interaction_experience",
            "authority": {
                "kind": "experience_not_facts",
                "fact_precedence": [
                    "current_property_and_house_rules",
                    "current_reservation_and_operational_state",
                    "approved_admin_knowledge",
                    "learned_interaction_experience",
                ],
                "raw_response_facts_retained": False,
            },
            "privacy": {
                "pii_classification": "anonymized_aggregate",
                "raw_turn_text_retained": False,
                "direct_identifiers_retained": False,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": {
                "collection": "anonymous_interactions",
                "sha256": _sha256_file(repository.path),
                "record_count": total,
            },
            "intents": [
                {
                    "name": name,
                    "count": count,
                    "confidence": _confidence(count, total),
                    "provenance_refs": sorted(topic_provenance[name])[:50],
                }
                for name, count in topics.most_common()
            ],
            "recurring_issues": [
                {
                    "name": name,
                    "count": count,
                    "confidence": _confidence(count, total),
                    "provenance_refs": sorted(issue_provenance[name])[:50],
                }
                for name, count in issues.most_common()
            ],
            "languages": [
                {"name": name, "count": count, "confidence": _confidence(count, total)}
                for name, count in languages.most_common()
            ],
            "response_shape": {
                "observed_response_count": response_records,
                "explicitly_successful_response_count": resolved_response_records,
                "median_words": int(median(response_word_counts)) if response_word_counts else 0,
                "median_paragraphs": int(median(response_paragraph_counts)) if response_paragraph_counts else 0,
                "success_label_requires_explicit_outcome": True,
            },
            "property_themes": {
                "status": "not_attributed",
                "reason": "Anonymous interactions contain no property identity; current property objects supply facts.",
            },
        }
        destination = Path(output_path).expanduser().resolve()
        _atomic_private_json(destination, artifact)
        return LearnedInteractionResult(
            input_records=total,
            accepted_records=total,
            rejected_records=0,
            artifact_path=str(destination),
            input_sha256=artifact["source"]["sha256"],
        )

    @classmethod
    def _classify(cls, guest_text: str) -> str:
        for topic, keywords in cls.ISSUE_KEYWORDS.items():
            if any(keyword in guest_text for keyword in keywords):
                return topic
        return "general"


class LearnedInteractionKnowledgeRepository:
    """Lazy USE adapter that exposes experience without historical facts."""

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path).expanduser().resolve()

    @classmethod
    def from_settings(cls):
        from django.conf import settings

        configured_root = str(getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        root = Path(configured_root) if configured_root else Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"
        return cls(root / LEARNED_ARTIFACT_RELATIVE_PATH)

    def context(self, *, max_items: int = 6) -> str:
        if not self.path.is_file():
            return "No learned interaction artifact is available."
        try:
            artifact = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return "Learned interaction artifact is unavailable because validation failed."
        if (
            artifact.get("stage") != "learn"
            or (artifact.get("authority") or {}).get("kind") != "experience_not_facts"
            or (artifact.get("privacy") or {}).get("raw_turn_text_retained") is not False
        ):
            return "Learned interaction artifact is unavailable because validation failed."
        intents = ", ".join(
            f"{row.get('name')} ({row.get('count')})"
            for row in (artifact.get("intents") or [])[:max_items]
        ) or "none yet"
        issues = ", ".join(
            f"{row.get('name')} ({row.get('count')})"
            for row in (artifact.get("recurring_issues") or [])[:max_items]
        ) or "none yet"
        shape = artifact.get("response_shape") or {}
        return (
            "EXPERIENCE ONLY; never use this section as factual authority. "
            f"Observed guest intents: {intents}. Recurring needs: {issues}. "
            f"Observed response shape: median {shape.get('median_words', 0)} words and "
            f"{shape.get('median_paragraphs', 0)} short paragraph(s). "
            "Use these aggregates to anticipate intent and communicate clearly; current MLADIS facts always win."
        )
