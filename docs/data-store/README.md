# MLADIS Object Lake

Simple Drive-backed JSON object store for MLADIS operational data.

Target Drive folder:
[MLADIS Drive Object Lake](https://drive.google.com/drive/folders/1ta4MMXH8gjO3-uIiYG9pEvgafEueVfmn)

## Purpose

The Django database remains the transactional source of truth. The Drive-backed object lake stores readable JSON/JSONL records for:

- accounts and customer profiles,
- bookings and reservations,
- request/inquiry records,
- agent conversations and FAQ training data,
- transactions, deposits, invoices, coupons, and promotions,
- stays, availability, pricing, and content,
- maintenance and cleaning evidence,
- app events for analytics and audits.

## Folder Contract

Runtime data is organized by business object type:

```text
BOOKINGS/
CUSTOMERS/
BOOKINGAGENTS/
TRANSACTIONS/
STAYS/
MAINTENANCE/
WEBSITE/
ADMIN/
EVENTS/
EXPORTS/
CATALOG.json
README.md
```

Do not add `year/month/day` partitions for live object state. The point of this object lake is that humans and agents can open the folder and understand the business data immediately.

## Live Object Writes

When `MLADIS_DATASTORE_ROOT` is configured, relevant model saves/deletes write:

```text
<FOLDER>/<model>-<id>.json
<FOLDER>/_history.jsonl
```

Example:

```text
BOOKINGS/bookinginquiry-15.json
CUSTOMERS/customerprofile-47.json
BOOKINGAGENTS/agentconversation-1.json
TRANSACTIONS/damagedeposit-13.json
```

## Snapshot Exports

Run this locally to refresh current JSONL snapshots in the same simple folders:

```bash
cd airbnb_agent
python manage.py export_data_lake
```

Run this only when you intentionally want to mirror the current local object lake to Drive:

```bash
cd airbnb_agent
python manage.py export_data_lake --sync-drive
```

## Env Vars

- `MLADIS_DATASTORE_ROOT`
- `MLADIS_DATASTORE_DRIVE_FOLDER_ID`
- `MLADIS_DATASTORE_DRIVE_REMOTE`
- `MLADIS_DATASTORE_DRIVE_COPY_TIMEOUT_SECONDS`
- `MLADIS_DATASTORE_LIVE_SYNC_DRIVE`
- `MLADIS_DATASTORE_LIVE_SYNC_ASYNC`

## Rules

- Keep customer/runtime JSON out of Git.
- Git stores code, tests, and contracts only.
- Drive stores private runtime JSON/JSONL.
- Use one current JSON file per object.
- Use `_history.jsonl` only for append-only change history.
- Do not store SSNs, EIN letters, raw signatures, bank records, passwords, OAuth secrets, identity documents, or payment cards.

## Documents

- [Drive object lake contract](drive-data-lake-contract.md)
- [Collection registry](collections.json)
