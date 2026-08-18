import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bookings.interaction_lake import AnonymousInteractionLakeWriter, load_interaction_documents


class Command(BaseCommand):
    help = "Import JSON/JSONL conversations into the identity-free interaction lake."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True, help="Private JSON or JSONL conversation export.")
        parser.add_argument("--root", default="", help="Local object-lake root; defaults to the configured runtime lake.")
        parser.add_argument("--sync-drive", action="store_true", help="Mirror the sanitized output to Drive.")
        parser.add_argument("--drive-remote", default="", help="rclone remote; defaults to MLADIS_DATASTORE_DRIVE_REMOTE.")
        parser.add_argument("--drive-folder-id", default="", help="Drive folder ID; defaults to MLADIS_DATASTORE_DRIVE_FOLDER_ID.")

    def handle(self, *args, **options):
        try:
            documents = load_interaction_documents(options["input"])
        except (OSError, ValueError) as error:
            raise CommandError(f"Could not read the private interaction export: {error}") from error

        writer = AnonymousInteractionLakeWriter(options["root"] or self._default_root())
        output_paths = set()
        for document in documents:
            if not isinstance(document, dict) or not isinstance(document.get("turns"), list):
                raise CommandError("Each interaction document must contain a turns list.")
            path = writer.write_conversation(
                source_system=document.get("source_system", "unknown"),
                channel=document.get("channel", "unknown"),
                language=document.get("language", ""),
                topic=document.get("topic", "general"),
                outcome=document.get("outcome", ""),
                turns=document["turns"],
                known_names=document.get("known_names", []),
                occurred_at=document.get("occurred_at"),
            )
            output_paths.add(path)

        if options["sync_drive"]:
            self._sync_drive(output_paths, options)

        self.stdout.write(self.style.SUCCESS(f"Imported {len(documents)} anonymized interaction(s)."))
        self.stdout.write(f"Output root: {writer.layout.root}")
        self.stdout.write("Output collection: INTERACTIONS/anonymous_interactions.jsonl")

    def _default_root(self):
        configured = (getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        return configured or Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"

    def _sync_drive(self, paths, options):
        if not paths:
            return
        if not shutil.which("rclone"):
            raise CommandError("rclone is required for --sync-drive.")
        remote = options["drive_remote"] or getattr(settings, "MLADIS_DATASTORE_DRIVE_REMOTE", "")
        folder_id = options["drive_folder_id"] or getattr(settings, "MLADIS_DATASTORE_DRIVE_FOLDER_ID", "")
        if not remote or not folder_id:
            raise CommandError("A Drive remote and folder ID are required for --sync-drive.")
        root = next(iter(paths)).parent.parent
        for path in paths:
            relative = path.relative_to(root).as_posix()
            command = [
                "rclone", "copyto", str(path), f"{remote}:{relative}",
                "--drive-root-folder-id", folder_id,
                "--transfers", "1", "--checkers", "1", "--retries", "3",
                "--low-level-retries", "3", "--stats-one-line",
            ]
            try:
                subprocess.run(command, check=True, timeout=getattr(settings, "MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS", 25))
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                raise CommandError(f"Drive sync failed for {relative}: {error}") from error
