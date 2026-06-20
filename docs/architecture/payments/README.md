# MLADIS Payment Transactions Architecture

Date: 2026-06-20
Status: design contract / implementation reference

This directory is the canonical documentation home for the **PaymentTransaction** object system that powers the Payments & Transactions workspace.

Payments and deposit holds are separate domain objects, but they must be designed together because both attach to a Reservation, share provider references, drive payment timelines, and appear together in operational views.

## Core rule

```text
PaymentTransaction is the source object for the Payments & Transactions page.
Rows, metric cards, transaction details, invoice preview, linked reservation, deposit history, quick actions, payment timeline, and notes are projections of PaymentTransaction state.
```

## Directory map

```text
docs/architecture/payments/
├── README.md
├── diagrams/
│   └── class-diagram.md
├── code/
│   └── stubs.md
├── instructions/
│   └── implementation-instructions.md
└── images/
    └── README.md
```

## Existing code alignment

Current MLADIS payment-related foundations include:

- `BookingInquiry` payment totals: subtotal, discount, deposit, total, currency.
- `DamageDeposit` and `ReservationPaymentHold` models for authorization/hold workflows.
- `DepositProvider` and `DepositStatus` enums shared by deposit and hold flows.

PaymentTransaction is the preferred domain object for actual payments, refunds, invoices, and reconciled transaction rows. It should relate to Reservation and optionally to DepositHold.

## Relationship to DepositHold

A `DepositHold` is an authorization object.

A `PaymentTransaction` is a money-movement object.

A deposit hold can generate or reference payment transactions when captured, released, refunded, failed, or reconciled.

## Design principle

The UI does not contain payment rows.

The UI contains `PaymentTransaction` objects, and rows/cards/details are visual projections of those objects.
