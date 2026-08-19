"""Durable authorization for narrowly scoped Airbnb customer responses.

The authorization ledger stores hashes and delivery state, not customer
messages or response bodies. A send must still present the exact private
thread, latest inbound message, draft, property, and current rule digest.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from django.conf import settings
from django.db.models import Q

from .models import BookableItem, HouseRule


AUTHORIZATION_SCHEMA_VERSION = "1.0"
AUTHORIZATION_RELATIVE_PATH = "OUTBOUND/AIRBNB/authorizations"


class OutboundAuthorizationError(RuntimeError):
    """Raised when a response is not authorized for a provider send."""


def private_hash(value: str) -> str:
    normalized = str(value or "").replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def current_rules_digest(item: BookableItem) -> tuple[str, int]:
    rules = list(
        HouseRule.objects.filter(is_active=True).filter(Q(item__isnull=True) | Q(item=item))
        .order_by("item_id", "sort_order", "id")
        .values("item_id", "title", "description", "source_label", "source_url")
    )
    payload = {
        "item": {
            "id": item.pk,
            "name": item.name,
            "is_active": item.is_active,
            "location_label": item.location_label,
            "max_guests": item.max_guests,
            "starting_price": str(item.starting_price) if item.starting_price is not None else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else "",
        },
        "rules": rules,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return private_hash(serialized), len(rules)


@dataclass(frozen=True)
class OutboundResponseAuthorization:
    authorization_id: str
    idempotency_key: str
    thread_key_hash: str
    inbound_message_hash: str
    draft_hash: str
    item_id: int
    rules_digest: str
    topic: str
    policy: str
    status: str
    created_at: str
    expires_at: str
    claimed_at: str = ""
    completed_at: str = ""
    provider_message_id: str = ""
    failure_reason: str = ""
    schema_version: str = AUTHORIZATION_SCHEMA_VERSION

    @classmethod
    def from_record(cls, record: Mapping[str, Any]):
        values = {field: record.get(field, "") for field in cls.__dataclass_fields__}
        values["item_id"] = int(values["item_id"] or 0)
        return cls(**values)


class OutboundAuthorizationRepository:
    """Private, atomic, idempotent authorization ledger."""

    SAFE_ID_RE = re.compile(r"^airbnb-[a-f0-9]{32}$")

    def __init__(self, root: str | os.PathLike[str] | None = None):
        if root is None:
            configured = str(getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
            datastore = (
                Path(configured)
                if configured
                else Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"
            )
            root = datastore / AUTHORIZATION_RELATIVE_PATH
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.lock_path = self.root / ".ledger.lock"

    def create(self, authorization: OutboundResponseAuthorization):
        with self._locked():
            path = self._path(authorization.authorization_id)
            if path.exists():
                existing = self._read_path(path)
                if existing.idempotency_key != authorization.idempotency_key:
                    raise OutboundAuthorizationError("Authorization identity collision.")
                return existing
            self._write_path(path, authorization)
            return authorization

    def get(self, authorization_id: str):
        with self._locked():
            path = self._path(authorization_id)
            if not path.is_file():
                raise OutboundAuthorizationError("Outbound authorization was not found.")
            return self._read_path(path)

    def claim(
        self,
        authorization_id: str,
        *,
        thread_key: str,
        latest_message: str,
        draft_hash: str,
        rules_digest: str,
        now: datetime | None = None,
    ):
        now = now or datetime.now(timezone.utc)
        with self._locked():
            path = self._path(authorization_id)
            authorization = self._read_path(path)
            if authorization.status != "authorized":
                raise OutboundAuthorizationError(
                    f"Authorization is {authorization.status}; duplicate or uncertain delivery is blocked."
                )
            if now >= self._datetime(authorization.expires_at):
                raise OutboundAuthorizationError("Outbound authorization expired before delivery.")
            expected = {
                "thread_key_hash": private_hash(thread_key),
                "inbound_message_hash": private_hash(latest_message),
                "draft_hash": str(draft_hash or ""),
                "rules_digest": str(rules_digest or ""),
            }
            for field_name, value in expected.items():
                if value != getattr(authorization, field_name):
                    raise OutboundAuthorizationError(
                        f"Outbound authorization no longer matches {field_name}."
                    )
            claimed = OutboundResponseAuthorization(
                **{
                    **asdict(authorization),
                    "status": "sending",
                    "claimed_at": now.isoformat(),
                }
            )
            self._write_path(path, claimed)
            return claimed

    def complete(self, authorization_id: str, *, provider_message_id: str, now=None):
        now = now or datetime.now(timezone.utc)
        if not str(provider_message_id or "").strip():
            raise OutboundAuthorizationError("Provider delivery evidence is required.")
        with self._locked():
            path = self._path(authorization_id)
            authorization = self._read_path(path)
            if authorization.status != "sending":
                raise OutboundAuthorizationError("Only a claimed send can be completed.")
            completed = OutboundResponseAuthorization(
                **{
                    **asdict(authorization),
                    "status": "sent",
                    "completed_at": now.isoformat(),
                    "provider_message_id": str(provider_message_id)[:200],
                }
            )
            self._write_path(path, completed)
            return completed

    def mark_uncertain(self, authorization_id: str, *, reason: str, now=None):
        now = now or datetime.now(timezone.utc)
        with self._locked():
            path = self._path(authorization_id)
            authorization = self._read_path(path)
            if authorization.status not in {"sending", "authorized"}:
                return authorization
            failed = OutboundResponseAuthorization(
                **{
                    **asdict(authorization),
                    "status": "delivery_uncertain",
                    "completed_at": now.isoformat(),
                    "failure_reason": str(reason or "delivery_not_verified")[:500],
                }
            )
            self._write_path(path, failed)
            return failed

    def _path(self, authorization_id: str):
        if not self.SAFE_ID_RE.fullmatch(str(authorization_id or "")):
            raise OutboundAuthorizationError("Invalid outbound authorization ID.")
        return self.root / f"{authorization_id}.json"

    @contextmanager
    def _locked(self):
        descriptor = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)

    @staticmethod
    def _datetime(value: str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise OutboundAuthorizationError("Authorization timestamp is invalid.") from error
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _read_path(path: Path):
        try:
            return OutboundResponseAuthorization.from_record(
                json.loads(path.read_text(encoding="utf-8"))
            )
        except (OSError, ValueError, TypeError) as error:
            raise OutboundAuthorizationError("Authorization ledger validation failed.") from error

    @staticmethod
    def _write_path(path: Path, authorization: OutboundResponseAuthorization):
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(asdict(authorization), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        temporary.replace(path)


class AirbnbAutoResponsePolicy:
    """Owner-approved policy for only the lowest-risk factual intents."""

    POLICY_NAME = "owner-approved-low-stakes-v1"
    AUTO_SEND_TOPICS = {"location", "amenities", "services"}
    BLOCKED_REPLY_TERMS = {
        "guarantee",
        "confirmed reservation",
        "reservation is confirmed",
        "refund",
        "waive",
        "exception",
        "exact address",
        "door code",
        "lockbox",
        "party is allowed",
        "visitors are allowed",
    }

    def reasons(self, draft, item: BookableItem | None):
        reasons = list(draft.risk_reasons)
        if draft.topic not in self.AUTO_SEND_TOPICS:
            reasons.append("topic_not_auto_send_eligible")
        if not draft.low_stakes:
            reasons.append("not_low_stakes")
        if draft.mode != "openai":
            reasons.append("live_model_not_available")
        if draft.grounding_status != "property_resolved" or item is None:
            reasons.append("property_not_resolved")
        elif not item.is_active:
            reasons.append("property_inactive")
        if item is not None:
            _digest, rule_count = current_rules_digest(item)
            if rule_count == 0:
                reasons.append("current_rules_missing")
        word_count = len(str(draft.reply or "").split())
        if word_count == 0 or word_count > 120:
            reasons.append("reply_length_outside_policy")
        lowered = str(draft.reply or "").casefold()
        if any(term in lowered for term in self.BLOCKED_REPLY_TERMS):
            reasons.append("reply_contains_restricted_commitment")
        return tuple(dict.fromkeys(reasons))


class OutboundAuthorizationService:
    """Create, claim, and complete policy-bound outbound authorizations."""

    def __init__(self, repository=None, policy=None):
        self.repository = repository or OutboundAuthorizationRepository()
        self.policy = policy or AirbnbAutoResponsePolicy()

    def authorize(self, draft, *, thread_key: str, latest_message: str, now=None):
        now = now or datetime.now(timezone.utc)
        if not str(thread_key or "").strip() or not str(latest_message or "").strip():
            raise OutboundAuthorizationError("Thread and latest inbound message are required.")
        item = BookableItem.objects.filter(pk=draft.item_id).first() if draft.item_id else None
        reasons = self.policy.reasons(draft, item)
        if reasons:
            raise OutboundAuthorizationError("Auto-send held: " + ",".join(reasons))
        rules_digest, _rule_count = current_rules_digest(item)
        if draft.rules_digest != rules_digest:
            raise OutboundAuthorizationError("Current property rules changed after drafting.")
        idempotency_key = private_hash(
            "|".join(
                [
                    str(thread_key),
                    str(latest_message),
                    draft.draft_hash,
                    str(item.pk),
                    rules_digest,
                    self.policy.POLICY_NAME,
                ]
            )
        )
        authorization = OutboundResponseAuthorization(
            authorization_id=f"airbnb-{idempotency_key[:32]}",
            idempotency_key=idempotency_key,
            thread_key_hash=private_hash(thread_key),
            inbound_message_hash=private_hash(latest_message),
            draft_hash=draft.draft_hash,
            item_id=item.pk,
            rules_digest=rules_digest,
            topic=draft.topic,
            policy=self.policy.POLICY_NAME,
            status="authorized",
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=10)).isoformat(),
        )
        return self.repository.create(authorization)

    def claim(self, authorization_id, *, thread_key, latest_message, draft_hash, now=None):
        authorization = self.repository.get(authorization_id)
        item = BookableItem.objects.filter(pk=authorization.item_id, is_active=True).first()
        if item is None:
            raise OutboundAuthorizationError("Authorized property is no longer active.")
        rules_digest, _rule_count = current_rules_digest(item)
        return self.repository.claim(
            authorization_id,
            thread_key=thread_key,
            latest_message=latest_message,
            draft_hash=draft_hash,
            rules_digest=rules_digest,
            now=now,
        )

    def complete(self, authorization_id, *, provider_message_id, now=None):
        return self.repository.complete(
            authorization_id,
            provider_message_id=provider_message_id,
            now=now,
        )

    def mark_uncertain(self, authorization_id, *, reason, now=None):
        return self.repository.mark_uncertain(authorization_id, reason=reason, now=now)
