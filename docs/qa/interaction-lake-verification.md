# Interaction and Reservation Lake Verification

This tracker records evidence for the two data-lake outputs used during the Airbnb-to-MLADIS transition.

| Feature | Coded | Local dev tested | Local user tested | Production dev tested | Production user tested | Current evidence |
|---|---|---|---|---|---|---|
| Anonymous conversation lake | Yes | Yes, automated redaction/signal tests | Yes | Not yet | Not yet | Read-only DOM capture completed for 1,775 normal/archived Airbnb threads; 1,775 anonymized Airbnb interaction records are in the protected local runtime lake. |
| Structured Airbnb reservation lake | Yes | Yes, writer/normalization/idempotence tests | Yes | Not yet | Not yet | Read-only DOM table index and direct-thread capture produced 1,775 unique reservation snapshots; records remain marked `needs_reconciliation` and were not created as live `BookingInquiry` rows. |
| Drive mirror | Existing infrastructure | Environment-dependent | Not yet | Not yet | Not yet | Requires the approved local `rclone` configuration and an intentional `--sync-drive` run. |
| Consent contact protection | Yes | Yes, decline/no-response hashing tests | Not yet | Not yet | Not yet | Unanswered or declined promotional permission clears contact values from the reservation snapshot and retains keyed hashes only. |

## Evidence Rules

- “Coded” means the service, command, contract, and tests exist.
- “Local dev tested” requires automated tests or a repeatable command result.
- “Local user tested” requires a browser-driven collection pass observed end to end.
- “Production dev tested” requires a production-safe read-only/API verification.
- “Production user tested” requires an observed production workflow, with no destructive or financial action implied.
- Never mark a state complete from intention, a screenshot, or a fixture alone.

## Collection Job Boundaries

The safest initial rollout is four short, read-only collection jobs:

1. Normal Airbnb conversations -> anonymized interaction records.
2. Archived Airbnb conversations -> anonymized interaction records.
3. Normal Airbnb reservation panels -> protected reservation snapshots.
4. Archived Airbnb reservation panels -> protected reservation snapshots.

One bounded batch may process all four inputs, but it must preserve the same separation. Conversation text is sanitized before `INTERACTIONS`; structured reservation fields go to private `BOOKINGS` snapshots. No outbound messages, reservation edits, cancellations, payment actions, or automatic live-booking creation are part of these jobs.

## Current Limitations

The repository has the storage contracts and idempotent writers. The observed
Airbnb collection pass captured all 1,307 normal and 468 archived thread keys.
The message surface rendered dates for 66 records, guest counts for 1,629,
and ratings for 1,628; review counts and potential earnings were not rendered
in this message view and remain nullable. Reservation snapshots remain
migration/learning records rather than operational MLADIS reservations until
reviewed reconciliation creates or links real `BookingInquiry` objects.

## Repeatable command

Future collection does not require this chat or a particular agent. Produce one
private combined JSON/JSONL export following the [Airbnb collection runbook](../data-store/airbnb-collection-runbook.md), then run:

```bash
cd airbnb_agent
.venv/bin/python manage.py collect_airbnb_data_lake \
  --input /private/path/airbnb-combined-export.json
```

Add `--sync-drive` only after confirming the approved `rclone` configuration.
The command reports counts and output paths, keeps reservation snapshots
idempotent, sanitizes interactions before writing, and never sends or changes
anything in Airbnb.
