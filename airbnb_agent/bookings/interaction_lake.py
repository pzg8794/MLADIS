"""Anonymous conversation records for the MLADIS learning data lake."""

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .data_lake import (
    DataLakeCollection,
    DataLakeDriveMirror,
    DataLakeJsonEncoder,
    SimpleObjectLakeLayout,
)


ANONYMOUS_INTERACTIONS_COLLECTION = DataLakeCollection(
    key="anonymous_interactions",
    folder="INTERACTIONS",
    entity_type="conversation_interaction",
    description="Identity-free conversation turns used to improve guest-response quality.",
    pii_classification="anonymized",
)


class AnonymousInteractionSanitizer:
    """Apply conservative, deterministic redaction before conversation storage."""

    EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    URL_RE = re.compile(r"\bhttps?://[^\s]+", re.I)
    PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d().\s-]{5,}\d)(?!\w)")
    BOOKING_REF_RE = re.compile(
        r"\b(?:MLADIS[-_ ]?REQ|REQ|RES|RESERVATION|R|WO|D)[-_ ]?\d{3,}\b|\b\d{7,}\b",
        re.I,
    )
    ADDRESS_RE = re.compile(
        r"\b\d{1,5}\s+[A-Za-z][A-Za-z.'-]*(?:\s+[A-Za-z][A-Za-z.'-]*){0,3}\s+"
        r"(?:street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd|court|ct)\b",
        re.I,
    )
    NAME_INTRO_RE = re.compile(
        r"\b(my name is|i am|i'm|soy|me llamo)\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]*"
        r"(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]*){0,2}",
        re.I,
    )
    CAPITALIZED_NAME_RE = re.compile(
        r"\b[A-ZÀ-Ý][a-zà-ÿ'-]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ'-]+){1,2}\b"
    )

    def sanitize_text(self, value, *, known_names=()):
        text = " ".join(str(value or "").split())
        if not text:
            return ""

        if isinstance(known_names, str):
            known_names = [known_names]

        for name in sorted({str(name).strip() for name in known_names if str(name).strip()}, key=len, reverse=True):
            text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", "[person]", text, flags=re.I)

        text = self.EMAIL_RE.sub("[email]", text)
        text = self.URL_RE.sub("[url]", text)
        text = self.PHONE_RE.sub("[phone]", text)
        text = self.BOOKING_REF_RE.sub("[reference]", text)
        text = self.ADDRESS_RE.sub("[address]", text)
        text = self.NAME_INTRO_RE.sub(lambda match: f"{match.group(1)} [person]", text)
        # Catch ordinary two-token names not supplied as participant metadata.
        text = self.CAPITALIZED_NAME_RE.sub("[person]", text)
        return text

    def safe_label(self, value, *, default=""):
        label = self.sanitize_text(value)
        return label[:120] if label else default


