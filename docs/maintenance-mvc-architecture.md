# MLADIS Maintenance MVC Architecture

Date: 2026-06-07

## Purpose

MLADIS needs a maintenance and cleaning workflow where property administrators can record work performed on a stay, attach proof, and let an agent generate structured bills, tax-support packets, and operational summaries.

The required core object attributes are:

- `title`
- `cost`
- `time`
- `pictures`

Those four fields are the minimum front-door contract. For tax and bill support, the system should also capture property, payee/vendor, proof of payment, description, and audit state.

This document is the implementation contract for adding the feature to the current MLADIS web app without breaking the modern frontend, admin, data lake, payments, OAuth, or booking flows.

## Current Branch Review

The branch `feature/maintenance-events-mvc` contains a useful first pass:

- `maintenance/models.py`
- `maintenance/admin.py`
- `maintenance/serializers.py`
- `maintenance/views.py`
- `maintenance/services.py`
- `maintenance/urls.py`
- `frontend/src/components/MaintenanceForm.jsx`
- `frontend/src/components/MaintenanceList.jsx`
- `docs/maintenance_feature.md`

Do not merge that branch directly into the current production branch.

The branch appears to be based on an older MLADIS snapshot and would remove or regress large parts of the current modern app, including frontend pages, admin styling, signin-contract files, deployment files, and modern ops views. The correct path is to transplant the maintenance domain into the current branch carefully.

## Architecture Rule

This feature must follow the MLADIS OOP and MVC contract:

- Model objects own business state, identity, invariants, and domain payloads.
- Controllers coordinate request/response flow and call services.
- Views render state and collect input; they do not invent business rules.
- Every operational object must have a data-store path.

Read these before implementation:

- [`docs/engineering/oop-mvc-contract.md`](engineering/oop-mvc-contract.md)
- [`docs/data-store/drive-data-lake-contract.md`](data-store/drive-data-lake-contract.md)
- [`AGENTS.md`](../AGENTS.md)

## Recommended App Boundary

Prefer integrating the maintenance feature into the existing `bookings` Django app for v1 unless there is a strong migration reason to keep a separate app.

Reasons:

- Current routes, modern ops pages, data lake, tests, and admin customizations already live under `airbnb_agent/bookings`.
- `BookableItem`, `BookingInquiry`, `Invoice`, data lake exporters, admin access, and ops APIs already live there.
- A standalone root-level `maintenance` app needs extra settings, URL wiring, DRF dependency decisions, deployment review, and frontend integration.

Acceptable implementation shapes:

1. Preferred v1: add `MaintenanceEvent` and `MaintenancePhoto` to `bookings.models`, `bookings.admin`, `bookings.views`, `bookings.services`, and `bookings.data_lake`.
2. Acceptable v2: keep a separate `maintenance` Django app only after rebasing it on the current branch and wiring it cleanly through current ops shell, data lake, tests, and settings.

## Domain Model

`MaintenanceEvent` is the aggregate root. `MaintenancePhoto` is a child entity.

### MaintenanceEvent

Required create-ready fields:

- `item`: FK to `BookableItem`
- `title`
- `cost_amount`
- `cost_currency`
- `reported_at` or `started_at`
- at least one photo for non-draft records

Recommended fields:

- `booking`: optional FK to `BookingInquiry`
- `work_type`: cleaning, repair, replacement, inspection, supplies, penalty, other
- `status`: draft, logged, scheduled, in_progress, completed, documented, billed, archived
- `vendor_name`
- `vendor_contact`
- `invoice_number`
- `proof_of_payment_ref`
- `payment_status`: unpaid, pending, paid, reimbursed, disputed
- `tax_category_code`
- `description`
- `ai_description`
- `ai_description_generated_at`
- `ai_description_model`
- `ai_description_metadata`
- `use_ai_description`
- `admin_notes`
- `created_by`
- `approved_by`
- timestamps

### MaintenancePhoto

Fields:

