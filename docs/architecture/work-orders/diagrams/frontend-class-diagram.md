# Frontend Class Diagram - WorkOrder Domain Projection

This diagram defines how the React frontend should represent work orders.

The frontend should not receive loose card data. It should map API payloads into domain objects and then render those objects.

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

## Frontend interpretation

`WorkOrderRepository` handles API communication and mapping.

`WorkOrderService` handles application-level operations such as filtering, selection, and report generation.

React components render object state. They must not invent business rules.
