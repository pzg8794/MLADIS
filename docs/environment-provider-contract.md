# MLADIS Environment And Provider Contract

This contract covers one-time provider setup for local and production MLADIS runs. Provider configuration must be saved once in the correct runtime location, verified, documented, and then reused. Agents must not repeatedly ask the owner to redo setup that has already been completed.

## Source Of Truth

Runtime secrets and provider credentials live in runtime environment files or secret managers, not in code and not in chat.

| Environment | Secret Location | Notes |
| --- | --- | --- |
| Local development | `airbnb_agent/.env` | Used by `./run_mladis_live.command`. Never commit. |
| Live VM | `/home/pitergarcia/airbnb_agent/.env` | Used by the `mladis` systemd service. Never overwrite during deploy. |
| Future managed hosting | Provider secret manager | Render/Fly/Cloud Run/etc. equivalent. |

On the owner's Mac, the active local checkout is `/Users/pitergarcia/Desktop/MLADIS-deploy-rebrand`. Do not run provider setup from older or duplicate checkouts unless the owner explicitly directs it.

Provider credential recovery order:

1. Confirm the active checkout's `airbnb_agent/.env` has the expected variables using boolean, prefix, or length-only checks.
2. Rebuild Django provider rows from that `.env` with `python manage.py sync_socialapps`.
3. Restart through `./run_mladis_live.command`.
4. If the `.env` is missing values, recover them only from the approved provider dashboard/secret manager or a prior known-working local database. Never print secrets and never commit recovered values.

Creating a new checkout, new `.env`, new service, or new port is not credential recovery. It is a regression risk.

Hidden provider rule:

- `SOCIAL_AUTH_HIDDEN_PROVIDERS=microsoft` keeps Microsoft out of the customer/operator login UI even if legacy Microsoft credentials exist in the runtime. Remove it only when Microsoft login is intentionally configured, tested, documented, and approved.

## One-Time Setup Rule

If a provider has already been configured in the correct environment, agents must not restart the setup from scratch.

Agents must first check:

```bash
cd airbnb_agent
python manage.py check
python - <<'PY'
from dotenv import dotenv_values
values = dotenv_values(".env")
print("stripe_secret_set=" + str(bool((values.get("STRIPE_SECRET_KEY") or "").strip())))
PY
```

Do not print secret values. Only report whether a key is present and whether it looks like the expected prefix.

## Stripe Contract

Stripe handles the secure damage-deposit checkout.

Local testing:

- Use `STRIPE_SECRET_KEY=sk_test_...`.
- Store it in `airbnb_agent/.env`.
- Configure it with:

```bash
cd airbnb_agent
scripts/configure_stripe_env.sh
```

Production:

- Use `STRIPE_SECRET_KEY=sk_live_...` only in the live runtime environment.
- Do not copy the live key into local development unless the owner explicitly approves it in the current thread.
- Production Stripe setup must include business profile, payout account, webhook review, test checkout, and live checkout smoke before being considered complete.

After changing Stripe values:

```bash
cd ..
./run_mladis_live.command
```

Then verify:

```bash
airbnb_agent/scripts/check_provider_contract.sh
airbnb_agent/scripts/check_local_runtime_contract.sh
```

Expected behavior:

- Missing local Stripe key: secure deposit modal says Stripe is not configured.
- Configured local test key: secure deposit modal opens Stripe test Checkout.
- Configured live key on production: secure deposit opens live Checkout only after production approval.
- Completed security deposit and reservation payment holds send confirmation emails to the guest and `BOOKING_INQUIRY_RECIPIENTS`.
- Local/test emails must have subjects beginning with `(TEST)`.

## Email Delivery Contract

`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` is development-only and prints emails to the Django terminal. It does not deliver to Gmail or any inbox.

The default MLADIS automation sender is the dedicated agent mailbox from `MLADIS_AGENT_ADMIN_EMAIL`, normally `agent-admin@mladis.com`. Runtime booking, payment, and admin notifications should use that identity unless the owner explicitly chooses another sender.

`MLADIS_AGENT_ADMIN_PASSWORD` is the Django/web-app login password for the automation user. It is not automatically a Google Workspace mailbox password and must not be assumed to work for SMTP. Real inbox delivery requires a mailbox app password, SMTP password, or provider relay credential saved in the runtime `.env`.

Approved local secret keys for the agent mailbox are:

- `MLADIS_AGENT_EMAIL_PASSWORD`
- `GMAIL_SMTP_APP_PASSWORD`
- `EMAIL_HOST_PASSWORD`

Real inbox delivery also requires SMTP/provider settings in the runtime `.env`:

- `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS` or `EMAIL_USE_SSL`
- `DEFAULT_FROM_EMAIL`
- `BOOKING_INQUIRY_RECIPIENTS`

Configure local SMTP once with:

```bash
cd airbnb_agent
scripts/configure_email_env.sh
```

Use a provider app password or SMTP password for `agent-admin@mladis.com`. The script uses `MLADIS_AGENT_ADMIN_EMAIL` as the default SMTP username and automatically reuses `MLADIS_AGENT_EMAIL_PASSWORD`, `GMAIL_SMTP_APP_PASSWORD`, or an existing `EMAIL_HOST_PASSWORD` when present. It stores values in `.env` without printing secrets.

Agents must not report “email works in local inbox” unless SMTP/provider settings are configured and a test email reaches the intended mailbox.

## PayPal Contract

PayPal handles alternative deposit authorization.

Required local/live variables:

- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `PAYPAL_ENVIRONMENT=sandbox` or `live`
- `PAYPAL_BRAND_NAME`

Local testing should use sandbox credentials. Live credentials must stay only in live runtime or the approved secret manager.

## OAuth Provider Contract

OAuth callback URLs must remain stable.

- Google local callback: `http://127.0.0.1:8000/oauth/google/login/callback/`
- GitHub local callback: `http://127.0.0.1:8000/oauth/github/login/callback/`
- Facebook local callback: `https://local.mladis.com/oauth/facebook/login/callback/`
- Production callbacks: `https://mladis.com/oauth/<provider>/login/callback/`

Do not use random `trycloudflare.com` URLs for normal provider setup.

## Restart Rule

Django loads `.env` at process startup. Any change to `.env` requires restarting the app with:

```bash
./run_mladis_live.command
```

Do not restart with ad hoc `python manage.py runserver 0.0.0.0:8000`.

## Verification Before Reporting Ready

Before saying provider work is complete, agents must run:

```bash
airbnb_agent/scripts/check_provider_contract.sh
airbnb_agent/scripts/check_local_runtime_contract.sh
```

If either check fails, fix the environment or named tunnel before reporting success.

## Security Rules

- Never paste API keys, webhook secrets, OAuth client secrets, EIN, SSN, bank data, or identity documents into chat.
- Never commit `.env` or copied secret files.
- Never print full secret values in terminal output.
- Mask provider facts as boolean/prefix-only checks.
- Use local test keys for local testing and live keys only in production.
