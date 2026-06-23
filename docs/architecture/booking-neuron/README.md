# Booking Neuron Design Documentation

Date: 2026-06-23  
Status: Active development  
Related ADR: `docs/architecture/0004-booking-neuron-homepage-design-system.md`

This directory documents the Booking Neuron's homepage design system, admin control layer, and FairAgent integration.

## Directory structure

```text
docs/architecture/booking-neuron/
├── README.md                           ← this file
├── design/
│   ├── homepage-layout.md              ← Option B bento layout spec
│   ├── visual-identity.md              ← palette, typography, tokens
│   └── admin-control-panels.md        ← admin UI panel specs
├── architecture/
│   ├── neuron-integration.md           ← neuron composition map
│   ├── component-map.md               ← frontend component structure
│   └── api-contract.md               ← backend API endpoints
└── images/
    ├── README.md
    ├── booking_homepage_bento_option_b.png
    ├── booking_admin_settings_panel.png
    ├── booking_property_card_manager.png
    └── booking_fairagent_settings_panel.png
```

## Design premise

The Booking Neuron homepage is a smart booking workspace, not a marketing landing page.

It renders real `Booking.Resource.Property` objects, `Booking.Availability` state, and neighborhood context — with admins controlling layout and behavior through structured neuron settings inside the MLADIS OpsShell.

## Approved direction

**Option B — Neighborhood Bento** was selected as the homepage layout.

Reason: It makes the page immediately operational. Users land on real inventory, geography, and trust signals simultaneously without scrolling.

## Neuron composition

```text
Booking [uses: Finance, Pyramid, FairAgent]
├── Booking.Resource.Property
├── Booking.Availability
├── Booking.Reservation.StayReservation
├── Booking.Policy.Deposit
├── Booking.Policy.Pricing
Finance
├── Finance.Transaction.Deposit
├── Finance.Transaction.Payment
FairAgent
├── FairAgent.Action
├── FairAgent.Decision
├── FairAgent.Explanation
└── FairAgent.Audit
```

## Development phases

1. Homepage shell — BentoHero, NeighborhoodBentoGrid, fallback-safe seed data
2. Property cards + map — OpsPropertyCard, MapPanel, real availability data
3. Admin settings — BookingAdminSettingsPage, HomepageSectionSorter, PropertyCardEditor
4. FairAgent integration — FairAgentConfigPanel, draft-reply approval flow
5. Production approval — smoke checks, mobile, build, local preview
