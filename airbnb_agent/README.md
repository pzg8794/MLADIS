# MLADIS Booking Agent

Django scaffold for the MLADIS booking website and future customer agent.

The app starts with three Santo Domingo Airbnb listings, direct admin-confirmed
reservation requests, customer accounts, coupons, client segmentation, invoices,
promotion emails, admin-test reservations, admin-managed site content/logo/rules,
a $200 Stripe authorization hold, mission donations, Airbnb image galleries,
review highlights, owner analytics, admin-only calendar setup, and an agent API
boundary that can later connect to live booking logic.

## Local Run

From the parent `MLADIS` folder, use the one-file launcher:

```bash
./run_mladis_live.command
```

The launcher uses `airbnb_agent/.env`, creates or reuses `.venv`, installs
requirements when `requirements.txt` changes, runs migrations, syncs OAuth
apps, runs Django checks, starts `http://127.0.0.1:8000`, and starts a
temporary Cloudflare tunnel when `cloudflared` is installed. The tunnel URL can
be used for live demos without going through Google Cloud.

Useful options:

```bash
MLADIS_PUBLIC_TUNNEL=0 ./run_mladis_live.command
MLADIS_CHECK_ONLY=1 ./run_mladis_live.command
MLADIS_SERVER=gunicorn ./run_mladis_live.command
MLADIS_FORCE_INSTALL=1 ./run_mladis_live.command
MLADIS_COLLECTSTATIC=1 ./run_mladis_live.command
MLADIS_STARTUP_TIMEOUT=120 ./run_mladis_live.command
```

For repeated development, local `collectstatic` is skipped unless
`MLADIS_COLLECTSTATIC=1`. Production deploy still collects static files through
the deployment script.

Manual local setup is still available:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Visit `http://localhost:8000`.

## Sign-In Contract

Social sign-in is protected by a local and GitHub CI contract. Before changing
OAuth settings, allauth provider settings, login/signup templates, OAuth
middleware, or social launch routes, run:

```bash
bash scripts/test_signin_contracts.sh
```

Use `http://127.0.0.1:8000` for auth testing. Do not test Django/allauth login
through the Vite dev server at `http://127.0.0.1:5173`.

The full contract is documented in
[../docs/sign-in-contract.md](../docs/sign-in-contract.md).

## Deployment

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Required environment variables: `SECRET_KEY`, `ALLOWED_HOSTS`
- Optional environment variables: `OPENAI_API_KEY`, `OPENAI_AGENT_MODEL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- Email variables: `DEFAULT_FROM_EMAIL`, `BOOKING_INQUIRY_RECIPIENTS`, `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`
- Deposit settings: `DEPOSIT_AMOUNT_CENTS=20000`, `DEPOSIT_CURRENCY=usd`
- Donation setting: `DONATION_CURRENCY=usd`
- Health check path: `/healthz`

## Current Live VM Deployment

The current public test site runs on one Google Compute Engine VM instead of
Cloud Run.

- Project: `mledis`
- VM: `mladis-test-1`
- Zone: `us-central1-a`
- Domain: `https://mladis.com/`
- systemd app service: `mladis`
- Reverse proxy/TLS: `caddy`
- Remote app directory: `/home/pitergarcia/airbnb_agent`

For normal code updates, use the root-level `./deploy_mladis_vm.command`.
That command packages `airbnb_agent/`, uploads it to the VM, creates a runtime
backup, installs requirements, runs `migrate`, `sync_socialapps`,
`provision_agent_admin`, `collectstatic`, `check`, and restarts `mladis`.

The deploy path is intentionally non-destructive by default. It preserves the
live `.env`, `.venv`, `db.sqlite3`, and `media/`. Enable remote prune only when
you explicitly want stale code files removed.

Full runbook: [../docs/live-vm-deployment.md](../docs/live-vm-deployment.md)

## Optimal Google Cloud Production

The correct production shape for this app on Google Cloud is:

- Cloud Run for the web service
- Cloud SQL Postgres for relational data
- Cloud Storage for `media/` uploads
- Secret Manager for secrets and database passwords

Recommended configuration:

- Use `CLOUDSQL_CONNECTION_NAME`, `DATABASE_NAME`, `DATABASE_USER`, and `DATABASE_PASSWORD` for the primary database.
- Use `GCS_MEDIA_BUCKET` for media storage so uploaded files do not live on the Cloud Run container filesystem.
- Keep WhiteNoise for collected static files baked into the deployed container image.
- Run exactly one migration step per release before or during deployment orchestration.

Google Cloud prerequisites:

- Billing must be enabled on the target GCP project before Cloud Run, Cloud SQL, and Secret Manager services can be activated.
- The Cloud Run service account needs database access and write access to the media bucket.

## Pilot Hosting With SQLite

If you want the fastest low-risk pilot before advertising, keep the app on one
VM and let exactly one running instance write to SQLite.

- Use SQLite only on a single machine with a persistent disk.
- Treat `db.sqlite3` and `media/` as the runtime state that must be backed up.
- Keep Git for code only. Do not use branches or commits as the live booking database.
- Create a point-in-time snapshot with `bash scripts/backup_runtime_state.sh`.
- Restore a snapshot only while the app is stopped with `bash scripts/restore_runtime_state.sh <archive.tar.gz>`.
- Copy the generated tarballs off the VM on a schedule if you want disaster recovery.

This works for a short pilot. The moment you need more than one app instance,
more frequent writes, or stronger operational safety, move to Postgres.

The website agent uses the OpenAI Responses API when `OPENAI_API_KEY` is set.
It persists guest questions, topics, replies, and OpenAI response metadata in
`AgentConversation` so admins can review what guests ask and improve the agent
knowledge over time. Without a key, it falls back to setup-mode replies.

## Admin Access And Social Login

- Seeded owner/admin access: `Piter Garcia <garciapiterz@gmail.com>`, business phone `631-575-4841`.
- Seeded admin access: `Diana Garcia <garciabdianas@gmail.com>`.
- Optional automation/agent admin access is provisioned from `.env` by `python manage.py provision_agent_admin`.
- Set `MLADIS_AGENT_ADMIN_EMAIL`, `MLADIS_AGENT_ADMIN_NAME`, `MLADIS_AGENT_ADMIN_PHONE`, `MLADIS_AGENT_ADMIN_USERNAME`, and optionally `MLADIS_AGENT_ADMIN_PASSWORD`. If no password is set, the user is created for social-login automation only.
- Any password, Google, Facebook, Microsoft, or GitHub login with that email is promoted to staff/superuser by the `AdminAccess` table.
- Manual `AdminAccess` entries in `/admin/` also work immediately on the current live database.
- Local test user created for this workspace: username `piter`. Change the password in `/admin/` before sharing or deploying.
- Social providers are scaffolded with django-allauth. By default, `.env` is the source of truth for Google, Facebook, Microsoft, and GitHub credentials; set `SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK=True` only if you intentionally want `/admin/socialaccount/socialapp/` rows to enable providers without matching env vars.
- Environment-based setup auto-syncs `SocialApp` records for the current `SITE_ID` when the login/signup page loads or a provider login starts.
- Local env variables: `SITE_DOMAIN`, `SITE_NAME`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `USE_X_FORWARDED_PROTO`, `ACCOUNT_DEFAULT_HTTP_PROTOCOL`, `SOCIAL_AUTH_ALLOW_ADMIN_FALLBACK`, `SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS`, `SOCIAL_AUTH_CANONICAL_ORIGIN`, `SOCIAL_AUTH_GOOGLE_ORIGIN`, `SOCIAL_AUTH_FACEBOOK_ORIGIN`, `SOCIAL_AUTH_MICROSOFT_ORIGIN`, `SOCIAL_AUTH_GITHUB_ORIGIN`, `MLADIS_AGENT_ADMIN_EMAIL`, `MLADIS_AGENT_ADMIN_NAME`, `MLADIS_AGENT_ADMIN_PHONE`, `MLADIS_AGENT_ADMIN_USERNAME`, `MLADIS_AGENT_ADMIN_PASSWORD`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `FACEBOOK_OAUTH_CLIENT_ID`, `FACEBOOK_OAUTH_CLIENT_SECRET`, `FACEBOOK_OAUTH_SCOPE`, `MICROSOFT_OAUTH_CLIENT_ID`, `MICROSOFT_OAUTH_CLIENT_SECRET`, `MICROSOFT_OAUTH_TENANT`, `MICROSOFT_OAUTH_LOGIN_URL`, `MICROSOFT_GRAPH_URL`, `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`.
- Keep provider callback URLs aligned with the provider-specific origin vars. For example, use `SOCIAL_AUTH_GOOGLE_ORIGIN=http://127.0.0.1:8000` and `SOCIAL_AUTH_GITHUB_ORIGIN=http://127.0.0.1:8000` locally, while `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://<active-tunnel>.trycloudflare.com` gives Facebook the HTTPS callback it requires.
- `SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS=microsoft` hides Microsoft from the login/signup UI until its client ID and secret exist.
- `SOCIAL_AUTH_CANONICAL_ORIGIN` is now only a fallback. Leave it empty for mixed local testing so Google/GitHub do not inherit the temporary Facebook tunnel origin.
- Microsoft local callback URL for Azure App Registration: `http://127.0.0.1:8000/oauth/microsoft/login/callback/`. Use `MICROSOFT_OAUTH_TENANT=common` for consumer + work accounts, `organizations` for work/school accounts, or the tenant ID if your Azure app is single-tenant.
- Keep `ACCOUNT_DEFAULT_HTTP_PROTOCOL=http` for plain local `127.0.0.1` logins. When requests come through Cloudflare Tunnel, `USE_X_FORWARDED_PROTO=True` lets Django/allauth keep the tunnel callback on `https` without forcing local callbacks to `https`.
- Facebook local development needs an HTTPS callback. A quick tunnel such as Cloudflare Tunnel works with `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://<active-tunnel>.trycloudflare.com`, `SITE_DOMAIN=127.0.0.1:8000`, `ALLOWED_HOSTS=localhost,127.0.0.1,.trycloudflare.com`, `CSRF_TRUSTED_ORIGINS=https://*.trycloudflare.com`, and `USE_X_FORWARDED_PROTO=True`.
- For the current Meta app, `FACEBOOK_OAUTH_SCOPE=public_profile` is the working local default. If Meta later approves `email`, update the scope to `public_profile,email` and re-save the active tunnel callback URL plus app domain in Meta.
- Meta basic settings can use the new public policy pages in this app: `https://<current-host>/privacy/` and `https://<current-host>/terms/`. For Facebook data deletion, use the callback URL option with `https://<current-host>/data-deletion/callback/`; the human-facing instructions page stays at `https://<current-host>/data-deletion/`. For the current Cloudflare tunnel, replace `<current-host>` with the active `.trycloudflare.com` hostname before saving the fields in Meta.