class AnonymousInteractionLakeWriter:
    """Append sanitized conversation records and mirror them when configured."""

    def __init__(self, root, *, sanitizer=None):
        self.layout = SimpleObjectLakeLayout(root)
        self.sanitizer = sanitizer or AnonymousInteractionSanitizer()

    @classmethod
    def from_settings(cls):
        configured_root = (getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        root = configured_root or Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"
        return cls(root)

    def _known_names_for(self, conversation):
        user = getattr(conversation, "user", None)
        return [
            getattr(conversation, "visitor_name", ""),
            getattr(user, "first_name", "") if user else "",
            getattr(user, "last_name", "") if user else "",
            getattr(user, "get_full_name", lambda: "")() if user else "",
            getattr(user, "email", "") if user else "",
        ]

    def write_agent_conversation(self, conversation):
        return self.write_conversation(
            source_system="mladis",
            channel="booking_agent",
            language=getattr(conversation, "language", "") or "",
            topic=getattr(conversation, "question_topic", "") or "",
            turns=[
                {"role": "guest", "text": getattr(conversation, "last_user_message", "")},
                {"role": "agent", "text": getattr(conversation, "last_agent_reply", "")},
            ],
            known_names=self._known_names_for(conversation),
            occurred_at=getattr(conversation, "created_at", None),
        )

    def build_agent_record(self, conversation):
        return self.build_record(
            source_system="mladis",
            channel="booking_agent",
            language=getattr(conversation, "language", "") or "",
            topic=getattr(conversation, "question_topic", "") or "",
            turns=[
                {"role": "guest", "text": getattr(conversation, "last_user_message", "")},
                {"role": "agent", "text": getattr(conversation, "last_agent_reply", "")},
            ],
            known_names=self._known_names_for(conversation),
            occurred_at=getattr(conversation, "created_at", None),
        )

    def write_conversation(self, **kwargs):
        self.layout.initialize()
        record = self.build_record(**kwargs)
        path = self.layout.collection_path(ANONYMOUS_INTERACTIONS_COLLECTION)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            existing_keys = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except ValueError:
                    continue
                if existing.get("record_key"):
                    existing_keys.add(existing["record_key"])
            if record["record_key"] in existing_keys:
                return path
        with path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, cls=DataLakeJsonEncoder, sort_keys=True) + "\n")
        DataLakeDriveMirror.from_settings(self.layout.root).copy_path(path)
        return path

    def build_record(
        self,
        *,
        source_system,
        channel,
        turns,
        language="",
        topic="",
        outcome="",
        known_names=(),
        occurred_at=None,
        observation_semantics="snapshot",
    ):
        normalized_turns = []
        for index, turn in enumerate(turns or []):
            if not isinstance(turn, dict):
                continue
            role = str(turn.get("role") or "unknown").strip().lower()
            if role not in {"guest", "host", "agent", "system", "unknown"}:
                role = "unknown"
            normalized_turns.append(
                {
                    "sequence": index,
                    "role": role,
                    "text": self.sanitizer.sanitize_text(turn.get("text"), known_names=known_names),
                }
            )

        supplied_occurred_at = occurred_at
        occurred_at = occurred_at or timezone.now()
        data = {
            "language": self.sanitizer.safe_label(language, default="unknown"),
            "topic": self.sanitizer.safe_label(topic, default="general"),
            "outcome": self.sanitizer.safe_label(outcome),
            "turn_count": len(normalized_turns),
            "turns": normalized_turns,
            "observation_semantics": self.sanitizer.safe_label(
                observation_semantics, default="snapshot"
            ),
            "redaction": {
                "direct_identifiers_removed": True,
                "source_ids_removed": True,
                "participant_names_removed": True,
            },
        }
        source_label = self.sanitizer.safe_label(source_system, default="unknown")
        channel_label = self.sanitizer.safe_label(channel, default="unknown")
        occurred_at_value = self._iso(occurred_at)
        identity = {
            "source_system": source_label,
            "channel": channel_label,
            "data": data,
        }
        # A caller-provided source timestamp helps distinguish identical
        # redacted turns from different captures. Generated write timestamps
        # are deliberately excluded so retries remain idempotent.
        if supplied_occurred_at is not None:
            identity["occurred_at"] = occurred_at_value
        serialized_identity = json.dumps(
            identity,
            cls=DataLakeJsonEncoder,
            sort_keys=True,
            separators=(",", ":"),
        )
        record_key = hashlib.sha256(
            f"{ANONYMOUS_INTERACTIONS_COLLECTION.key}:{serialized_identity}".encode("utf-8")
        ).hexdigest()
        return {
            "schema_version": "1.0",
            "collection": ANONYMOUS_INTERACTIONS_COLLECTION.key,
            "entity_type": ANONYMOUS_INTERACTIONS_COLLECTION.entity_type,
            "record_key": f"conversation:{record_key}",
            "source_system": source_label,
            "channel": channel_label,
            "pii_classification": "anonymized",
            "occurred_at": occurred_at_value,
            "extracted_at": timezone.now().isoformat(),
            "data": data,
        }

    def _iso(self, value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value


def load_interaction_documents(path):
    """Load JSON or JSONL documents for the explicit Airbnb import command."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    payload = json.loads(text)
    return payload if isinstance(payload, list) else [payload]
