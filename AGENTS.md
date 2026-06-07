# MLADIS Agent Notes

## Change Discipline

- Update repository documentation for any operator-facing workflow change.
- Update this file when repository-wide agent workflow expectations change.
- Prefer the smallest behavior-scoped test slice first, then widen only if the touched code path crosses a broader surface.

## Architecture Discipline

- OOP and MVC are mandatory for MLADIS. Treat them as the system bible, not as optional style.
- Model/domain objects own business state, identity, invariants, and rules. For example, every visitor must be represented through a user/session context object, whether anonymous or authenticated.
- Controllers coordinate the request/response flow, ask model/domain objects for decisions, and return explicit payloads. They must not bury business rules in templates or React components.
- Views/templates/components render the model state they receive. They must not invent parallel auth, agent, booking, payment, or permission state.
- Do not duplicate the same state across independent components. If the nav, booking form, and agent panel need login state, they must receive it from the same user/session model or controller payload.
- Agent access must be modeled as an `AgentInstance` attached to a user/session context. The UI asks the backend controller for the current context and renders from that object.
- Any shortcut that directly checks loose booleans in multiple views instead of using the shared model/context is a bug, even if the screen appears to work.
- When fixing regressions, repair the model/controller boundary first, then simplify the view. Do not stack UI patches over a broken state model.
- Read `docs/engineering/oop-mvc-contract.md` before changing login/logout, agent access, bookings, payments, reservations, customer accounts, or admin workflows.

## Deployment Safety

- Prefer the non-destructive root deploy script: `./deploy_mladis_vm.command`.
- If the local worktree contains unrelated changes, deploy only the touched production files instead of packaging the whole repo.
- Do not overwrite `.env`, `db.sqlite3`, `media/`, or `.venv` during normal deploys.

## Local Startup

- Read `docs/local-runtime-contract.md` before starting, stopping, restarting, or debugging the local site.
- Keep the local site live for the owner during active UI/app work. Do not stop the Django server, tunnel, or launcher and leave the owner without a working test URL unless the owner explicitly asks you to stop it.
- Use `./run_mladis_live.command` from the repo root for the working local Django app. This is the only normal local startup path.
- Do not start MLADIS with ad hoc `python manage.py runserver`, `npm run dev`, `preview_*` scripts, `nohup`, or background shell servers during normal testing.
- Never tell the owner to use `http://0.0.0.0:8000`. `0.0.0.0` is a bind address, not the owner-facing MLADIS test URL.
- The launcher builds the React frontend into Django static assets by default, runs Django setup, stops stale Django processes on the same port, starts the stable `mladis-local` Cloudflare named tunnel, exports `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com`, then starts Django on `http://127.0.0.1:8000`.
- Use `https://local.mladis.com` for browser testing when Facebook sign-in matters. `http://127.0.0.1:8000` is the internal local Django origin and the Google/GitHub local callback origin.
- Do not test Django/allauth social sign-in through the Vite dev server at `http://127.0.0.1:5173`.
- If you must restart for migrations, static assets, env changes, or a broken server, restart through the same launcher immediately and verify `/healthz` before reporting back.
- Before any final response after local web work, confirm the owner has a live test URL, normally `http://127.0.0.1:8000` and, when the tunnel is healthy, `https://local.mladis.com`.
- If frontend preview servers are running in parallel, stop them before debugging auth so redirects and cookies stay easy to reason about.
- If the Google Drive checkout is slow or Git starts hanging on ignored files, create a fast clone under `~/Documents` or `~/Desktop`, copy only `airbnb_agent/.env` if needed, and use GitHub as the synchronization point.
- The local launcher caches dependency installs by `requirements.txt`, skips local `collectstatic` unless `MLADIS_COLLECTSTATIC=1`, builds frontend assets unless `MLADIS_BUILD_FRONTEND=0`, writes named-tunnel output to `/private/tmp/mladis-tunnel.log`, and defaults to a 60 second startup timeout.
- Before claiming local runtime is ready, run `airbnb_agent/scripts/check_local_runtime_contract.sh`.

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

