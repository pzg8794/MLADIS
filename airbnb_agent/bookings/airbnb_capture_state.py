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
        """Return unseen documents and the count skipped from the checkpoint."""
        selected = []
        skipped = 0
        seen = set()
        for document in documents:
            key = self.key_for(document, kind)
            if key in seen or self.entries.get(key, {}).get(kind):
                skipped += 1
                continue
            seen.add(key)
            selected.append(document)
        return selected, skipped

    def mark(self, document, kind):
        key = self.key_for(document, kind)
        entry = self.entries.setdefault(key, {})
        entry[kind] = True
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

    @staticmethod
    def _thread_key(scope, thread_id):
        return f"{str(scope or 'unknown').strip()}:{str(thread_id).strip()}"
