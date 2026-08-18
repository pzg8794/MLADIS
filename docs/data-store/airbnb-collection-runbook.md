# Airbnb Collection Runbook

This is the repeatable process for importing the two Airbnb transition datasets
without relying on a particular Codex conversation or browser session.

The collector accepts one private export file and writes two separate outputs:

- `BOOKINGS/airbnb_reservation_snapshots.jsonl`: protected, structured
  reservation snapshots for reconciliation and repeat-stay analysis.
- `INTERACTIONS/anonymous_interactions.jsonl`: identity-free conversation
  records for response-quality learning.

The source is the rendered Airbnb DOM, not a screenshot. The message table is
the durable index: each row carries a unique thread key and may also expose
the stay dates, guest count, listing, status, rating, review, or earnings
fields that Airbnb chose to render. When richer reservation fields are only
available after opening a thread or reservation panel, capture that DOM as a
resumable detail batch. Never infer missing fields and never put raw message
bodies in the reservation collection.

The Django database remains the operational source of truth. These files are a
private migration/learning lake; they do not create live reservations or send
messages.

## One-command entry point

From the MLADIS repository:

```bash
cd airbnb_agent
.venv/bin/python manage.py collect_airbnb_data_lake \
  --input /private/path/airbnb-combined-export.json
```

The command is safe to rerun for reservation snapshots: the reservation writer
uses a deterministic key and updates an existing snapshot instead of adding a
duplicate. Interaction records are append-only because a repeated conversation
capture is treated as a new learning observation; retain the export scope and
capture date so a later deduplication/quality pass can distinguish repeats.

For an intentional protected Drive mirror, verify the configured `rclone`
remote and folder first, then run:

```bash
cd airbnb_agent
.venv/bin/python manage.py collect_airbnb_data_lake \
  --input /private/path/airbnb-combined-export.json \
  --sync-drive
```

The command prints counts and output paths only. It must never print message
contents, names, email addresses, phone numbers, reservation references, or
source URLs.

## Browser DOM capture and resume

The reusable browser helper is:

```text
airbnb_agent/scripts/capture_airbnb_messages.mjs
```

It exposes two read-only operations for the already-authorized host browser:

```js
captureAirbnbTableIndex({ normalTab, archivedTab, outputPath })
captureAirbnbThreadBatch({ tab, scope, listUrl, threadRows, outputPath })
```

First capture the normal and archived table index. Then pass small batches of
the indexed rows to `captureAirbnbThreadBatch`; it skips `(scope, thread_id)`
pairs already present in the private JSONL checkpoint. A browser restart or a
later agent can therefore resume without repeating completed threads. The
helper prefers each row's observed `href` and navigates directly to that
thread, so Airbnb's virtualized table window cannot hide older records. If a
row has no href it falls back to clicking a visible row. It reads rendered DOM
content, returns to the supplied list URL after a batch, and never sends a
message or changes a reservation.

The private thread checkpoint may contain `detail_text` so a later parser can
look for structured reservation labels rendered in the detail view. That raw
checkpoint must stay outside Git and access-controlled; only normalized
reservation fields and sanitized conversation turns are written to the lake.

The combined collector accepts both forms directly:

```bash
cd airbnb_agent
.venv/bin/python manage.py collect_airbnb_data_lake \
  --input /private/path/mladis-airbnb-thread-index.json

.venv/bin/python manage.py collect_airbnb_data_lake \
  --input /private/path/mladis-airbnb-thread-captures.jsonl
```

The first command creates one private reservation snapshot per unique table
thread. The second enriches the reservation snapshot and writes sanitized
conversation turns to `INTERACTIONS`. Use the same output root for both runs;
reservation snapshots upsert by deterministic key. Keep the raw checkpoint
outside Git and with restrictive file permissions.

The detail parser only records fields it can match in the rendered DOM. Dates,
guest counts, nights, ratings, review counts/text, and potential earnings are
therefore nullable per record. A missing value means Airbnb did not expose that
field in the captured table/detail surface; it is not permission to infer a
value from conversation prose or another reservation.

## Combined export format