- Read `docs/agent-admin-login.md` before using, changing, rotating, or debugging the dedicated automation/agent admin account.
- Provision automation or agent admin access as a dedicated Django user plus a matching `AdminAccess` record keyed to the same email; do not reuse owner credentials for routine automation.
- Use `bash airbnb_agent/scripts/ensure_agent_admin_credentials.sh` to create missing `MLADIS_AGENT_ADMIN_*` `.env` values, generate a hidden random password when needed, and provision the Django user/AdminAccess record.
- Use `python manage.py provision_agent_admin` only when the `.env` values already exist and you only need to refresh Django records.
- The one-file launcher and deploy flow are expected to run `ensure_agent_admin_credentials.sh`; if admin login fails, run that helper instead of asking the owner for a password or creating ad hoc users.
- For browser testing, log in at `/accounts/login/` or `/admin/` with `MLADIS_AGENT_ADMIN_EMAIL` as the stable identity; `MLADIS_AGENT_ADMIN_USERNAME` is only a preferred username and may be uniquified if it is already taken.
- Never ask the owner to know, invent, or type the agent admin password. Use the hidden runtime secret from `.env` only when automation needs to submit it, and never print, paste, screenshot, or commit it.
- For external systems such as Google Workspace, Google Cloud, Stripe, and PayPal, each dedicated automation identity should enroll its own MFA method; do not reuse the owner account's authenticator setup for automation access.
- Google Cloud owner grants for external automation identities can land as `roles/resourcemanager.projectOwnerInvitee`; treat that as a pending owner invitation and complete the mailbox acceptance step before assuming active owner access.
- PayPal business access is managed under Business Settings -> Manage Users; for full automation coverage, invite the account as an `Other user` and grant all permissions, then finish activation from the email invitation.

## Business Operations

- Use `docs/business/` as the private source of truth for MLADIS LLC formation facts, post-formation deadlines, and administrative records.
- Do not copy private legal addresses, government portal references, transaction IDs, tax IDs, bank details, or owner contact details from `docs/business/` into public frontend pages or customer emails.
- If app features need legal-business facts, model them explicitly behind admin-only access instead of reading directly from the Markdown docs.
- The current business goal is to make MLADIS LLC fundable for government programs, CDFIs, banks, SBA-backed lenders, grants, and later private investors. The active tracker is `docs/business/funding-readiness/`.
- When resuming bank, lender, CDFI, SBA, grant, investor, P&L, forecast, Airbnb export, or use-of-funds work, start with `docs/business/funding-readiness/financial-institution-resume-plan.md`; do not re-plan from scratch.
- Service/account/tool transfer work is deferred until the MLADIS web application is robust/completed. When resumed, start from `docs/business/services-and-costs-inventory.md`, implement exactly one service transfer at a time, and do not batch migrate, cancel, rotate, or reconfigure accounts without backup/export, smoke test, rollback notes, and evidence.
- After any business-formation, compliance, banking, bookkeeping, certification, grant, lender, investor, or government-funding work, update `docs/business/mladis-llc-next-steps.md` and the matching file under `docs/business/funding-readiness/`.
- Do not submit EIN, SAM.gov, grants, loans, bank accounts, certification applications, or investor materials without explicit owner approval in the current thread. Prepare packets and drafts; leave SSN, EIN, tax, bank, and identity fields for the owner or a secure official portal.
- Never commit reusable signature images, signature stamps, identity documents, EIN letters, SSNs, bank records, or tax returns. If the owner asks for help signing a document, require explicit per-document authorization and keep any reusable signature asset outside Git.
- For counterparty contracts, use the MLADIS-owned Dropbox Sign account under `garcp37@mladis.com`; do not fall back to typed `/s/` signatures as the final workflow when an e-sign request is practical.
- Do not send an e-sign request until every recipient email, signer name, and field assignment has been confirmed in the current thread or visible signing UI.
- Use `docs/business/signing/ready-for-signature-2026-06-03/` for the current branded signing files. If the docs are regenerated, use `docs/business/signing/scripts/generate_polished_signing_packet.py`, render the DOCX files to PDFs/page PNGs, scan generated DOCX/PDF text for stale placeholder language, inspect the rendered pages, and update the signing indexes before upload.
- Keep business-visitor and immigration-support work inside `docs/business/immigration/`; commit only blank templates, policy language, source links, and public-safe visit process notes. Completed visa-history answers, passport details, visa numbers, I-94 records, attorney advice, and similar sensitive materials stay outside Git or in encrypted/private storage.
- Use `docs/business/brand-assets/` as the source for official MLADIS brand/logo assets when preparing business packets, invoices, website assets, dashboards, pitch materials, or customer-facing MLADIS collateral. Do not replace these with placeholder logos when a suitable asset exists there.

## Deposit Operations

