# MLADIS One-Object Task Rules

## Core Rule

Each AI task changes exactly one system object. A task may not silently expand
into another object because files are nearby, a test fails elsewhere, or an
agent sees an opportunity to refactor.

Common objects include:

```text
auth
payments
invoices
deposits
reservations
guests
calendar
reports
admin
homepage
navigation
settings
docs
shipping
work_orders
```

If work requires a second object, stop and ask Piter to split or explicitly
expand the task.

## Required Scope Declaration

Before editing, report:

```text
Active branch:
Active object:
Allowed files:
Forbidden files:
Required tests:
Worktree status:
Stash status:
Stop condition:
Proceeding: yes/no
```

The allowed list must be narrow and concrete. The forbidden list must name
high-risk neighboring objects, especially auth.

## Scope Enforcement

- `payments` forbids auth, guests, calendar, homepage, admin branding, and
  navigation unless navigation is explicitly the active object.
- `guests` forbids payments, auth, calendar, and unrelated ops pages.
- `calendar` forbids auth, payments, guests, and unrelated global navigation.
- `docs` permits only the declared documentation files.
- Cross-object failures are reported, not opportunistically repaired.
- Shared files such as `views.py`, `urls.py`, `tests.py`, and `styles.css` are
  allowed only when the declared object genuinely requires them. Keep edits
  limited to that object's sections.

## Payments Example

For a payments task, allowed files may include:

```text
airbnb_agent/bookings/ops_finance.py
airbnb_agent/bookings/views.py
airbnb_agent/bookings/urls.py
airbnb_agent/bookings/templates/bookings/modern_ops_payments.html
airbnb_agent/bookings/tests.py
frontend/src/domain/payments.ts
frontend/src/application/PaymentsService.ts
frontend/src/application/PaymentsFactory.ts
frontend/src/infrastructure/PaymentsRepository.ts
frontend/src/ui/pages/OpsPaymentsPage.tsx
frontend/src/ui/pages/ops-payments-page.css
```

Forbidden during a payments task:

```text
auth files
allauth files
OAuth files
login templates
signup templates
settings files
middleware files
guest pages
calendar pages
homepage
admin branding
navigation unless explicitly required
```

Touching login or auth during a payments task is a failed scope check.

## Auth Is Sealed

Auth files may be edited only when the active object is explicitly `auth`.

The following are forbidden during every non-auth task:

```text
settings.py
social_auth.py
allauth provider settings
account templates
socialaccount templates
login templates
signup templates
middleware
OAuth callback/origin settings
run_mladis_live.command
docs/sign-in-contract.md
```

Before any auth edit:

1. Read `docs/sign-in-contract.md`.
2. Declare the precise auth files allowed.
3. Confirm no non-auth object is being changed.
4. Run `bash scripts/test_signin_contracts.sh` from `airbnb_agent`.

Do not run auth tests as an excuse to edit auth during a non-auth task.

## Commit Boundaries

Each commit must contain one object only.

Good:

```text
ops/payments: fix pagination and invoice links
ops/guests: fix row selection toggle
docs: add codex environment contract
```

Bad:

```text
payments and login fixes
visual parity pass
misc fixes
dashboard polish and auth cleanup
```

If staged files cross object boundaries, unstage them and split the task or
stop for approval.

## Stop Conditions

Stop before editing when any of these are true:

- branch is not `codex/dev` or an explicitly approved feature branch;
- working tree is dirty before the task;
- an unexpected worktree exists;
- an unexpected stash exists;
- untracked source files are unexplained;
- the requested change requires forbidden files;
- the task requires more than one object;
- local runtime comes from a different checkout;
- a destructive cleanup would risk unpreserved work.
