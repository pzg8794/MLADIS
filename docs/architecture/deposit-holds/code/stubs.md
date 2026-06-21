# DepositHold Code Stubs

These are implementation stubs, not final production code.

## Backend model vocabulary

```python
class DepositHoldKind(models.TextChoices):
    DAMAGE_DEPOSIT = "damage_deposit", "Damage deposit"
    STAY_PAYMENT_HOLD = "stay_payment_hold", "Stay payment hold"
    SECURITY_EXCEPTION = "security_exception", "Security exception"


class DepositHoldStatus(models.TextChoices):
    NEW = "new", "New"
    REQUIRES_CONFIGURATION = "requires_configuration", "Requires configuration"
    CHECKOUT_CREATED = "checkout_created", "Checkout created"
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    APPROVED = "approved", "Approved"
    CAPTURED = "captured", "Captured"
    RELEASED = "released", "Released"
    CANCELED = "canceled", "Canceled"
    FAILED = "failed", "Failed"
    DISPUTED = "disputed", "Disputed"


class DepositHold(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    hold_number = models.CharField(max_length=40, unique=True)
    reservation = models.ForeignKey("bookings.BookingInquiry", on_delete=models.SET_NULL, null=True, blank=True, related_name="deposit_holds")
    item = models.ForeignKey("bookings.BookableItem", on_delete=models.SET_NULL, null=True, blank=True, related_name="deposit_holds")

    guest_name = models.CharField(max_length=160)
    guest_email = models.EmailField(blank=True)
    kind = models.CharField(max_length=32, choices=DepositHoldKind.choices, default=DepositHoldKind.DAMAGE_DEPOSIT)
    status = models.CharField(max_length=32, choices=DepositHoldStatus.choices, default=DepositHoldStatus.NEW)
    risk_level = models.CharField(max_length=16, default="low")

    amount_cents = models.PositiveIntegerField(default=20000)
    currency = models.CharField(max_length=3, default="usd")
    provider = models.CharField(max_length=24, default="stripe")
    provider_checkout_session_id = models.CharField(max_length=255, blank=True)
    provider_payment_intent_id = models.CharField(max_length=255, blank=True)
    provider_authorization_id = models.CharField(max_length=255, blank=True)

    requested_at = models.DateTimeField(auto_now_add=True)
    authorized_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    captured_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    guest_note = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_amount(self):
        return f"${self.amount_cents / 100:,.2f} {self.currency.upper()}"

    @property
    def is_active(self):
        return self.status in {DepositHoldStatus.PENDING, DepositHoldStatus.AUTHORIZED, DepositHoldStatus.APPROVED}

    @property
    def is_expiring_soon(self):
        if not self.expires_at:
            return False
        return self.is_active and self.expires_at <= timezone.now() + timezone.timedelta(hours=24)

    def can_release(self):
        return self.status in {DepositHoldStatus.PENDING, DepositHoldStatus.AUTHORIZED, DepositHoldStatus.APPROVED}

    def to_row_payload(self):
        return {
            "id": str(self.pk),
            "hold_number": self.hold_number,
            "guest_name": self.guest_name,
            "reservation_id": self.reservation_id,
            "listing": self.item.business_display_name if self.item else "",
            "amount": {"cents": self.amount_cents, "currency": self.currency, "display": self.display_amount},
            "status": self.status,
            "risk_level": self.risk_level,
            "expires_at": self.expires_at.isoformat() if self.expires_at else "",
        }
```

## Frontend domain object

```ts
export class DepositHold {
  constructor(
    public readonly id: string,
    public readonly holdNumber: string,
    public readonly reservation: DepositReservationLink | null,
    public readonly guest: DepositGuest,
    public readonly listing: DepositListing,
    public readonly amount: Money,
    public readonly status: DepositHoldStatus,
    public readonly risk: DepositRiskState,
    public readonly timeline: HoldTimelineEvent[],
    public readonly paymentAttempts: PaymentTransactionLink[],
    public readonly guestNote: string,
  ) {}

  isActive(): boolean {
    return ['pending', 'authorized', 'approved'].includes(this.status.value);
  }

  isExpiringSoon(): boolean {
    return this.status.expiresSoon;
  }

  canApprove(): boolean {
    return ['pending', 'authorized'].includes(this.status.value);
  }

  canRelease(): boolean {
    return ['pending', 'authorized', 'approved'].includes(this.status.value);
  }
}
```
