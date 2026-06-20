# MLADIS Agent Notes

## Change Discipline

- Update repository documentation for any operator-facing workflow change.
- Update this file when repository-wide agent workflow expectations change.
- Prefer the smallest behavior-scoped test slice first, then widen only if the touched code path crosses a broader surface.

## Architecture Discipline

- OOP and MVC are mandatory for MLADIS. Treat them as the system bible, not as optional style.
- MLADIS is the umbrella intelligence platform, not only the current booking/vacation-rental product. Read `docs/architecture/0001-mladis-universe-neuron-model.md` before creating or reshaping Finance, Booking, Research, Education, Fitness, Portfolio, Pyramid, FairAgent, data-store, or cross-domain features.
- Treat the neuron pattern as the system architecture rule: `Neuron [uses: OtherNeuron] -> Neuron.SubNeuron -> Neuron.SubNeuron.Object -> Neuron.SubNeuron.Object.Specialization`.
- Use composition with `[uses: ...]` across neuron families. Use inheritance only when an object is truly a specialization inside the same family. Artifacts are not neurons.
- Model/domain objects own business state, identity, invariants, and rules. For example, every visitor must be represented through a user/session context object, whether anonymous or authenticated.
- Controllers coordinate the request/response flow, ask model/domain objects for decisions, and return explicit payloads. They must not bury business rules in templates or React components.
- Views/templates/components render the model state they receive. They must not invent parallel auth, agent, booking, payment, or permission state.
- Do not duplicate the same state across independent components. If the nav, booking form, and agent panel need login state, they must receive it from the same user/session model or controller payload.
- Agent access must be modeled as an `AgentInstance` attached to a user/session context. The UI asks the backend controller for the current context and renders from that object.
- Any shortcut that directly checks loose booleans in multiple views instead of using the shared model/context is a bug, even if the screen appears to work.
- When fixing regressions, repair the model/controller boundary first, then simplify the view. Do not stack UI patches over a broken state model.
- Read `docs/engineering/oop-mvc-contract.md` before changing login/logout, agent access, bookings, payments, reservations, customer accounts, or admin workflows.
- The current `bookings/` Django app is the first Booking branch implementation. Do not hard-code MLADIS as only a booking company in architecture docs, funding docs, or reusable domain code. Product copy can describe the active booking product; system architecture should preserve MLADIS as the broader universe.
- Read `docs/architecture/0003-gentelella-v4-full-site-rebrand.md` before broad frontend, admin, public-site, mobile, dashboard, or theme work. Gentelella v4 is the selected View-system reference only; do not move MLADIS domain rules into CSS, templates, or React page components, and do not show framework names such as Gentelella, Django, React, or Vite in customer/operator UI copy unless the owner explicitly asks.

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
- The launcher defines the local runtime from exactly two variables: `MLADIS_LOCAL_DOMAIN` and `MLADIS_PORT`. Defaults are `127.0.0.1` and `8000`; `MLADIS_LOCAL_ORIGIN` is derived from those values and must not be hardcoded elsewhere.
- The launcher builds the React frontend into Django static assets by default, runs Django setup, stops stale Django processes on the configured port, starts the stable `mladis-local` Cloudflare named tunnel, exports `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com`, then starts Django on the derived local origin, normally `http://127.0.0.1:8000`.
- Use `https://local.mladis.com` for browser testing when Facebook sign-in matters. The derived local origin is the internal local Django origin and the Google/GitHub local callback origin.
- Do not test Django/allauth social sign-in through the Vite dev server at `http://127.0.0.1:5173`.
- If you must restart for migrations, static assets, env changes, or a broken server, restart through the same launcher immediately and verify `/healthz` before reporting back.
- Before any final response after local web work, confirm the owner has a live test URL, normally `http://127.0.0.1:8000` and, when the tunnel is healthy, `https://local.mladis.com`.
- Do not run a second MLADIS service on port `8010` during normal work. That old rebrand-preview path is retired; test the active app through the canonical launcher and configured local port.
- Do not create or keep separate repo copies, `.env` copies, or service copies for different local ports. OAuth credentials belong in the canonical `airbnb_agent/.env`, and `sync_socialapps` must recreate provider rows from that file. If social login regresses, check that `.env` and `SocialApp` sync first; do not create another port-specific runtime.
- On this Mac, the active fast local checkout is `/Users/pitergarcia/Desktop/MLADIS-deploy-rebrand`. Treat the older Google Drive checkout as a legacy/reference checkout unless the owner explicitly says to work there.
- Never guess where OAuth/payment/email secrets are. The source-of-truth order is: canonical `airbnb_agent/.env`, then an owner-approved secret manager or provider dashboard, then a prior working local database only as a last-resort recovery source. Never print recovered secrets.
- If social login says providers are unavailable, do not edit UI copy first. Confirm `.env` contains provider credentials with boolean/length-only checks, run `python manage.py sync_socialapps`, restart through `./run_mladis_live.command`, and only then inspect templates.
- If frontend preview servers are running in parallel, stop them before debugging auth so redirects and cookies stay easy to reason about.
- If the Google Drive checkout is slow or Git starts hanging on ignored files, create a fast clone under `~/Documents` or `~/Desktop`, copy only `airbnb_agent/.env` if needed, and use GitHub as the synchronization point.
- The local launcher caches dependency installs by `requirements.txt`, skips local `collectstatic` unless `MLADIS_COLLECTSTATIC=1`, builds frontend assets unless `MLADIS_BUILD_FRONTEND=0`, writes named-tunnel output to `/private/tmp/mladis-tunnel.log`, and defaults to a 60 second startup timeout.
- Before claiming local runtime is ready, run `airbnb_agent/scripts/check_local_runtime_contract.sh`.

