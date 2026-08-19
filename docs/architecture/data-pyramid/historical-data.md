# Historical Data Pyramid

This document defines the first practical CLEAN and PREPARE implementation for
Airbnb history. It complements `docs/data-store/pyramid-data-lifecycle.md` and
does not replace the existing COLLECT contracts.

## Boundaries

```text
Airbnb/Object Lake COLLECT evidence
        |
        v
HistoricalDataPreparationService
  CLEAN: normalize, redact, fingerprint, deduplicate, retain conflicts
  PREPARE: relationship projections and reconciliation candidates
        |
        +--> hot working partitions
        +--> protected historical archive partitions
        +--> compact GuestHistoryIndex
```

JSON and JSONL are storage representations only. They are never treated as
the Guest, Reservation, Payment, DepositHold, Invoice, or WorkOrder domain
objects.

## Authority

| Surface | Authority |
| --- | --- |
| MLADIS Django transactional store | Current operational truth and authorized writes |
| Drive/Object Lake | Durable private COLLECT evidence and historical CLEAN/PREPARE archive |
| Private Git working segment | Not used by the initial implementation |
| Public GitHub | Code, tests, schemas, contracts, sanitized documentation only |

The prepared sidecar is read-mostly. It does not create or update authoritative
Django records. Promotion is an explicit, idempotent service boundary that
requires an approved promotion key and a transactional adapter supplied by the
caller.

## CLEAN

`HistoricalCleaner` reads an explicit inventory of existing Object Lake
collections. It does not recursively scan the lake. For every observation it:

- normalizes names, dates, timestamps, currencies, and money values where the
  field meaning is known;
- preserves source collection, source key, source model, source primary key,
  source path/line, capture timestamps, and upstream observation fingerprints;
- redacts provider references, secrets, URLs, private message text, and fields
  covered by the existing privacy boundary;
- deduplicates by stable source identity plus content fingerprint while
  retaining duplicate counts and source locations;
- emits unresolved conflict sets when the same subject has competing facts;
- records uncertainty instead of guessing when a date or amount cannot be
  parsed.

The cleaned output is deterministic and rebuildable from COLLECT. A malformed
input record fails the run rather than silently becoming a partial fact.

## PREPARE

`PreparedRelationshipProjector` builds complete, read-mostly relationship
contexts. It preserves the reconciliation boundaries:

```text
AirbnbGuestRecord
    -> GuestIdentityResolver boundary
    -> Guest / CustomerProfile candidate

AirbnbReservationSnapshot
    -> ReservationReconciliation boundary
    -> Reservation / BookingInquiry candidate
```

Each guest/year context can expose references to:

```text
Guest
  -> Reservation
       -> Property
       -> Payment
       -> DepositHold
       -> Invoice
       -> Message
       -> WorkOrder
```

The context records reconciliation status and unresolved conflict references.
It does not convert source JSON directly into authoritative application
objects, and it does not invent missing relationships.

## Hot and cold storage

Storage selection is owned by `HotPartitionPolicy`, not by Guest or Reservation
business objects. The initial policies are:

- `CurrentOperationalYearPolicy`: the current operational year is hot;
- `RollingTwelveMonthPolicy`: an approximately rolling 12-month window is hot;
- cold partitions: 2021, 2022, 2023, 2024, and 2025 by default.

Changing policy changes placement only. It does not change identity,
relationships, or reconciliation behavior.

## GuestHistoryIndex and rehydration

`GuestHistoryIndexRepository` stores only compact lookup metadata:

- stable MLADIS guest identity;
- latest activity;
- partition years and hot/cold tier;
- reservation/payment/deposit/invoice/message/work-order counts;
- verified archive references and hashes;
- rehydration state.

Normal lookup is active-store-first. On an active miss, `HistoryLookupService`
uses the index to select one exact guest/year partition, verifies the recorded
size and SHA-256, reads only that archive, and returns a temporary prepared
context. Missing, unreadable, or hash-mismatched archives fail closed.

Rehydration is temporary by default. Promotion is separate and idempotent:
only approved reconciled candidates may be promoted, and a promotion key
prevents duplicate active records. No archive is loaded during module import,
application startup, or an ordinary active lookup.

## Commands

The protected runbook is the operational entry point:

```bash
cd airbnb_agent
python manage.py prepare_airbnb_history \
  --collect-root /protected/MLADIS-DATASTORE \
  --output-root /protected/MLADIS-HISTORY \
  --hot-policy current-year \
  --private-working-segment

python manage.py rehydrate_airbnb_history \
  --history-root /protected/MLADIS-HISTORY \
  --guest-id customer_profile:42 \
  --year 2024 \
  --private-working-segment
```

Both commands are explicit, protected operations. They do not send messages,
charge cards, change deposits, accept/cancel reservations, or write
transactional records.

## Privacy and Git policy

Real collected records, raw messages, reservation identifiers, contact data,
provider references, archive files, manifests, and temporary contexts remain
outside public Git. Committed tests use sanitized fixtures only. The initial
implementation does not use a private Git dataset; Drive/Object Lake remains
the durable archive and the Django store remains operational truth.

## Deferred work

- Connect a reviewed Drive adapter without changing the filesystem storage
  contract.
- Connect GuestIdentityResolver and ReservationReconciliation implementations
  when their authoritative service contracts are approved.
- Add an explicit transactional promotion adapter with audit events.
- Add LEARN/USE projections after CLEAN/PREPARE evidence is reviewed.
