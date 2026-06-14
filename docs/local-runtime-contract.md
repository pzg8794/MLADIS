# MLADIS Local Runtime Contract

This contract exists because MLADIS local testing depends on stable origins for OAuth, payments, cookies, CSRF, and browser redirects. Agents must not invent alternate ways to run the app.

## Canonical Command

Run the app from the repository root:

```bash
./run_mladis_live.command
```

This is the only normal local startup path.

## Canonical URLs

The launcher creates one Django app instance with two testing URLs:

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:8000` | Internal local Django origin. Use for fast local checks and Google/GitHub local callbacks. |
| `https://local.mladis.com` | Stable public local tunnel. Use for Facebook login, OAuth flows requiring HTTPS, Stripe/PayPal redirect testing, and owner browser testing. |

These are not two different apps and not two different startup methods. They must point to the same running Django process.

## Single Local Origin Rule

Local domain and port are defined once by the launcher:

```bash
MLADIS_LOCAL_DOMAIN=127.0.0.1
MLADIS_PORT=8000
MLADIS_LOCAL_ORIGIN=http://$MLADIS_LOCAL_DOMAIN:$MLADIS_PORT
```

Agents may override `MLADIS_LOCAL_DOMAIN` or `MLADIS_PORT` only for an explicit owner-approved exception. Do not set or hardcode a separate local origin. Do not run the old `8010` preview service during normal work.

## No Port-Specific Copies

Do not create duplicate MLADIS checkouts, duplicate `.env` files, or duplicate services just to test a different port or preview branch. That creates OAuth drift: one runtime can have working provider credentials while another silently falls back to empty/example credentials.

The canonical rule is one active local Django service, one canonical `airbnb_agent/.env`, one launcher path, and one stable HTTPS tunnel mapped to that same service.

If social sign-in shows disabled providers, first verify the canonical `.env` and run `python manage.py sync_socialapps`. Do not change templates, create another checkout, or start a second port until the credential source has been checked.

## Canonical Local Checkout

On this Mac, the active fast checkout is:

```txt
/Users/pitergarcia/Desktop/MLADIS-deploy-rebrand
```

Run local MLADIS from that checkout unless the owner explicitly tells you to switch. The older Google Drive checkout is a legacy/reference checkout and must not be used as a parallel runtime.

## Credential Recovery Order

Agents must not guess where OAuth, Stripe, email, PayPal, or other provider credentials live.

When credentials appear missing:

1. Check the canonical `airbnb_agent/.env` with boolean, prefix, or length-only diagnostics. Never print secret values.
2. Run `python manage.py sync_socialapps` so Django `SocialApp` rows match the canonical `.env`.
3. Restart with `./run_mladis_live.command`.
4. Verify `/accounts/login/`, `/healthz`, `check_local_runtime_contract.sh`, and the sign-in contract.
5. If the canonical `.env` is genuinely missing values, recover them only from an owner-approved secret manager/provider dashboard or a prior working local database. Treat database recovery as a last-resort emergency path and never print the recovered values.

Do not edit login templates, create fallback UI, create a second checkout, start another port, or ask the owner to redo setup until this recovery order has been followed.

## Forbidden Normal Startup Paths

Do not use these during normal MLADIS work:

```bash
python manage.py runserver 0.0.0.0:8000
python manage.py runserver
npm run dev
nohup python manage.py runserver ...
preview_* scripts
port 8010 prototype servers
random trycloudflare URLs
```

Exceptions require explicit owner approval in the current thread and must be documented in the final response.

## Required Health Checks

Before reporting that local work is ready, verify:

```bash
airbnb_agent/scripts/check_local_runtime_contract.sh
```

The checker must confirm:

- Django answers at `http://127.0.0.1:8000/healthz`.
- The stable tunnel answers at `https://local.mladis.com/healthz`.
- Port `8000` is not bound to `0.0.0.0` or `*`.
- The `mladis-local` Cloudflare named tunnel is running.

## Environment Contract

Runtime secrets are saved once in `airbnb_agent/.env` and loaded by Django at startup.

- Stripe local testing requires `STRIPE_SECRET_KEY=sk_test_...`.
- Production may use `sk_live_...`, but live keys must not be copied into local dev without explicit owner approval.
- After any `.env` change, restart with `./run_mladis_live.command`.
- Do not paste secrets into chat, docs, screenshots, or Git.

## If `local.mladis.com` Is Down

Do not switch to `0.0.0.0`, Vite, or a random tunnel. Fix the named tunnel:

```bash
cloudflared tunnel info mladis-local
cloudflared tunnel run --url http://127.0.0.1:8000 mladis-local
```

Then restart through `./run_mladis_live.command` and rerun the health checker.
