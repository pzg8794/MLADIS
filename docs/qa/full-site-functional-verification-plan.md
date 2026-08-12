# MLADIS Full-Site Functional Verification Plan

Status: execution plan

Baseline release: `release/2026.08.11-1`

Production: https://mladis.com/

Local: https://local.mladis.com/

## Purpose

This plan defines the evidence required before anyone may claim that every
MLADIS function works. A successful build, route smoke test, or visual review is
necessary but is not sufficient. The claim requires an inventory of every user
action, automated execution of that inventory, visible expected-result checks,
database or provider evidence for state-changing flows, and a retained evidence
ledger.

## Claim Standard

MLADIS may be described as fully functional only when all of the following are
true for the release under test:

1. Every reachable route, form, button, link, menu item, API action, scheduled
   action, and provider callback is represented by a unique test-case ID.
2. Every enabled function passes its expected-result checks in local and
   production-safe environments.
3. Functions that cannot operate because a provider or workflow is unavailable
   are hidden or disabled with an honest reason; they are not counted as
   working.
4. All state-changing tests prove both the visible result and the persisted
   database/provider result.
5. No `P0` or `P1` defects remain open. Every `P2` or `P3` issue is documented
   with an owner and disposition.
6. The release passes desktop, tablet, and mobile layout checks without
   overlapping controls, clipped text, inaccessible actions, or horizontal page
   overflow.
7. The evidence ledger is complete, reproducible, and tied to one immutable Git
   release tag.

## Test Environments

### Local integration

- Start only with `./run_mladis_live.command`.
- Confirm port `8000` belongs to the canonical checkout.
- Use the local SQLite database and approved local `.env` without printing
  secrets.
- Use real local records. Synthetic records are allowed only in test fixtures
  and must be identified as test data.

### Provider sandboxes

- Stripe test mode for checkout, authorization, success, failure, and webhook
  flows.
- PayPal sandbox only after approved credentials are configured.
- Console or capture backend for email content tests; a controlled deliverability
  inbox for end-to-end delivery tests.
- Approved OpenAI test account for FairAgent and maintenance AI actions.

### Production smoke

- Read-only checks for all operational pages and APIs.
- One reversible canary record per state-changing object when production
  mutation evidence is required.
- Never use a real guest charge, capture, refund, or irreversible communication
  as a smoke test.

## Tooling

- Django test client for authorization, controllers, API contracts, redirects,
  persistence, and service behavior.
- Browser automation for visible UI behavior, field validation, navigation,
  downloads, responsive checks, and console/network errors.
- Computer control only where a provider flow cannot be driven through the
  browser API; capture the visible expected result after each action.
- Stripe and PayPal CLIs/webhook tools for sandbox provider evidence.
- `curl` for health, redirect, cache, and public endpoint contracts.
- Database queries for before/after persistence evidence.
- Screenshots at desktop, tablet, and mobile viewports for all primary workflows.
- CI jobs that archive the machine-readable ledger, screenshots, logs, and
  provider event IDs as release artifacts.

## Phase 1: Generate the Function Inventory

Create `docs/qa/function-inventory.csv` from repository inspection, then review
it manually. Sources include:

- Django URL patterns and HTTP methods.
- React route selection.
- HTML forms, links, buttons, menu items, dialogs, tabs, toggles, and downloads.
- Repository/service methods exposed to UI actions.
- Webhooks, management commands, scheduled actions, and email triggers.
- Provider-dependent flows.

Required columns:

```text
id,object,route,role,control,action,precondition,expected_ui,
expected_persistence,expected_external_effect,environment,automated,
evidence,status,defect
```

No function is omitted because it is unfinished. Unfinished behavior is recorded
as unavailable and must be hidden or honestly disabled in the product.

## Phase 2: Role and State Matrix

Run every applicable function under these identities:

- Anonymous visitor.
- Authenticated guest.
- Staff operator.
- Administrator.
- Automation agent where supported.

Run object workflows through all meaningful states:

- Reservation: draft, pending, confirmed, canceled, completed.
- Invoice/payment: pending, sent, paid, failed, canceled.
- Deposit hold: requested, approved, on hold, released, failed, expired, review.
- Work order: open, pending, in progress, completed, overdue.
- Guest: new, repeat, VIP, blocked.
- Calendar: available, reserved, blocked, price override.

## Phase 3: Workflow Suites

### Public site and booking request

- Header navigation, language selection, property cards, gallery, map, rules,
  FAQs, account links, privacy/terms, and responsive menu.
- Reservation form validation, property/date/guest/coupon selection, price
  preview, duplicate prevention, successful request, confirmation, and account
  visibility.
- Agent question submission and expected answer/error states.

### Authentication and account

- Email login, logout, invalid credentials, signup, protected-route return URL,
  and styled failure pages.
- Google, GitHub, and Facebook provider launch/callback contracts.
- Account reservation list, selection, details, edit, cancellation, invoice and
  payment launch, and payment confirmation.

### Reservations

- Search, filter, pagination, selection toggle, status changes, details, linked
  guest, property, payment, deposit, and calendar context.
- Reject invalid transitions in the service/API, not only in the UI.

