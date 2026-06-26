# MLADIS Deposit Holds Architecture

Date: 2026-06-20
Status: design contract / implementation reference

This directory is the canonical documentation home for the **DepositHold** object system that powers the Deposits & Holds workspace.

DepositHold and PaymentTransaction are separate domain objects, but they must be designed together because hold authorization, capture, release, failed attempts, receipts, and refunds all connect to payment provider transactions.

For the platform-wide transaction spine, read
`docs/architecture/transactions/README.md`.

## Core rule

```text
DepositHold is the source object for the Deposits & Holds page.
Rows, metric cards, expiring-soon panels, guest hold details, authorization timeline, linked payment attempts, risk state, guest notes, and hold actions are projections of DepositHold state.
```

## Simplified transaction-spine rule

Use the name `DepositHold`, not generic `Deposit`.

DepositHold is a Transaction type:

```text
Guest -> Transaction -> DepositHold -> Invoice
```

DepositHold represents security/damage authorization hold state, provider
authorization state, and the release/capture/failure/expiration lifecycle.

DepositHold is the only deposit object.

Do not introduce separate Refund or Adjustment objects at this stage. Released
means the hold was lifted or canceled. Released is not always the same as
refunded, because money may never have been captured.

## Directory map

```text
docs/architecture/deposit-holds/
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

Current MLADIS deposit/hold foundations include:

- `DamageDeposit` for refundable damage-deposit authorization workflows.
- `ReservationPaymentHold` for stay-payment authorization holds.
- `DepositProvider` enum for Stripe/PayPal providers.
- `DepositStatus` enum for new, configuration, checkout-created, authorized, captured, canceled, and failed states.

DepositHold is the preferred domain object for authorization holds. It can wrap
or gradually replace `DamageDeposit` and `ReservationPaymentHold` depending on
migration risk.

## Relationship to Reservation and Payment

A `DepositHold` controls authorization state.

A `Payment` records money collection.

A `Reservation` transaction can group related `Payment` and `DepositHold`
transactions.

A hold may expose linked payment attempts or provider references over time, but
release, capture, failure, expiration, and guest-action states remain part of
the DepositHold lifecycle.

## Design principle

The UI does not contain deposit rows.

The UI contains `DepositHold` objects, and rows/cards/details are visual projections of those objects.

Production and normal local app behavior must use real records only: no fake
deposit objects, fake rows, fake invoices, fake pagination, dead links, or
`href="#"`. Fallback/sample data belongs only in tests or explicitly marked
fixtures.
