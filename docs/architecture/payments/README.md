# MLADIS Payment Transactions Architecture

Date: 2026-06-20
Status: design contract / implementation reference

This directory is the canonical documentation home for the **PaymentTransaction** object system that powers the Payments & Transactions workspace.

Payments and deposit holds are separate domain objects, but they must be designed together because both attach to a Reservation, share provider references, drive payment timelines, and appear together in operational views.

For the platform-wide transaction spine, read
`docs/architecture/transactions/README.md`.

## Core rule

```text
PaymentTransaction is the source object for the Payments & Transactions page.
Rows, metric cards, transaction details, invoice preview, linked reservation, deposit history, quick actions, payment timeline, and notes are projections of PaymentTransaction state.
```

## Simplified transaction-spine rule

Long-term, Payment is a Transaction type:

```text
Guest -> Transaction -> Payment -> Invoice
```

Payment represents money collection, provider reference, payment status, and
invoice/receipt behavior. Payment must not be modeled as a disconnected
dashboard row.

Every Payment transaction is invoiceable. A Payment transaction can generate or
reference its own `Invoice`.

Do not introduce Refund or Adjustment objects at this stage unless Piter
explicitly approves a future financial lifecycle expansion.

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

PaymentTransaction is the current transitional domain object for invoice-backed
payment projections and reconciled transaction rows. Future implementation
should move this toward the simpler `Payment extends Transaction` model without
breaking existing invoices, reservations, or holds.

## Relationship to DepositHold and Reservation

A `DepositHold` is an authorization-hold transaction type.

A `Payment` is a money-collection transaction type.

A `Reservation` transaction can group related `Payment` and `DepositHold`
transactions.

Release, capture, failure, expiration, and guest-action states belong inside
the `DepositHold` lifecycle. Released is not always refunded because money may
never have been captured.

## Design principle

The UI does not contain payment rows.

The UI contains `PaymentTransaction` objects, and rows/cards/details are visual projections of those objects.

Production and normal local app behavior must use real records only: no fake
payment objects, fake rows, fake invoices, fake pagination, dead links, or
`href="#"`. Fallback/sample data belongs only in tests or explicitly marked
fixtures.
