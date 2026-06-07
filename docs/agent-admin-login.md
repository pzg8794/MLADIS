# MLADIS Agent Admin Login Runbook

This runbook explains how agents should use the dedicated automation/admin account for MLADIS web-app testing. It intentionally does not include passwords, OAuth secrets, or recovery codes.

## Rule

Use a dedicated agent admin identity for routine automation and testing. Do not use Piter's owner account unless the owner explicitly asks for that in the current thread.

## Credential Source

Agent admin credentials are configured through environment variables, not Git:

```txt
MLADIS_AGENT_ADMIN_EMAIL
MLADIS_AGENT_ADMIN_NAME
MLADIS_AGENT_ADMIN_PHONE
MLADIS_AGENT_ADMIN_USERNAME
MLADIS_AGENT_ADMIN_PASSWORD
```

Local credentials live in `airbnb_agent/.env` or the local runtime environment. Live credentials live in the VM/runtime environment. Never print these values in terminal output, commit them, paste them into docs, or include them in screenshots.

Use `MLADIS_AGENT_ADMIN_EMAIL` as the stable login identity. `MLADIS_AGENT_ADMIN_USERNAME` is only the preferred Django username and may be uniquified by Django if an older user already owns the preferred value. Email login is the durable path for agents.

If `MLADIS_AGENT_ADMIN_PASSWORD` is omitted, agents must not ask the owner to invent one. Run the helper below; it creates a strong random password in the runtime `.env`, keeps the value hidden, and provisions the Django user.

## Provision Or Refresh

The normal launcher/deploy flow provisions the account automatically through:

```bash
cd airbnb_agent
bash scripts/ensure_agent_admin_credentials.sh
```

That helper:

- Creates missing `MLADIS_AGENT_ADMIN_*` values with the dedicated `agent-admin@mladis.com` identity.
- Generates `MLADIS_AGENT_ADMIN_PASSWORD` if it is missing.
- Does not print the password.
- Runs `python manage.py provision_agent_admin`.

To rotate the password without printing it:

```bash
cd airbnb_agent
MLADIS_ROTATE_AGENT_ADMIN_PASSWORD=1 bash scripts/ensure_agent_admin_credentials.sh
```

To refresh the Django records without changing credentials:

```bash
cd airbnb_agent
source .venv/bin/activate
python manage.py provision_agent_admin
```

That command creates or updates:

- A Django user for the agent admin email.
- A matching `AdminAccess` record.
- Staff/superuser access.
- A linked `CustomerProfile` marked as VIP.

If the preferred username is already taken, the provisioning command may create a unique username such as `mladis-agent-2`. That is fine. Browser login should still use the email from `MLADIS_AGENT_ADMIN_EMAIL`.

## Local Login

Start the app with the one approved launcher from the repo root:

```bash
./run_mladis_live.command
```

Use these URLs:

- Password/admin testing: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/) or [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- Facebook OAuth testing: [https://local.mladis.com/accounts/login/](https://local.mladis.com/accounts/login/)

Do not use the Vite dev server at `http://127.0.0.1:5173` for Django/allauth sign-in testing.

For password/admin testing, use the configured email plus the hidden runtime password. Do not ask Piter to know or type that password; read it only from the local runtime when an automated browser test needs to submit it, and never print it.

## Production Login

Use:

- [https://mladis.com/accounts/login/](https://mladis.com/accounts/login/)
- [https://mladis.com/admin/](https://mladis.com/admin/)

The production runtime must have the same `MLADIS_AGENT_ADMIN_*` environment variables set before `python manage.py provision_agent_admin` runs.

## Verification Checklist

After login, verify:

- `/accounts/` loads as the agent/admin user.
- `/admin/` opens MLADIS Admin.
- `/ops/admin/` opens the modern operations dashboard.
- `/ops/reports/` opens reports.
- `/admin/bookings/bookableitem/calendar/` opens the admin business calendar.
- The user appears in `/admin/bookings/adminaccess/` with active staff/superuser access.

## Troubleshooting

If the agent admin login fails:

1. Confirm the app was started with `./run_mladis_live.command`.
2. Run `cd airbnb_agent && bash scripts/ensure_agent_admin_credentials.sh`.
3. Confirm the relevant `.env` file has `MLADIS_AGENT_ADMIN_EMAIL` without printing secret values.
4. If password login is expected, confirm `MLADIS_AGENT_ADMIN_PASSWORD` exists without printing it, then log in with `MLADIS_AGENT_ADMIN_EMAIL`.
5. If using social login, confirm the provider account email exactly matches `MLADIS_AGENT_ADMIN_EMAIL`.
6. For Facebook local testing, use `https://local.mladis.com`, not plain `127.0.0.1`.

Do not create a random one-off superuser unless the owner explicitly asks. If a temporary emergency user is created, document it and remove or rotate it afterward.

Do not ask the owner to type an agent admin password. Either use the existing runtime secret, rotate it with the helper, or use the configured social-login account.

## Security Notes

- Never commit `.env`, passwords, OAuth secrets, API keys, recovery codes, EIN values, bank records, or identity documents.
- Do not reuse owner credentials for routine automation.
- Do not include credentials in PR descriptions, test logs, screenshots, chat messages, or Markdown docs.
- Rotate the agent admin password after any accidental exposure.
