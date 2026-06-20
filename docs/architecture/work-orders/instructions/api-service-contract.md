# WorkOrder API and Service Contract

This document defines the backend controller/service/API boundary for Work Orders.

## Rule

Controllers and React components do not own business rules.

Business rules live in:

- `WorkOrder`
- `WorkOrderService`
- `WorkOrderAIService`
- `WorkOrderReportService`
- `WorkOrderDataLakeService`

## Recommended API routes

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

## Snapshot payload

`GET /api/ops/work-orders/` returns a workspace snapshot.

```json
{
  "metrics": [],
  "rows": [],
  "filters": {},
  "generated_at": "2026-06-19T00:00:00Z"
}
```

## WorkOrder card/detail payload

```json
{
  "id": "uuid",
  "number": "WO-2026-0104",
  "title": "AC not cooling",
  "summary": "Guest reported AC not cooling properly.",
  "property": {
    "id": 1,
    "name": "3 Beds Apt, Vacation Home & Pool, G-101",
    "slug": "g-101",
    "admin_url": "/admin/bookings/bookableitem/1/change/"
  },
  "reservation": {
    "id": 1042,
    "request_key": "R-1042",
    "guest_name": "Piter Garcia",
    "date_range": "Jun 8 - Jun 14, 2026",
    "admin_url": "/admin/bookings/bookinginquiry/1042/change/"
  },
  "assignee": {
    "name": "Carlos M.",
    "role": "Technician",
    "avatar_label": "CM"
  },
  "priority": "high",
  "status": "in_progress",
  "cost": {
    "amount": "180.00",
    "currency": "USD",
    "display": "$180.00"
  },
  "dates": {
    "reported_at": "2026-06-10T09:30:00",
    "started_at": "",
    "completed_at": "",
    "due_at": "",
    "display": "Jun 10, 9:30 AM"
  },
  "evidence": {
    "photo_count": 3,
    "photos": []
  },
  "notes": {
    "manual": "Guest reported AC not cooling properly.",
    "internal": "",
    "ai_summary": "",
    "ai_diagnostics": "",
    "ai_recommendation": "",
    "active_mode": "manual"
  },
  "report": {
    "status": "ready",
    "preview_title": "Maintenance Report & Invoice",
    "can_generate": true,
    "document_url": "",
    "invoice_url": ""
  },
  "timeline": []
}
```

## Required service behavior

### `WorkOrderService.create_work_order`

Must:

- validate property/listing
- validate optional reservation belongs to the selected listing
- validate title, status, priority, reported time
- create timeline event `work_order_created`
- return a stable WorkOrder payload

### `WorkOrderService.transition_status`

Must:

- validate allowed transition
- set `completed_at` if moving to completed and no completed time exists
- create timeline event `work_order_status_changed`
- emit data-lake event

### `WorkOrderService.add_photo`

Must:

- attach photo as child entity
- compute metadata where possible
- choose cover photo when appropriate
- create timeline event `work_order_photo_uploaded`

### `WorkOrderReportService.generate_maintenance_report`

Must:

- build immutable report context
- generate preview/document snapshot
- create `WorkOrderReportSnapshot`
- never overwrite source WorkOrder evidence

### `WorkOrderAIService.generate_report_draft`

Must:

- use WorkOrder object payload
- use photo evidence where available
- return draft text only
- require human review before final report generation

## Data lake events

Every important action should emit an event:

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
