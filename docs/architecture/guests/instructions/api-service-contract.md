# Guest API and Service Contract

This document defines the backend controller/service/API boundary for the Guests workspace.

## Rule

Controllers and React components do not own business rules.

Business rules live in:

- `Guest`
- `GuestService`
- `GuestAnalyticsService`
- `GuestMessageService`
- `GuestTimelineService`
- `GuestDataLakeService`

## Recommended API routes

```text
GET    /api/ops/guests/
POST   /api/ops/guests/
GET    /api/ops/guests/<id>/
PATCH  /api/ops/guests/<id>/
POST   /api/ops/guests/<id>/merge/
POST   /api/ops/guests/<id>/tags/
DELETE /api/ops/guests/<id>/tags/<slug>/
POST   /api/ops/guests/<id>/preferences/
POST   /api/ops/guests/<id>/messages/
POST   /api/ops/guests/<id>/marketing-consent/request/
POST   /api/ops/guests/<id>/marketing-consent/update/
GET    /api/ops/guests/<id>/reservations/
GET    /api/ops/guests/<id>/payments/
GET    /api/ops/guests/<id>/deposits/
GET    /api/ops/guests/<id>/timeline/
```

## Snapshot payload

`GET /api/ops/guests/` returns the workspace snapshot.

```json
{
  "metrics": [],
  "rows": [],
  "filters": {},
  "generated_at": "2026-06-21T00:00:00Z"
}
```

## Guest payload

```json
{
  "id": "1",
  "key": "guest-1",
  "identity": {
    "name": "Maria Rodriguez",
    "initials": "MR",
    "country": "Dominican Republic",
    "preferred_language": "en",
    "source": "direct_website"
  },
  "contact": {
    "email": "maria.rodriguez@email.com",
    "phone": "+1 (809) 555-0198",
    "last_contact_at": "2026-06-05T09:45:00Z",
    "profile_admin_url": "/admin/bookings/customerprofile/1/change/",
    "full_profile_url": "/ops/guests/1/"
  },
  "profile": {
    "birthday": "1987-05-18",
    "travel_style": "Leisure",
    "guest_since": "2024-01-12",
    "notes": "Loves the top-floor units. Prefers late check-out when available. Traveling with kids."
  },
  "status": {
    "value": "active",
    "label": "Active",
    "tone": "success"
  },
  "segment": {
    "value": "vip",
    "label": "VIP",
    "tone": "warning"
  },
  "marketing": {
    "consent_status": "opted_in",
    "consent_label": "Opted in",
    "requested_at": "",
    "consent_at": "2026-06-01T12:00:00Z",
    "can_receive_promotions": true
  },
  "tags": [
    {"label": "Family", "slug": "family", "tone": "neutral"},
    {"label": "Pool Lover", "slug": "pool-lover", "tone": "info"},
    {"label": "Repeat", "slug": "repeat", "tone": "success"}
  ],
  "preferences": [],
  "messages": {"draft": "", "items": []},
  "stays": [],
  "payments": {
    "total_spend": {"amount_cents": 432000, "currency": "USD", "display": "$4,320"},
    "payment_count": 5,
    "last_payment_at": "2026-06-05T00:00:00Z"
  },
  "deposits": {
    "active_holds": 1,
    "released_holds": 4,
    "dispute_count": 0
  },
  "documents": [],
  "timeline": []
}
```

## Required service behavior

### `GuestService.create_guest`

Must:

- normalize email and phone where possible
- require at least one durable contact path unless explicitly creating an anonymous/manual guest
- prevent duplicate guest creation when a normalized email already exists
- create timeline event `guest_created`
- emit data-lake event

### `GuestService.sync_from_reservation`

Must:

- find or create guest by normalized email/contact
- link reservation to guest
- update missing guest contact fields without overwriting verified data
- create timeline event `guest_synced_from_reservation`

### `GuestService.merge_guests`

Must:

- move reservations, feedback, Airbnb records, messages, preferences, and tags to the primary guest
- preserve duplicate profile history
- emit `guest_merged` event
- never delete source evidence silently

### `GuestMessageService.send_message`

Must:

- stage or send message through approved channels
- require staff confirmation for outbound guest communication
- record timeline event `guest_message_sent` or `guest_message_drafted`

### `GuestAnalyticsService.compute_segment`

Must:

- derive repeat/VIP signals from stays, spend, feedback, and explicit admin tags
- preserve explicit blacklist/block status over computed segment
- avoid changing manually assigned segment unless an approved policy allows it

## Data lake events

Every important action should emit an event:

```text
guest_created
guest_updated
guest_synced_from_reservation
guest_merged
guest_tag_added
guest_tag_removed
guest_preference_recorded
guest_message_drafted
guest_message_sent
guest_marketing_consent_requested
guest_marketing_consent_updated
guest_segment_changed
```

Each event should include:

- guest_id
- actor_id when available
- reservation_id when relevant
- old segment/status when relevant
- new segment/status when relevant
- contact/source metadata when relevant
- timestamp
- request/session metadata when available