## Sign-In Contract

- Read `docs/sign-in-contract.md` before changing auth settings, allauth provider config, login/signup templates, OAuth middleware, or social launch routes.
- Run `bash airbnb_agent/scripts/test_signin_contracts.sh` before committing or pushing any sign-in change.
- Keep `SOCIAL_AUTH_CANONICAL_ORIGIN` empty during mixed local testing; use provider-specific origins instead.
- Keep Google and GitHub local callbacks aligned with the derived local origin, normally `http://127.0.0.1:8000`.
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
- The runtime object lake must stay simple and human-readable: `BOOKINGS`, `CUSTOMERS`, `BOOKINGAGENTS`, `TRANSACTIONS`, `STAYS`, `MAINTENANCE`, `WEBSITE`, `ADMIN`, `EVENTS`, and `EXPORTS`.
- Do not use `year/month/day`, `bronze`, `silver`, or other warehouse-style partitions for live business object state. Current object state belongs in `<FOLDER>/<model>-<id>.json`; change history belongs in `<FOLDER>/_history.jsonl`.
- Use `python manage.py export_data_lake` to refresh local collection snapshots such as `CUSTOMERS/customer_profiles.jsonl` and `BOOKINGS/booking_requests.jsonl`.
- Use `python manage.py export_data_lake --sync-drive` only when MLADIS operational records must be mirrored to the configured Drive data store.
- Use `python manage.py export_data_lake --redacted --sync-drive` for analytics and agent-training experiments unless the task explicitly requires private contact fields.
- Do not commit generated JSONL exports, customer contact data, chatbot private messages, payment processor IDs, identity records, or raw production lake files. Keep generated exports in the protected Drive folder or another approved private storage target.
- The current Drive target is `https://drive.google.com/drive/folders/1ta4MMXH8gjO3-uIiYG9pEvgafEueVfmn`; keep `MLADIS_DATASTORE_DRIVE_FOLDER_ID` aligned with that folder unless the owner explicitly changes the storage location.
- Every functional customer, booking, request, payment, agent, invoice, promotion, cancellation, maintenance, calendar, content, or admin-action object needs a transactional model and a live data-store path.
- If `MLADIS_DATASTORE_ROOT` is configured, relevant model saves/deletes must update the simple object JSON file and append the folder's `_history.jsonl`; this is the object-state contract for OOP/MVC recoverability.
- Workflow actions should also append focused `<FOLDER>/_events.jsonl` rows for business events such as checkout-created, email-sent, provider-failed, or request-created.
- If `MLADIS_DATASTORE_LIVE_SYNC_DRIVE=True`, touched live JSONL files are mirrored to the configured Drive folder ID. Keep `MLADIS_DATASTORE_LIVE_SYNC_ASYNC=True` for request paths so Drive latency cannot freeze bookings or admin work. Git is never the production data lake; it stores code, schemas, and contracts only.
- Data-store writes must never block or break the customer/admin transaction path if the local file or Drive mirror fails.

