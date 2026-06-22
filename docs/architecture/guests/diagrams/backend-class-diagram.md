# Backend Class Diagram - Guest Aggregate

This diagram defines the backend domain model, aggregate boundaries, service layer, and supporting enums for the Guests workspace.

Current code alignment:

- `CustomerProfile` is the existing persistence model.
- `Guest` is the preferred domain/API/frontend vocabulary.
- Short term: wrap `CustomerProfile` with `Guest` services and serializers.
- Long term: migrate the aggregate name when risk is low.

```mermaid
classDiagram
direction LR

class Guest {
  +int id
  +UUID publicToken
  +string displayName
  +string email
  +string phone
  +string country
  +string preferredLanguage
  +GuestSegment segment
  +GuestStatus status
  +GuestSource source
  +MarketingConsentStatus marketingConsentStatus
  +datetime marketingConsentRequestedAt
  +datetime marketingConsentAt
  +string marketingConsentSource
  +string notes
  +datetime createdAt
  +datetime updatedAt
  +initials() string
  +isRepeatGuest() boolean
  +isVip() boolean
  +isBlocked() boolean
  +canReceivePromotions() boolean
  +lastContactAt() datetime
  +totalSpend() Money
  +pastStayCount() int
  +toRowPayload() dict
  +toDetailPayload() dict
  +toAgentPayload() dict
  +toDataLakeRecord() dict
}

class GuestPreference {
  +UUID id
  +string key
  +string value
  +string source
  +datetime observedAt
  +toPayload() dict
}

class GuestTag {
  +UUID id
  +string label
  +string slug
  +string tone
}

class GuestMessage {
  +UUID id
  +string direction
  +string channel
  +string body
  +string status
  +datetime createdAt
  +datetime sentAt
  +toPayload() dict
}

class GuestStaySummary {
  +UUID id
  +string reservationKey
  +string listingName
  +date checkIn
  +date checkOut
  +Money total
  +string status
  +toPayload() dict
}

class GuestFeedback {
  +UUID id
  +string source
  +decimal rating
  +string feedbackText
  +string feedbackSummary
  +boolean isPublic
  +datetime createdAt
  +toPayload() dict
}

class GuestDocument {
  +UUID id
  +string documentType
  +string title
  +string status
  +string documentUrl
  +datetime createdAt
}

class GuestTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +string note
  +JSON metadata
  +datetime createdAt
  +toPayload() dict
}

class Reservation {
  +int id
  +string requestKey
  +date checkIn
  +date checkOut
  +string status
  +displayTotal() string
}

class PaymentTransaction {
  +UUID id
  +string transactionNumber
  +Money amount
  +string status
}

class DepositHold {
  +UUID id
  +string holdNumber
  +Money amount
  +string status
}

class GuestService {
  +createGuest(payload, actor) Guest
  +updateGuest(guest, payload, actor) Guest
  +mergeGuests(primaryGuest, duplicateGuest, actor) Guest
  +addTag(guest, tag, actor) Guest
  +removeTag(guest, tag, actor) Guest
  +recordPreference(guest, key, value, actor) GuestPreference
  +sendMessage(guest, message, actor) GuestMessage
  +syncFromReservation(reservation) Guest
  +syncFromAirbnbRecord(record) Guest
}

class GuestAnalyticsService {
  +computePastStayCount(guest) int
  +computeTotalSpend(guest) Money
  +computeLastContact(guest) datetime
  +computeSegment(guest) GuestSegment
}

class GuestDataLakeService {
  +emitObjectEvent(eventType, guest, actor, metadata) void
  +exportGuest(guest) dict
}

class GuestSegment {
  <<enumeration>>
  NEW
  AVERAGE
  REPEAT
  VIP
  BLACKLISTED
}

class GuestStatus {
  <<enumeration>>
  ACTIVE
  INACTIVE
  BLOCKED
  ARCHIVED
}

class GuestSource {
  <<enumeration>>
  DIRECT_WEBSITE
  AIRBNB
  BOOKING_COM
  VRBO
  CORPORATE_BOOKING
  MANUAL
  SOCIAL
  AGENT
}

class MarketingConsentStatus {
  <<enumeration>>
  UNKNOWN
  OPTED_IN
  OPTED_OUT
  REQUESTED
}

Guest "1" *-- "many" GuestPreference : preferences
Guest "1" *-- "many" GuestTag : tags
Guest "1" *-- "many" GuestMessage : messages
Guest "1" *-- "many" GuestStaySummary : stay summaries
Guest "1" *-- "many" GuestFeedback : feedback
Guest "1" *-- "many" GuestDocument : documents
Guest "1" *-- "many" GuestTimelineEvent : activity

Guest "1" --> "many" Reservation : books stays
Guest "1" --> "many" PaymentTransaction : pays
Guest "1" --> "many" DepositHold : authorizes holds

Guest --> GuestSegment
Guest --> GuestStatus
Guest --> GuestSource
Guest --> MarketingConsentStatus

GuestService --> Guest
GuestService --> GuestPreference
GuestService --> GuestMessage
GuestService --> GuestDataLakeService
GuestAnalyticsService --> Guest
GuestDataLakeService --> Guest
```

## Backend interpretation

`Guest` is the aggregate root for guest relationship management.

Current persistence can remain `CustomerProfile` while services/API expose `Guest` vocabulary.

Guest owns the relationship story:

- identity and contact data
- source/channel
- preferred language
- segmentation
- marketing consent
- tags and preferences
- messages
- stay history
- feedback
- documents
- payments/deposits/reservation links
- activity timeline

Services coordinate workflows. They do not replace the object model.
