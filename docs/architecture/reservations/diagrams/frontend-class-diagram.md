# Frontend Class Diagram - Reservation Domain Projection

This diagram defines how the React frontend should represent the Reservations Workspace.

The frontend should not decorate loose rows with fake state. It should map API payloads into `Reservation` domain objects and render projections from those objects.

```mermaid
classDiagram
direction LR

class Reservation {
  +string id
  +string key
  +string requestKey
  +ReservationGuest guest
  +ReservationStay stay
  +ReservationDates dates
  +ReservationStatusState status
  +ReservationRiskState risk
  +ReservationPaymentPlan paymentPlan
  +ReservationDepositHold depositHold
  +ReservationDocumentState documents
  +ReservationMessageThread messages
  +ReservationTimelineEvent[] timeline
  +ReservationAgentAssessment agent
  +displayTitle() string
  +displaySubtitle() string
  +canSendCheckInInstructions() boolean
  +canApproveDeposit() boolean
  +canGenerateInvoice() boolean
}

class ReservationGuest {
  +string name
  +string email
  +string phone
  +string initials
  +string country
  +string profileAdminUrl
  +string threadUrl
}

class ReservationStay {
  +number id
  +string name
  +string unitLabel
  +string listingUrl
  +string adminUrl
}

class ReservationDates {
  +string checkIn
  +string checkOut
  +number nights
  +string displayRange
}

class ReservationStatusState {
  +string value
  +string label
  +string tone
}

class ReservationRiskState {
  +string level
  +string label
  +string[] signals
}

class Money {
  +number amountCents
  +string currency
  +format() string
}

class ReservationPaymentPlan {
  +Money total
  +Money stayPayment
  +Money deposit
  +string status
  +ReservationPaymentStep[] steps
  +isPaid() boolean
}

class ReservationPaymentStep {
  +string label
  +Money amount
  +string status
  +string dueLabel
}

class ReservationDepositHold {
  +Money amount
  +string status
  +string label
  +string expiresAt
  +canApprove() boolean
  +canRelease() boolean
}

class ReservationDocumentState {
  +boolean propertyRulesAccepted
  +boolean damageTermsAccepted
  +string propertyRulesVersion
  +string damageTermsVersion
  +allAccepted() boolean
}

class ReservationMessageThread {
  +ReservationMessage[] messages
  +string suggestedDraft
  +latestMessage() ReservationMessage
}

class ReservationMessage {
  +string id
  +string senderLabel
  +string body
  +string status
  +string timestamp
  +boolean fromStaff
}

class ReservationTimelineEvent {
  +string type
  +string label
  +string actor
  +string timestamp
  +string note
}

class ReservationAgentAssessment {
  +string riskLevel
  +string suggestedReply
  +string[] missingInformation
  +string[] recommendedActions
  +string[] positiveSignals
}

class ReservationsSnapshot {
  +Reservation[] rows
  +Reservation selected
  +ReservationMetric[] metrics
  +ReservationFilterState filters
  +string generatedAt
}

class ReservationMetric {
  +string label
  +string value
  +string tone
}

class ReservationFilterState {
  +string query
  +string listing
  +string channel
  +string sourceCountry
  +string riskLevel
  +string dateRange
  +string status
}

class ReservationRepository {
  +loadSnapshot() ReservationsSnapshot
  +loadReservation(id) Reservation
  +updateStatus(id, status) Reservation
  +sendMessage(id, message) ReservationMessage
  +approveDeposit(id) ReservationDepositHold
  +releaseDeposit(id) ReservationDepositHold
  +generateInvoice(id) void
}

class ReservationService {
  +loadWorkspace() ReservationsSnapshot
  +selectReservation(id) Reservation
  +filterRows(snapshot, filters) Reservation[]
  +computeMetrics(rows) ReservationMetric[]
  +buildAgentPanel(reservation) ReservationAgentAssessment
}

class OpsReservationsPage {
  +snapshot
  +selectedReservation
  +filters
  +activeTab
  +render()
}

class ReservationTable {
  +rows
  +selectedId
  +onSelect(row)
}

class ReservationRow {
  +reservation
  +render()
}

class ReservationDetailPanel {
  +reservation
  +activeTab
  +render()
}

class ReservationGuestCard {
  +guest
  +stay
  +dates
  +paymentPlan
  +render()
}

class ReservationMessagePanel {
  +thread
  +activeTab
  +render()
}

class ReservationDepositPanel {
  +depositHold
  +paymentPlan
  +render()
}

class FairAgentPanel {
  +assessment
  +reservation
  +render()
}

ReservationsSnapshot "1" *-- "many" Reservation
ReservationsSnapshot "1" *-- "many" ReservationMetric
ReservationsSnapshot "1" *-- "1" ReservationFilterState

Reservation "1" *-- "1" ReservationGuest
Reservation "1" *-- "1" ReservationStay
Reservation "1" *-- "1" ReservationDates
Reservation "1" *-- "1" ReservationStatusState
Reservation "1" *-- "1" ReservationRiskState
Reservation "1" *-- "1" ReservationPaymentPlan
ReservationPaymentPlan "1" *-- "many" ReservationPaymentStep
Reservation "1" *-- "1" ReservationDepositHold
Reservation "1" *-- "1" ReservationDocumentState
Reservation "1" *-- "1" ReservationMessageThread
ReservationMessageThread "1" *-- "many" ReservationMessage
Reservation "1" *-- "many" ReservationTimelineEvent
Reservation "1" *-- "1" ReservationAgentAssessment

ReservationService --> ReservationRepository
ReservationService --> ReservationsSnapshot
ReservationService --> Reservation
OpsReservationsPage --> ReservationService
OpsReservationsPage --> ReservationTable
OpsReservationsPage --> ReservationDetailPanel
OpsReservationsPage --> FairAgentPanel
ReservationTable --> ReservationRow
ReservationDetailPanel --> ReservationGuestCard
ReservationDetailPanel --> ReservationMessagePanel
ReservationDetailPanel --> ReservationDepositPanel
```

## Frontend interpretation

`ReservationRepository` handles API communication and mapping.

`ReservationService` handles application-level operations such as filtering, selection, metrics, and action orchestration.

React components render object state. They must not invent business rules.
