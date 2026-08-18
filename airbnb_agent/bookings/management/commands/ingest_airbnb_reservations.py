import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bookings.airbnb_reservation_lake import (
    AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION,
    AirbnbReservationSnapshotWriter,
    load_reservation_documents,
)


class Command(BaseCommand):
    help = "Import structured private Airbnb reservation snapshots into the protected object lake."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True, help="Private JSON or JSONL reservation snapshot export.")
        parser.add_argument("--root", default="", help="Local object-lake root; defaults to the configured runtime lake.")
        parser.add_argument("--sync-drive", action="store_true", help="Mirror the protected output to Drive.")
        parser.add_argument("--drive-remote", default="", help="rclone remote; defaults to MLADIS_DATASTORE_DRIVE_REMOTE.")
        parser.add_argument("--drive-folder-id", default="", help="Drive folder ID; defaults to MLADIS_DATASTORE_DRIVE_FOLDER_ID.")

    def handle(self, *args, **options):
        try:
            documents = load_reservation_documents(options["input"])
        except (OSError, ValueError) as error:
            raise CommandError(f"Could not read the private reservation export: {error}") from error

        writer = AirbnbReservationSnapshotWriter(options["root"] or self._default_root())
        results = writer.write_snapshots(documents)
        if options["sync_drive"]:
            self._sync_collection(writer, options)

        self.stdout.write(self.style.SUCCESS(
            f"Imported {sum(results.values())} Airbnb reservation snapshot(s): "
            f"{results['created']} created, {results['updated']} updated."
        ))
        self.stdout.write(f"Output root: {writer.layout.root}")
        self.stdout.write("Output collection: BOOKINGS/airbnb_reservation_snapshots.jsonl")

    def _default_root(self):
        configured = (getattr(settings, "MLADIS_DATASTORE_ROOT", "") or "").strip()
        return configured or Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"

    def _sync_collection(self, writer, options):
        if not shutil.which("rclone"):
            raise CommandError("rclone is required for --sync-drive.")
        remote = options["drive_remote"] or getattr(settings, "MLADIS_DATASTORE_DRIVE_REMOTE", "")
        folder_id = options["drive_folder_id"] or getattr(settings, "MLADIS_DATASTORE_DRIVE_FOLDER_ID", "")
        if not remote or not folder_id:
            raise CommandError("A Drive remote and folder ID are required for --sync-drive.")
        path = writer.layout.collection_path(AIRBNB_RESERVATION_SNAPSHOTS_COLLECTION)
        relative = path.relative_to(writer.layout.root).as_posix()
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
