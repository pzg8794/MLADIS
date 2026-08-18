# Airbnb Reservation Snapshot Contract

## Purpose

`BOOKINGS/airbnb_reservation_snapshots.jsonl` is the private reservation side of the MLADIS learning and migration lake. It stores structured reservation-panel information captured from the authorized Airbnb host workspace so MLADIS can reconcile stays, identify repeat reservations, and prepare a reviewed migration into its own reservation objects.

This is intentionally separate from `INTERACTIONS/anonymous_interactions.jsonl`:

- `INTERACTIONS` removes identity and source references for conversation-quality learning.
- `BOOKINGS/airbnb_reservation_snapshots` retains protected reservation identifiers and structured stay data needed for reconciliation.

## Record Policy

Each record has a deterministic `mladis_reservation_key` derived from the Airbnb confirmation code, thread, guest/stay identity, and listing/date fields. Re-running a collector updates the existing record rather than creating a duplicate.

The snapshot may contain:

- guest identity and contact fields,
- listing/property identifiers and address data,
- check-in/check-out dates, nights, guest counts, status, and cancellation policy,
- rating and review fields when displayed by the source reservation object,
- total, potential earnings, payout, fee, deposit, currency, and payment-status
  fields when displayed,
- source thread/confirmation references and capture scope,
- a reconciliation confidence and review marker.

The reservation object is composed from the strongest source available. The
Airbnb message table supplies a durable thread key and any stay/listing/status
fields rendered in that row. A reservation detail panel should be captured
when it exposes richer fields such as guest count, rating, review, earnings,
or cancellation/payment facts. Missing fields remain empty and are marked for
reconciliation; the collector never fabricates a value from a neighboring
row, a message, or a visual guess.

The snapshot must not contain:

- raw conversation bodies,
- payment card data, passwords, OAuth secrets, or identity documents,
- guessed values presented as confirmed reservation facts.

Snapshots captured from a conversation reservation panel are marked `needs_reconciliation: true`. They are not automatically inserted as `BookingInquiry` records, because a chat-derived record can be incomplete or duplicated. A later reviewed import may link it to a real MLADIS reservation.

Phone numbers and email addresses may be retained in this protected private
collection because they are operational contact fields. They may be used to
request permission for future promotional communication, but marketing
consent must be explicitly recorded. The presence of a phone number, email
address, prior Airbnb conversation, or prior stay is never treated as
promotional opt-in. If the guest declines or an explicitly tracked permission
request receives no response, the snapshot clears the contact values and
retains only stable keyed hashes plus the consent outcome (`opted_out` or
`no_response`).

## Approved Import

The preferred one-command collector accepts a combined private JSON/JSONL
export and routes reservation records to this collection while routing
conversation turns to `INTERACTIONS`:

```bash
cd airbnb_agent
python manage.py collect_airbnb_data_lake --input /private/path/airbnb-combined-export.json
```

For a reservation-only export, the focused command remains available:

```bash
cd airbnb_agent
python manage.py ingest_airbnb_reservations --input /private/path/reservations.jsonl
```

For an intentional protected Drive mirror, add `--sync-drive` after verifying the configured `rclone` remote and folder. The command never sends Airbnb messages, changes a reservation, charges a guest, or creates a live booking.

The collector can be run as four small jobs (normal conversations, archived conversations, normal reservation panels, archived reservation panels) or as one bounded batch that feeds both the interaction and reservation writers. Every run must record its scope and use the same idempotent reservation writer. See the [Airbnb collection runbook](airbnb-collection-runbook.md) for the single-file input shape and review checklist.

For browser collection, use the reusable read-only helper
`airbnb_agent/scripts/capture_airbnb_messages.mjs` to first write a complete
normal/archived table index, then resume detailed thread batches into JSONL.
The table index is sufficient to create one private reservation snapshot per
unique thread. Detailed thread captures enrich communication counts and the
identity-free interaction lake; they do not replace the structured reservation
record or store raw chat bodies in `BOOKINGS`.

## Privacy and Access

This collection is private operational data. Keep runtime JSON/JSONL in the protected Drive object-lake folder or the local runtime datastore, never in Git. Do not copy these records into the anonymized learning collection. Access and retention must follow the MLADIS business data policy and applicable host/customer obligations.
