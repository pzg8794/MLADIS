# MLADIS Work Order OOP Class Design

Date: 2026-06-19
Status: design contract / implementation reference

## Purpose

This document defines the object-oriented design for the MLADIS Maintenance & Work Orders section.

The screen must not be implemented as disconnected cards, loose JSON blobs, or UI-only mock data. The screen is a projection of domain objects.

Core rule:

```text
WorkOrder is the source object.
The list row, selected detail panel, report preview, photo strip, metrics, filters, and timeline are projections of WorkOrder state.
```

This is the design rule that keeps MLADIS from becoming random UI code.

## Existing Code Alignment

The current codebase already has a maintenance foundation:

- `MaintenanceEvent` exists as the current backend aggregate root.
- `MaintenancePhoto` exists as the child evidence entity.
- `OpsMaintenanceEvent` exists as the current frontend domain projection.
- `OpsMaintenancePage` exists as the current UI page.
- `docs/maintenance-mvc-architecture.md` defines the first MVC/OOP contract for maintenance.

The next implementation should either:

1. Rename `MaintenanceEvent` to `WorkOrder`, preferred long-term vocabulary, or
2. Keep `MaintenanceEvent` internally for migration safety while wrapping it with a clearer `WorkOrder` domain/API vocabulary.

The product language should become `WorkOrder` because the page is explicitly about work orders, assignment, workflow, cost, evidence, reports, and operational history.

## Backend Class Diagram

```mermaid
classDiagram
direction LR

class WorkOrder {
  +UUID id
  +string workOrderNumber
  +string title
  +string summary
  +string description

  +WorkOrderType workType
  +WorkOrderStatus status
  +WorkOrderPriority priority
  +WorkOrderSource source

  +Decimal costAmount
  +string costCurrency
  +WorkOrderPaymentStatus paymentStatus
  +string invoiceNumber
  +string proofOfPaymentRef

  +datetime reportedAt
  +datetime scheduledFor
  +datetime startedAt
  +datetime completedAt
  +datetime dueAt
  +string timezoneName

  +string vendorName
  +string vendorContact
  +string assignedToName
  +string assignedRoleLabel

  +string manualNotes
  +string internalNotes
  +string aiSummary
  +string aiDiagnostics
  +string aiRecommendation
  +datetime aiGeneratedAt
  +string aiModel
  +JSON aiMetadata
  +boolean useAiSummary

  +WorkOrderReportStatus reportStatus
  +datetime reportGeneratedAt
  +string reportDocumentUrl
  +string invoiceDocumentUrl

  +displayCost() string
  +durationMinutes() int
  +isOverdue() boolean
  +isReportReady() boolean
  +effectiveNotes() string
  +coverPhotoUrl() string
  +canTransitionTo(nextStatus) boolean
  +transitionTo(nextStatus, actor, note) void
  +toCardPayload() dict
  +toDetailPayload() dict
  +toAgentPayload() dict
  +toDataLakeRecord() dict
}

class WorkOrderPhoto {
  +UUID id
  +File image
  +string caption
  +int sortOrder
  +boolean isCover
  +string checksumSha256
  +string mimeType
  +int fileSizeBytes
  +datetime capturedAt
  +datetime uploadedAt

  +imageUrl() string
  +toAgentPayload() dict
}

class WorkOrderTimelineEvent {
  +UUID id
  +string eventType
  +string label
  +string note
  +JSON metadata
  +datetime createdAt

  +toPayload() dict
}

class WorkOrderReportSnapshot {
  +UUID id
  +string reportType
  +string title
  +string status
  +string documentUrl
  +JSON sourcePayload
  +datetime generatedAt

  +toPreviewPayload() dict
}

class BookableItem {
  +int id
  +string name
  +string slug
  +businessDisplayName() string
}

class BookingInquiry {
  +int id
  +string requestKey
  +string guestName
  +string email
  +date checkIn
  +date checkOut
  +int guests
  +string status
  +displayTotal() string
}

class User {
  +int id
  +string username
  +string email
}

class WorkOrderService {
  +createWorkOrder(payload, actor) WorkOrder
  +updateWorkOrder(workOrder, payload, actor) WorkOrder
  +assignWorkOrder(workOrder, assignee, actor) WorkOrder
  +transitionStatus(workOrder, nextStatus, actor, note) WorkOrder
  +addPhoto(workOrder, file, caption, actor) WorkOrderPhoto
  +addNote(workOrder, note, actor) WorkOrderTimelineEvent
  +generateReport(workOrder, actor) WorkOrderReportSnapshot
  +exportWorkOrder(workOrder, actor) dict
}

class WorkOrderAIService {
  +generateSummary(workOrder) string
  +generateDiagnostics(workOrder) string
  +generateRecommendation(workOrder) string
  +generateReportDraft(workOrder) dict
}

class WorkOrderReportService {
  +buildReportContext(workOrder) dict
  +generateMaintenanceReport(workOrder) WorkOrderReportSnapshot
  +generateInvoicePreview(workOrder) WorkOrderReportSnapshot
}

class WorkOrderDataLakeService {
  +emitObjectEvent(eventType, workOrder, actor, metadata) void
  +exportWorkOrder(workOrder) dict
  +exportPhotos(workOrder) list
}

class WorkOrderStatus {
  <<enumeration>>
  OPEN
  IN_PROGRESS
  PENDING
  COMPLETED
  OVERDUE
  CANCELLED
  ARCHIVED
}

class WorkOrderPriority {
  <<enumeration>>
  LOW
  MEDIUM
  HIGH
  URGENT
}

class WorkOrderType {
  <<enumeration>>
  CLEANING
  REPAIR
  REPLACEMENT
  INSPECTION
  SUPPLIES
  SAFETY
  OTHER
}

class WorkOrderSource {
  <<enumeration>>
  STAFF
  GUEST
  SYSTEM
  CALENDAR
  AIRBNB
  ADMIN
}

class WorkOrderPaymentStatus {
  <<enumeration>>
  UNPAID
  PENDING
  PAID
  REIMBURSED
  DISPUTED
}

class WorkOrderReportStatus {
  <<enumeration>>
  NOT_READY
  READY
  GENERATED
  SENT
}

BookableItem "1" --> "many" WorkOrder : owns maintenance
BookingInquiry "0..1" --> "many" WorkOrder : may trigger
User "0..1" --> "many" WorkOrder : assigned_to
User "1" --> "many" WorkOrder : created_by
User "0..1" --> "many" WorkOrder : approved_by

WorkOrder "1" *-- "many" WorkOrderPhoto : evidence
WorkOrder "1" *-- "many" WorkOrderTimelineEvent : history
WorkOrder "1" *-- "many" WorkOrderReportSnapshot : generated docs

WorkOrder --> WorkOrderStatus
WorkOrder --> WorkOrderPriority
WorkOrder --> WorkOrderType
WorkOrder --> WorkOrderSource
WorkOrder --> WorkOrderPaymentStatus
WorkOrder --> WorkOrderReportStatus

WorkOrderService --> WorkOrder
WorkOrderService --> WorkOrderPhoto
WorkOrderService --> WorkOrderTimelineEvent
WorkOrderService --> WorkOrderReportSnapshot
WorkOrderService --> WorkOrderAIService
WorkOrderService --> WorkOrderReportService
WorkOrderService --> WorkOrderDataLakeService
```