- `event`: FK to `MaintenanceEvent`
- `image`
- `caption`
- `sort_order`
- `is_cover`
- `checksum_sha256`
- `mime_type`
- `file_size_bytes`
- `width_px`
- `height_px`
- `captured_at`
- `uploaded_at`

Pictures must remain separate child rows. Do not attempt to store multiple files on one model field.

## Value Objects

Expose these domain helpers from the model or a small value-object module:

```python
class Money:
    amount: Decimal
    currency: str

class TimeWindow:
    reported_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    duration_minutes: int | None
    timezone: str
```

The model should expose:

```python
event.money
event.time_window
event.effective_description
event.to_agent_payload()
event.to_data_lake_record()
event.is_tax_ready
```

`effective_description` should prefer `ai_description` only when `use_ai_description` is true and an AI description exists. Manual notes and AI notes must both remain on the object so the system preserves audit provenance.

## Validation Contract

Keep cross-field invariants in `MaintenanceEvent.clean()`, but do not rely on `clean()` alone.

Django does not call `full_clean()` automatically when saving a model. The service layer must call `full_clean()` before persisting manually-created maintenance objects.

Minimum invariants:

- title cannot be blank
- cost amount must be non-negative
- currency must be a valid 3-letter code
- time must be present
- completed time cannot be before started time
- non-draft events require at least one photo
- completed/documented/billed events require property, cost, time, photo, and description
- paid/reimbursed events require proof of payment or a documented exception

Use two validation levels:

- create-ready: title, cost, time, pictures
- tax-ready: create-ready plus property, vendor/payee or payee note, proof-of-payment reference, description, and stable timestamps

## MVC Mapping

### Model

Django domain objects:

- `MaintenanceEvent`
- `MaintenancePhoto`
- optional `MaintenanceDocumentSnapshot`

### Controller

Django view/API layer plus services:

- `OpsMaintenanceAPIView`
- `OpsMaintenanceEventDetailAPIView`
- `OpsMaintenancePhotoUploadAPIView`
- `OpsMaintenanceAIDescriptionAPIView`
- `MaintenanceService`
- `MaintenanceVisionAgent`
- `MaintenanceDocumentService`
- `MaintenanceDataLakeService`

The controller must:

- require staff/admin access for v1
- validate object permissions when property managers are introduced
- call services for creates, updates, document generation, and export
- return stable payloads to React

### View

React/modern ops UI:

- `OpsMaintenancePage`
- `MaintenanceEventForm`
- `MaintenanceEventList`
- `MaintenanceEventDrawer`
- `MaintenancePhotoStrip`
- `MaintenanceTaxPacketPanel`

Django admin remains a fallback/power-user console, not the primary mobile workflow.

## API Contract

Recommended routes:

```text
GET  /api/ops/maintenance/
POST /api/ops/maintenance/
GET  /api/ops/maintenance/<uuid:event_id>/
PATCH /api/ops/maintenance/<uuid:event_id>/
POST /api/ops/maintenance/<uuid:event_id>/photos/
GET  /api/ops/maintenance/<uuid:event_id>/agent-payload/
POST /api/ops/maintenance/<uuid:event_id>/ai-description/
POST /api/ops/maintenance/<uuid:event_id>/documents/
POST /api/ops/maintenance/<uuid:event_id>/export/
```

For mobile reliability, allow creating the event metadata first and uploading photos immediately after. The UI can still present this as one workflow.

## V1 Integrated Implementation

The integrated v1 lives inside the existing `bookings` app instead of the older standalone maintenance branch.

Implemented backend objects:

- `bookings.MaintenanceEvent`
- `bookings.MaintenancePhoto`
- `MaintenanceService`
- `MaintenanceVisionAgent`
- `OpsMaintenanceAPIView`
- `OpsMaintenanceAgentPayloadAPIView`
- `OpsMaintenanceAIDescriptionAPIView`

Implemented routes:

