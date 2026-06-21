# Operations Object Page Process

This process is mandatory for every `/ops/*` object page. Use it for payments,
deposit holds, reservations, maintenance, customers, properties, tasks,
FairAgent, reports, calendar, and future system objects.

## Rule

An ops page is not a screenshot. It is a functional object workspace.

Use real database objects first. Use mock data only as fallback or filler for
fields that do not exist yet. Never replace real objects with fake rows just to
match a design mock.

## Layers

1. Domain object
   - Define the source object and identity.
   - The object owns state labels, statuses, action eligibility, display money,
     risk/tone decisions, timeline events, linked records, and admin/provider
     references.
   - Example: `PaymentTransactionProjection` owns transaction row/detail payloads.
   - Example: `DepositHoldProjection` owns hold row/detail/action payloads.

2. Controller/API
   - Django views coordinate requests only.
   - Views call the object service and return explicit JSON or template context.
   - Views must not assemble business rules directly in templates or React.

3. Repository/service
   - Frontend repositories know HTTP paths.
   - Frontend services know filtering, action guards, and workspace behavior.
   - React pages do not know raw endpoint details.

4. View/component
   - Templates and React components render object state.
   - Components can choose layout and local selection state, but must not invent
     fake object state, fake counts, or fake links.

5. Actions
   - Every visible object action must either perform a real local state change,
     navigate to the real owner of the action, or be hidden/disabled.
   - Provider-side money actions must never be faked. If Stripe/PayPal capture,
     refund, or release is not actually invoked, the UI must treat the operation
     as a local ledger/admin action only.

6. Verification
   - Add focused backend tests for the object payload and each state-changing
     action.
   - Build frontend assets after React changes.
   - Use browser screenshots or Playwright checks on the existing local runtime.
   - Do not start a second service to verify a page.

7. Commit
   - Stage only files related to the completed object page.
   - Commit and push after the page is functional and verified.

## Current Reference Objects

Payments:
- Backend source objects: `Invoice`, `ReservationPaymentHold`, `DamageDeposit`.
- Aggregate projection: `PaymentTransactionProjection`.
- API: `/api/ops/payments/`.
- Action route: `/api/ops/payments/<transaction_key>/<action>/`.

Deposit holds:
- Backend source objects: `DamageDeposit`, `ReservationPaymentHold`.
- Aggregate projection: `DepositHoldProjection`.
- API: `/api/ops/deposits/`.
- Action route: `/api/ops/deposit-holds/<hold_key>/<action>/`.

Reservations:
- Frontend reference pattern: `domain/reservations.ts`,
  `infrastructure/OpsReservationsRepository.ts`,
  `application/OpsReservationsService.ts`,
  `application/OpsReservationsFactory.ts`,
  `ui/pages/OpsReservationsPage.tsx`.

## Checklist

- [ ] Read the object architecture/design docs first.
- [ ] Identify the aggregate root and linked objects.
- [ ] Build backend projection/service payloads.
- [ ] Expose JSON/action routes.
- [ ] Build frontend domain objects.
- [ ] Build frontend repository/service/factory.
- [ ] Render the page from the domain object, not static arrays.
- [ ] Preserve the canonical ops navigation.
- [ ] Add backend tests for payloads and actions.
- [ ] Build assets and verify in the existing local runtime.
- [ ] Commit and push.
