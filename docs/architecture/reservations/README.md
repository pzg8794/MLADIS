# MLADIS Reservations Architecture

Date: 2026-06-19
Status: design contract / implementation reference

This directory is the canonical documentation home for the **Reservation** object system that powers the Reservations Workspace.

The attached Reservations Workspace screenshot is a functionality and layout reference. The implementation source of truth is the object model in this directory.

## Core rule

```text
Reservation is the source object.
The list row, guest card, messages panel, payment/deposit panel, documents, activity timeline, FairAgent panel, filters, and metrics are projections of Reservation state.
```

## Directory map

```text
docs/architecture/reservations/
├── README.md
├── diagrams/
│   ├── backend-class-diagram.md
│   └── frontend-class-diagram.md
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

Current MLADIS code already has reservation foundations:

- Backend reservation-like model: `BookingInquiry`
- Status enum: `BookingStatus`
- Stay/listing model: `BookableItem`
- Customer model: `CustomerProfile`
- Payment/deposit related fields on `BookingInquiry`
- Payment hold model/migration history for reservation holds
- Frontend page: `OpsReservationsPage`
- Frontend factory/service/repository path for ops reservation snapshots

The next implementation should either:

1. Rename or promote `BookingInquiry` into `Reservation`, preferred long-term vocabulary once migration risk is low, or
2. Keep `BookingInquiry` internally while exposing `Reservation` as the domain/API/frontend vocabulary.

Preferred short-term direction: keep database stability by wrapping `BookingInquiry` with `Reservation` services, serializers, and frontend domain objects.

Preferred long-term direction: formalize `Reservation` as the aggregate name after existing booking flows are stable.

## Design principle

The UI does not contain reservation cards.

The UI contains `Reservation` objects, and every card, row, badge, tab, assistant recommendation, deposit action, and timeline item is a visual projection of those objects.

This is the MLADIS way: design the object system first, then let backend models, APIs, services, frontend domain classes, and UI components express that system consistently.
