# MLADIS Agent Notes

## Change Discipline

- Update repository documentation for any operator-facing workflow change.
- Update this file when repository-wide agent workflow expectations change.
- Prefer the smallest behavior-scoped test slice first, then widen only if the touched code path crosses a broader surface.

## Deployment Safety

- Prefer the non-destructive root deploy script: `./deploy_mladis_vm.command`.
- If the local worktree contains unrelated changes, deploy only the touched production files instead of packaging the whole repo.
- Do not overwrite `.env`, `db.sqlite3`, `media/`, or `.venv` during normal deploys.

## Local Startup

- Use `./run_mladis_live.command` from the repo root for the working local Django app. This is the only normal local startup path.
- Do not start MLADIS with ad hoc `python manage.py runserver`, `npm run dev`, `preview_*` scripts, `nohup`, or background shell servers during normal testing.
- The launcher builds the React frontend into Django static assets by default, runs Django setup, stops stale Django processes on the same port, starts the stable `mladis-local` Cloudflare named tunnel, exports `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com`, then starts Django on `http://127.0.0.1:8000`.
- Use `https://local.mladis.com` for browser testing when Facebook sign-in matters. `http://127.0.0.1:8000` is the internal local Django origin and the Google/GitHub local callback origin.
- Do not test Django/allauth social sign-in through the Vite dev server at `http://127.0.0.1:5173`.
- If frontend preview servers are running in parallel, stop them before debugging auth so redirects and cookies stay easy to reason about.
- If the Google Drive checkout is slow or Git starts hanging on ignored files, create a fast clone under `~/Documents` or `~/Desktop`, copy only `airbnb_agent/.env` if needed, and use GitHub as the synchronization point.
- The local launcher caches dependency installs by `requirements.txt`, skips local `collectstatic` unless `MLADIS_COLLECTSTATIC=1`, builds frontend assets unless `MLADIS_BUILD_FRONTEND=0`, writes named-tunnel output to `/private/tmp/mladis-tunnel.log`, and defaults to a 60 second startup timeout.

## Sign-In Contract

- Read `docs/sign-in-contract.md` before changing auth settings, allauth provider config, login/signup templates, OAuth middleware, or social launch routes.
- Run `bash airbnb_agent/scripts/test_signin_contracts.sh` before committing or pushing any sign-in change.
- Keep `SOCIAL_AUTH_CANONICAL_ORIGIN` empty during mixed local testing; use provider-specific origins instead.
- Keep Google and GitHub local callbacks on `http://127.0.0.1:8000`.
- Use the Cloudflare named tunnel for Facebook local callbacks. The launcher exports `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com` unless an explicit shell override is provided.
- Do not validate Facebook from plain `http://127.0.0.1:8000`; Meta requires the stable HTTPS callback.
- Keep Meta allow-listed with `https://local.mladis.com/oauth/facebook/login/callback/` for local testing and `https://mladis.com/oauth/facebook/login/callback/` for production.
- Keep provider-native account pickers enabled with allauth provider settings. Do not add an MLADIS-side account-confirmation interstitial for GitHub or Google.
- Keep Microsoft hidden with `SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=microsoft` until its credentials and callback are fully configured.
- Keep `/ops/oauth/` wired to the staff OAuth diagnostics page; it is part of the sign-in contract because operators use it to copy exact provider callbacks.

## Access Provisioning

- Provision automation or agent admin access as a dedicated Django user plus a matching `AdminAccess` record keyed to the same email; do not reuse owner credentials for routine automation.
- Use `python manage.py provision_agent_admin` with `MLADIS_AGENT_ADMIN_*` `.env` values to create or refresh that dedicated Django user and `AdminAccess` record.
- For external systems such as Google Workspace, Google Cloud, Stripe, and PayPal, each dedicated automation identity should enroll its own MFA method; do not reuse the owner account's authenticator setup for automation access.
- Google Cloud owner grants for external automation identities can land as `roles/resourcemanager.projectOwnerInvitee`; treat that as a pending owner invitation and complete the mailbox acceptance step before assuming active owner access.
- PayPal business access is managed under Business Settings -> Manage Users; for full automation coverage, invite the account as an `Other user` and grant all permissions, then finish activation from the email invitation.

## Business Operations

- Use `docs/business/` as the private source of truth for MLADIS LLC formation facts, post-formation deadlines, and administrative records.
- Do not copy private legal addresses, government portal references, transaction IDs, tax IDs, bank details, or owner contact details from `docs/business/` into public frontend pages or customer emails.
- If app features need legal-business facts, model them explicitly behind admin-only access instead of reading directly from the Markdown docs.

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
