from django.core.management.base import BaseCommand

from bookings.services import DamageDepositService, ReservationPaymentHoldService


class Command(BaseCommand):
    help = "Reconcile Stripe authorization state, capture due stay holds, and release completed/canceled holds."

    def handle(self, *args, **options):
        stay_result = ReservationPaymentHoldService().process_lifecycle()
        deposit_result = DamageDepositService().process_lifecycle()

        self.stdout.write(
            "Stay holds: "
            f"{stay_result['reconciled']} reconciled, "
            f"{stay_result['captured']} captured, "
            f"{stay_result['released']} released."
        )
        self.stdout.write(
            "Damage deposits: "
            f"{deposit_result['reconciled']} reconciled, "
            f"{deposit_result['released']} released."
        )
        errors = [*stay_result["errors"], *deposit_result["errors"]]
        if errors:
            for error in errors:
                self.stderr.write(error)
            raise RuntimeError(f"Payment lifecycle completed with {len(errors)} error(s).")

        self.stdout.write(self.style.SUCCESS("Payment lifecycle complete."))
