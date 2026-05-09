from django.core.management.base import BaseCommand, CommandError

from bookings.airbnb_import import AirbnbGuestImportService


class Command(BaseCommand):
    help = "Import or update Airbnb guest records from a Gmail-export JSON/CSV file."

    def add_arguments(self, parser):
        parser.add_argument("input_path", help="Path to a Gmail/Airbnb export file in JSON or CSV format.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and count records without writing to the database.",
        )

    def handle(self, *args, **options):
        try:
            result = AirbnbGuestImportService().import_file(
                options["input_path"],
                dry_run=options["dry_run"],
            )
        except Exception as error:
            raise CommandError(str(error)) from error

        mode = "Dry run" if options["dry_run"] else "Imported"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: {result.created} created, {result.updated} updated, {result.skipped} skipped."
            )
        )
