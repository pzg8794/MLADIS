# ADR 0004: Booking Neuron — Homepage Design System & Admin Control Layer

Status: Accepted for active development  
Date: 2026-06-23  
Branch: `feature/gentelella-v4-rebrand`  
Related:

- `docs/architecture/0001-mladis-universe-neuron-model.md`
- `docs/architecture/0003-gentelella-v4-full-site-rebrand.md`
- `docs/architecture/booking-neuron/`

---

## 1. Summary

This document captures the visual design system, homepage layout direction, and admin control architecture for the **Booking Neuron's public-facing homepage** (`mladis.com` / `booking` product expression).

It establishes:

- the approved homepage layout (Option B — Neighborhood Bento)
- the warm light palette and visual identity
- the admin settings subsystem for operators to control the homepage and booking behavior
- the FairAgent AI configuration panel for the Booking Neuron
- the MLADIS neuron integration contract

This documentation exists so that development can begin immediately without re-litigating design decisions.

---

## 2. Design Direction: Approved — Option B (Neighborhood Bento)

The homepage will use a **typography-first, warm-light, bento-style layout**.

This was chosen over a cinematic/hero-image approach because it makes the page immediately operational: users land on real inventory, geography, and trust signals simultaneously — without scrolling.

### 2.1 Core principle

```text
The homepage is a smart booking workspace, not a marketing landing page.
It renders real Booking.Resource.Property objects, Booking.Availability, and neighborhood context.
The page does not invent business logic. It projects neuron state.
```

### 2.2 Homepage section order

| # | Section | Purpose |
|---|---|---|
| 1 | Warm Text Hero | Establish identity, location, and two primary CTAs |
| 2 | Neighborhood Bento Grid | Featured property cards + live map panel |
| 3 | Trust Strip | Ratings, deposit clarity, human support promise |
| 4 | Neighborhood Cards | Area context that supports booking confidence |
| 5 | Rules + Stay Rhythm | Transparent expectations |
| 6 | AI Booking Panel | FairAgent-assisted booking entry point |
| 7 | Mission Section | MLADIS brand and human story |

### 2.3 Bento grid layout

```text
┌─────────────────────────────────────────────────────┐
│  TEXT HERO (left-aligned, warm cream bg)            │
│  Headline + subline + 2 CTAs                        │
└─────────────────────────────────────────────────────┘
┌───────────────┬───────────────┬─────────────────────┐
│ FEATURED      │ PROPERTY      │ MAP PANEL           │
│ PROPERTY CARD │ CARD (small)  │ Neighborhood pins   │
│ (tall)        ├───────────────┤ + compact legend    │
│               │ PROPERTY      │                     │
│               │ CARD (small)  │                     │
└───────────────┴───────────────┴─────────────────────┘
```

Each bento cell has exactly one job. The map supports decision-making but does not dominate the inventory.

---

## 3. Visual Identity System

### 3.1 Palette

```text
Page background:    #f7f6f2  (warm ivory)
Card surface:       #ffffff  (clean white)
Card shadow:        0 4px 12px oklch(0.2 0.01 80 / 0.08)
Primary action:     #01696f  (deep teal — CTAs, active states, links)
Primary hover:      #0c4e54
Gold accent:        #d19900  (ratings and highlights only)
Text primary:       #1a1a1a  (near-black charcoal)
Text muted:         #7a7974
Divider:            #dcd9d5
Status — active:    #437a22  (success green)
Status — pending:   #da7101  (warm orange)
Status — blocked:   #a12c7b  (error maroon)
```

### 3.2 Typography

```text
Display font:   Cabinet Grotesk (Fontshare) — headings 24px and above
Body font:      Satoshi (Fontshare) — body, labels, UI chrome
Max web app heading size: --text-xl (24–36px)
Body text: 16px minimum
UI chrome / table text: 14px
Tiny labels: 12px floor
```

### 3.3 Visual rules

- No gradient buttons. Teal solid only for CTAs.
- No purple/blue gradient backgrounds.
- No colored side-border cards.
- Surface elevation via shadow, not borders.
- Alpha-blended borders: `oklch(from var(--color-text) l c h / 0.12)`
- Rounded cards: `--radius-lg` (0.75rem) for property cards, `--radius-md` for chips and badges.
- Light and dark mode required — default to system preference.

---

## 4. Design Reference Images

The following images were generated during design planning and are stored as visual references.

They are design references only. Implementation must follow the object architecture.

```text
docs/architecture/booking-neuron/images/
├── booking_homepage_bento_option_b.png     ← Approved homepage direction (Option B warm light)
├── booking_admin_settings_panel.png        ← Admin settings panel for Booking Neuron config
├── booking_property_card_manager.png       ← Cover photo and property card admin UI
└── booking_fairagent_settings_panel.png    ← FairAgent AI configuration panel
```

