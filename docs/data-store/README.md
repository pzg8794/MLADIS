# MLADIS Data Store

Production-ready data lake contract for MLADIS operational data.

Target Drive folder:
[MLADIS Drive Data Store](https://drive.google.com/drive/folders/1ta4MMXH8gjO3-uIiYG9pEvgafEueVfmn)

## Purpose

The Django database remains the transactional source of truth. The Drive-backed data store is the durable JSON/JSONL lake for:

- registered accounts and customer profiles,
- booking requests and reservation lifecycle records,
- request/inquiry messages,
- chatbot conversations and FAQ training signals,
- deposits, donations, invoices, promotions, and feedback,
- calendar availability and pricing records,
- analytics-ready snapshots for future reporting and agent learning.

## Core Rules

- Keep customer data out of Git. Commit only schemas, contracts, docs, and code.
- Use JSONL for record collections because it is append-friendly, searchable by keys, and easy to load into future data tools.
- Use JSON for manifests, schemas, catalogs, and operational metadata.
- Store raw/private exports only in the protected Drive folder or a secure production storage provider.
- Do not place SSNs, EIN letters, bank records, passwords, identity documents, reusable signatures, payment cards, or OAuth secrets in this lake.
- Prefer redacted exports for analytics and agent-training experiments unless private contact fields are needed.

## Operator Commands

Create the local schema/catalog skeleton only:

```bash
cd airbnb_agent
python manage.py export_data_lake --schema-only --include-placeholders
```

Create or refresh the schema/catalog skeleton directly in the configured Drive folder:

```bash
cd airbnb_agent
python manage.py export_data_lake --schema-only --include-placeholders --sync-drive
```

Export all collections with direct private fields and write the current run to Drive:

```bash
cd airbnb_agent
python manage.py export_data_lake --sync-drive
```

Export analytics-safe redacted records and write the current run to Drive:

```bash
cd airbnb_agent
python manage.py export_data_lake --redacted --sync-drive
```

Export one collection and write it to Drive:

```bash
cd airbnb_agent
python manage.py export_data_lake --collection agent_conversations --redacted --sync-drive
```

The Drive writer uses:

- `MLADIS_DATASTORE_DRIVE_FOLDER_ID`
- `MLADIS_DATASTORE_DRIVE_REMOTE`
- `MLADIS_DATASTORE_DRIVE_PACER_MIN_SLEEP`
- `MLADIS_DATASTORE_DRIVE_TPS_LIMIT`

The command writes only the current export run, schemas, catalog, manifest, and root README to Drive. It does not blindly upload older local JSONL runs.

## Documents

- [Drive data lake contract](drive-data-lake-contract.md)
- [Collection registry](collections.json)
