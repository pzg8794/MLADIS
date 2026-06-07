# Drive Data Lake Contract

## Storage Model

MLADIS uses an OOP application model and a lake-style export model:

- Django models and services control live transactional behavior.
- Data lake collections are immutable export files written as JSONL.
- Live object lifecycle events are append-only JSONL records in `bronze/app_events/object_events` when `MLADIS_DATASTORE_ROOT` is configured.
- Manifests and schemas are JSON.
- Each record has a stable envelope so future tools can search by keys without guessing source tables.
- No operational object should become part of a customer, booking, payment, agent, or admin workflow without either a transactional database record and an export collection, or a live `object_events` log plus a documented reason.

## Root Layout

```text
MLADIS-DATASTORE/
  README.md
  _catalog/
    collections.json
  _manifests/
    export-run-<timestamp>-<id>.json
  schemas/
    v1/
      <collection>.schema.json
  bronze/
    app_events/
      object_events/
    imports/
  silver/
    accounts/
    customers/
    bookings/
    requests/
    agent/
    payments/
    marketing/
    content/
  gold/
    analytics/
  quarantine/
```

## Partition Pattern

Every record collection uses date partitions:

```text
<zone>/<subject>/<collection>/year=YYYY/month=MM/day=DD/<collection>-<export_run_id>.jsonl
```

Example:

```text
silver/agent/agent_conversations/year=2026/month=06/day=06/agent_conversations-20260606T230000-a1b2c3d4.jsonl
```

Live object events use the same partition pattern and append to a daily file:

```text
bronze/app_events/object_events/year=YYYY/month=MM/day=DD/object_events-live-YYYYMMDD.jsonl
```

## Record Envelope

Every JSONL line follows this contract:

```json
{
  "schema_version": "1.0",
  "collection": "agent_conversations",
  "entity_type": "agent_conversation",
  "record_key": "agent_conversation:42",
  "source_system": "mladis-django",
  "source_model": "bookings.AgentConversation",
  "source_pk": "42",
  "pii_classification": "private",
  "occurred_at": "2026-06-06T18:30:00-04:00",
  "extracted_at": "2026-06-06T19:00:00-04:00",
  "natural_keys": {
    "email": "guest@example.com"
  },
  "data": {}
}
```

## Zones

- `bronze`: raw app/import event exports with light normalization.
- `silver`: entity-level operational records keyed around the MLADIS domain model.
- `gold`: curated analytics outputs generated from bronze/silver.
- `quarantine`: malformed or untrusted imports that need review before loading.

## Collection Families

- `accounts`: subscriptions and login identities.
- `customers`: customer profiles, imported Airbnb guests, and feedback.
- `requests`: booking inquiries and information requests.
- `bookings`: reservation lifecycle, availability blocks, and price overrides.
- `agent`: chatbot logs, FAQ records, and agent training signals.
- `payments`: damage deposits, reservation payment holds, donations, invoices, and payment-state records.
- `marketing`: promotions, coupon linkage, and campaign delivery.
- `content`: stays, services, inventory, and public listing metadata.

## Required Live Event Logging

The following workflows must emit a live `object_events` record when the root is configured:

- reservation request created,
- damage deposit checkout created,
- damage deposit provider configuration failure,
- damage deposit provider failure,
- reservation payment hold checkout created,
- reservation payment hold provider configuration failure,
- reservation payment hold provider failure,
- security deposit and reservation payment confirmation emails sent,
- agent conversation created or updated,
- customer/account creation or profile linking,
- invoice creation/sending,
- promotion creation/sending,
- cancellation, capture, release, or refund actions.

Each event must include:

- `event_name`,
- `object_model`,
- `object_pk`,
- request path when available,
- authenticated user id when available,
- session key when available,
- a small data payload with stable keys such as `request_key`, status, provider, item id, customer profile id, or invoice number.

If a feature cannot emit a live event yet, it must have a matching export collection and a test or TODO in the feature docs explaining how the object is recoverable in the lake.

## Privacy Classes

- `public`: safe for public pages or marketing.
- `internal`: business operational data without direct customer contact details.
- `private`: direct customer data or sensitive operational notes.
- `redacted`: hashed or removed direct identifiers for analytics and model-training experiments.

## Production Guidance

Use the database for live booking behavior. Use the lake for:

- recovery snapshots,
- longitudinal analytics,
- agent training review,
- customer segmentation,
- marketing-consent audits,
- financial and reservation reporting,
- future pipelines into BigQuery, DuckDB, vector stores, or warehouse tools.

Do not build customer-facing workflows that read directly from JSONL while the Django database already has the transactional record. JSONL exports should be read by batch/reporting/agent-learning jobs.