## Damage Deposit Flow

Guests start booking first, then the site opens the secure deposit step. The
deposit flow uses Stripe Checkout with manual capture, so MLADIS can authorize the
$200 damage deposit without capturing it immediately. Stripe displays eligible safe
payment methods from the Stripe account configuration; methods that cannot support a
hold may not appear.

Webhook endpoint:

```txt
/stripe/webhook/
```

## Initial Airbnb Listings

- `588632365342578374`: 6 Bedrooms Vacation Home & Pool, 4.69 rating, 26 reviews, 6 bedrooms, 8 beds, 4 private baths
- `587194328968598250`: 3 Bedrooms Vacation Home & Pool G-102, 4.88 rating, 24 reviews, 3 bedrooms, 4 beds, 2 private baths
- `582161420407543691`: 3 Bedrooms Vacation Home & Pool G-101, 4.93 rating, 42 reviews, 3 bedrooms, 4 beds, 2 private baths

## Marketing Pages

- `/` is the travel-forward homepage with stay cards, Airbnb-hosted images, review proof, booking, deposit, mission, and agent sections.
- `/stays/<slug>/` gives every stay its own page with hero image, gallery, review summary, guest highlights, apartment rules in a book layout, and booking form with the agent on the left.
- `/about/` sells the Dominican Republic/Santo Domingo Norte travel story and includes Stripe donation checkout plus an agent panel.
- `/accounts/` lets customers see and manage their reservation requests and invoices.
- `/ops/dashboard/` gives staff reservation, cancellation, inquiry, visit, and agent-question analytics.
- `/ops/calendar/` is staff-only and supports the v1 manual Airbnb iCal setup path for Google Calendar.

## Admin Workflow

- Use `/admin/` to manage stays, galleries, guest highlights, rules, coupons,
  cancellation policies, customer profiles, invoices, extra bill templates,
  promotions, donations, deposits, admin access, logo/site settings, and content blocks.
- Booking requests are emailed to `BOOKING_INQUIRY_RECIPIENTS` and stored in admin.
- Admin-test reservations can be created by staff from the public booking form
  and are recorded with zero cost.
- Promotions can target all clients or favorite/VIP/average/blacklisted segments.
- Airbnb guest history can be imported repeatedly from Gmail-export JSON/CSV files with
  `python manage.py import_airbnb_guests imports/airbnb-guests.json`. Imported Airbnb
  contacts default to unknown marketing consent and are excluded from promotion sends until
  an admin marks them opted in.
- Staff can visit `/ops/oauth/` to see the exact social-login callback URLs that must be
  allow-listed in Google, Facebook, GitHub, and Microsoft app dashboards.
