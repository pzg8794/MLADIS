# Deposit Admin Operations

This document covers the admin-side lifecycle controls for MLADIS damage deposits.

## Supported Providers

- Stripe deposits use Checkout plus manual-capture PaymentIntents.
- PayPal deposits use Orders v2 with `AUTHORIZE` and a stored authorization ID.

Both providers converge on the same `DamageDeposit` status model:

- `checkout_created`: the guest reached checkout but the hold is not yet authorized.
- `requires_capture`: the hold is authorized and can now be captured or released.
- `captured`: the hold was converted into a real charge.
- `canceled`: the hold was released without charging the guest.

## Admin List Actions

In Django Admin, the `Damage deposits` changelist now exposes two bulk actions:

- `Capture selected authorized deposits`
- `Release selected authorized deposits`

These actions only run on deposits that are actually ready to manage:

- Stripe: `payment_provider=stripe`, `status=requires_capture`, and `stripe_payment_intent_id` present.
- PayPal: `payment_provider=paypal`, `status=requires_capture`, and `paypal_authorization_id` present.

Ineligible rows are skipped instead of failing the whole batch.

## Per-Deposit Confirmation Flow

On each capturable deposit change page, Admin now shows object-tool links for:

- `Capture deposit`
- `Release deposit`

Those links open a confirmation page before any provider API call is made.

Provider-specific release behavior:

- Stripe release cancels the PaymentIntent hold.
- PayPal release voids the authorization.

This confirmation step is meant to reduce accidental captures or releases from the detail page.

## Audit Trail

Every successful capture or release appends a timestamped note to `DamageDeposit.notes`.

Examples:

- Stripe capture note includes the PaymentIntent ID and latest charge when available.
- Stripe release note includes the PaymentIntent ID.
- PayPal capture note includes the authorization ID and capture ID when returned.
- PayPal release note includes the authorization ID.

## Validation

The current focused validation command for this slice is:

```bash
cd airbnb_agent
.venv/bin/python manage.py test bookings.tests.DamageDepositTests bookings.tests.DamageDepositAdminTests
```
