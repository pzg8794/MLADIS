# Backend Class Diagram - WorkOrder Aggregate

This diagram defines the backend domain model, aggregate boundaries, service layer, and supporting enums for the Work Orders system.

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
  +datetime reportedAt
  +datetime scheduledFor
  +datetime startedAt
  +datetime completedAt
  +datetime dueAt
  +string vendorName
  +string vendorContact
  +string assignedToName
  +string manualNotes
  +string internalNotes
  +string aiSummary
  +string aiDiagnostics
  +string aiRecommendation
  +WorkOrderReportStatus reportStatus
  +displayCost() string
  +durationMinutes() int
  +isOverdue() boolean
  +isReportReady() boolean
  +effectiveNotes() string
  +toCardPayload() dict
  +toDetailPayload() dict
  +toAgentPayload() dict
}

class WorkOrderPhoto {
  +UUID id
  +File image
  +string caption
  +int sortOrder
  +boolean isCover
  +string checksumSha256
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
  +date checkIn
  +date checkOut
  +int guests
  +string status
}

class StaffAccount {
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
  +generateReport(workOrder, actor) WorkOrderReportSnapshot
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
StaffAccount "0..1" --> "many" WorkOrder : assigned_to
StaffAccount "1" --> "many" WorkOrder : created_by

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
WorkOrderService --> WorkOrderReportSnapshot
WorkOrderService --> WorkOrderAIService
WorkOrderService --> WorkOrderReportService
WorkOrderService --> WorkOrderDataLakeService
```

## Backend interpretation

`WorkOrder` is the aggregate root.

`WorkOrderPhoto`, `WorkOrderTimelineEvent`, and `WorkOrderReportSnapshot` are child entities owned by the aggregate.

`BookableItem`, `BookingInquiry`, and `StaffAccount` are external domain objects referenced by the aggregate.

Services coordinate workflows. They do not replace the object model.
