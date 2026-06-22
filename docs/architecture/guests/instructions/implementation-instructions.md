# Guest Implementation Instructions

These instructions are for Codex, Cursor, or any AI/developer implementing the Guests workspace.

## Non-negotiable process

1. Read this directory first.
2. Do not start from loose React state or decorated mock rows.
3. Do not create disconnected guest cards.
4. Build or wrap the Guest object model first.
5. Map backend payloads into frontend domain objects.
6. Render UI projections from those objects.
7. Preserve existing MLADIS routes and staff permissions unless a migration plan says otherwise.

## Implementation order

### Phase 1 - Backend vocabulary alignment

Choose one:

- Option A: keep `CustomerProfile` internally and expose `Guest` through services/API/frontend.
- Option B: rename `CustomerProfile` to `Guest` or `GuestProfile` through a careful migration.

Preferred short-term direction: Option A.

Preferred long-term direction: Option B after reservations, payments, deposits, feedback, imports, and admin flows are stable.

### Phase 2 - Backend services

Create or refactor:

```text
airbnb_agent/bookings/services/guests.py
```

Include:

- `GuestService`
- `GuestAnalyticsService`
- `GuestMessageService`
- `GuestTimelineService`
- `GuestDataLakeService`

### Phase 3 - API layer

Create stable API endpoints under `/api/ops/guests/`.

The API should return normalized Guest payloads. Do not leak raw Django model internals directly into the frontend.

### Phase 4 - Frontend domain layer

Create:

```text
frontend/src/domain/guests.ts
```

This file owns the frontend `Guest` class and value objects.

### Phase 5 - Repository layer

Create:

```text
frontend/src/infrastructure/GuestRepository.ts
```

Repository responsibilities:

- fetch Guest snapshot
- map API payloads into objects
- create/update guests
- send/stage messages
- add/remove tags
- record preferences
- fetch reservations/payments/deposits/activity for selected guest

### Phase 6 - Application service layer

Create:

```text
frontend/src/application/GuestService.ts
```

Application service responsibilities:

- load workspace
- select guest
- filter guests
- compute metrics
- call repository for mutations
- orchestrate relationship-management actions safely

### Phase 7 - UI layer

Create or refactor:

```text
frontend/src/ui/pages/OpsGuestsPage.tsx
frontend/src/ui/components/guests/
```

Components must render domain object state only.

## Required UI pieces

The final page should include:

1. Page header
2. Segment/status filter tabs
3. Search and filter row
4. Guest table/list
5. Selected guest profile card
6. Detail tabs: messages, documents, payments, deposits, activity
7. Message composer/action panel
8. Last stays / linked reservations panel
9. Tags and preferences area
10. Pagination and export controls

## Safety rules

- Preserve existing admin pages.
- Preserve existing `CustomerProfile` data.
- Preserve reservation links.
- Preserve payment/deposit links.
- Preserve Airbnb import records.
- No deployment from this task.
- Guest messages require explicit staff confirmation.
- Marketing consent must not be inferred as opt-in without evidence.
- Blacklist/block state must override computed VIP/repeat status in action availability.
- Merge operations must preserve source evidence and emit audit events.

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

- A Guest object powers each row/card.
- Selecting a row passes the selected Guest object into the profile, tabs, and linked-stays panels.
- Metrics and tabs are derived from Guest objects or a backend snapshot generated from Guest querysets.
- Profile card uses Guest.identity, Guest.contact, Guest.profile, Guest.segment, Guest.tags, and Guest.preferences.
- Message panel uses Guest.messages.
- Documents tab uses Guest.documents.
- Payments tab uses Guest.payments and linked PaymentTransaction projections.
- Deposits tab uses Guest.deposits and linked DepositHold projections.
- Activity tab uses Guest.timeline.
- Last stays panel uses Guest.stays and linked Reservation projections.
- Business rules live in domain/services, not React components.
