# MLADIS Agent Notes

## Change Discipline

- Update repository documentation for any operator-facing workflow change.
- Update this file when repository-wide agent workflow expectations change.
- Prefer the smallest behavior-scoped test slice first, then widen only if the touched code path crosses a broader surface.

## Deployment Safety

- Prefer the non-destructive root deploy script: `./deploy_mladis_vm.command`.
- If the local worktree contains unrelated changes, deploy only the touched production files instead of packaging the whole repo.
- Do not overwrite `.env`, `db.sqlite3`, `media/`, or `.venv` during normal deploys.

## Access Provisioning

- Provision automation or agent admin access as a dedicated Django user plus a matching `AdminAccess` record keyed to the same email; do not reuse owner credentials for routine automation.
- Use `python manage.py provision_agent_admin` with `MLADIS_AGENT_ADMIN_*` `.env` values to create or refresh that dedicated Django user and `AdminAccess` record.
- For external systems such as Google Workspace, Google Cloud, Stripe, and PayPal, each dedicated automation identity should enroll its own MFA method; do not reuse the owner account's authenticator setup for automation access.
- Google Cloud owner grants for external automation identities can land as `roles/resourcemanager.projectOwnerInvitee`; treat that as a pending owner invitation and complete the mailbox acceptance step before assuming active owner access.
- PayPal business access is managed under Business Settings -> Manage Users; for full automation coverage, invite the account as an `Other user` and grant all permissions, then finish activation from the email invitation.

## Deposit Operations

- Keep Stripe and PayPal deposit lifecycle behavior aligned at the admin layer whenever practical.
- Preserve audit notes on `DamageDeposit.notes` when capturing or releasing a hold.
- Authorized deposits should require an explicit confirmation step before capture or release from the change page.

## Calendar Operations

- The business calendar is managed from `BookableItem` admin via the custom calendar view, not from the legacy feed-setup page.
- Calendar availability combines active `BookingInquiry` records with manual `AvailabilityBlock` ranges.
- Nightly pricing shown in the calendar uses `BookableItem.starting_price` by default and overlays active `DailyPriceOverride` ranges when present.
- The calendar page includes a click-to-fill range helper that prefills both the block and price forms from selected days in the grid.
- The calendar grid also includes direct day-cell actions: `Block day`, `Price day`, and edit links to overlapping reservation, block, and price override records when present.