## Maintenance Operations

- Read `docs/maintenance-mvc-architecture.md` before adding or changing property maintenance, cleaning, repair, bill, photo-evidence, or maintenance-document automation.
- Do not raw-merge `feature/maintenance-events-mvc` into the current app. Transplant the maintenance domain into the current modern MLADIS branch so the modern frontend, admin shell, data lake, OAuth, payments, and deployment contracts are preserved.
- Maintenance work must model `MaintenanceEvent` as the aggregate root and `MaintenancePhoto` as child evidence records. The required core event attributes are title, cost, time, and pictures.
- Use the Django database as the maintenance source of truth, and export maintenance records/photos/document payloads through the Drive-backed JSON/JSONL data-store contract. Do not make Drive JSON files the live transaction database.
- Cleaning is a maintenance work type, not a separate ad hoc workflow, unless a later design explicitly creates a separate cleaning lifecycle.

## Ops Page Building Pattern

Follow this pattern when building or extending any ops page (Customers, Properties, Guests, Payments, Deposits, Reservations, or any future `/ops/*` route). **Reservations is the next page being built after Properties, Guests, Payments, and Deposits.**

### File roles
- **`bookings/views.py`** — add a CBV (TemplateView) protected by `@method_decorator(ops_staff_required, name="dispatch")`. The view calls the service, decorates the payload, and passes context to the template. Business rules live here, not in the template.
- **`bookings/services.py`** — add a dedicated service class (e.g. `CustomersCRMService`, `ReservationsCRMService`). Expose `mock_*` methods that return hard-coded sensible data while real DB queries are not yet wired, and real `table_row_payload` / `detail_payload` methods once models carry the data.
- **`bookings/templates/bookings/modern_ops_<page>.html`** — one template per page; extends `bookings/base_ops.html` and imports a single scoped CSS file with a versioned query-string (`?v=<page>-vN`).
- **`bookings/static/frontend/modern-dashboard/assets/ops-<page>.css`** — all styles for that page, namespaced with a page-specific BEM prefix (e.g. `.ops-cx-*` for Customers, `.ops-rsv-*` for Reservations, `.ops-gst-*` for Guests) to prevent bleed across pages.

### Real-data-first contract
- Every ops page must be a functional MVC page, not a static picture of a mock. The Django view calls a page service; the service queries real transactional models first; the template renders the service payload; scoped CSS only styles that payload.
- Mock data is allowed only as fallback or filler when the real data set cannot yet populate the complete mock layout. Never replace available database records with mock records just to match a screenshot.
- Services must keep the boundary obvious: real queryset methods, payload builders, and `mock_*` fallback methods belong in `bookings/services.py`. Templates must not invent fake state, fake counts, fake selections, or fake links.
- Buttons, row selections, detail panels, admin links, API exports, and empty states must remain functional even when some cards use mock fallback rows.
- Guests, Payments, Properties, and the current Maintenance page are the reference implementation style. New pages such as FairAgent must follow the same service/view/template/scoped-CSS pattern.

