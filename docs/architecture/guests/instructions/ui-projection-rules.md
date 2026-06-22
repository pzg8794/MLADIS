# Guest UI Projection Rules

This file defines how the Guests workspace should render.

## Core rule

```text
The UI does not own the truth.
The Guest object owns the truth.
The UI renders projections of Guest state.
```

## What this means

Do not build the page like this:

```text
Status tabs data
Table row data
Profile card data
Message panel data
Last-stays panel data
Payment/deposit data
```

Build it like this:

```text
Guest objects
  -> Guest metrics
  -> Guest status/segment tabs
  -> Guest rows
  -> selected Guest profile card
  -> selected Guest messages
  -> selected Guest documents
  -> selected Guest payments
  -> selected Guest deposits
  -> selected Guest activity
  -> selected Guest stay history
```

## Page areas

### 1. Header

Title:

```text
Guests
```

Subtitle:

```text
Manage guest relationships, profiles, travel details, and communication history.
```

Actions:

- Filters
- Export
- Add Guest

### 2. Segment/status tabs

Tabs should be derived from Guest objects.

Suggested tabs:

- All
- Repeat Guests
- VIP
- New
- Blocked

### 3. Search and filters

Filters should query Guest fields:

- name
- email
- phone
- reservation key
- source/channel
- country
- tags
- segment
- status

### 4. Guest table/list

Each row is a `Guest` projection.

Columns:

- checkbox
- guest
- country
- channel
- past stays
- total spend
- status/segment
- last contact

Clicking a row selects the Guest and updates all lower/right panels.

### 5. Guest profile card

The selected Guest drives:

- initials/avatar
- name
- VIP/repeat/new/blocked badge
- email
- phone
- country
- full profile link
- preferred language
- birthday
- travel style
- guest since
- tags
- notes

### 6. Detail tabs

Tabs:

- Messages
- Documents
- Payments
- Deposits
- Activity

Each tab renders a projection of the selected Guest.

### 7. Message panel

The selected Guest drives:

- message thread
- inbound/outbound message styling
- read state
- composer
- send action

No messaging logic belongs in the React component. The panel calls application services.

### 8. Last stays panel

The selected Guest drives:

- upcoming stay
- linked reservations
- past stays
- total spend
- stay statuses

Reservation remains its own aggregate. This panel is a Guest projection of Reservation summaries.

## UI component responsibilities

### `OpsGuestsPage`

Owns page state:

- snapshot
- filters
- selected guest ID
- active tab
- loading/error state

It does not own business rules.

### `GuestTable`

Renders rows and selection behavior.

It does not compute segment, total spend, or messaging rules.

### `GuestRow`

Renders one Guest summary.

### `GuestProfileCard`

Renders identity, contact, tags, preferences, and notes from the selected Guest.

### `GuestMessagePanel`

Renders the selected Guest message thread and sends through services.

### `GuestStayPanel`

Renders selected Guest stay history from Reservation summary projections.

### `GuestActivityPanel`

Renders selected Guest timeline events.

## Visual design direction

The page should feel like a modern SaaS guest relationship cockpit:

- clean workspace
- dark navy / teal MLADIS identity
- dense but readable table
- clear segment/status badges
- selected-row detail panels
- message thread that feels calm and professional
- strong hierarchy for guest identity and stay history
- minimal clutter

The design can be fresh and modern, but it must still be object-driven.
