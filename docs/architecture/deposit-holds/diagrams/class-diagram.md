# DepositHold Class Diagram

This diagram defines the DepositHold aggregate and its relationship to Reservation and PaymentTransaction.

```mermaid
classDiagram
direction LR

class DepositHold {
  +UUID id
  +string holdNumber
  +DepositHoldKind kind
  +DepositHoldStatus status
  +Money amount
  +string provider
  +string providerCheckoutSessionId
  +string providerPaymentIntentId
  +string providerAuthorizationId
  +datetime requestedAt
  +datetime authorizedAt
  +datetime expiresAt
  +datetime capturedAt
  +datetime releasedAt
  +datetime failedAt
  +DepositRiskLevel riskLevel
  +string guestNote
  +string internalNotes
  +displayAmount() string
  +isActive() boolean
  +isExpiringSoon() boolean
  +canApprove() boolean
  +canCapture() boolean
  +canRelease() boolean
  +canRequestGuestAction() boolean
  +toRowPayload() dict
  +toDetailPayload() dict
  +toDataLakeRecord() dict
}

class Reservation {
  +int id
  +string requestKey
  +string guestName
  +string guestEmail
  +date checkIn
  +date checkOut
}

class StayListing {
  +int id
  +string name
  +string slug
  +string unitLabel
}

class PaymentTransaction {
  +UUID id
  +string transactionNumber
  +PaymentTransactionStatus status
  +Money amount
  +string provider
  +string providerTransactionId
  +datetime receivedAt
}

class HoldTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +string note
  +JSON metadata
  +datetime createdAt
}

class DepositHoldService {
  +createHold(payload, actor) DepositHold
  +approveHold(hold, actor) DepositHold
  +captureHold(hold, amount, actor) PaymentTransaction
  +releaseHold(hold, actor) DepositHold
  +requestGuestAction(hold, actor) DepositHold
  +generateReceipt(hold, actor) PaymentTransaction
  +emitTimeline(hold, eventType, actor, metadata) void
}

class DepositHoldProviderService {
  +createAuthorization(hold) DepositHold
  +captureAuthorization(hold, amount) PaymentTransaction
  +releaseAuthorization(hold) DepositHold
  +syncProviderStatus(hold) DepositHold
}

class DepositHoldKind {
  <<enumeration>>
  DAMAGE_DEPOSIT
  STAY_PAYMENT_HOLD
  SECURITY_EXCEPTION
}

class DepositHoldStatus {
  <<enumeration>>
  NEW
  REQUIRES_CONFIGURATION
  CHECKOUT_CREATED
  PENDING
  AUTHORIZED
  APPROVED
  CAPTURED
  RELEASED
  CANCELED
  FAILED
  DISPUTED
}

class DepositRiskLevel {
  <<enumeration>>
  LOW
  MEDIUM
  HIGH
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

Reservation "1" --> "many" DepositHold : has holds
StayListing "1" --> "many" DepositHold : property/listing
DepositHold "1" --> "many" PaymentTransaction : linked attempts
DepositHold "1" *-- "many" HoldTimelineEvent : authorization timeline
DepositHold --> DepositHoldKind
DepositHold --> DepositHoldStatus
DepositHold --> DepositRiskLevel
PaymentTransaction --> PaymentTransactionStatus
DepositHoldService --> DepositHold
DepositHoldService --> PaymentTransaction
DepositHoldService --> DepositHoldProviderService
DepositHoldProviderService --> DepositHold
DepositHoldProviderService --> PaymentTransaction
```

## Interpretation

`DepositHold` is the aggregate for authorization state.

It is not the same as a completed payment. It may create or link to PaymentTransaction objects when money movement occurs.