- Read `docs/environment-provider-contract.md` before changing Stripe, PayPal, OAuth provider secrets, local `.env`, or live runtime provider configuration.
- Keep Stripe and PayPal deposit lifecycle behavior aligned at the admin layer whenever practical.
- Preserve audit notes on `DamageDeposit.notes` when capturing or releasing a hold.
- Authorized deposits should require an explicit confirmation step before capture or release from the change page.
- If the public secure-deposit modal says Stripe is not configured, do not rewrite the booking flow. Confirm `airbnb_agent/.env` has `STRIPE_SECRET_KEY` set, use `airbnb_agent/scripts/configure_stripe_env.sh` if the owner needs a safe local prompt, and restart Django so settings reload.
- Use `MLADIS_AGENT_ADMIN_EMAIL` as the default outbound automation mailbox, normally `agent-admin@mladis.com`, for booking, payment, and admin notification email setup.
- For real inbox delivery, reuse stored `MLADIS_AGENT_EMAIL_PASSWORD`, `GMAIL_SMTP_APP_PASSWORD`, or `EMAIL_HOST_PASSWORD` from `.env`; do not ask the owner to redo SMTP setup if one of those secrets is already present.
- Do not treat `MLADIS_AGENT_ADMIN_PASSWORD` as the mailbox SMTP/app password. That value is for web-app login unless a separate provider setup explicitly says otherwise.
- If local email is still console-only, run `airbnb_agent/scripts/configure_email_env.sh`; it defaults to the agent mailbox and stores SMTP settings without printing secrets.
- Before claiming payment/provider setup is ready, run `airbnb_agent/scripts/check_provider_contract.sh`.

## Data Store Operations

- Treat the Django database as the transactional source of truth and the Drive-backed MLADIS data store as the JSON/JSONL export lake for analytics, recovery, agent learning, and audit work.
- Start from `docs/data-store/README.md` and `docs/data-store/drive-data-lake-contract.md` before changing subscriptions, bookings, requests, chatbot logs, payments, feedback, or analytics export behavior.
- Use `python manage.py export_data_lake --schema-only --include-placeholders --sync-drive` to create or refresh the Drive folder/catalog/schema skeleton.
- Use `python manage.py export_data_lake --sync-drive` when MLADIS operational records must be written to the configured Drive data store.
- Use `python manage.py export_data_lake --redacted --sync-drive` for analytics and agent-training experiments unless the task explicitly requires private contact fields.
- Do not commit generated JSONL exports, customer contact data, chatbot private messages, payment processor IDs, identity records, or raw production lake files. Keep generated exports in the protected Drive folder or another approved private storage target.
- The current Drive target is `https://drive.google.com/drive/folders/1ta4MMXH8gjO3-uIiYG9pEvgafEueVfmn`; keep `MLADIS_DATASTORE_DRIVE_FOLDER_ID` aligned with that folder unless the owner explicitly changes the storage location.
- Every functional customer, booking, request, payment, agent, invoice, promotion, cancellation, or admin-action object needs a data-store path. Prefer a transactional model plus export collection; add a live `object_events` JSONL log for lifecycle actions where possible.
- If `MLADIS_DATASTORE_ROOT` is configured, reservation and deposit workflows should append live object events without blocking the customer if the data-store write fails.

## Maintenance Operations

- Read `docs/maintenance-mvc-architecture.md` before adding or changing property maintenance, cleaning, repair, bill, photo-evidence, or maintenance-document automation.
- Do not raw-merge `feature/maintenance-events-mvc` into the current app. Transplant the maintenance domain into the current modern MLADIS branch so the modern frontend, admin shell, data lake, OAuth, payments, and deployment contracts are preserved.
- Maintenance work must model `MaintenanceEvent` as the aggregate root and `MaintenancePhoto` as child evidence records. The required core event attributes are title, cost, time, and pictures.
- Use the Django database as the maintenance source of truth, and export maintenance records/photos/document payloads through the Drive-backed JSON/JSONL data-store contract. Do not make Drive JSON files the live transaction database.
- Cleaning is a maintenance work type, not a separate ad hoc workflow, unless a later design explicitly creates a separate cleaning lifecycle.

## Calendar Operations

- The business calendar is managed from `BookableItem` admin via the custom calendar view, not from the legacy feed-setup page.
- Calendar availability combines active `BookingInquiry` records with manual `AvailabilityBlock` ranges.
- Nightly pricing shown in the calendar uses `BookableItem.starting_price` by default and overlays active `DailyPriceOverride` ranges when present.
- The calendar page includes a click-to-fill range helper that prefills both the block and price forms from selected days in the grid.
- The calendar grid also includes direct day-cell actions: `Block day`, `Price day`, and edit links to overlapping reservation, block, and price override records when present.
