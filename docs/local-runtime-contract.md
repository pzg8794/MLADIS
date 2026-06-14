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

## Forbidden Normal Startup Paths

Do not use these during normal MLADIS work:

```bash
python manage.py runserver 0.0.0.0:8000
python manage.py runserver
npm run dev
nohup python manage.py runserver ...
preview_* scripts
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