### CSS discipline
- Bump the version suffix (`?v=<page>-vN` → `vN+1`) on the CSS `<link>` in the template every time the CSS file changes to force a hard browser refresh.
- Use `table-layout: fixed` with a `<colgroup>` block (inline `style="width:..."` on each `<col>`) for all ops tables — this is the only reliable way to pin column widths across browsers. CSS-only `thead th` width rules can silently lose to `table-layout: auto` fallback.
- Use `display: flex` (not grid) on the main layout container when the sidebar needs a smooth `flex-basis` width transition.

### Sidebar (FairAgent) pattern
- Layout: `display: flex; gap: 16px` on `.ops-<page>-layout`. Main column: `flex: 1; min-width: 0`. Sidebar: `flex: 0 0 44px` (collapsed) / `flex: 0 0 320px` (open), with `transition: flex-basis 0.25s ease, width 0.25s ease`.
- Default state: collapsed (44px strip showing only the ✦ icon). Never open by default — the IntersectionObserver approach causes always-open bugs when the target card is always in the viewport.
- JS triggers: `mouseenter` opens, `mouseleave` closes (unless pinned). A specific element click (e.g. a Messages tab or compose input) sets `isPinned = true`; a `document` click outside the sidebar sets `isPinned = false` and closes. Use `e.stopPropagation()` on pinning triggers to prevent the document handler from immediately unpinning them.

### Collapsible sections pattern
- Use native `<details>`/`<summary>` — no JS needed. Default closed (`<details>`); add the `open` attribute for sections that should start expanded.
- Summary layout: `display: flex; justify-content: space-between` with a chevron `▾` that rotates 180° via `details[open] .chevron { transform: rotate(180deg) }`.
- Scrollable body: wrap list content in a `<div class="...scroll">` inside `<details>` with `max-height: Xpx; overflow-y: auto; scrollbar-width: thin`.

### Commit discipline
- Commit once each major artifact is complete and verified: view, template, CSS, and service are each a natural commit boundary.
- Commit message format: `ops/<page>: <what was done>` (e.g. `ops/customers: add collapsible Last Stays and Linked Reservations`).
- Push after each page reaches a stable, visually verified state. Do not accumulate multiple pages' work in one push.

### Payments and Deposits contract
- Payments and Deposits are separate ops pages and separate sidebar routes. Never point one nav item at the other's URL.
- Payments composes its page from the shared transactional objects: `Invoice`, `ReservationPaymentHold`, and `DamageDeposit`.
- Deposits remains the hold/deposit ledger page centered on `DamageDeposit` records.
- The two pages must cross-link: Payments should expose the related deposits ledger for a transaction, and Deposits should remain the canonical place to inspect or act on hold/deposit records.

## Calendar Operations

- The business calendar is managed from `BookableItem` admin via the custom calendar view, not from the legacy feed-setup page.
- Calendar availability combines active `BookingInquiry` records with manual `AvailabilityBlock` ranges.
- Nightly pricing shown in the calendar uses `BookableItem.starting_price` by default and overlays active `DailyPriceOverride` ranges when present.
- The calendar page includes a click-to-fill range helper that prefills both the block and price forms from selected days in the grid.
- The calendar grid also includes direct day-cell actions: `Block day`, `Price day`, and edit links to overlapping reservation, block, and price override records when present.

## Left Navigation — Single Source of Truth

**ABSOLUTE RULE: THE OPS LEFT NAV IS DATA-DRIVEN. DO NOT HAND-COPY OR HAND-EDIT MENU ARRAYS.**

Every ops page — whether Django-rendered or React — must show the same left navigation menu with the same labels in the same order linking to the same URLs. There is one canonical nav object.

### Canonical Source

The canonical nav object is **`bookings/ops_navigation.py::OPS_NAV_ITEMS`**.

That Python object feeds:
- `base_ops.html` through the `ops_nav_items` context value.
- React pages through the `ops_nav_public_items|json_script:"mladis-ops-nav-items"` runtime JSON embedded in `modern_dashboard.html`.
- The Stays command grid through the same `mladis-ops-nav-items` runtime JSON embedded by `base_ops.html`.