## Frontend Class Diagram

```mermaid
classDiagram
direction LR

class WorkOrder {
  +string id
  +string number
  +string title
  +string summary
  +WorkOrderProperty property
  +WorkOrderReservation reservation
  +WorkOrderAssignee assignee
  +WorkOrderPriorityState priority
  +WorkOrderStatusState status
  +Money cost
  +WorkOrderDates dates
  +WorkOrderEvidence evidence
  +WorkOrderNotes notes
  +WorkOrderReportState report
  +WorkOrderTimelineEvent[] timeline

  +isSelected() boolean
  +isOverdue() boolean
  +isReportReady() boolean
  +displaySubtitle() string
}

class WorkOrderProperty {
  +number id
  +string name
  +string slug
  +string adminUrl
}

class WorkOrderReservation {
  +number id
  +string requestKey
  +string guestName
  +string dateRange
  +string adminUrl
}

class WorkOrderAssignee {
  +string name
  +string role
  +string avatarLabel
}

class Money {
  +number amountCents
  +string currency
  +format() string
}

class WorkOrderDates {
  +string reportedAt
  +string scheduledFor
  +string startedAt
  +string completedAt
  +string dueAt
  +string display
  +durationLabel() string
}

class WorkOrderPhoto {
  +string id
  +string url
  +string caption
  +boolean isCover
}

class WorkOrderEvidence {
  +WorkOrderPhoto[] photos
  +number photoCount
  +coverPhoto() WorkOrderPhoto
}

class WorkOrderNotes {
  +string manual
  +string internal
  +string aiSummary
  +string aiDiagnostics
  +string aiRecommendation
  +string activeMode
  +effectiveText() string
}

class WorkOrderReportState {
  +string status
  +string previewTitle
  +boolean canGenerate
  +string documentUrl
  +string invoiceUrl
}

class WorkOrderTimelineEvent {
  +string type
  +string label
  +string actor
  +string timestamp
  +string note
}

class WorkOrdersSnapshot {
  +WorkOrderMetric[] metrics
  +WorkOrder[] rows
  +WorkOrder selected
  +WorkOrderFilterState filters
  +string generatedAt
}

class WorkOrderMetric {
  +string label
  +string value
  +string trendLabel
  +string accent
  +number[] sparkline
}

class WorkOrderFilterState {
  +string query
  +string status
  +string priority
  +string property
  +string assignee
  +string dateRange
}

class WorkOrderRepository {
  +loadSnapshot() WorkOrdersSnapshot
  +loadWorkOrder(id) WorkOrder
  +createWorkOrder(draft) WorkOrder
  +updateWorkOrder(id, patch) WorkOrder
  +uploadPhoto(id, file) WorkOrderPhoto
  +transitionStatus(id, nextStatus) WorkOrder
  +generateReport(id) WorkOrderReportState
}

class WorkOrderService {
  +loadDashboard() WorkOrdersSnapshot
  +selectWorkOrder(id) WorkOrder
  +filterRows(snapshot, filters) WorkOrder[]
  +computeMetrics(rows) WorkOrderMetric[]
  +buildDetailPanel(workOrder) WorkOrderDetailViewModel
  +generateReport(workOrder) WorkOrderReportState
}

class OpsWorkOrdersPage {
  +snapshot
  +selectedWorkOrder
  +filters
  +render()
}

class WorkOrderTable {
  +rows
  +selectedId
  +onSelect(row)
}

class WorkOrderRow {
  +workOrder
  +render()
}

class WorkOrderDetailPanel {
  +workOrder
  +render()
}

class WorkOrderReportPreview {
  +report
  +workOrder
  +render()
}

class WorkOrderTimeline {
  +events
  +render()
}

WorkOrdersSnapshot "1" *-- "many" WorkOrder
WorkOrdersSnapshot "1" *-- "many" WorkOrderMetric
WorkOrdersSnapshot "1" *-- "1" WorkOrderFilterState

WorkOrder "1" *-- "1" WorkOrderProperty
WorkOrder "1" *-- "0..1" WorkOrderReservation
WorkOrder "1" *-- "0..1" WorkOrderAssignee
WorkOrder "1" *-- "1" Money
WorkOrder "1" *-- "1" WorkOrderDates
WorkOrder "1" *-- "1" WorkOrderEvidence
WorkOrderEvidence "1" *-- "many" WorkOrderPhoto
WorkOrder "1" *-- "1" WorkOrderNotes
WorkOrder "1" *-- "1" WorkOrderReportState
WorkOrder "1" *-- "many" WorkOrderTimelineEvent

WorkOrderService --> WorkOrderRepository
WorkOrderService --> WorkOrdersSnapshot
WorkOrderService --> WorkOrder
OpsWorkOrdersPage --> WorkOrderService
OpsWorkOrdersPage --> WorkOrderTable
OpsWorkOrdersPage --> WorkOrderDetailPanel
WorkOrderTable --> WorkOrderRow
WorkOrderDetailPanel --> WorkOrderReportPreview
WorkOrderDetailPanel --> WorkOrderTimeline
```

