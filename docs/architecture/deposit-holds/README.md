# MLADIS Deposit Holds Architecture

Date: 2026-06-20
Status: design contract / implementation reference

This directory is the canonical documentation home for the **DepositHold** object system that powers the Deposits & Holds workspace.

DepositHold and PaymentTransaction are separate domain objects, but they must be designed together because hold authorization, capture, release, failed attempts, receipts, and refunds all connect to payment provider transactions.

## Core rule

```text
DepositHold is the source object for the Deposits & Holds page.
Rows, metric cards, expiring-soon panels, guest hold details, authorization timeline, linked payment attempts, risk state, guest notes, and hold actions are projections of DepositHold state.
```

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

DepositHold is the preferred domain object for authorization holds. It can wrap or gradually replace `DamageDeposit` and `ReservationPaymentHold` depending on migration risk.

## Relationship to PaymentTransaction

A `DepositHold` controls authorization state.

A `PaymentTransaction` records money movement.

A hold may have many linked payment attempts/transactions over time, especially when authorization, capture, release, refund, retry, and dispute events happen.

## Design principle

The UI does not contain deposit rows.

The UI contains `DepositHold` objects, and rows/cards/details are visual projections of those objects.