### 4.1 Homepage (Option B — approved)

Warm ivory background. Left-aligned typography hero with headline about Santo Domingo Norte stays.
Three-part bento grid below: tall featured property card, two stacked small property cards, live map panel.
Trust strip with ratings badges. Clean sans-serif throughout.

### 4.2 Admin Settings Panel

Two-column layout inside OpsShell. Left column: tabbed Booking Neuron settings form with fields for rate, minimum stay, deposit percentage, advance booking window, and toggle switches for AI-assisted pricing and auto-approval. Right column: homepage section order control with drag-and-drop section visibility.

See: `docs/architecture/booking-neuron/images/booking_admin_settings_panel.png`

### 4.3 Property Card Manager

Grid of property card previews with edit controls per card. Cover photo upload, crop, AI-enhance options. Live preview of where the card appears in the bento homepage layout.

See: `docs/architecture/booking-neuron/images/booking_property_card_manager.png`

### 4.4 FairAgent AI Settings Panel

Agent behavior toggles (auto-draft replies, pricing suggestions, deposit explanations, language detection). Guardrails section with human-approval requirements. Live agent preview showing guest query and AI-drafted reply awaiting staff approval.

See: `docs/architecture/booking-neuron/images/booking_fairagent_settings_panel.png`

---

## 5. Neuron Integration Contract

The homepage and its admin system are expressions of the Booking Neuron. They do not own business logic.

```text
Booking [uses: Finance, Pyramid, FairAgent]
│
├── Booking.Resource.Property        → property cards, inventory
├── Booking.Availability.Calendar    → map panel, date picker
├── Booking.Availability.Window      → availability display
├── Booking.Reservation.StayReservation → booking flow entry
├── Booking.Policy.Deposit           → trust strip, deposit info
├── Booking.Policy.Pricing           → rate display, AI pricing
├── Booking.Policy.Cancellation      → rules section
│
Finance
├── Finance.Transaction.Deposit      → deposit holds
├── Finance.Transaction.Payment      → booking payment flow
│
FairAgent
├── FairAgent.Action                 → draft guest replies
├── FairAgent.Decision               → pricing suggestion
├── FairAgent.Explanation            → deposit/policy explanation to guests
└── FairAgent.Audit                  → all AI suggestions logged
```

### 5.1 OOP/MVC contract

```text
Model:       Booking.Resource.Property, Booking.Availability, Booking.Policy
Repository:  PropertyRepository, AvailabilityRepository, PolicyRepository
Service:     BookingService, AvailabilityService, PricingService
Controller:  Django views/API endpoints — /api/booking/properties/, /api/booking/availability/
View:        React components — OpsPropertyCard, BentoHomePage, BookingAgentPanel
```

Pages render object projections. Pages do not own business rules.

---

## 6. Admin Control Subsystem

Admins control the Booking Neuron homepage and behavior through the MLADIS OpsShell, not through direct database edits.

### 6.1 Homepage Layout Control

Admins can:

- reorder homepage sections (drag-and-drop section order)
- toggle section visibility (show/hide each section)
- set the featured property (which card appears in the tall left slot)
- enable/disable the AI Booking Panel section
- preview homepage changes before publishing

Backend object: `Booking.Resource.HomepageLayout` (configuration object)

### 6.2 Property Card Manager

Admins can:

- upload and manage cover photos per property
- set crop/position for card thumbnail
- toggle property visibility (Published / Draft / Paused)
- preview how the card renders in the bento grid
- request AI image enhancement (FairAgent action, human-approved)

Backend object: `Booking.Resource.Property` + `Artifact.Picture`

### 6.3 Booking Neuron Settings

Admins can configure:

| Setting | Type | Default |
|---|---|---|
| Base nightly rate | Currency | Set per property |
| Minimum stay (nights) | Integer | 2 |
| Advance booking window (days) | Integer | 90 |
| Deposit percentage | Percentage | 30% |
| AI-assisted pricing | Toggle | Off |
| Auto-approve reservations | Toggle | Off |
| Show availability calendar publicly | Toggle | On |
| Language options | Multi-select | EN, ES |

Backend object: `Booking.Policy.Pricing`, `Booking.Policy.Deposit`, `Booking.Policy.Access`

### 6.4 FairAgent Configuration

Admins can configure the AI Booking Agent:

