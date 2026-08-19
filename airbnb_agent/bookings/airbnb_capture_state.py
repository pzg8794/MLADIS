"""Private, local checkpoint state for resumable Airbnb lake imports.

The checkpoint contains source thread keys and must stay outside Git and the
Drive learning collections. It prevents a later import from appending the
same conversation twice while keeping source identifiers out of the
anonymized interaction lake.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class AirbnbCaptureState:
    """Track successfully written reservation and interaction captures."""

    SCHEMA_VERSION = "1.0"
    FILENAME = ".airbnb_capture_state.json"

    def __init__(self, root, *, entries=None):
        self.root = Path(root).expanduser().resolve()
        self.path = self.root / "BOOKINGS" / self.FILENAME
        self.entries = entries or {}

    @classmethod
    def load(cls, root):
        state = cls(root)
        if state.path.is_file():
            try:
                payload = json.loads(state.path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                payload = {}
            if isinstance(payload, dict) and isinstance(payload.get("threads"), dict):
                state.entries = {
                    str(key): dict(value)
                    for key, value in payload["threads"].items()
                    if isinstance(value, dict)
                }
        state._bootstrap_existing_snapshots()
        return state

    def select_new(self, documents, kind):
        """Return captures whose content is new since the last successful write.

        Thread identity alone is not a sufficient resume key: an existing
        Airbnb thread can receive another message or a reservation can change
        status.  The checkpoint therefore tracks a private content fingerprint
        per thread and per collection.
        """
        selected = []
        skipped = 0
        seen = set()
        for document in documents:
            key = self.key_for(document, kind)
            fingerprint = self.fingerprint_for(document, kind)
            entry = self.entries.get(key, {})
            known_fingerprints = self._known_fingerprints(entry, kind)
            observation_key = (key, fingerprint)
            if fingerprint in known_fingerprints or observation_key in seen:
                skipped += 1
                continue
            # Older checkpoints stored only a boolean per thread.  A legacy
            # interaction entry can still be resumed when its message count
            # grows; the first successful pass upgrades it with a fingerprint.
            if not known_fingerprints and entry.get(kind) and self._legacy_observation_is_unchanged(
                document, entry, kind
            ):
                skipped += 1
                continue
            seen.add(observation_key)
            selected.append(document)
        return selected, skipped

    def mark(self, document, kind):
        key = self.key_for(document, kind)
        entry = self.entries.setdefault(key, {})
        entry[kind] = True
        fingerprints = entry.setdefault("fingerprints", {}).setdefault(kind, [])
        fingerprint = self.fingerprint_for(document, kind)
        if fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
        entry.setdefault("observation_counts", {})[kind] = self._observation_count(document, kind)
        entry["last_seen_at"] = datetime.now(timezone.utc).isoformat()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "threads": self.entries,
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(self.path)

    def _bootstrap_existing_snapshots(self):
        """Seed state from the already completed reservation lake.

        The current Airbnb import contains a detailed interaction for every
        imported reservation. Marking both sides prevents the first resume
        after upgrading MLADIS from duplicating the known completed batch.
        """
        snapshot_path = self.root / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl"
        if not snapshot_path.is_file():
            return
        try:
            lines = snapshot_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            data = record.get("data") if isinstance(record, dict) else None
            source = data.get("source") if isinstance(data, dict) else None
            if not isinstance(source, dict) or not source.get("thread_id"):
                continue
            key = self._thread_key(source.get("scope"), source.get("thread_id"))
            entry = self.entries.setdefault(key, {})
            entry.setdefault("reservations", True)
            entry.setdefault("interactions", True)
            entry.setdefault("fingerprints", {}).setdefault("reservations", []).append(
                self.fingerprint_for(record, "reservations")
            )
            entry.setdefault("observation_counts", {}).setdefault(
                "interactions", (data.get("communication") or {}).get("message_count")
            )

    @classmethod
    def key_for(cls, document, kind):
        if not isinstance(document, dict):
            raise ValueError("Airbnb capture documents must be objects.")

        source = document.get("source")
        if not isinstance(source, dict):
            source = {}
        scope = document.get("dataset") or source.get("scope") or "unknown"
        thread_id = document.get("thread_id") or source.get("thread_id")
        if thread_id:
            return cls._thread_key(scope, thread_id)

        capture_key = document.get("_capture_key") or document.get("capture_key")
        if capture_key:
            return str(capture_key)

        stable = dict(document)
        stable.pop("captured_at", None)
        stable.pop("extracted_at", None)
        encoded = json.dumps(stable, default=str, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(f"{kind}:{encoded}".encode("utf-8")).hexdigest()
        return f"content:{digest}"

    @classmethod
    def fingerprint_for(cls, document, kind):
        """Return a private, deterministic fingerprint for one observation."""
        if not isinstance(document, dict):
            raise ValueError("Airbnb capture documents must be objects.")

        if kind == "reservations":
            from .airbnb_reservation_lake import AirbnbReservationSnapshotWriter

            payload = document.get("data") if document.get("collection") else None
            if not isinstance(payload, dict):
                payload = AirbnbReservationSnapshotWriter("").build_record(document).get("data", {})
        elif kind == "interactions":
            from .interaction_lake import AnonymousInteractionLakeWriter

            if document.get("collection") == "anonymous_interactions":
                payload = document.get("data") or {}
            else:
                payload = AnonymousInteractionLakeWriter("").build_record(
                    source_system=document.get("source_system", "airbnb"),
                    channel=document.get("channel", "host_messages"),
                    language=document.get("language", ""),
                    topic=document.get("topic", "general"),
                    outcome=document.get("outcome", ""),
                    turns=document.get("turns", []),
                    known_names=document.get("known_names", []),
                    occurred_at=document.get("occurred_at"),
                ).get("data", {})
        else:
            payload = dict(document)

        encoded = json.dumps(payload, default=str, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(f"{kind}:{encoded}".encode("utf-8")).hexdigest()

    @staticmethod
    def _known_fingerprints(entry, kind):
        fingerprints = entry.get("fingerprints") if isinstance(entry, dict) else None
        values = fingerprints.get(kind) if isinstance(fingerprints, dict) else None
        return set(values or [])

    @classmethod
    def _legacy_observation_is_unchanged(cls, document, entry, kind):
        counts = entry.get("observation_counts") if isinstance(entry, dict) else None
        if not isinstance(counts, dict) or counts.get(kind) is None:
            # A legacy checkpoint without an observation count is upgraded by
            # accepting one pass; subsequent runs use fingerprints.
            return False
        current_count = cls._observation_count(document, kind)
        return current_count is not None and current_count <= counts.get(kind)

    @staticmethod
    def _observation_count(document, kind):
        if not isinstance(document, dict):
            return None
        if kind == "interactions":
            turns = document.get("turns")
            return len(turns) if isinstance(turns, list) else None
        if kind == "reservations":
            if document.get("collection") == "airbnb_reservation_snapshots":
                data = document.get("data") or {}
                communication = data.get("communication") or {}
            else:
                communication = document.get("communication") or {}
            value = communication.get("message_count")
            try:
                return int(value) if value is not None else None
            except (TypeError, ValueError):
                return None

    @staticmethod
    def _thread_key(scope, thread_id):
        return f"{str(scope or 'unknown').strip()}:{str(thread_id).strip()}"
