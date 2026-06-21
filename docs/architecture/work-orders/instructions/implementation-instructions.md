# WorkOrder Implementation Instructions

These instructions are for Codex, Cursor, or any AI/developer implementing the Work Orders page.

## Non-negotiable process

1. Read this directory first.
2. Do not start from random UI components.
3. Do not create disconnected cards.
4. Build the WorkOrder object model first.
5. Map backend payloads into frontend domain objects.
6. Render UI projections from those objects.
7. Preserve existing MLADIS routes and staff permissions unless a migration plan says otherwise.

## Implementation order

### Phase 1 - Backend vocabulary alignment

Choose one:

- Option A: Rename `MaintenanceEvent` to `WorkOrder` through a careful migration.
- Option B: Keep `MaintenanceEvent` internally but expose `WorkOrder` in services/API/frontend.

Preferred long-term direction: Option A.

Safe short-term direction: Option B.

### Phase 2 - Backend services

Create or refactor:

```text
airbnb_agent/bookings/services/work_orders.py
```

Include:

- `WorkOrderService`
- `WorkOrderAIService`
- `WorkOrderReportService`
- `WorkOrderDataLakeService`

### Phase 3 - API layer

Create stable API endpoints under `/api/ops/work-orders/`.

The API should return a normalized snapshot. Do not leak raw Django model internals directly into the frontend.

### Phase 4 - Frontend domain layer

Create:

```text
frontend/src/domain/work-orders.ts
```

This file owns the frontend WorkOrder class and value objects.

### Phase 5 - Repository layer

Create:

```text
frontend/src/infrastructure/WorkOrderRepository.ts
```

Repository responsibilities:

- fetch WorkOrder snapshot
- map API payloads into objects
- submit creates/updates
- upload photos
- request AI/report generation

### Phase 6 - Application service layer

Create:

```text
frontend/src/application/WorkOrderService.ts
```

Application service responsibilities:

- load dashboard
- select work order
- filter work orders
- compute metrics
- call repository for mutations

### Phase 7 - UI layer

Create or refactor:

```text
frontend/src/ui/pages/OpsWorkOrdersPage.tsx
frontend/src/ui/components/work-orders/
```

Components must render domain object state only.

## Required UI pieces

The final page should include:

1. Page header
2. Metrics row
3. WorkOrder table/list
4. Selected WorkOrder detail panel
5. Photo evidence strip
6. Linked listing/reservation section
7. AI-generated report preview
8. Activity timeline

## Required safety rules

- Do not delete existing admin pages.
- Do not break existing Django admin records.
- Do not remove existing maintenance data.
- Do not perform deployment from this task.
- Do not connect irreversible AI/payment/report actions without a review step.
- AI-generated report text must remain draft/reviewable until staff confirms.

## Validation commands before PR completion

From repo root:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test bookings
cd frontend
npm install
npm run build
```

If migrations are required, create and review them intentionally.

## Acceptance criteria

The implementation passes only when:

- A WorkOrder object powers each row/card.
- Selecting a row passes the selected WorkOrder object into the detail panel.
- Metrics are derived from WorkOrder objects or a backend snapshot generated from WorkOrder querysets.
- Report preview uses WorkOrder report state.
- Timeline is WorkOrder history, not static UI text.
- Photos are WorkOrderPhoto child objects.
- Business rules live in domain/services, not React components.
