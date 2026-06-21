# DepositHold Implementation Instructions

These instructions are for Codex, Cursor, or any AI/developer implementing the Deposits & Holds workspace.

## Non-negotiable process

1. Read this directory and `docs/architecture/payments/` first.
2. Do not start from loose deposit table rows.
3. Build or wrap the DepositHold object first.
4. Link holds to Reservation and related PaymentTransaction attempts.
5. Map backend payloads into frontend domain objects.
6. Render UI projections from those objects.

## Required backend services

Recommended file:

```text
airbnb_agent/bookings/services/deposit_holds.py
```

Services:

- `DepositHoldService`
- `DepositHoldProviderService`
- `DepositHoldTimelineService`
- `DepositHoldDataLakeService`

## Required API routes

```text
GET    /api/ops/deposit-holds/
GET    /api/ops/deposit-holds/<uuid>/
POST   /api/ops/deposit-holds/<uuid>/approve/
POST   /api/ops/deposit-holds/<uuid>/capture/
POST   /api/ops/deposit-holds/<uuid>/release/
POST   /api/ops/deposit-holds/<uuid>/request-guest-action/
POST   /api/ops/deposit-holds/<uuid>/generate-receipt/
POST   /api/ops/deposit-holds/<uuid>/add-note/
GET    /api/ops/deposit-holds/<uuid>/timeline/
```

## Required frontend files

```text
frontend/src/domain/deposit-holds.ts
frontend/src/application/DepositHoldService.ts
frontend/src/infrastructure/DepositHoldRepository.ts
frontend/src/ui/pages/OpsDepositHoldsPage.tsx
frontend/src/ui/components/deposit-holds/DepositHoldTable.tsx
frontend/src/ui/components/deposit-holds/DepositHoldRow.tsx
frontend/src/ui/components/deposit-holds/DepositHoldDetails.tsx
frontend/src/ui/components/deposit-holds/AuthorizationTimeline.tsx
frontend/src/ui/components/deposit-holds/LinkedPaymentAttempts.tsx
```

## UI projection rules

The Deposits & Holds page should include:

- metric cards: active holds, expiring soon, released this week, disputes
- expiring soon panel
- search/filter row
- deposit hold table
- selected deposit hold detail panel
- reservation/stay summary
- authorization timeline
- linked payment attempts
- guest note
- approve/release/request/generate receipt actions

All of these must be projections of `DepositHold` objects.

## Safety rules

- Provider authorization/capture/release must happen server-side only.
- Capture and release require explicit staff action.
- A hold is not a payment transaction until money movement occurs.
- Provider status sync should record provider metadata before mutating hold state.
- Never delete original provider references.

## Acceptance criteria

The implementation passes only when:

- A DepositHold object powers each row.
- Selecting a row passes the selected DepositHold into the detail panel.
- Authorization timeline is DepositHold history.
- Linked payment attempts are PaymentTransaction links.
- Hold actions call DepositHold services.
- Business rules live in domain/services, not React components.
