from pathlib import Path
import shutil
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from bookings.data_lake import MLADISDataLakeExporter


class Command(BaseCommand):
    help = "Create or export the MLADIS JSON/JSONL data-lake structure."

    def add_arguments(self, parser):
        parser.add_argument(
            "--root",
            default="",
            help="Destination root folder. Falls back to MLADIS_DATASTORE_ROOT, then runtime_datastore/MLADIS-DATASTORE.",
        )
        parser.add_argument(
            "--collection",
            action="append",
            dest="collections",
            default=None,
            help="Collection key to export. May be repeated. Defaults to all collections.",
        )
        parser.add_argument(
            "--schema-only",
            action="store_true",
            help="Create folder/catalog/schema structure without exporting database records.",
        )
        parser.add_argument(
            "--include-placeholders",
            action="store_true",
            help="With --schema-only, also writes one placeholder JSONL file per collection path.",
        )
        parser.add_argument(
            "--redacted",
            action="store_true",
            help="Hash or remove direct PII fields for analytics-safe exports.",
        )
        parser.add_argument(
            "--sync-drive",
            action="store_true",
            help="After exporting, write the current run to the configured Google Drive data-store folder using rclone.",
        )
        parser.add_argument(
            "--drive-remote",
            default="",
            help="rclone Drive remote to use with --sync-drive. Falls back to MLADIS_DATASTORE_DRIVE_REMOTE.",
        )
        parser.add_argument(
            "--drive-folder-id",
            default="",
            help="Google Drive folder ID to use with --sync-drive. Falls back to MLADIS_DATASTORE_DRIVE_FOLDER_ID.",
        )

    def handle(self, *args, **options):
        root = self._resolve_root(options["root"])
        try:
            result = MLADISDataLakeExporter(root, redacted=options["redacted"]).export(
                collections=options["collections"],
                schema_only=options["schema_only"],
                include_placeholders=options["include_placeholders"],
            )
        except ValueError as error:
            raise CommandError(str(error)) from error

        mode = "Schema-only setup" if result.schema_only else "Export"
        self.stdout.write(self.style.SUCCESS(f"{mode} complete: {result.root}"))
        self.stdout.write(f"Export run: {result.export_run_id}")
        self.stdout.write(f"Manifest: {result.manifest_path}")
        for key, count in sorted(result.collection_counts.items()):
            self.stdout.write(f"- {key}: {count}")
        if options["sync_drive"]:
            self._sync_current_run_to_drive(
                result,
                drive_remote=options["drive_remote"],
                drive_folder_id=options["drive_folder_id"],
                include_placeholders=options["include_placeholders"],
            )

    def _resolve_root(self, explicit_root):
        value = explicit_root or getattr(settings, "MLADIS_DATASTORE_ROOT", "")
        if value:
            return Path(value)
        return Path(settings.BASE_DIR) / "runtime_datastore" / "MLADIS-DATASTORE"

    def _sync_current_run_to_drive(self, result, *, drive_remote="", drive_folder_id="", include_placeholders=False):
        if not shutil.which("rclone"):
            raise CommandError("rclone is required for --sync-drive, but it was not found on PATH.")
        remote = drive_remote or getattr(settings, "MLADIS_DATASTORE_DRIVE_REMOTE", "")
        folder_id = drive_folder_id or getattr(settings, "MLADIS_DATASTORE_DRIVE_FOLDER_ID", "")
        if not remote:
            raise CommandError("Set MLADIS_DATASTORE_DRIVE_REMOTE or pass --drive-remote to use --sync-drive.")
        if not folder_id:
            raise CommandError("Set MLADIS_DATASTORE_DRIVE_FOLDER_ID or pass --drive-folder-id to use --sync-drive.")

        files = self._files_for_drive_sync(result, include_placeholders=include_placeholders)
        if not files:
            raise CommandError("No data-store files were selected for Drive sync.")

        self.stdout.write(f"Writing {len(files)} data-store file(s) to Drive folder {folder_id} via {remote}.")
        for path in files:
            relative_path = path.relative_to(result.root).as_posix()
            self.stdout.write(f"Drive write: {relative_path}")
            self._rclone_copyto(path, f"{remote}:{relative_path}", folder_id)
        self.stdout.write(self.style.SUCCESS("Drive data-store write complete."))

    def _files_for_drive_sync(self, result, *, include_placeholders=False):
        root = result.root
        files = [
            root / "README.md",
            root / "CATALOG.json",
            result.manifest_path,
        ]
        if result.schema_only:
            if include_placeholders:
                files.extend(sorted(root.rglob("*-placeholder.jsonl")))
        else:
            files.extend(sorted(path for path in root.rglob("*.jsonl") if "EXPORTS" not in path.parts))
        return [path for path in files if path.exists()]

    def _rclone_copyto(self, source, destination, folder_id):
        command = [
            "rclone",
            "copyto",
            str(source),
            destination,
            "--drive-root-folder-id",
            folder_id,
            "--drive-pacer-min-sleep",
            getattr(settings, "MLADIS_DATASTORE_DRIVE_PACER_MIN_SLEEP", "3s"),
            "--drive-pacer-burst",
            "1",
            "--tpslimit",
            getattr(settings, "MLADIS_DATASTORE_DRIVE_TPS_LIMIT", "0.25"),
            "--transfers",
            "1",
            "--checkers",
            "1",
            "--retries",
            "6",
            "--low-level-retries",
            "6",
            "--stats-one-line",
        ]
        try:
            subprocess.run(command, check=True, timeout=getattr(settings, "MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS", 25))
        except subprocess.TimeoutExpired as error:
            raise CommandError(f"Drive write timed out for {source.name}: {error}") from error
        except subprocess.CalledProcessError as error:
            raise CommandError(f"Drive write failed for {source.name}: {error}") from error
