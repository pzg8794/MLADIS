# Reservation UI Projection Rules

This file defines how the Reservations Workspace should render.

## Core rule

```text
The UI does not own the truth.
The Reservation object owns the truth.
The UI renders projections of Reservation state.
```

## What this means

Do not build the page like this:

```text
Status tabs data
Table row data
Guest card data
Message panel data
Deposit panel data
FairAgent data
```

Build it like this:

```text
Reservation objects
  -> Reservation status tabs
  -> Reservation rows
  -> selected Reservation guest card
  -> selected Reservation messages
  -> selected Reservation payments/deposits
  -> selected Reservation documents
  -> selected Reservation activity
  -> selected Reservation FairAgent panel
```

## Page areas

### 1. Header

Title:

```text
Reservations Workspace
```

Subtitle:

```text
Manage, review, and action reservations with AI-powered assistance.
```

Actions:

- Date range
- Filters
- Export

### 2. Status tabs

Tabs should be derived from Reservation objects.

Required tabs:

- All
- Confirmed
- Pending
- Hold
- Cancelled
- Completed

### 3. Search and filters

Filters should query Reservation fields:

- guest name
- email
- confirmation/request key
- listing
- channel
- source country
- risk level
- date range

### 4. Reservation table/list

Each row is a `Reservation` projection.

Columns:

- checkbox
- guest
- stay/listing
- dates
- guests
- deposit
- payment
- channel/source
- risk

Clicking a row selects the Reservation and updates all lower/right panels.

### 5. Guest summary card

The selected Reservation drives:

- guest initials/avatar
- guest name
- status badge
- email/contact
- country
- listing
- check-in/check-out
- nights
- guests
- total amount
- profile/admin links

### 6. Detail tabs

Tabs:

- Messages
- Payments
- Deposits
- Documents
- Activity

Each tab renders a projection of the selected Reservation.

### 7. Deposit/payment panel

The selected Reservation drives:

- deposit amount
- hold status
- expiration
- approve/release buttons
- payment timeline

No payment logic belongs in the React component. The panel calls application services.

### 8. FairAgent panel

FairAgent renders `ReservationAgentAssessment`:

- suggested reply
- risk assessment
- missing information
- recommended actions

FairAgent can suggest and stage actions, but the staff user chooses the actual action.

## UI component responsibilities

### `OpsReservationsPage`

Owns page state:

- snapshot
- filters
- selected reservation ID
- active tab
- loading/error state

It does not own business rules.

### `ReservationTable`

Renders rows and selection behavior.

It does not compute payment/deposit rules.

### `ReservationRow`

Renders one Reservation summary.

### `ReservationDetailPanel`

Renders the selected Reservation.

### `ReservationGuestCard`

Renders guest/stay/date/payment summary from the selected Reservation.

### `ReservationMessagePanel`

Renders the selected Reservation message thread.

### `ReservationDepositPanel`

Renders the selected Reservation deposit and payment plan.

### `FairAgentPanel`

Renders the selected Reservation agent assessment.

## Visual design direction

The page should feel like a modern SaaS reservations cockpit:

- clean workspace
- dark navy / teal MLADIS identity
- dense but readable table
- status badges with clear labels
- selected row detail inspector
- assistant panel that feels helpful, not noisy
- strong hierarchy for payment/deposit actions
- minimal clutter

The design can be fresh and modern, but it must still be object-driven.
