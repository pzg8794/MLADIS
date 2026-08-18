"""Run one bounded Airbnb export through both MLADIS data-lake writers."""

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bookings.airbnb_reservation_lake import AirbnbReservationSnapshotWriter
from bookings.interaction_lake import AnonymousInteractionLakeWriter


INTERACTION_KINDS = {
    "conversation",
    "conversation_interaction",
    "interaction",
    "interactions",
    "anonymous_interaction",
    "anonymous_interactions",
}
RESERVATION_KINDS = {
    "booking",
    "reservation",
    "reservations",
    "reservation_snapshot",
    "airbnb_reservation",
    "airbnb_reservations",
}


class Command(BaseCommand):
    help = "Collect one Airbnb export into protected BOOKINGS and anonymized INTERACTIONS collections."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            required=True,
            help="Private combined JSON/JSONL export containing reservations and conversation interactions.",
        )
        parser.add_argument(
            "--root",
            default="",
            help="Local object-lake root; defaults to the configured runtime lake.",
        )
        parser.add_argument("--sync-drive", action="store_true", help="Mirror both output collections to Drive.")
        parser.add_argument("--drive-remote", default="", help="rclone remote; defaults to MLADIS_DATASTORE_DRIVE_REMOTE.")
        parser.add_argument(
            "--drive-folder-id",
            default="",
            help="Drive folder ID; defaults to MLADIS_DATASTORE_DRIVE_FOLDER_ID.",
        )

    def handle(self, *args, **options):
        reservations, interactions = self._load_documents(options["input"])
        if not reservations and not interactions:
            raise CommandError("The combined export did not contain reservations or interactions.")

        root = options["root"] or self._default_root()
        reservation_writer = AirbnbReservationSnapshotWriter(root)
        interaction_writer = AnonymousInteractionLakeWriter(root)

        reservation_results = reservation_writer.write_snapshots(reservations)
        interaction_paths = set()
        for document in interactions:
            turns = document.get("turns")
            if not isinstance(turns, list):
                raise CommandError("Each interaction document must contain a turns list.")
            interaction_paths.add(
                interaction_writer.write_conversation(
                    source_system=document.get("source_system", "airbnb"),
                    channel=document.get("channel", "host_messages"),
                    language=document.get("language", ""),
                    topic=document.get("topic", "general"),
                    outcome=document.get("outcome", ""),
                    turns=turns,
                    known_names=document.get("known_names", []),
                    occurred_at=document.get("occurred_at"),
                )
            )

        if options["sync_drive"]:
            self._sync_outputs(
                root=Path(root),
                interaction_paths=interaction_paths,
                options=options,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Collected Airbnb data lake export: "
                f"{len(interactions)} interaction(s), "
                f"{sum(reservation_results.values())} reservation snapshot(s)."
            )
        )
        self.stdout.write(
            f"Reservations: {reservation_results['created']} created, {reservation_results['updated']} updated."
        )
        self.stdout.write(f"Output root: {Path(root)}")
        self.stdout.write("Output collections: BOOKINGS/airbnb_reservation_snapshots.jsonl and INTERACTIONS/anonymous_interactions.jsonl")

    def _load_documents(self, path):
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise CommandError(f"Combined export not found: {source}")
        try:
            if source.suffix.lower() == ".jsonl":
                payload = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
            else:
                payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise CommandError(f"Could not read the combined export: {error}") from error

        reservations = []
        interactions = []
        if isinstance(payload, dict):
            reservations.extend(self._list_value(payload, "reservations"))
            reservations.extend(self._list_value(payload, "reservation_snapshots"))
            interactions.extend(self._list_value(payload, "interactions"))
            interactions.extend(self._list_value(payload, "conversation_interactions"))
            reservations.extend(self._thread_index_reservations(payload))
            if not reservations and not interactions:
                self._append_classified(payload, reservations, interactions)
        elif isinstance(payload, list):
            for document in payload:
                if not isinstance(document, dict):
                    raise CommandError("Every combined export row must be an object.")
                if self._is_thread_capture(document):
                    reservations.append(self._thread_capture_reservation(document))
                    interactions.append(self._thread_capture_interaction(document))
                elif self._is_thread_index(document):
                    reservations.append(self._thread_index_reservation(document))
                else:
                    self._append_classified(document, reservations, interactions)
        else:
            raise CommandError("The combined export must be a JSON object, JSON list, or JSONL file.")
        return reservations, interactions

    def _thread_index_reservations(self, payload):
        reservations = []
        for scope in ("normal", "archived"):
            rows = payload.get(scope)
            if rows in (None, ""):
                continue
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise CommandError(f"Combined export field '{scope}' must be a list of objects.")
            reservations.extend(self._thread_index_reservation(row, scope=scope) for row in rows)
        return reservations

    @staticmethod
    def _is_thread_capture(document):
        return (
            document.get("dataset") in {"normal", "archived"}
            and isinstance(document.get("messages"), list)
            and "thread_id" in document
        )

    @staticmethod
    def _is_thread_index(document):
        return (
            document.get("dataset") in {"normal", "archived"}
            and "thread_id" in document
            and "text" in document
            and "messages" not in document
        )

    def _thread_capture_reservation(self, document):
        preview = document.get("preview") or ""
        detail_text = document.get("detail_text") or ""
        guest_name = self._thread_guest_name(document.get("messages") or [])
        return self._thread_index_reservation(
            {
                "dataset": document.get("dataset"),
                "thread_id": document.get("thread_id"),
                "href": document.get("href") or "",
                "text": f"{preview}\n{detail_text}",
                "guest_name": guest_name,
                "message_count": document.get("message_count") or len(document.get("messages") or []),
                "captured_at": document.get("captured_at"),
            }
        )

    def _thread_capture_interaction(self, document):
        known_names = []
        turns = []
        for message in document.get("messages") or []:
            turn, speaker = self._parse_thread_message(message)
            if speaker:
                known_names.append(speaker)
            if turn["text"]:
                turns.append(turn)
        return {
            "source_system": "airbnb",
            "channel": f"host_messages_{document.get('dataset', 'unknown')}",
            "known_names": known_names,
            "turns": turns,
            "occurred_at": document.get("captured_at"),
        }

    def _thread_index_reservation(self, document, *, scope=None):
        scope = scope or document.get("dataset") or "unknown"
        thread_id = str(document.get("thread_id") or "").strip()
        href = str(document.get("href") or "").strip()
        text = " ".join(str(document.get("text") or "").split())
        listing_title = self._listing_title(text)
        status = self._reservation_status(text)
        check_in, check_out = self._date_range(text)
        guest_count = self._number_before(text, "guest")
        nights = self._number_before(text, "night")
        potential_earnings = self._money_after_marker(text, "potential earnings")
        if potential_earnings is None:
            potential_earnings = self._money_after_marker(text, "earnings")
        rating = self._rating_after_marker(text, ("rating", "stars"))
        review_count = self._review_count(text)
        captured_at = document.get("captured_at")
        return {
            "source": {
                "scope": scope,
                "thread_id": thread_id,
                "thread_url": href,
                "captured_from": "airbnb_message_table",
            },
            "guest": {"name": document.get("guest_name", "")},
            "property": {"listing_title": listing_title},
            "lifecycle": {"status": status, "check_in": check_in, "check_out": check_out},
            "occupancy": {"guests": guest_count, "nights": nights},
            "financials": {"potential_earnings": potential_earnings},
            "rating": rating,
            "review_count": review_count,
            "communication": {
                "message_count": document.get("message_count"),
                "last_message_at": captured_at,
            },
            "captured_at": captured_at,
            "notes": "Table-index snapshot; stay fields require reservation-panel reconciliation.",
        }

    @staticmethod
    def _thread_guest_name(messages):
        for message in messages:
            match = re.match(r"(.+?)\s+·\s+(?:Booker|Guest)\b", str(message or "").strip(), re.I)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip()[:160]
        return ""

    @staticmethod
    def _date_range(text):
        match = re.search(
            r"\b([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})\s*(?:–|-)\s*"
            r"([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})\b",
            text,
        )
        if not match:
            return "", ""
        for fmt in ("%B %d, %Y", "%b %d, %Y"):
            try:
                return (
                    datetime.strptime(match.group(1), fmt).date().isoformat(),
                    datetime.strptime(match.group(2), fmt).date().isoformat(),
                )
            except ValueError:
                continue
        return "", ""

    @staticmethod
    def _number_before(text, word):
        match = re.search(rf"\b(\d+)\s+{word}s?\b", text, re.I)
        return int(match.group(1)) if match else None

    @staticmethod
    def _money_after_marker(text, marker):
        marker_pattern = re.escape(marker)
        patterns = (
            rf"{marker_pattern}[^$\d]{{0,24}}\$\s*([\d,]+(?:\.\d{{1,2}})?)",
            rf"\$\s*([\d,]+(?:\.\d{{1,2}})?)[^\n$\d]{{0,24}}{marker_pattern}",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).replace(",", "")
        return None

    @staticmethod
    def _rating_after_marker(text, markers):
        for marker in markers:
            marker_pattern = re.escape(marker)
            patterns = (
                rf"(\d(?:\.\d{{1,2}})?)\s+{marker_pattern}\b",
                rf"{marker_pattern}[^\d]{{0,12}}(\d(?:\.\d{{1,2}})?)",
            )
            for pattern in patterns:
                match = re.search(pattern, text, re.I)
                if match:
                    return match.group(1)
        return None

    @staticmethod
    def _review_count(text):
        patterns = (
            r"\d(?:\.\d{1,2})?\s+rating\s+from\s+(\d+)\s+reviews?",
            r"(?:from|based\s+on)\s+(\d+)\s+reviews?",
            r"(\d+)\s+reviews?",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _listing_title(text):
        if not text:
            return ""
        match = re.search(r"(?:·|•)\s*([^·•]+(?:Bedrooms?|bedrooms?)[^·•]*)", text, re.I)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip(" .")[:240]
        return ""

    @staticmethod
    def _reservation_status(text):
        lowered = text.lower()
        for marker, status in (
            ("reservation request expired", "expired"),
            ("request expired", "expired"),
            ("canceled", "canceled"),
            ("cancelled", "canceled"),
            ("declined", "declined"),
            ("confirmed", "confirmed"),
            ("inquiry sent", "inquiry"),
        ):
            if marker in lowered:
                return status
        return "unknown"

    @staticmethod
    def _parse_thread_message(message):
        lines = [re.sub(r"\s+", " ", line).strip() for line in str(message or "").splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return {"role": "unknown", "text": ""}, ""

        first = lines[0]
        role = "unknown"
        speaker = ""
        speaker_match = re.match(r"(.+?)\s+·\s+(Booker|Guest|Host)\b", first, re.I)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            role = "host" if speaker_match.group(2).lower() == "host" else "guest"
            lines[0] = first[speaker_match.end():].strip()
        elif re.match(r"^(?:You|Diana)\b", first, re.I):
            role = "host"
            lines[0] = re.sub(r"^(?:You|Diana)\b(?:\s+·\s+Host)?", "", first, flags=re.I).strip()
        elif re.match(r"^(?:Inquiry sent|Reservation request|Booking request)\b", first, re.I):
            role = "system"

        lines = [line for line in lines if not re.fullmatch(r"\d{1,2}:\d{2}(?:\s*[AP]M)?", line, re.I)]
        text = " ".join(lines).strip()
        return {"role": role, "text": text}, speaker

    @staticmethod
    def _list_value(payload, key):
        value = payload.get(key, [])
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise CommandError(f"Combined export field '{key}' must be a list.")
        if not all(isinstance(item, dict) for item in value):
            raise CommandError(f"Every item in '{key}' must be an object.")
        return value

    def _append_classified(self, document, reservations, interactions):
        kind = str(
            document.get("dataset")
            or document.get("kind")
            or document.get("type")
            or document.get("collection")
            or ""
        ).strip().lower().replace("-", "_")
        if kind in INTERACTION_KINDS or "turns" in document:
            interactions.append(document)
            return
        if kind in RESERVATION_KINDS or {"guest", "property", "lifecycle"}.intersection(document):
            reservations.append(document)
            return
        raise CommandError(
            "Could not classify a combined export row. Add dataset='interactions' or dataset='reservations'."
        )

    def _default_root(self):
        configured = (getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        return configured or Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"

    def _sync_outputs(self, *, root, interaction_paths, options):
        if not shutil.which("rclone"):
            raise CommandError("rclone is required for --sync-drive.")
        remote = options["drive_remote"] or getattr(settings, "MLADIS_DATASTORE_DRIVE_REMOTE", "")
        folder_id = options["drive_folder_id"] or getattr(settings, "MLADIS_DATASTORE_DRIVE_FOLDER_ID", "")
        if not remote or not folder_id:
            raise CommandError("A Drive remote and folder ID are required for --sync-drive.")

        output_paths = {
            root / "BOOKINGS" / "airbnb_reservation_snapshots.jsonl",
            root / "INTERACTIONS" / "anonymous_interactions.jsonl",
        }
        output_paths.update(interaction_paths)
        for path in sorted(path for path in output_paths if path.exists()):
            relative = path.relative_to(root).as_posix()
            command = [
                "rclone",
                "copyto",
                str(path),
                f"{remote}:{relative}",
                "--drive-root-folder-id",
                folder_id,
                "--transfers",
                "1",
                "--checkers",
                "1",
                "--retries",
                "3",
                "--low-level-retries",
                "3",
                "--stats-one-line",
            ]
            try:
                subprocess.run(
                    command,
                    check=True,
                    timeout=getattr(settings, "MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS", 25),
                )
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                raise CommandError(f"Drive sync failed for {relative}: {error}") from error