If you need to change the left navigation, change `OPS_NAV_ITEMS` first. Then update the TypeScript fallback in `frontend/src/ui/opsNavigation.ts` only so local Vite/dev mode still works without Django-rendered JSON.

### Runtime Consumers

| Consumer | File | Rule |
|---|---|---|
| **Django sidebar** | `bookings/templates/bookings/base_ops.html` | Render from `ops_nav_items`. Do not add a new hardcoded sidebar list. |
| **React sidebar** | `frontend/src/ui/components/DashboardLayout.tsx` via `frontend/src/ui/opsNavigation.ts` | Consume `OPS_NAV_ITEMS`. Do not create a local `navItems` array. |
| **Admin shortcuts** | `frontend/src/ui/pages/AdminPage.tsx` via `frontend/src/ui/opsNavigation.ts` | Consume `OPS_NAV_ITEMS`. Do not create a local shortcuts nav list. |
| **Stays command grid** | `bookings/static/frontend/modern-dashboard/assets/ops-stays-command.js` | Read `mladis-ops-nav-items`; fallback list is only for emergency/no-Django contexts. |
| **Compiled React bundle** | `bookings/static/frontend/modern-dashboard/assets/app.js` | Generated by `npm run build:django`; do not patch this as the only source of truth. |

### Canonical Nav — This Is The Only Truth

| # | Label | URL | Notes |
|---|---|---|---|
| 1 | Dashboard | `/ops/dashboard/` | React app |
| 2 | Reservations | `/ops/reservations/` | React app |
| 3 | Calendar | `/ops/calendar/` | React app |
| 4 | Stays | `/ops/stays/` | Django (`modern_ops_stays.html`) |
| 5 | Maintenance | `/ops/maintenance/` | React app |
| 6 | Payments | `/ops/payments/` | Django (`modern_ops_payments.html`) |
| 7 | Deposits | `/ops/deposits/` | React app |
| 8 | Reports | `/ops/reports/` | React app |
| 9 | Agent Intelligence | `/ops/agent/` | React app |
| 10 | Listings | `/ops/listings/` | React app |
| 11 | Customers | `/ops/customers/` | Django (`modern_ops_customers.html`) |
| 12 | Tasks | `/ops/workboard/` | React app |
| 13 | Settings | `/ops/settings/` | React app |
| 14 | Users | `/ops/admin/` | React app |

**If a label or URL is changed, it must be changed in all three sources in the same commit. No partial updates.**

**Current architecture note:** the runtime source is now centralized in `OPS_NAV_ITEMS`, but agents must still update the TypeScript fallback in the same commit when changing `OPS_NAV_ITEMS`, then rebuild the shipped bundle.

### Rules (Non-Negotiable)

1. **Never create a new hardcoded left-nav array in a page/component/template. Import or render the canonical object.**
2. **Never change nav labels or URLs in `app.js` only. Change `OPS_NAV_ITEMS`, update the TypeScript fallback, rebuild, and commit all outputs together.**
3. **Never add or remove a nav item in only one consumer. The Django runtime object, TypeScript fallback, Stays fallback, and docs must stay aligned.**
4. **Payments always -> `/ops/payments/`. Deposits always -> `/ops/deposits/`. These are separate pages with separate routes. Never conflate them.**
5. **Every URL in the canonical nav must have a route in `urls.py`. Missing routes = 404 = bug to fix immediately.**
6. **If the browser shows different left menus between `/ops/dashboard/` and `/ops/payments/`, stop and fix nav parity before doing any visual work.**

### How to Patch Each Source

**`bookings/ops_navigation.py`** — edit `OPS_NAV_ITEMS`. This is the canonical source.

