# MLADIS Guests Architecture

Date: 2026-06-21
Status: design contract / implementation reference

This directory is the canonical documentation home for the **Guest** object system that powers the Guests workspace.

The attached Guests screenshot is a functionality and layout reference. The implementation source of truth is the object model in this directory.

## Core rule

```text
Guest is the source object.
The list row, profile card, messages panel, documents tab, payments tab, deposits tab, activity timeline, last-stays panel, filters, tags, and metrics are projections of Guest state.
```

## Directory map

```text
docs/architecture/guests/
├── README.md
├── diagrams/
│   ├── backend-class-diagram.md
│   ├── frontend-class-diagram.md
│   └── reservation-relationship-diagram.md
├── code/
│   ├── backend-model-stubs.md
│   └── frontend-domain-stubs.md
├── instructions/
│   ├── api-service-contract.md
│   ├── implementation-instructions.md
│   └── ui-projection-rules.md
└── images/
    └── README.md
```

## Existing code alignment

Current MLADIS code already has guest/customer foundations:

- Backend model: `CustomerProfile`
- Related import model: `AirbnbGuestRecord`
- Related feedback model: `CustomerFeedback`
- Reservation model link: `BookingInquiry.customer_profile`
- Customer/guest segmentation: `ClientSegment`
- Contact/source tracking: `ContactSource`
- Marketing consent tracking: `MarketingConsentStatus`
- Frontend/ops page family: Guests/Customers CRM pages

The next implementation should either:

1. Keep `CustomerProfile` internally and expose `Guest` as the domain/API/frontend vocabulary, preferred short-term direction, or
2. Rename/promote `CustomerProfile` to `GuestProfile` or `Guest` after migration risk is low.

Preferred short-term direction: keep database stability by wrapping `CustomerProfile` with `Guest` services, serializers, and frontend domain objects.

Preferred long-term direction: formalize `Guest` as the aggregate name once reservations, payments, deposits, feedback, and messaging are stable.

## Design principle

The UI does not contain guest rows.

The UI contains `Guest` objects, and every row, profile card, tab, message, stay history item, payment/deposit link, activity event, tag, and metric is a visual projection of those objects.

This is the MLADIS way: design the object system first, then let backend models, APIs, services, frontend domain classes, and UI components express that system consistently.
