# Frontend Class Diagram - Guest Domain Projection

This diagram defines how the React frontend should represent the Guests workspace.

The frontend should not decorate loose rows with fake state. It should map API payloads into `Guest` domain objects and render projections from those objects.

```mermaid
classDiagram
direction LR

class Guest {
  +string id
  +string key
  +GuestIdentity identity
  +GuestContact contact
  +GuestProfile profile
  +GuestStatusState status
  +GuestSegmentState segment
  +GuestMarketingState marketing
  +GuestPreference[] preferences
  +GuestTag[] tags
  +GuestMessageThread messages
  +GuestStaySummary[] stays
  +GuestPaymentSummary payments
  +GuestDepositSummary deposits
  +GuestDocument[] documents
  +GuestTimelineEvent[] timeline
  +displayName() string
  +initials() string
  +isVip() boolean
  +isRepeatGuest() boolean
  +isBlocked() boolean
  +canMessage() boolean
  +canReceivePromotions() boolean
}

class GuestIdentity {
  +string name
  +string initials
  +string country
  +string preferredLanguage
  +string source
}

class GuestContact {
  +string email
  +string phone
  +string lastContactAt
  +string profileAdminUrl
  +string fullProfileUrl
}

class GuestProfile {
  +string birthday
  +string travelStyle
  +string guestSince
  +string notes
}

class GuestStatusState {
  +string value
  +string label
  +string tone
}

class GuestSegmentState {
  +string value
  +string label
  +string tone
}

class GuestMarketingState {
  +string consentStatus
  +string consentLabel
  +string requestedAt
  +string consentAt
  +boolean canReceivePromotions
}

class GuestPreference {
  +string key
  +string value
  +string source
}

class GuestTag {
  +string label
  +string slug
  +string tone
}

class GuestMessageThread {
  +GuestMessage[] messages
  +string draft
  +latestMessage() GuestMessage
}

class GuestMessage {
  +string id
  +string senderLabel
  +string body
  +string status
  +string timestamp
  +boolean fromStaff
}

class GuestStaySummary {
  +string id
  +string reservationKey
  +string listingName
  +string dateRange
  +Money total
  +string status
  +string reservationUrl
}

class GuestPaymentSummary {
  +Money totalSpend
  +number paymentCount
  +string lastPaymentAt
}

class GuestDepositSummary {
  +number activeHolds
  +number releasedHolds
  +number disputeCount
}

class GuestDocument {
  +string id
  +string title
  +string type
  +string status
  +string url
}

class GuestTimelineEvent {
  +string type
  +string label
  +string actor
  +string timestamp
  +string note
}

class GuestsSnapshot {
  +Guest[] rows
  +Guest selected
  +GuestMetric[] metrics
  +GuestFilterState filters
  +string generatedAt
}

class GuestMetric {
  +string label
  +string value
  +string tone
}

class GuestFilterState {
  +string query
  +string source
  +string country
  +string tags
  +string segment
  +string status
}

class GuestRepository {
  +loadSnapshot() GuestsSnapshot
  +loadGuest(id) Guest
  +createGuest(draft) Guest
  +updateGuest(id, patch) Guest
  +sendMessage(id, message) GuestMessage
  +addTag(id, tag) Guest
  +removeTag(id, tag) Guest
}

class GuestService {
  +loadWorkspace() GuestsSnapshot
  +selectGuest(id) Guest
  +filterRows(snapshot, filters) Guest[]
  +computeMetrics(rows) GuestMetric[]
  +buildProfilePanel(guest) Guest
}

class OpsGuestsPage {
  +snapshot
  +selectedGuest
  +filters
  +activeTab
  +render()
}

class GuestTable {
  +rows
  +selectedId
  +onSelect(row)
}

class GuestRow {
  +guest
  +render()
}

class GuestProfileCard {
  +guest
  +render()
}

class GuestMessagePanel {
  +thread
  +render()
}

class GuestStayPanel {
  +stays
  +render()
}

class GuestActivityPanel {
  +events
  +render()
}

GuestsSnapshot "1" *-- "many" Guest
GuestsSnapshot "1" *-- "many" GuestMetric
GuestsSnapshot "1" *-- "1" GuestFilterState

Guest "1" *-- "1" GuestIdentity
Guest "1" *-- "1" GuestContact
Guest "1" *-- "1" GuestProfile
Guest "1" *-- "1" GuestStatusState
Guest "1" *-- "1" GuestSegmentState
Guest "1" *-- "1" GuestMarketingState
Guest "1" *-- "many" GuestPreference
Guest "1" *-- "many" GuestTag
Guest "1" *-- "1" GuestMessageThread
GuestMessageThread "1" *-- "many" GuestMessage
Guest "1" *-- "many" GuestStaySummary
Guest "1" *-- "1" GuestPaymentSummary
Guest "1" *-- "1" GuestDepositSummary
Guest "1" *-- "many" GuestDocument
Guest "1" *-- "many" GuestTimelineEvent

GuestService --> GuestRepository
GuestService --> GuestsSnapshot
GuestService --> Guest
OpsGuestsPage --> GuestService
OpsGuestsPage --> GuestTable
OpsGuestsPage --> GuestProfileCard
OpsGuestsPage --> GuestMessagePanel
OpsGuestsPage --> GuestStayPanel
GuestTable --> GuestRow
```

## Frontend interpretation

`GuestRepository` handles API communication and mapping.

`GuestService` handles application-level operations such as filtering, selection, metrics, and action orchestration.

React components render object state. They must not invent business rules.
