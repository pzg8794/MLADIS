# PaymentTransaction Code Stubs

These are implementation stubs, not final production code.

## Backend model vocabulary

```python
class PaymentTransactionType(models.TextChoices):
    STAY_PAYMENT = "stay_payment", "Stay payment"
    DEPOSIT_CAPTURE = "deposit_capture", "Deposit capture"
    REFUND = "refund", "Refund"
    PAYOUT = "payout", "Payout"
    ADJUSTMENT = "adjustment", "Adjustment"


class PaymentTransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    SETTLED = "settled", "Settled"
    REFUNDED = "refunded", "Refunded"
    FAILED = "failed", "Failed"
    DISPUTED = "disputed", "Disputed"


class PaymentTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    transaction_number = models.CharField(max_length=40, unique=True)
    reservation = models.ForeignKey("bookings.BookingInquiry", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_transactions")
    deposit_hold = models.ForeignKey("bookings.DepositHold", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_transactions")
    item = models.ForeignKey("bookings.BookableItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="payment_transactions")

    guest_name = models.CharField(max_length=160)
    guest_email = models.EmailField(blank=True)
    transaction_type = models.CharField(max_length=32, choices=PaymentTransactionType.choices)
    status = models.CharField(max_length=32, choices=PaymentTransactionStatus.choices, default=PaymentTransactionStatus.PENDING)
    channel = models.CharField(max_length=40, blank=True)
    method = models.CharField(max_length=40, blank=True)

    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="usd")
    provider = models.CharField(max_length=24, blank=True)
    provider_transaction_id = models.CharField(max_length=255, blank=True)
    provider_payment_intent_id = models.CharField(max_length=255, blank=True)
    provider_charge_id = models.CharField(max_length=255, blank=True)

    received_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_amount(self):
        return f"${self.amount_cents / 100:,.2f} {self.currency.upper()}"

    @property
    def is_paid(self):
        return self.status in {PaymentTransactionStatus.PAID, PaymentTransactionStatus.SETTLED}

    def to_row_payload(self):
        return {
            "id": str(self.pk),
            "transaction_number": self.transaction_number,
            "guest_name": self.guest_name,
            "reservation_id": self.reservation_id,
            "listing": self.item.business_display_name if self.item else "",
            "channel": self.channel,
            "method": self.method,
            "amount": {"cents": self.amount_cents, "currency": self.currency, "display": self.display_amount},
            "status": self.status,
        }
```

## Frontend domain object

```ts
export class PaymentTransaction {
  constructor(
    public readonly id: string,
    public readonly transactionNumber: string,
    public readonly reservation: PaymentReservationLink | null,
    public readonly depositHold: PaymentDepositHoldLink | null,
    public readonly guest: PaymentGuest,
    public readonly listing: PaymentListing,
    public readonly channel: string,
    public readonly method: string,
    public readonly amount: Money,
    public readonly status: PaymentTransactionStatus,
    public readonly invoice: InvoicePreview | null,
    public readonly timeline: PaymentTimelineEvent[],
    public readonly notes: string,
  ) {}

  isPaid(): boolean {
    return this.status.value === 'paid' || this.status.value === 'settled';
  }

  canRefund(): boolean {
    return this.isPaid();
  }
}
```
