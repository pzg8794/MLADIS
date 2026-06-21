# PaymentTransaction and DepositHold Relationship Contract

Date: 2026-06-20
Status: design contract / implementation reference

Payments and deposit holds are separate objects, but they must be designed together.

## Core distinction

```text
DepositHold = authorization state.
PaymentTransaction = money movement state.
```

A hold can exist before money is captured.

A payment transaction exists when a provider/payment workflow creates a money-movement record, such as a paid stay charge, deposit capture, refund, failed charge, payout, or adjustment.

## Relationship rules

1. A Reservation may have many PaymentTransaction objects.
2. A Reservation may have many DepositHold objects.
3. A DepositHold may have many linked PaymentTransaction attempts.
4. A PaymentTransaction may optionally reference a DepositHold.
5. A PaymentTransaction must not be used as the source of truth for authorization expiration.
6. A DepositHold must not be used as the source of truth for settled revenue.
7. Provider references must never be deleted after creation.
8. Payment provider actions must be server-side only.
9. Capture/release/refund require explicit staff action unless a separate scheduled automation contract is approved.

## Relationship diagram

```mermaid
classDiagram
direction LR

class Reservation {
  +int id
  +string requestKey
  +string guestName
  +date checkIn
  +date checkOut
  +displayTotal() string
}

class DepositHold {
  +UUID id
  +string holdNumber
  +DepositHoldKind kind
  +DepositHoldStatus status
  +Money amount
  +string provider
  +string providerAuthorizationId
  +datetime authorizedAt
  +datetime expiresAt
  +datetime capturedAt
  +datetime releasedAt
  +canCapture() boolean
  +canRelease() boolean
}

class PaymentTransaction {
  +UUID id
  +string transactionNumber
  +PaymentTransactionType type
  +PaymentTransactionStatus status
  +Money amount
  +string provider
  +string providerTransactionId
  +datetime receivedAt
  +datetime settledAt
  +datetime refundedAt
  +isPaid() boolean
  +canRefund() boolean
}

class Invoice {
  +UUID id
  +string invoiceNumber
  +InvoiceStatus status
  +Money amountDue
  +string documentUrl
}

class ProviderEvent {
  +UUID id
  +string provider
  +string eventType
  +string providerEventId
  +JSON payload
  +datetime receivedAt
}

class PaymentTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +datetime createdAt
}

class HoldTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +datetime createdAt
}

class PaymentReconciliationService {
  +matchProviderEvent(event) PaymentTransaction
  +reconcileTransaction(transaction) PaymentTransaction
}

class DepositHoldProviderService {
  +createAuthorization(hold) DepositHold
  +captureAuthorization(hold, amount) PaymentTransaction
  +releaseAuthorization(hold) DepositHold
  +syncProviderStatus(hold) DepositHold
}

class DataLakeService {
  +emitPaymentEvent(transaction, metadata) void
  +emitHoldEvent(hold, metadata) void
  +emitRelationshipEvent(reservation, hold, transaction) void
}

Reservation "1" --> "many" DepositHold : authorizations
Reservation "1" --> "many" PaymentTransaction : money movement
DepositHold "1" --> "0..many" PaymentTransaction : capture/refund/attempts
PaymentTransaction "0..many" --> "0..1" Invoice : invoice/receipt
ProviderEvent "many" --> "0..1" DepositHold : may update authorization
ProviderEvent "many" --> "0..1" PaymentTransaction : may create/reconcile
DepositHold "1" *-- "many" HoldTimelineEvent : authorization timeline
PaymentTransaction "1" *-- "many" PaymentTimelineEvent : payment timeline

PaymentReconciliationService --> ProviderEvent
PaymentReconciliationService --> PaymentTransaction
DepositHoldProviderService --> DepositHold
DepositHoldProviderService --> PaymentTransaction
DataLakeService --> Reservation
DataLakeService --> DepositHold
DataLakeService --> PaymentTransaction
```

## Lifecycle bridge diagram

```mermaid
flowchart TD
  A[Reservation created] --> B[DepositHold requested]
  B --> C[Provider authorization created]
  C --> D{Hold outcome}

  D -->|Authorized| E[DepositHold status: AUTHORIZED]
  D -->|Failed| F[DepositHold status: FAILED]
  D -->|Canceled| G[DepositHold status: CANCELED]

  E --> H{Staff/provider action}
  H -->|Release hold| I[DepositHold released]
  H -->|Capture hold| J[PaymentTransaction created: DEPOSIT_CAPTURE]
  H -->|Guest pays stay| K[PaymentTransaction created: STAY_PAYMENT]

  J --> L[Payment timeline updated]
  K --> L
  I --> M[Hold timeline updated]

  L --> N[Invoice or receipt snapshot]
  M --> O[Data lake hold event]
  N --> P[Data lake payment event]

  P --> Q[Reservation payment/deposit projection updates]
  O --> Q
```

## UI ownership

Payments & Transactions page:

```text
PaymentTransaction objects
  -> metrics
  -> rows
  -> transaction detail panel
  -> invoice preview
  -> linked reservation
  -> deposit history
  -> payment timeline
```

Deposits & Holds page:

```text
DepositHold objects
  -> metrics
  -> rows
  -> expiring-soon panel
  -> selected hold detail
  -> authorization timeline
  -> linked payment attempts
  -> guest note
  -> hold actions
```

## Shared services

The two systems may share:

- provider clients
- webhook ingestion
- timeline/event logging
- data lake export
- money formatting
- reservation links
- invoice/receipt generation

They should not share aggregate state directly.

## Event bridge

A provider event can update both systems through services:

```text
provider webhook received
  -> PaymentProviderEvent stored
  -> PaymentReconciliationService matches/creates PaymentTransaction
  -> DepositHoldProviderService updates hold authorization state if relevant
  -> DataLakeService emits object events for both affected objects
```
