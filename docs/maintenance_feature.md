# Maintenance Feature — Developer Guide

## Overview

The `maintenance` Django app implements an MVC-structured module that allows property administrators to log maintenance and cleaning events against any property in MLADIS. Each event has four required attributes:

| Attribute | Field(s) | Notes |
|-----------|----------|-------|
| **Title** | `title` | Required, max 200 chars |
| **Cost** | `cost_amount` + `cost_currency` | Non-negative decimal, defaults USD |
| **Time** | `start_at` (+ optional `end_at`) | ISO 8601, required |
| **Pictures** | `MaintenancePhoto` (1-to-many) | At least 1 required |

---

## Installation

1. Add `"maintenance"` to `INSTALLED_APPS` in your settings file.
2. Add maintenance URLs to your main `urls.py`:
   ```python
   path("api/", include("maintenance.urls")),
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Install Pillow (if not already): `pip install Pillow`

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/maintenance/` | List events (filter: `?property=<id>&status=DONE&category=CLEANING`) |
| `POST` | `/api/maintenance/` | Create event (multipart form or JSON) |
| `GET` | `/api/maintenance/{id}/` | Retrieve single event |
| `PATCH` | `/api/maintenance/{id}/` | Update event |
| `DELETE` | `/api/maintenance/{id}/` | Delete event |
| `GET` | `/api/maintenance/{id}/invoice-payload/` | Agent-ready JSON for bill/tax generation |

---

## Agent Payload Schema

```json
{
  "maintenance_id": "UUID",
  "property_code": "G-101",
  "property_display_name": "G-101 – Oceanfront Condo",
  "booking_id": null,
  "title": "Turnover cleaning after checkout",
  "category": "CLEANING",
  "cost": { "amount": "85.00", "currency": "USD" },
  "time": {
    "start_at": "2026-06-07T10:00:00-04:00",
    "end_at": "2026-06-07T12:00:00-04:00",
    "duration_minutes": 120
  },
  "pictures": [
    { "id": "UUID", "url": "https://.../maintenance_photos/img.jpg", "caption": "Before" }
  ],
  "created_by": "admin@mladis.com",
  "created_at": "2026-06-07T12:05:00-04:00",
  "status": "DONE",
  "tax_category_code": "CLEANING_SERVICES"
}
```

---

## React Components

- **`MaintenanceForm`** (`frontend/src/components/MaintenanceForm.jsx`) — create form, supports camera capture on mobile.
- **`MaintenanceList`** (`frontend/src/components/MaintenanceList.jsx`) — table view per property, includes "Get Payload" button.

---

## Integration Checklist

- [ ] Verify FK labels (`bookings.BookableItem`, `bookings.BookingInquiry`) match your actual app/model names and update `models.py` + migration accordingly.
- [ ] Add `maintenance` to `INSTALLED_APPS`.
- [ ] Wire `maintenance.urls` into the main `urls.py`.
- [ ] Run `python manage.py migrate`.
- [ ] Connect `MaintenanceExportService.export_event()` to your Drive data-lake exporter (see `maintenance/services.py`).
- [ ] Import `<MaintenanceForm>` and `<MaintenanceList>` into the property admin page in the React frontend.