- `/ops/maintenance/`
- `/api/ops/maintenance/`
- `/api/ops/maintenance/<uuid>/agent-payload/`
- `/api/ops/maintenance/<uuid>/ai-description/`

Implemented frontend objects:

- `OpsMaintenanceSnapshot`
- `OpsMaintenanceEvent`
- `OpsMaintenancePhoto`
- `OpsMaintenancePage`

Implemented data-lake collection:

- `silver/operations/maintenance_events`

Implemented AI work-description state:

- `ai_description`
- `ai_description_generated_at`
- `ai_description_model`
- `ai_description_metadata`
- `use_ai_description`

The first v1 uses `FileField` photo evidence with checksum, MIME type, file size, captions, cover photo, and upload timestamps. Image width/height extraction and generated invoice/tax document snapshots are future improvements, because they require either image-processing dependencies or a document-generation workflow.

## AI Work Description Contract

The maintenance vision agent is an application/service object, not a React shortcut.

- The UI can show an `AI description` button on an existing maintenance record.
- The controller must require staff/admin access before invoking the agent.
- The service reads existing `MaintenancePhoto` objects and asks the configured OpenAI vision model for concise work notes.
- The model persists the generated text and metadata in `ai_description`, `ai_description_generated_at`, `ai_description_model`, and `ai_description_metadata`.
- The model keeps `description` as the manual note field and uses `use_ai_description` to decide the active description for `effective_description`.
- `to_agent_payload()` must include both manual and AI descriptions plus the active mode.
- Generating an AI description must emit a data-store object event, currently `maintenance_event.ai_description_generated`.
- Missing `OPENAI_API_KEY` must return a clear setup error and must not break the maintenance page.

Config:

```text
OPENAI_API_KEY=
OPENAI_MAINTENANCE_VISION_MODEL=
MAINTENANCE_AI_MAX_PHOTOS=6
```

## Agent Payload

The agent payload must keep the four required pillars easy to parse:

```json
{
  "schema_version": "1.0",
  "record_type": "maintenance_event",
  "event_id": "uuid",
  "title": "Turnover cleaning after checkout",
  "cost": {
    "amount": "55.00",
    "currency": "USD"
  },
  "time": {
    "reported_at": "2026-06-07T14:00:00-04:00",
    "started_at": "2026-06-07T14:15:00-04:00",
    "completed_at": "2026-06-07T16:00:00-04:00",
    "duration_minutes": 105,
    "timezone": "America/Santo_Domingo"
  },
  "pictures": [
    {
      "photo_id": "uuid",
      "url": "/media/maintenance/events/uuid/photo.jpg",
      "caption": "After cleaning",
      "checksum_sha256": "..."
    }
  ],
  "property": {
    "item_id": 1,
    "display_name": "3 Beds Apt, Vacation Home & Pool, G-101",
    "slug": "g-101"
  },
  "booking": {
    "booking_inquiry_id": 42,
    "request_key": "MLADIS-REQ-20260607-000042"
  },
  "vendor": {
    "name": "Cleaning vendor or payee",
    "invoice_number": "optional",
    "proof_of_payment_ref": "optional"
  },
  "tax": {
    "category_code": "cleaning",
    "is_tax_ready": true
  }
}
```

## Data Lake Contract

Add maintenance to the data lake collection families:

- `silver/operations/maintenance_events`
- `silver/operations/maintenance_photos`
- `silver/payments/maintenance_bills` if a bill/invoice record is generated
- live object events under `bronze/app_events/object_events`

Required live events:

- `maintenance_event_created`
- `maintenance_event_updated`
- `maintenance_photo_uploaded`
- `maintenance_event_completed`
- `maintenance_agent_payload_generated`
- `maintenance_document_generated`
- `maintenance_event_exported`

Each live event should include:

- event id
- item id
- booking inquiry id when linked
- status
- work type
- cost amount and currency
- photo count
- actor/user id
- request path/session key when available

Do not commit JSONL exports or private customer/vendor records to Git. Generated files belong in the configured Drive-backed data store.

