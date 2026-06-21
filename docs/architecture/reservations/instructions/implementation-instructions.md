# Reservation Implementation Instructions

These instructions are for Codex, Cursor, or any AI/developer implementing the Reservations Workspace.

## Non-negotiable process

1. Read this directory first.
2. Do not start from loose React state or decorated mock rows.
3. Do not create disconnected reservation cards.
4. Build or wrap the Reservation object model first.
5. Map backend payloads into frontend domain objects.
6. Render UI projections from those objects.
7. Preserve existing MLADIS routes and staff permissions unless a migration plan says otherwise.

## Implementation order

### Phase 1 - Backend vocabulary alignment

Choose one:

- Option A: keep `BookingInquiry` internally and expose `Reservation` through services/API/frontend.
- Option B: rename `BookingInquiry` to `Reservation` through a careful migration.

Preferred short-term direction: Option A.

Preferred long-term direction: Option B after payment/deposit/reservation flows are stable.

### Phase 2 - Backend services

Create or refactor:

```text
airbnb_agent/bookings/services/reservations.py
```

Include:

- `ReservationService`
- `ReservationAgentService`
- `ReservationPaymentService`
- `ReservationDepositService`
- `ReservationTimelineService`
- `ReservationDataLakeService`

### Phase 3 - API layer

Create stable API endpoints under `/api/ops/reservations/`.

The API should return normalized Reservation payloads. Do not leak raw Django model internals directly into the frontend.

### Phase 4 - Frontend domain layer

Create:

```text
frontend/src/domain/reservations.ts
```

This file owns the frontend `Reservation` class and value objects.

### Phase 5 - Repository layer

Create:

```text
frontend/src/infrastructure/ReservationRepository.ts
```

Repository responsibilities:

- fetch Reservation snapshot
- map API payloads into objects
- update status
- stage/send messages
- approve/release deposits
- generate invoices
- fetch FairAgent assessment

### Phase 6 - Application service layer

Create:

```text
frontend/src/application/ReservationService.ts
```

Application service responsibilities:

- load workspace
- select reservation
- filter reservations
- compute metrics
- call repository for mutations
- orchestrate assistant-guided actions safely

### Phase 7 - UI layer

Create or refactor:

```text
frontend/src/ui/pages/OpsReservationsPage.tsx
frontend/src/ui/components/reservations/
```

Components must render domain object state only.

## Required UI pieces

The final page should include:

1. Page header
2. Status filter tabs
3. Search and filter row
4. Reservation table/list
5. Selected guest/booking summary card
6. Detail tabs: messages, payments, deposits, documents, activity
7. Message composer/action panel
8. Deposit/payment panel
9. FairAgent assistant panel
10. Pagination and export controls

## Safety rules

- Preserve existing admin pages.
- Preserve existing `BookingInquiry` data.
- Preserve payment/deposit fields.
- No deployment from this task.
- Payment actions require server-side confirmation and staff action.
- Guest messages require explicit staff confirmation.
- FairAgent can suggest actions, but services execute only when staff chooses an action.

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

- A Reservation object powers each row/card.
- Selecting a row passes the selected Reservation object into the detail panel.
- Metrics and tabs are derived from Reservation objects or a backend snapshot generated from Reservation querysets.
- Guest card uses Reservation.guest, Reservation.stay, Reservation.dates, and Reservation.paymentPlan.
- Deposit panel uses Reservation.depositHold and Reservation.paymentPlan.
- Message panel uses Reservation.messages.
- Documents tab uses Reservation.documents.
- Activity tab uses Reservation.timeline.
- FairAgent panel uses Reservation.agent.
- Business rules live in domain/services, not React components.