Use one JSON object with `reservations` and `interactions` arrays. A JSONL file
is also supported when each row is explicitly classifiable with
`dataset: "reservations"` or `dataset: "interactions"`.

```json
{
  "scope": "normal",
  "captured_at": "2026-08-18T12:00:00-04:00",
  "reservations": [
    {
      "source": {
        "scope": "normal",
        "thread_id": "private-thread-id",
        "thread_url": "https://www.airbnb.com/hosting/messages/private-thread-id",
        "confirmation_code": "private-confirmation-code"
      },
      "guest": {
        "name": "Private Guest",
        "email": "guest@example.com",
        "phone": "+1 809 555 0100"
      },
      "property": {
        "listing_id": "private-listing-id",
        "listing_title": "Stay title",
        "address": "Private address"
      },
      "lifecycle": {
        "booking_date": "2026-08-01",
        "check_in": "2026-09-01",
        "check_out": "2026-09-03",
        "status": "confirmed"
      },
      "occupancy": {"guests": 2, "nights": 2},
      "financials": {"total_amount": "200.00", "currency": "usd"},
      "marketing_consent": {
        "status": "requested",
        "response_received": false
      }
    }
  ],
  "interactions": [
    {
      "source_system": "airbnb",
      "channel": "host_messages",
      "language": "en",
      "topic": "arrival",
      "known_names": ["Private Guest"],
      "turns": [
        {"role": "guest", "text": "Private conversation text."},
        {"role": "host", "text": "Private host response."}
      ]
    }
  ]
}
```

The example is a shape only. The actual export stays outside Git and outside
the repository. Do not place the example's private-looking values in a
committed fixture or production data file.

## Collection scopes

The initial collection can be performed as four low-stake, read-only scopes:

1. normal Airbnb conversations -> `INTERACTIONS`;
2. archived Airbnb conversations -> `INTERACTIONS`;
3. normal reservation panels -> `BOOKINGS`;
4. archived reservation panels -> `BOOKINGS`.

They may be captured into separate private files and merged into one combined
export before the command runs, or collected in one bounded browser pass. Each
record must carry its scope (`normal` or `archived`) in the private reservation
source fields. Conversation scope can be represented in its channel/topic.

The collector is read-only with respect to Airbnb. It must not send a message,
edit a reservation, cancel a stay, charge a guest, capture/release a deposit,
or create a live `BookingInquiry`.

## Contact and consent policy

Phone numbers and email addresses are operational contact fields and may remain
in the protected `BOOKINGS` snapshot while MLADIS requests permission for
future promotional communication. Their presence never means promotional
consent.

When a guest declines, explicitly denies, or does not answer a tracked
permission request, the reservation writer clears the contact values and
retains only keyed hashes with status `opted_out` or `no_response`. No
marketing message is sent automatically by this collector.

Conversation text always goes through the identity-redaction sanitizer before
it reaches `INTERACTIONS`. Reservation snapshots never contain raw message
bodies.

## Review and retry checklist

Before running:

1. Confirm the export came from the authorized host workspace.
2. Confirm the input is stored in a private, access-controlled location.
3. Confirm the export contains structured fields, not passwords, payment-card
   data, identity documents, or raw message bodies in reservation records.
4. Confirm the target local datastore and optional Drive remote are correct.

After running:

1. Check the command counts and both output collection paths.
2. Confirm reservation snapshots have `needs_reconciliation: true`.
3. Confirm interaction output contains no names, contact values, source IDs, or
   thread URLs.
4. Record the run in `docs/qa/interaction-lake-verification.md`.
5. Delete the raw export according to the approved retention policy after the
   output has been reviewed and mirrored if required.

If a run is interrupted, rerun the same file. Reservation records are
idempotent. Review interaction counts before mirroring if the same file may
have been partially processed.

## Related contracts

- [Airbnb reservation snapshot contract](airbnb-reservation-snapshot-contract.md)
- [Anonymous interaction lake contract](anonymous-interaction-lake-contract.md)
- [Interaction and reservation verification tracker](../qa/interaction-lake-verification.md)
