# PaymentTransaction Class Diagram

This diagram defines the PaymentTransaction aggregate and its relationship to Reservation, Invoice, DepositHold, and provider events.

```mermaid
classDiagram
direction LR

class PaymentTransaction {
  +UUID id
  +string transactionNumber
  +PaymentTransactionType type
  +PaymentTransactionStatus status
  +PaymentChannel channel
  +PaymentMethod method
  +Money amount
  +string provider
  +string providerTransactionId
  +string providerPaymentIntentId
  +string providerChargeId
  +datetime receivedAt
  +datetime settledAt
  +datetime refundedAt
  +string notes
  +displayAmount() string
  +isPaid() boolean
  +isRefunded() boolean
  +canRefund() boolean
  +canMarkPaid() boolean
  +toRowPayload() dict
  +toDetailPayload() dict
  +toDataLakeRecord() dict
}

class Reservation {
  +int id
  +string requestKey
  +string guestName
  +date checkIn
  +date checkOut
  +displayTotal() string
}

class Invoice {
  +UUID id
  +string invoiceNumber
  +InvoiceStatus status
  +Money amountDue
  +datetime issueDate
  +datetime dueDate
  +string documentUrl
  +toPreviewPayload() dict
}

class DepositHold {
  +UUID id
  +string holdNumber
  +Money amount
  +DepositHoldStatus status
  +datetime authorizedAt
  +datetime expiresAt
  +canCapture() boolean
  +canRelease() boolean
}

class PaymentProviderEvent {
  +UUID id
  +string provider
  +string eventType
  +string eventId
  +JSON payload
  +datetime receivedAt
}

class PaymentTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +string note
  +JSON metadata
  +datetime createdAt
}

class PaymentTransactionService {
  +createTransaction(payload, actor) PaymentTransaction
  +markPaid(transaction, actor) PaymentTransaction
  +issueRefund(transaction, actor) PaymentTransaction
  +downloadInvoice(transaction) Invoice
  +linkReservation(transaction, reservation) PaymentTransaction
  +emitTimeline(transaction, eventType, actor, metadata) void
}

class PaymentReconciliationService {
  +matchProviderEvent(event) PaymentTransaction
  +reconcileTransaction(transaction) PaymentTransaction
  +detectDuplicates(transaction) list
}

class PaymentTransactionType {
  <<enumeration>>
  STAY_PAYMENT
  DEPOSIT_CAPTURE
  REFUND
  PAYOUT
  ADJUSTMENT
}

class PaymentTransactionStatus {
  <<enumeration>>
  PENDING
  PAID
  SETTLED
  REFUNDED
  FAILED
  DISPUTED
}

class PaymentChannel {
  <<enumeration>>
  DIRECT_WEBSITE
  AIRBNB
  BOOKING_COM
  VRBO
  CORPORATE_BOOKING
  MANUAL
}

class PaymentMethod {
  <<enumeration>>
  CARD
  APPLE_PAY
  GOOGLE_PAY
  PAYPAL
  ACH_TRANSFER
  CASH
  OTHER
}

Reservation "1" --> "many" PaymentTransaction : has payments
Invoice "0..1" --> "many" PaymentTransaction : invoices
DepositHold "0..1" --> "many" PaymentTransaction : may generate
PaymentTransaction "1" *-- "many" PaymentProviderEvent : provider events
PaymentTransaction "1" *-- "many" PaymentTimelineEvent : timeline
PaymentTransaction --> PaymentTransactionType
PaymentTransaction --> PaymentTransactionStatus
PaymentTransaction --> PaymentChannel
PaymentTransaction --> PaymentMethod
PaymentTransactionService --> PaymentTransaction
PaymentTransactionService --> Invoice
PaymentReconciliationService --> PaymentProviderEvent
PaymentReconciliationService --> PaymentTransaction
```

## Interpretation

`PaymentTransaction` is the aggregate for money movement.

It is not the same as a deposit hold. It can be linked to a hold when a hold creates a capture, release, refund, failed attempt, or dispute-related payment record.
