# Reservation API and Service Contract

This document defines the backend controller/service/API boundary for the Reservations Workspace.

## Rule

Controllers and React components do not own business rules.

Business rules live in:

- `Reservation`
- `ReservationService`
- `ReservationAgentService`
- `ReservationPaymentService`
- `ReservationDepositService`
- `ReservationTimelineService`
- `ReservationDataLakeService`

## Recommended API routes

```text
GET    /api/ops/reservations/
POST   /api/ops/reservations/
GET    /api/ops/reservations/<id>/
PATCH  /api/ops/reservations/<id>/
POST   /api/ops/reservations/<id>/status/
POST   /api/ops/reservations/<id>/messages/
POST   /api/ops/reservations/<id>/send-check-in-instructions/
POST   /api/ops/reservations/<id>/request-id-verification/
POST   /api/ops/reservations/<id>/approve-deposit/
POST   /api/ops/reservations/<id>/release-deposit/
POST   /api/ops/reservations/<id>/generate-invoice/
POST   /api/ops/reservations/<id>/documents/accept/
GET    /api/ops/reservations/<id>/agent-assessment/
GET    /api/ops/reservations/<id>/timeline/
```

## Snapshot payload

`GET /api/ops/reservations/` returns the workspace snapshot.

```json
{
  "metrics": [],
  "rows": [],
  "filters": {},
  "generated_at": "2026-06-19T00:00:00Z"
}
```

## Reservation payload

```json
{
  "id": "42",
  "key": "direct-42",
  "request_key": "MLADIS-REQ-20260619-000042",
  "guest": {
    "name": "Piter Garcia",
    "email": "local-reservation-qa@mladis.test",
    "phone": "",
    "country": "Dominican Republic",
    "profile_admin_url": "/admin/bookings/customerprofile/1/change/",
    "thread_url": ""
  },
  "stay": {
    "id": 4,
    "name": "3 Beds Apt, Vacation Home & Pool, G-101",
    "unit_label": "G-101",
    "listing_url": "/stays/g-101/",
    "admin_url": "/admin/bookings/bookableitem/4/change/"
  },
  "dates": {
    "check_in": "2026-11-09",
    "check_out": "2026-11-12",
    "nights": 3,
    "display_range": "2026-11-09 - 2026-11-12"
  },
  "status": {
    "value": "pending",
    "label": "Pending",
    "tone": "warning"
  },
  "risk": {
    "level": "low",
    "label": "Low Risk",
    "signals": ["Verified contact path", "Stay details available"]
  },
  "payment_plan": {
    "total": {"amount_cents": 125000, "currency": "USD", "display": "$1,250"},
    "stay_payment": {"amount_cents": 105000, "currency": "USD", "display": "$1,050"},
    "deposit": {"amount_cents": 20000, "currency": "USD", "display": "$200"},
    "status": "pending",
    "steps": []
  },
  "deposit_hold": {
    "amount": {"amount_cents": 20000, "currency": "USD", "display": "$200"},
    "status": "pending",
    "label": "Pending",
    "expires_at": ""
  },
  "documents": {
    "property_rules_accepted": false,
    "damage_terms_accepted": false,
    "property_rules_version": "2026-06-15",
    "damage_terms_version": "2026-06-15"
  },
  "messages": {
    "suggested_draft": "",
    "items": []
  },
  "timeline": [],
  "agent": {
    "risk_level": "low",
    "suggested_reply": "",
    "missing_information": [],
    "recommended_actions": [],
    "positive_signals": []
  }
}
```

## Required service behavior

### `ReservationService.transition_status`

Must:

- validate allowed status transition
- persist state to the current `BookingInquiry` record
- record timeline event `reservation_status_changed`
- emit data-lake event
- return stable Reservation payload

### `ReservationService.send_message`

Must:

- create/stage message record
- never send irreversible guest communication without explicit staff action
- record timeline event `reservation_message_sent` or `reservation_message_drafted`

### `ReservationDepositService.approve_deposit`

Must:

- verify deposit exists and can be approved/captured
- call the payment provider through server-side code only
- record provider response safely
- record timeline and data-lake event

### `ReservationDepositService.release_deposit`

Must:

- verify hold exists and can be released
- call payment provider through server-side code only
- record timeline and data-lake event

### `ReservationAgentService.assess_risk`

Must:

- use Reservation object state
- identify missing information
- recommend safe next actions
- return suggestions only, not execute actions directly

## Data lake events

Every important action should emit an event:

```text
reservation_created
reservation_updated
reservation_status_changed
reservation_message_drafted
reservation_message_sent
reservation_deposit_requested
reservation_deposit_approved
reservation_deposit_released
reservation_invoice_generated
reservation_document_accepted
reservation_agent_assessment_generated
```

Each event should include:

- reservation_id
- guest/customer id when available
- property/listing id
- actor_id
- old status
- new status
- payment/deposit status when relevant
- timestamp
- request/session metadata when available
