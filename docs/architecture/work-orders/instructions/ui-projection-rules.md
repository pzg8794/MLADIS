# WorkOrder UI Projection Rules

This file defines how the Maintenance & Work Orders screen should render.

## Core rule

```text
The UI does not own the truth.
The WorkOrder object owns the truth.
The UI renders projections of WorkOrder state.
```

## What this means

Do not build the page like this:

```text
MetricCard data
TableRow data
DetailPanel data
Timeline data
ReportPreview data
```

Build it like this:

```text
WorkOrder objects
  -> WorkOrder metrics
  -> WorkOrder rows
  -> selected WorkOrder detail
  -> selected WorkOrder photos
  -> selected WorkOrder timeline
  -> selected WorkOrder report preview
```

## Page areas

### 1. Header

Title:

```text
Maintenance & Work Orders
```

Subtitle:

```text
Track, manage, and automate property maintenance and vendor work.
```

Actions:

- Filters
- Export
- New Work Order

### 2. Metrics

Metrics should be derived from WorkOrder objects.

Required cards:

- Open Work Orders
- Overdue Items
- This Month Cost
- Completed Jobs

Each card can show:

- icon
- value
- short trend label
- sparkline

### 3. WorkOrder list/table

Each row is a `WorkOrder` projection.

Columns:

- checkbox
- title
- property
- reservation
- assigned to
- priority
- cost
- date
- status

Clicking a row selects the WorkOrder and updates the detail panel.

### 4. Detail panel

The detail panel receives exactly one selected WorkOrder.

It renders:

- work order number
- status badge
- title
- property name
- reservation link
- edit/more/auto-generate actions
- cost/time/assignee/priority/status summary
- pictures
- notes
- linked listing
- linked reservation
- report preview
- timeline

### 5. Pictures

Photos are `WorkOrderPhoto` child entities.

Do not store photos as static UI mock data.

### 6. Report preview

Report preview is a projection of `WorkOrderReportState`.

The generate button should be enabled only when `workOrder.isReportReady()` is true.

### 7. Timeline

Timeline is a list of `WorkOrderTimelineEvent` objects.

It should include events like:

- created
- assigned
- status changed
- note added
- picture added
- report generated

## UI component responsibilities

### `OpsWorkOrdersPage`

Owns page state:

- snapshot
- filters
- selected work order ID
- loading/error state

It does not own business rules.

### `WorkOrderTable`

Renders rows and selection behavior.

It does not compute status rules.

### `WorkOrderRow`

Renders one WorkOrder summary.

### `WorkOrderDetailPanel`

Renders the selected WorkOrder.

### `WorkOrderReportPreview`

Renders report readiness and generated document state.

### `WorkOrderTimeline`

Renders WorkOrder timeline events.

## Visual design direction

The page should feel like a modern SaaS operations cockpit:

- clean workspace
- dark navy / teal MLADIS identity
- soft cards
- clear status chips
- dense but readable tables
- right-side detail inspector
- strong hierarchy
- minimal clutter

The design can be fresh and modern, but it must still be object-driven.
