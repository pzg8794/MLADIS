# MLADIS Work Orders Architecture

Date: 2026-06-19
Status: design contract / implementation reference

This directory is the canonical documentation home for the **Maintenance & Work Orders** object system.

The goal is to prevent the page from becoming a collection of disconnected UI cards. The page must be built from domain objects first.

## Core rule

```text
WorkOrder is the source object.
The list row, selected detail panel, report preview, photo strip, metrics, filters, and timeline are projections of WorkOrder state.
```

## Directory map

```text
docs/architecture/work-orders/
├── README.md
├── diagrams/
│   ├── backend-class-diagram.md
│   └── frontend-class-diagram.md
├── code/
│   ├── backend-model-stubs.md
│   └── frontend-domain-stubs.md
├── instructions/
│   ├── api-service-contract.md
│   ├── implementation-instructions.md
│   └── ui-projection-rules.md
└── images/
    └── README.md
```

## Existing code alignment

The current codebase already has a maintenance foundation:

- Backend model: `MaintenanceEvent`
- Backend child model: `MaintenancePhoto`
- Frontend domain object: `OpsMaintenanceEvent`
- Frontend page: `OpsMaintenancePage`
- Existing architecture note: `docs/maintenance-mvc-architecture.md`

The next implementation should either:

1. Rename `MaintenanceEvent` to `WorkOrder`, preferred long-term vocabulary, or
2. Keep `MaintenanceEvent` internally for migration safety while exposing `WorkOrder` as the domain/API/frontend vocabulary.

The product language should be `WorkOrder` because the screen is about work assignment, workflow status, cost, evidence, generated reports, and operational history.

## Design principle

The UI does not contain cards.

The UI contains `WorkOrder` objects, and cards are visual projections of those objects.

This is the MLADIS way: design the object system first, then let backend models, APIs, services, frontend domain classes, and UI components express that system consistently.
