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

## Local Stripe Setup

Stripe Checkout cannot open unless Django has a Stripe secret key loaded at startup.
For local testing, use a Stripe test secret key and store it only in `airbnb_agent/.env`.

Run:

```bash
cd airbnb_agent
scripts/configure_stripe_env.sh
```

The helper prompts for `STRIPE_SECRET_KEY` without echoing it to the terminal and writes it to `.env`.
After changing `.env`, restart Django because `config/settings.py` loads the Stripe key during process startup.

Expected local behavior:

- `STRIPE_SECRET_KEY` blank: the secure-deposit modal shows `Stripe is not configured yet...`.
- `STRIPE_SECRET_KEY=sk_test_...`: the secure-deposit modal opens Stripe Checkout in test mode.
- `STRIPE_SECRET_KEY=sk_live_...`: use only after production webhooks, legal/payment settings, and live checkout review are ready.

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

## Confirmation Email Contract

Every reservation request and completed authorization hold must send confirmation email to both sides:

- Guest/customer: the email address on the booking request or payment hold.
- Admins: `BOOKING_INQUIRY_RECIPIENTS` from the runtime environment, currently Piter for local operations.

Required email events:

- Reservation request created: `MLADIS_RESERVATION_REQUEST_V1`.
- Security deposit hold authorized: `MLADIS_DAMAGE_DEPOSIT_CONFIRMATION_V1`.
- Reservation payment hold authorized: `MLADIS_RESERVATION_PAYMENT_CONFIRMATION_V1`.

Local/test mode subjects must start with `(TEST)`. This applies when Django is running with `DEBUG=True`, console/locmem email backend, a Stripe `sk_test_...` key, or PayPal sandbox for PayPal holds.

Confirmation emails are sent when the provider confirms the hold is authorized, not merely when the checkout link is created. Notes include an email-confirmation marker so a Stripe webhook and browser return URL do not send duplicate confirmations.

## Validation

The current focused validation command for this slice is:

```bash
cd airbnb_agent
.venv/bin/python manage.py test bookings.tests.DamageDepositTests bookings.tests.DamageDepositAdminTests bookings.tests.ReservationPricingAndPaymentHoldTests
```