### Calendar

- Calendar/List/Rooms/Analytics navigation.
- Month/week/day periods, date movement, property filters, row visibility,
  selection, block creation/removal, price overrides, reservation rendering,
  Settings/New Booking actions, and right-rail collapse/focus behavior.

### Guests

- Real unique guest rows, search, filters, pagination, export, selection toggle,
  profile, messages, documents, payments, deposits, activity, stays, tags,
  preferences, consent, and merge safeguards.
- Outbound messages require explicit staff confirmation and captured evidence.

### Properties

- Search/filter/pagination, selection toggle, public preview, calendar context,
  listing edit, readiness, linked reservations, images, and honest empty states.

### Maintenance and tasks

- Work-order search/filter/pagination and distinct row-to-detail mapping.
- Selection toggle, create/edit/status/assignee/priority, notes, pictures,
  linked property/reservation, activity timeline, report generation, and AI
  description draft/apply.
- Task board filtering, selection, reassign, move, complete, and persistence.

### Payments and deposits

- Real-record search/filter/pagination, row/detail toggle, linked reservation,
  guest, invoice, hold, timeline, notes, and downloads.
- Stripe sandbox checkout for stay only, deposit only, and combined checkout.
- Required document acceptance, one user payment interaction, backend-separated
  authorizations, success confirmation, webhook idempotency, and failure recovery.
- Send invoice/mark paid only when service rules allow.
- Refund remains disabled until its dedicated workflow passes this plan.
- Deposit approve/release/request-guest-action, stale-selection clearing, and
  receipt/payment-link honesty.

### Reports, Command Center, Admin, and Settings

- All metrics reconcile against real database queries for the same period.
- Date/filter/export controls operate or are disabled honestly.
- Command Center links open the correct workspace.
- Settings tabs persist changes, survive reload, enforce permissions, and do not
  expose secrets.
- Admin operations, user/role access, integration status, and audit history.

### FairAgent

- Conversation creation, FAQ retrieval, knowledge sources, guardrails,
  escalation, safe booking actions, provider errors, usage accounting, and no
  unsupported claim or action.

## Phase 4: Automated Browser Execution

For each UI test case:

1. Arrange a known database state through fixtures or service APIs.
2. Open the exact route at a named viewport and role.
3. Capture the pre-action screenshot and relevant DOM state.
4. Perform the same click/type/select action a user performs.
5. Assert the expected visible result, URL, enabled/disabled state, and absence
   of console or failed-network errors.
6. Query the database or provider event to verify the persisted/external result.
7. Capture the post-action screenshot and evidence identifiers.
8. Restore or clean up the reversible test record.

Desktop baseline: `1440x1000`.

Tablet baseline: `834x1112`.

Mobile baseline: `390x844`.

## Phase 5: Nonfunctional Gates

- Accessibility: keyboard-only operation, focus visibility, form labels,
  landmarks, dialog focus, and automated WCAG checks.
- Security: permission boundaries, CSRF, object ownership, webhook signature,
  secret exposure, and unsafe direct-object references.
- Reliability: duplicate submissions, double clicks, refresh/retry behavior,
  idempotent webhooks, provider timeouts, and stale-session recovery.
- Performance: route load budgets, API response budgets, image sizes, JavaScript
  bundle review, and database query counts.
- Compatibility: current Chrome, Safari, Firefox, and mobile Safari/Chrome.

## Evidence Ledger and Reporting

Every execution produces:

- Immutable release tag and environment metadata.
- Function inventory revision.
- Test-case result with timestamp and role.
- Screenshot or download artifact when the result is visual.
- Database record IDs and before/after fields for mutations.
- Provider event IDs for external actions.
- Console and failed-request logs.
- Defect link and severity for failures.

The release report must distinguish:

- `PASS`: expected UI and underlying effect verified.
- `UNAVAILABLE`: control hidden or disabled with an honest reason.
- `BLOCKED`: required external credential/service unavailable.
- `FAIL`: behavior exists but did not meet its contract.
- `NOT TESTED`: never acceptable in a full-function claim.

## Execution Order

1. Build and approve the complete function inventory.
2. Automate public, auth, account, and booking-request critical paths.
3. Automate reservation, payment, deposit, and webhook critical paths.
4. Automate each ops workspace and object relationship.
5. Run responsive, accessibility, security, reliability, and compatibility gates.
6. Fix failures object by object on dedicated branches.
7. Repeat the complete suite against a release candidate.
8. Publish the evidence ledger and release report.
9. Claim full functionality only when the Claim Standard is satisfied.

## Current Release Baseline

For `release/2026.08.11-1`, the following evidence exists:

- 198 bookings tests passed.
- 9 sign-in contract tests passed.
- Django checks and migration drift checks passed.
- Production frontend assets built successfully.
- Production health, homepage, and login routes returned `200`.
- The `mladis` service is active and its local VM health endpoint returned `ok`.
- All 17 protected operational routes rendered with `200` under an existing
  authenticated staff account using the production Django test client.

This is a healthy release and smoke baseline. It is not yet evidence that every
interactive function works. That claim requires executing the complete plan.
