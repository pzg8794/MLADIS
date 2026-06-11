# Drive Object Lake Contract

## Storage Model

MLADIS uses a simple Drive-backed object lake, not a deeply partitioned warehouse layout.

- The Django database remains the transactional source of truth.
- The object lake stores readable JSON objects for recovery, audit, analysis, and agent learning.
- Business object state is stored in human-readable top-level folders.
- Do not use `year/month/day` partitions for live business object state.
- Do not store runtime JSON files in Git.

## Root Layout

```text
MLADIS-DATASTORE/
  README.md
  CATALOG.json
  BOOKINGS/
    bookinginquiry-15.json
    booking_requests.jsonl
    reservations.jsonl
    _history.jsonl
    _events.jsonl
  CUSTOMERS/
    user-9.json
    customerprofile-47.json
    airbnbguestrecord-41.json
    customer_profiles.jsonl
    airbnb_guest_records.jsonl
    customer_feedback.jsonl
    subscriptions.jsonl
    _history.jsonl
  BOOKINGAGENTS/
    agentconversation-1.json
    agentfaq-8.json
    agent_conversations.jsonl
    agent_faq.jsonl
    _history.jsonl
  TRANSACTIONS/
    damagedeposit-13.json
    reservationpaymenthold-4.json
    damage_deposits.jsonl
    reservation_payment_holds.jsonl
    donations.jsonl
    invoices.jsonl
    promotions.jsonl
    _history.jsonl
    _events.jsonl
  STAYS/
    bookableitem-1.json
    availabilityblock-2.json
    dailypriceoverride-1.json
    inventory.jsonl
    availability_blocks.jsonl
    daily_price_overrides.jsonl
    _history.jsonl
  MAINTENANCE/
    maintenanceevent-<id>.json
    maintenancephoto-<id>.json
    maintenance_events.jsonl
    _history.jsonl
  WEBSITE/
    sitesettings-1.json
    sitecontentblock-<id>.json
    _history.jsonl
  ADMIN/
    adminaccess-<id>.json
    _history.jsonl
  EVENTS/
    page_visits.jsonl
    object_events.jsonl
    object_states.jsonl
  EXPORTS/
    export-run-<timestamp>-<id>.json
```

## Folder Meaning

- `BOOKINGS`: booked/reservation objects and booking request lifecycle.
- `CUSTOMERS`: clients, user accounts, imported guests, feedback, and consent state.
- `BOOKINGAGENTS`: chat agent conversations, FAQ, and training knowledge.
- `TRANSACTIONS`: payments, deposits, holds, invoices, donations, coupons, and promotions.
- `STAYS`: apartments/stays, availability, pricing, rules, galleries, and calendar feeds.
- `MAINTENANCE`: cleaning, repair, maintenance, cost, time, and photo evidence objects.
- `WEBSITE`: site settings, logo/content, and public copy records.
- `ADMIN`: admin access and internal business configuration.
- `EVENTS`: high-volume app events that are not one durable business object.
- `EXPORTS`: export manifests only.

## Object Files

Each saved business object writes one current JSON file:

```text
<FOLDER>/<model>-<id>.json
```

Example:

```text
CUSTOMERS/customerprofile-47.json
BOOKINGS/bookinginquiry-15.json
TRANSACTIONS/damagedeposit-13.json
BOOKINGAGENTS/agentconversation-1.json
```

Each folder can also have `_history.jsonl` for append-only state changes. This gives agents and humans a current object file plus a simple change log without digging through partitions.

## Snapshot Files

Current collection snapshots are plain JSONL files inside the matching folder:

```text
CUSTOMERS/customer_profiles.jsonl
BOOKINGS/booking_requests.jsonl
TRANSACTIONS/damage_deposits.jsonl
STAYS/inventory.jsonl
```

## Live Write Rule

When `MLADIS_DATASTORE_ROOT` is configured:

1. Save/delete a relevant model.
2. Write/update its current JSON file in the correct top-level folder.
3. Append the same state envelope to that folder's `_history.jsonl`.
4. If `MLADIS_DATASTORE_LIVE_SYNC_DRIVE=True`, mirror those touched files to the configured Drive folder.

Drive mirroring should run asynchronously for request paths through `MLADIS_DATASTORE_LIVE_SYNC_ASYNC=True`, so Drive latency cannot freeze booking or admin work.

## Required Objects

Every functional object must have a data-store path:

- subscriptions and login identities,
- customers and imported Airbnb guests,
- booking requests and reservation lifecycle records,
- request/inquiry records,
- chatbot conversations, FAQ, and training records,
- payments, deposit holds, donations, invoices, promotions, coupons, and cancellation records,
- maintenance events and photo evidence,
- calendar availability, pricing, feed, stay, and inventory records,
- site settings, admin-managed content, and business configuration records.

## Privacy

Never write these to the object lake:

- SSNs,
- EIN letters,
- bank login records,
- raw signatures,
- identity documents,
- passwords,
- OAuth secrets,
- payment card numbers.

Sensitive auth/provider fields must be redacted before writing JSON.

## Drive Target

Runtime JSON belongs in the protected Drive folder:

```text
https://drive.google.com/drive/folders/1ta4MMXH8gjO3-uIiYG9pEvgafEueVfmn
```

Git stores only code, tests, schemas/contracts, and documentation.
