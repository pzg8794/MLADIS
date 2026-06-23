# Guest Relationship Diagram

Guest is a relationship aggregate. It connects reservations, payments, deposits, messages, feedback, and stay history without replacing those objects.

## Core distinction

```text
Guest = relationship and identity state.
Reservation = stay/booking state.
PaymentTransaction = money movement state.
DepositHold = authorization state.
```

## Relationship diagram

```mermaid
classDiagram
direction LR

class Guest {
  +int id
  +string displayName
  +string email
  +string phone
  +GuestSegment segment
  +MarketingConsentStatus marketingConsentStatus
  +preferredLanguage
  +isVip() boolean
  +isRepeatGuest() boolean
  +canReceivePromotions() boolean
}

class Reservation {
  +int id
  +string requestKey
  +date checkIn
  +date checkOut
  +int guests
  +string status
  +displayTotal() string
}

class PaymentTransaction {
  +UUID id
  +string transactionNumber
  +Money amount
  +string status
  +datetime receivedAt
}

class DepositHold {
  +UUID id
  +string holdNumber
  +Money amount
  +string status
  +datetime expiresAt
}

class GuestMessage {
  +UUID id
  +string channel
  +string direction
  +string body
  +datetime createdAt
}

class GuestFeedback {
  +UUID id
  +string source
  +decimal rating
  +string feedbackSummary
  +boolean isPublic
}

class GuestTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +datetime createdAt
}

class GuestService {
  +syncFromReservation(reservation) Guest
  +mergeGuests(primaryGuest, duplicateGuest, actor) Guest
  +recordContact(guest, message, actor) GuestMessage
}

class GuestAnalyticsService {
  +computePastStayCount(guest) int
  +computeTotalSpend(guest) Money
  +computeLastContact(guest) datetime
  +computeSegment(guest) GuestSegment
}

Guest "1" --> "many" Reservation : books stays
Guest "1" --> "many" PaymentTransaction : payment history
Guest "1" --> "many" DepositHold : hold history
Guest "1" *-- "many" GuestMessage : communication
Guest "1" *-- "many" GuestFeedback : feedback
Guest "1" *-- "many" GuestTimelineEvent : activity

Reservation "1" --> "many" PaymentTransaction : stay payments
Reservation "1" --> "many" DepositHold : stay holds

GuestService --> Guest
GuestService --> Reservation
GuestAnalyticsService --> Guest
GuestAnalyticsService --> Reservation
GuestAnalyticsService --> PaymentTransaction
GuestAnalyticsService --> DepositHold
```

## Lifecycle bridge diagram

```mermaid
flowchart TD
  A[Reservation request created] --> B[Find or create Guest by normalized email/contact]
  B --> C[Reservation links to Guest]
  C --> D[Guest profile projection updates]
  D --> E[Guest row shows segment, source, country, past stays, total spend]

  C --> F[PaymentTransaction created or reconciled]
  C --> G[DepositHold requested or updated]
  C --> H[GuestMessage sent or received]
  C --> I[GuestFeedback imported or entered]

  F --> J[Guest total spend updates]
  G --> K[Guest deposit history updates]
  H --> L[Guest last contact updates]
  I --> M[Guest feedback/tags update]

  J --> N[Guest metrics and filters update]
  K --> N
  L --> N
  M --> N
```

## Interpretation

A Guest should not own Reservation, PaymentTransaction, or DepositHold state directly.

A Guest owns identity, relationship, consent, preference, tag, message, feedback, and activity state.

Reservation, PaymentTransaction, and DepositHold remain their own aggregates and project summary information into the Guest workspace.
