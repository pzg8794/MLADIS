# PaymentTransaction Implementation Instructions

These instructions are for Codex, Cursor, or any AI/developer implementing the Payments & Transactions workspace.

## Non-negotiable process

1. Read this directory and `docs/architecture/deposit-holds/` first.
2. Do not start from loose table rows.
3. Build or wrap the PaymentTransaction object first.
4. Link payments to Reservation and, when relevant, DepositHold.
5. Map backend payloads into frontend domain objects.
6. Render UI projections from those objects.

## Required backend services

Recommended file:

```text
airbnb_agent/bookings/services/payments.py
```

Services:

- `PaymentTransactionService`
- `PaymentReconciliationService`
- `InvoiceService`
- `PaymentTimelineService`
- `PaymentDataLakeService`

## Required API routes

```text
GET    /api/ops/payments/
GET    /api/ops/payments/<uuid>/
POST   /api/ops/payments/<uuid>/mark-paid/
POST   /api/ops/payments/<uuid>/refund/
POST   /api/ops/payments/<uuid>/download-invoice/
POST   /api/ops/payments/<uuid>/add-note/
GET    /api/ops/payments/<uuid>/timeline/
```

## Required frontend files

```text
frontend/src/domain/payments.ts
frontend/src/application/PaymentTransactionService.ts
frontend/src/infrastructure/PaymentTransactionRepository.ts
frontend/src/ui/pages/OpsPaymentsPage.tsx
frontend/src/ui/components/payments/PaymentTransactionTable.tsx
frontend/src/ui/components/payments/PaymentTransactionRow.tsx
frontend/src/ui/components/payments/PaymentTransactionDetails.tsx
frontend/src/ui/components/payments/InvoicePreview.tsx
frontend/src/ui/components/payments/PaymentTimeline.tsx
```

## UI projection rules

The Payments & Transactions page should include:

- metric cards: total collected, pending payments, refunded, payouts in transit
- filter row: channel, status, date range, method
- transaction table
- selected transaction details panel
- invoice preview
- linked reservation
- deposit history
- quick actions
- payment timeline
- notes

All of these must be projections of `PaymentTransaction` objects.

## Safety rules

- Payment provider mutation must happen server-side only.
- Refunds require explicit staff confirmation.
- Mark-as-paid requires audit metadata.
- Invoice generation creates a snapshot and must not overwrite raw transaction records.
- Provider webhooks/events should be stored as provider events before changing transaction status.

## Acceptance criteria

The implementation passes only when:

- A PaymentTransaction object powers each row.
- Selecting a row passes the selected PaymentTransaction into the detail panel.
- Invoice preview uses the selected PaymentTransaction invoice state.
- Linked reservation comes from PaymentTransaction.reservation.
- Deposit history comes from PaymentTransaction.depositHold or reservation deposit history.
- Business rules live in domain/services, not React components.