**`frontend/src/ui/opsNavigation.ts`** — mirror the same item set in `fallbackOpsNavItems` for local dev mode. The normal Django-rendered app reads `mladis-ops-nav-items` at runtime.

**`app.js`** — rebuild with `npm run build:django` from `frontend/`. If and only if a production hotfix requires direct compiled-bundle patching, still backport the same change to `OPS_NAV_ITEMS` and `frontend/src/ui/opsNavigation.ts` before committing.

**`ops-stays-command.js`** — this reads `mladis-ops-nav-items` first. Its `fallbackModules` exists only for no-Django/emergency contexts and must mirror `OPS_NAV_ITEMS`.

### Verifying Nav Parity

After any nav change:
1. Load `/ops/dashboard/` → expand the sidebar → confirm labels match canonical table above.
2. Load `/ops/payments/` → expand the sidebar → confirm same labels.
3. Load `/ops/stays/` → confirm the quick-launch grid matches.
4. Run `python manage.py check` from `airbnb_agent/` and `npm run build:django` from `frontend/`.

### `ops-stays-command.js`
A third nav-like list lives in `ops-stays-command.js` (the `/ops/stays/` command-center IIFE). The `modules` array in this file is kept in sync with the canonical nav above. The descriptions and colors may differ from the sidebar — only the Label and URL must match exactly.

### Invariant
**Payments must always route to `/ops/payments/`; Deposits must always route to `/ops/deposits/`. These must agree across all three sources: `base_ops.html`, `app.js`, and `ops-stays-command.js`.** Any agent that changes a payments or deposits route must update all three sources in the same commit.


## Payments page — additional contracts

- The Payments table has **11 columns**: checkbox, Transaction ID, Guest, Reservation, Listing, Channel, Method, Date, Amount, Status, Invoice.
- The Invoice column renders a `↗` chip link (`ops-pay-invoice-link`) that opens the invoice-print URL without interrupting row-click selection (`event.stopPropagation()`). Width is fixed at 4% via `<col class="ops-pay-col-invoice">`.
- The detail rail is fixed at `300px` wide (`flex: 0 0 300px`).
- **NEVER add a script to force the sidebar open on any ops page.** The global rule (line "Default state: collapsed…") applies to every page including Payments. Adding `is-sidebar-expanded` / `is-expanded` via an inline script is forbidden.

## Payments page — design reference

The approved mock image is committed at **`docs/design/mocks/payments-page-mock.png`**.
All future visual work on the Payments page MUST reference this file.

When the user provides a mock image (any page), agents MUST:
1. Copy the image to `docs/design/mocks/<page-name>-mock.png` in the same commit as the visual work.
2. Update AGENTS.md with a "design reference" section pointing to the saved file.
3. Never stop working until the live page matches the mock — do not "clap and stop" early.

### Payments page visual spec (from mock)
- **Topbar**: hamburger · search · `+ New ▾` · bell · calendar · user avatar+name+role
- **Header right**: 📅 date-range `▾` · filter-funnel Filters · ↓ Export
- **KPI cards**: 4 cards, each has a 36px colored rounded-square icon (white SVG inside) + label + value + trend; sparkline wave path at bottom
- **Filter bar**: `All Channels ▾` `All Statuses ▾` 📅 `Jun 6 – Jun 12, 2026 ▾` `All Methods ▾` `Clear filters` (plain text, no border) · 🔍 search right-aligned
- **Table**: 11 cols; selected row highlighted; `↗` invoice chip
- **Pagination**: `‹ 1 2 3 … 13 ›`
- **Detail panel (300px)**: ✕ close · TXN-ID + status badge inline · amount USD · "Total Paid" · Invoice Preview (thumbnail + #number + Paid badge + issue/due/amount-due rows + Download invoice btn) · Linked Reservation (R-xxx ↗ + "View reservation" btn) · Deposit History | Quick Actions (two-column grid, "Edit" link, "Send invoice"/"Mark as paid" actions) · Payment Timeline (dots + action links) · Notes ("Add note" link)
