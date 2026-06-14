# MLADIS Live VM Deployment

This is the current live hosting setup for MLADIS and the deployment workflow for normal code updates.

## Live Stack

- Google Cloud project: `mledis`
- Compute Engine VM: `mladis-test-1`
- Zone: `us-central1-a`
- Machine type: `e2-micro`
- Static IP: `34.63.199.174`
- Public domain: `https://mladis.com/`
- Redirect domain: `https://www.mladis.com/` to apex
- App server: Gunicorn behind systemd service `mladis`
- Reverse proxy and TLS: Caddy via systemd service `caddy`
- App directory on VM: `/home/pitergarcia/airbnb_agent`
- Current database: SQLite on the VM persistent disk
- Static/media strategy: WhiteNoise for collected static files, local `media/` on the VM

## Domain And DNS

- Apex `A` record points to `34.63.199.174`
- `www` is a `CNAME` to `mladis.com`
- Google Workspace mail records must stay in place during DNS edits
- Caddy terminates HTTPS for `mladis.com` and redirects `www.mladis.com` to the apex domain

## OAuth And Canonical Domain

OAuth providers and Django must stay aligned with the public domain.

Required live environment values:

- `SITE_DOMAIN=mladis.com`
- `SITE_NAME=MLADIS`
- `SOCIAL_AUTH_CANONICAL_ORIGIN=https://mladis.com`
- `ALLOWED_HOSTS` must include `mladis.com`, `www.mladis.com`, and the staging host when needed
- `CSRF_TRUSTED_ORIGINS` must include the live HTTPS origins

Provider dashboards must include the live origins and callbacks:

```txt
Google:   https://mladis.com/oauth/google/login/callback/
GitHub:   https://mladis.com/oauth/github/login/callback/
Facebook: https://mladis.com/oauth/facebook/login/callback/
```

If a provider can begin login from `www.mladis.com` before Caddy redirects to
the apex domain, include the matching `https://www.mladis.com/oauth/...`
callbacks too. The Meta app should also allow the stable local callback
`https://local.mladis.com/oauth/facebook/login/callback/` for development.

## One-File Deployment Pipeline

Use the root-level command:

```bash
./deploy_mladis_vm.command
```

What it does:

1. Packages the local `airbnb_agent/` code without `.env`, `.venv`, `db.sqlite3`, `media/`, or build artifacts.
2. Uploads the release archive to the Compute Engine VM.
3. Creates a runtime backup on the VM using `scripts/backup_runtime_state.sh`.
4. Syncs the new code into `/home/pitergarcia/airbnb_agent`.
5. Reuses or creates the remote `.venv`.
6. Runs `pip install -r requirements.txt`.
7. Runs `python manage.py migrate --noinput`.
8. Runs `python manage.py sync_socialapps`.
9. Runs `python manage.py provision_agent_admin`.
10. Runs `python manage.py collectstatic --noinput`.
11. Runs `python manage.py check`.
12. Restarts the `mladis` systemd service.

### Default Safety Behavior

- The deploy command is non-destructive by default.
- It does not replace `.env`, `db.sqlite3`, `media/`, or `.venv`.
- It does not delete remote code files unless you explicitly opt in.
- It creates a runtime backup before syncing code.

### Optional Flags

Use environment variables when you need special behavior:

```bash
MLADIS_DEPLOY_PRUNE=1 ./deploy_mladis_vm.command
MLADIS_RELOAD_CADDY=1 ./deploy_mladis_vm.command
MLADIS_GCE_INSTANCE=mladis-test-1 ./deploy_mladis_vm.command
MLADIS_GCE_ZONE=us-central1-a ./deploy_mladis_vm.command
```

Supported overrides:

- `MLADIS_GCP_PROJECT_ID`
- `MLADIS_GCE_INSTANCE`
- `MLADIS_GCE_ZONE`
- `MLADIS_REMOTE_APP_DIR`
- `MLADIS_REMOTE_SERVICE`
- `MLADIS_REMOTE_USER_HOME`
- `MLADIS_DEPLOY_PRUNE`
- `MLADIS_RELOAD_CADDY`
- `MLADIS_DEPLOY_LABEL`

`MLADIS_DEPLOY_PRUNE=1` enables remote file deletion during sync. Keep it off unless you intentionally want old code files removed.

`MLADIS_RELOAD_CADDY=1` is only needed when a release also changes live Caddy behavior on the VM.

## Rollback And Runtime Recovery

The current pilot setup uses SQLite and local media files, so runtime backups matter.

- Create backup manually on the VM: `bash scripts/backup_runtime_state.sh`
- Restore backup on the VM: `bash scripts/restore_runtime_state.sh <archive.tar.gz>`
- Stop the app service before restore when doing a manual recovery

If a code deploy fails after syncing but before the service restart is healthy, use the runtime backup plus the previous code copy or redeploy the prior commit.

## Admin Access

The source of truth for elevated access is the `AdminAccess` model.

- Matching emails are promoted to `is_staff` and `is_superuser` on login
- The current seeded admin emails are `garciapiterz@gmail.com` and `garciabdianas@gmail.com`
- A dedicated automation/agent admin can be provisioned from `.env` using `MLADIS_AGENT_ADMIN_EMAIL`, `MLADIS_AGENT_ADMIN_NAME`, `MLADIS_AGENT_ADMIN_PHONE`, `MLADIS_AGENT_ADMIN_USERNAME`, and optional `MLADIS_AGENT_ADMIN_PASSWORD`
- Manual admin entry in `/admin/` also works immediately on the live database

Manual entry is useful for urgent live changes. The migration-backed seed is what keeps the same admin access reproducible across new environments or rebuilt databases.

## Operational Notes

- Normal code deploys should not require DNS changes
- Normal code deploys should not require Caddy edits
- Social login changes usually require both `.env` updates and provider console updates
- After any domain/auth change, rerun `python manage.py sync_socialapps` and `python manage.py check`
- Damage deposit operator workflows are documented in `docs/deposit-admin-operations.md`
- Admin stay-calendar workflows are documented in `docs/admin-business-calendar.md`
- The current VM setup is cost-conscious and appropriate for testing, not horizontal scale
