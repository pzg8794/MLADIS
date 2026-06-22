# Ops Left-Nav Object Strategy Audit

Last updated: 2026-06-22

## Required Pattern

Every left-nav operations page must prefer real backend/API data and then fill only missing portions from isolated fallback fixtures:

React page -> application service -> repository -> API when available -> isolated fallback values when needed -> complete domain object -> UI projection.

Fallback/sample data is allowed and required for incomplete backend areas, but it must not live inside React page behavior. The page should not need to know whether values came from the API, fallback fixtures, or a mixed snapshot.

Domain objects expose metadata when helpful:

- `source: "api" | "fallback" | "mixed"`
- `missingFields: string[]`
- `isComplete: boolean`

## Route And Vocabulary Decisions

- `/ops/payments/` is a Payments workspace route. It must never be replaced by Deposits.
- `/ops/deposits/` is a DepositHold workspace route. It must never be merged into Payments.
- `/ops/properties/` is the canonical Properties route.
- `/ops/stays/` remains a legacy compatibility redirect/alias to Properties.
- `/ops/customers/` remains a compatibility URL for now, while the frontend domain vocabulary should become `Guest`.
- `/ops/admin/` is the Admin workspace. The left-nav label is Admin, not Users.

## Current Alignment

| Page | Domain Object | Data Strategy | Status |
| --- | --- | --- | --- |
| Payments | `PaymentsWorkspace` | Uses `/api/ops/payments/`; backend may return mixed live/mock rows. | Aligned |
| Properties | `PropertyListingsWorkspace` / `PropertyListing` | Isolated fallback repository until a properties projection API exists. | Aligned for UI projection |
| Reports | `ReportWorkspace` | Uses `/api/ops/reports/` summary cards, fallback chart/table projections for missing pieces. | Aligned |
| Tasks | `TaskWorkspace` / `Task` | Tries workboard repository, falls back because no `/api/ops/workboard/` route is registered. | Aligned for UI projection |
| Admin | `AdminWorkspace` | Uses `/api/ops/admin/` summary cards, fallback shortcut/feed/health projections for missing pieces. | Aligned |
| Settings | `SettingsWorkspace` | Uses `/api/ops/settings/` snapshot while preserving the local editable draft model. | Partially aligned |
| Guests | `GuestWorkspace` | Existing page uses `OpsWorkspaceService.loadCustomers`; domain vocabulary still needs full rename. | Existing stronger baseline |
| Calendar | `CalendarWorkspace` | Existing page uses `OpsWorkspaceService.loadCalendar` with real actions. | Existing stronger baseline |
| FairAgent | `AgentWorkspace` | Existing page uses `OpsWorkspaceService.loadAgent`. | Existing stronger baseline |
| Reservations | `OpsReservation` | Existing dedicated service/repository/domain implementation. | Strong baseline |
| Deposits | `DepositHold` | Existing dedicated service/repository/domain implementation. | Strong baseline |
| Maintenance | `WorkOrder` target | Existing service/repository-style page is the current baseline before rename/refactor. | Baseline |
| Command Center | `CommandCenterSnapshot` | Existing dashboard service/repository snapshot, later should compose summaries from object services. | Baseline |

## Remaining Work

Settings still contains a large local editable draft model and several UI-specific lists. Do not remove that functionality. The next Settings refactor should extract tab definitions, side-rail health/usage/change fixtures, and integration/key lists into `SettingsWorkspace` projections while keeping the local draft state as the editing controller state.

The next backend endpoint to add is `/api/ops/workboard/`, so `TaskWorkspace` can replace its fallback columns with real task records without rewriting `OpsWorkboardPage.tsx`.