## Domain Object Contract

### WorkOrder

`WorkOrder` is the aggregate root. Every card, table row, detail panel, report preview, timeline entry, and metric must be derived from one or more `WorkOrder` objects.

Primary attributes:

- identity: `id`, `workOrderNumber`
- title: `title`, `summary`, `description`
- classification: `workType`, `source`
- workflow: `status`, `priority`
- property relationship: `item`
- optional reservation relationship: `reservation`
- assignment: `assignedToName`, `assignedToUser`, `vendorName`, `vendorContact`
- cost/payment: `costAmount`, `costCurrency`, `paymentStatus`, `invoiceNumber`, `proofOfPaymentRef`
- time: `reportedAt`, `scheduledFor`, `startedAt`, `completedAt`, `dueAt`, `timezoneName`
- evidence: `photos`
- notes: `manualNotes`, `internalNotes`, `aiSummary`, `aiDiagnostics`, `aiRecommendation`
- generated docs: `reportStatus`, `reportDocumentUrl`, `invoiceDocumentUrl`
- audit: timeline events and data-lake events

### WorkOrderPhoto

`WorkOrderPhoto` is a child entity. Photos must not be stored as an array or comma-separated field on the parent object.

Photo objects support:

- proof/evidence
- report generation
- AI diagnostics
- cover thumbnail selection
- checksum-based duplicate detection

### WorkOrderTimelineEvent

Timeline events preserve the operational story of the work order.

Examples:

- `work_order_created`
- `work_order_assigned`
- `work_order_status_changed`
- `work_order_note_added`
- `work_order_photo_uploaded`
- `work_order_report_generated`

### WorkOrderReportSnapshot

Reports are generated snapshots. A generated report must not replace the source WorkOrder. It should capture the data used to generate the document at that moment.

This preserves auditability.

## Backend Validation Rules

A WorkOrder can be created when it has:

- property/listing
- title
- status
- priority
- reported time

A WorkOrder becomes report-ready when it has:

- property/listing
- title
- cost
- status
- notes or AI summary
- at least one photo or documented exception
- linked reservation when caused by a stay
- timeline history

A WorkOrder becomes completed when:

- status transition is valid
- completed time is present or automatically set
- required notes are present
- required evidence exists or is explicitly waived by staff

## Service Layer Contract

Controllers and UI components must not directly implement business rules.

Required service classes:

```python
class WorkOrderService:
    def create_work_order(self, payload, actor): ...
    def update_work_order(self, work_order, payload, actor): ...
    def assign_work_order(self, work_order, assignee, actor): ...
    def transition_status(self, work_order, next_status, actor, note=""): ...
    def add_photo(self, work_order, file, caption, actor): ...
    def add_note(self, work_order, note, actor): ...
    def generate_report(self, work_order, actor): ...
    def export_work_order(self, work_order, actor): ...
```

```python
class WorkOrderAIService:
    def generate_summary(self, work_order): ...
    def generate_diagnostics(self, work_order): ...
    def generate_recommendation(self, work_order): ...
    def generate_report_draft(self, work_order): ...
```

```python
class WorkOrderReportService:
    def build_report_context(self, work_order): ...
    def generate_maintenance_report(self, work_order): ...
    def generate_invoice_preview(self, work_order): ...
```

```python
class WorkOrderDataLakeService:
    def emit_object_event(self, event_type, work_order, actor, metadata): ...
    def export_work_order(self, work_order): ...
    def export_photos(self, work_order): ...
```

## API Contract

Recommended endpoints:

```text
GET    /api/ops/work-orders/
POST   /api/ops/work-orders/
GET    /api/ops/work-orders/<uuid>/
PATCH  /api/ops/work-orders/<uuid>/
POST   /api/ops/work-orders/<uuid>/assign/
POST   /api/ops/work-orders/<uuid>/transition/
POST   /api/ops/work-orders/<uuid>/photos/
POST   /api/ops/work-orders/<uuid>/notes/
POST   /api/ops/work-orders/<uuid>/generate-report/
GET    /api/ops/work-orders/<uuid>/agent-payload/
GET    /api/ops/work-orders/<uuid>/timeline/
```

## Frontend Implementation Contract

Recommended files:

```text
frontend/src/domain/work-orders.ts
frontend/src/application/WorkOrderService.ts
frontend/src/infrastructure/WorkOrderRepository.ts
frontend/src/ui/pages/OpsWorkOrdersPage.tsx
frontend/src/ui/components/work-orders/WorkOrderMetricCard.tsx
frontend/src/ui/components/work-orders/WorkOrderTable.tsx
frontend/src/ui/components/work-orders/WorkOrderRow.tsx
frontend/src/ui/components/work-orders/WorkOrderDetailPanel.tsx
frontend/src/ui/components/work-orders/WorkOrderTimeline.tsx
frontend/src/ui/components/work-orders/WorkOrderReportPreview.tsx
frontend/src/ui/components/work-orders/WorkOrderPhotoStrip.tsx
```

Rules:

- Domain classes live in `frontend/src/domain`.
- API/repository classes live in `frontend/src/infrastructure`.
- Service/factory logic lives in `frontend/src/application`.
- React components live in `frontend/src/ui`.
- UI components render state; they do not invent business rules.

## UI Projection Rules

The Maintenance & Work Orders page contains:

1. Metrics row
2. WorkOrder table/list
3. Selected WorkOrder detail panel
4. Photo evidence strip
5. Linked listing/reservation section
6. AI-generated report preview
7. Activity timeline

Each part must be a projection of WorkOrder state.

### Metrics

Metrics are computed from WorkOrder objects:

- open work orders
- overdue items
- this month cost
- completed jobs

### Table Row

Each row shows:

- title
- property
- reservation
- assigned to
- priority
- cost
- date
- status

### Detail Panel

The selected WorkOrder drives:

- header number/status/title
- action buttons
- cost/time/assignee/priority/status summary
- pictures
- notes
- linked listing
- linked reservation
- AI-generated report preview
- activity timeline

## Data Lake / Event Logging

Every important action emits an object event:

```text
work_order_created
work_order_updated
work_order_assigned
work_order_status_changed
work_order_photo_uploaded
work_order_note_added
work_order_report_generated
work_order_exported
```

Each event should include:

- work_order_id
- property_id
- reservation_id if available
- actor_id
- old status
- new status
- cost amount/currency
- priority
- timestamp
- request/session metadata when available

## Design Principle

The UI does not contain cards.

The UI contains WorkOrder objects, and cards are only visual projections of those objects.

This is the MLADIS way: design the object system first, then let the frontend and backend express that system consistently.
