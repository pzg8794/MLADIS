# Booking Neuron — Admin Control Panel Specifications

Date: 2026-06-23  
Status: Ready for development  
Related: `docs/architecture/0004-booking-neuron-homepage-design-system.md`

This document specifies the admin control panels that operators use to manage the Booking Neuron homepage and behavior from within the MLADIS OpsShell.

## Admin panel inventory

### Panel 1: Booking Neuron Settings

Route: `/ops/booking/settings/`  
Component: `BookingAdminSettingsPage`  
Backend: `PATCH /api/booking/settings/`

Tabbed sections:

**Public Site**
- Site name override (display only)
- Homepage tagline (editable)
- Primary CTA button text
- Secondary CTA button text

**Availability**
- Minimum stay (nights)
- Maximum stay (nights)
- Advance booking window (days)
- Check-in time
- Check-out time
- Blocked dates manager

**Policies**
- Deposit percentage
- Deposit due date rule (at booking / X days before arrival)
- Cancellation policy selector (Flexible / Moderate / Strict)
- Late checkout fee
- Cleaning fee

**AI Agent**
- FairAgent enabled toggle
- Auto-draft guest replies toggle
- AI pricing suggestions toggle
- Confidence threshold slider
- Human approval requirements (always required for: Cancellations, Refunds, Special rates)

**Notifications**
- New reservation email
- Cancellation email
- Guest check-in reminder
- Payment due reminder
- Staff notification recipients

---

### Panel 2: Homepage Layout Control

Route: `/ops/booking/homepage/`  
Component: `BookingHomepageLayoutPage`  
Backend: `PATCH /api/booking/homepage/layout/`

Features:

- Drag-and-drop section reorder
- Toggle section visibility (eye icon per section)
- Featured property selector (which card appears in tall left bento slot)
- "Preview homepage" button (renders live preview before publishing)
- "Publish changes" button (saves layout to `Booking.Resource.HomepageLayout`)

Section list (draggable):

```text
[👁] 1. Warm Text Hero
[👁] 2. Neighborhood Bento Grid
[👁] 3. Trust Strip
[👁] 4. Neighborhood Cards
[👁] 5. Rules + Stay Rhythm
[👁] 6. AI Booking Panel
[👁] 7. Mission Section
```

---

### Panel 3: Property Card Manager

Route: `/ops/booking/properties/`  
Component: `BookingPropertyCardManagerPage`  
Backend: `PATCH /api/booking/properties/<id>/`, `POST /api/booking/properties/<id>/cover-photo/`

Per property card:

- Cover photo upload (drag-drop or file picker)
- Crop and position tool
- "Enhance with AI" button (FairAgent action — requires human approval)
- Visibility toggle: Published / Draft / Paused
- Card preview (shows exactly how card renders in bento grid)
- Edit property details link

---

### Panel 4: FairAgent AI Configuration

Route: `/ops/booking/fair-agent/`  
Component: `BookingFairAgentConfigPage`  
Backend: `PATCH /api/booking/fair-agent/config/`

Sections:

**Agent Behavior**

| Toggle | Default |
|---|---|
| Auto-draft guest replies | Off |
| AI-assisted availability suggestions | Off |
| Smart pricing recommendations | Off |
| Deposit policy explanations | On |
| Language detection (EN/ES) | On |

**Guardrails**

| Setting | Value |
|---|---|
| Max discount AI can suggest | 10% |
| Require human approval: Cancellations | Always |
| Require human approval: Refunds | Always |
| Require human approval: Special rates | Always |
| Confidence threshold | 80% |

**Agent Preview**

Live panel showing:
- Sample guest question input
- AI-drafted reply in a chat bubble
- "Approve & Send" button (teal)
- "Edit before sending" link
- FairAgent status badge: `Active — Human-supervised mode`

**Training & Knowledge Base**

- List of FAQ items the agent can reference
- Add / Edit / Delete FAQ entries
- Link to Pyramid knowledge store (future Phase 5)

---

## UI pattern

All admin panels must:

- render inside `OpsShell` with Booking Neuron highlighted in left nav
- use `OpsSettingsPanel` component for form sections
- use `OpsActionButton` for save/publish actions
- use `OpsStatusBadge` for FairAgent status and property visibility
- use teal as the only action color
- not have colored side-border cards
- be usable on mobile (stacked, not overflow)