| Setting | Type | Default |
|---|---|---|
| Auto-draft guest replies | Toggle | Off |
| AI-assisted availability suggestions | Toggle | Off |
| Smart pricing recommendations | Toggle | Off |
| Deposit policy explanations | Toggle | On |
| Language detection (EN/ES) | Toggle | On |
| Max discount AI can suggest | Percentage | 10% |
| Require human approval: Cancellations | Required | Always |
| Require human approval: Refunds | Required | Always |
| Require human approval: Special rates | Required | Always |
| Confidence threshold | Slider | 80% |

Backend object: `FairAgent.Policy` + `FairAgent.Action` (Booking context)

---

## 7. Frontend Component Map

```text
frontend/src/ui/pages/
├── BookingHomePage.tsx              ← public homepage
├── BookingAdminSettingsPage.tsx     ← admin settings workspace
├── BookingPropertyCardManagerPage.tsx
└── BookingFairAgentConfigPage.tsx

frontend/src/ui/components/booking/
├── BentoHero.tsx                    ← typography hero section
├── NeighborhoodBentoGrid.tsx        ← 3-panel bento layout
├── OpsPropertyCard.tsx              ← property card (reusable)
├── MapPanel.tsx                     ← neighborhood map with pins
├── TrustStrip.tsx                   ← ratings + trust signals
├── NeighborhoodCard.tsx             ← area context cards
├── AIBookingPanel.tsx               ← FairAgent booking entry
├── HomepageSectionSorter.tsx        ← admin drag-drop section order
├── PropertyCardEditor.tsx           ← cover photo + card admin
└── FairAgentConfigPanel.tsx         ← AI settings form
```

---

## 8. Backend API Contract

```text
# Public endpoints
GET    /api/booking/homepage/layout/
GET    /api/booking/properties/
GET    /api/booking/properties/<id>/availability/
POST   /api/booking/reservations/
GET    /api/booking/policies/

# Admin endpoints
PATCH  /api/booking/homepage/layout/
PATCH  /api/booking/properties/<id>/
POST   /api/booking/properties/<id>/cover-photo/
PATCH  /api/booking/settings/
PATCH  /api/booking/fair-agent/config/
GET    /api/booking/fair-agent/draft-reply/
POST   /api/booking/fair-agent/approve-reply/
```

---

## 9. Development Phases

### Phase 1 — Homepage shell (active)

- Build `BentoHero` and `NeighborhoodBentoGrid` components
- Use fallback-safe `PropertyRepository` with real seed data
- Connect `Booking.Resource.Property` real data when available
- Implement warm light palette tokens in `opsTheme.ts`
- Mobile-first: 375px single-column flow collapses bento grid

### Phase 2 — Property cards + map

- Build `OpsPropertyCard` as reusable shared component
- Integrate map panel (Mapbox or Leaflet with neighborhood pins)
- Connect real availability from `Booking.Availability.Calendar`
- Ensure cards render from `PropertyRepository`, not hardcoded HTML

### Phase 3 — Admin settings

- Build `BookingAdminSettingsPage` inside OpsShell
- Implement `HomepageSectionSorter` drag-drop
- Build `PropertyCardEditor` with photo upload
- Connect `Booking.Policy` settings to admin form

### Phase 4 — FairAgent integration

- Build `FairAgentConfigPanel` admin UI
- Connect `FairAgent.Policy` to booking context
- Implement draft-reply flow with human approval gate
- Log all FairAgent actions through `FairAgent.Audit`

### Phase 5 — Production approval

- Desktop smoke check
- Mobile smoke check
- Django/frontend build passes
- OpsShell nav consistent
- Admin settings saving correctly
- Local preview approved before merge to main

---

## 10. Acceptance Criteria

The Booking Neuron homepage system is complete when:

- [ ] Homepage renders from real `Booking.Resource.Property` objects
- [ ] Bento grid is responsive (3-column desktop → 1-column mobile)
- [ ] Admin can reorder homepage sections without a code deploy
- [ ] Admin can set featured property card from the OpsShell
- [ ] Admin can upload and crop cover photos
- [ ] FairAgent draft replies require human approval before sending
- [ ] All FairAgent actions are logged in `FairAgent.Audit`
- [ ] Settings panel saves to `Booking.Policy` objects
- [ ] OOP/MVC boundaries respected throughout
- [ ] No business logic in React view components

---

## 11. Guiding Principle

The homepage is the public face of the Booking Neuron.

It must feel like:

```text
Premium AI-guided neighborhood booking.
Not a real-estate dashboard.
Not a generic Airbnb clone.
Not an admin panel accidentally made public.
```

The admin control layer is what makes this possible:

```text
Operators control the experience through structured neuron settings.
FairAgent assists but never acts without approval.
Pyramid logs evidence of every state change.
```

This is the Booking Neuron functioning as MLADIS intended.