## Frontend UX

The UI must work on desktop and mobile.

Core mobile flow:

1. Select property.
2. Tap "Add work".
3. Enter title, cost, and time.
4. Add or take pictures.
5. Save as logged/completed.
6. Open agent payload or bill packet when needed.

Use:

- compact mobile-first form controls
- sticky save button on mobile
- image previews
- photo count and required-state warning
- "Save draft" for unreliable mobile connection
- "Complete event" only when core validation passes

The browser `capture` attribute can improve mobile camera capture, but it is not supported equally everywhere. Treat it as progressive enhancement, not the only capture path.

## Current Branch Issues To Fix Before Integration

The existing `feature/maintenance-events-mvc` branch should be improved before any transplant:

- Do not raw-merge it into the current production branch; it regresses large modern-app areas.
- The React multipart shape uses keys like `pictures[0]image`, while the serializer expects nested `pictures`; use `request.FILES.getlist("pictures")` or a documented `photos` key.
- The serializer bypasses the service layer during create; create/update should go through `MaintenanceService`.
- The service creates the parent row before running `full_clean()`.
- The service uses `float(cost_amount)`; use `Decimal`.
- The data lake export is a stub and does not use the current `bookings.data_lake` envelope.
- `property_code` references `property.code`, but `BookableItem` currently has no `code` field.
- Permissions allow authenticated safe reads; v1 should be staff/admin-only unless property-manager permissions are explicitly modeled.
- The frontend components are standalone `.jsx` components outside the current TypeScript/OOP `domain`, `application`, `infrastructure`, `ui` structure.

## Implementation Plan

1. Add domain objects and migrations to the current branch.
2. Add admin fallback with inline photos.
3. Add services that call `full_clean()` and use `transaction.atomic()`.
4. Add ops API controllers under current `bookings.urls`.
5. Add maintenance data lake collections and live object events.
6. Add modern React OOP frontend:
   - domain models in `frontend/src/domain`
   - repository in `frontend/src/infrastructure`
   - service/factory in `frontend/src/application`
   - page/components in `frontend/src/ui`
7. Add "Maintenance" to the unified ops left menu.
8. Add docs and tests.
9. Run local full checks.
10. Deploy only after owner reviews mobile and desktop flows.

## Test Plan

Backend:

- model validation for create-ready and tax-ready rules
- service calls `full_clean()`
- event/photo creation is atomic
- staff-only API permissions
- agent payload includes title, cost, time, pictures
- data lake export includes maintenance collections
- object event logging does not break customer workflow when the data-store write fails

Frontend:

- mobile form fits without horizontal overflow
- image capture/upload works on desktop and mobile
- required fields show clear errors
- save draft and complete event work
- list/search/filter works
- agent payload modal/drawer works

Operational:

- `npm run build:django`
- `python manage.py check`
- `python manage.py test`
- `python manage.py export_data_lake --schema-only --include-placeholders --sync-drive`
- manual mobile smoke on `https://local.mladis.com` and `http://127.0.0.1:8000`

## Source Anchors

- IRS recordkeeping guidance: https://www.irs.gov/businesses/small-businesses-self-employed/what-kind-of-records-should-i-keep
- Django model validation: https://docs.djangoproject.com/en/dev/ref/models/instances/
- Django file uploads: https://docs.djangoproject.com/en/2.1/topics/http/file-uploads/
- Django FileField/ImageField storage notes: https://docs.djangoproject.com/en/dev/ref/models/fields/
- Django REST Framework ViewSets: https://www.django-rest-framework.org/api-guide/viewsets/
- Django REST Framework generic views: https://www.django-rest-framework.org/api-guide/generic-views/
- Django REST Framework permissions: https://www.django-rest-framework.org/api-guide/permissions/
- JSON Lines: https://jsonlines.org/
- JSON Schema object/required fields: https://json-schema.org/understanding-json-schema/reference/object
- MDN capture attribute: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/capture
