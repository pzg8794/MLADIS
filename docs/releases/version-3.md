# MLADIS Production Version 3

Release date: 2026-06-22 21:45 EDT

Production URL: https://mladis.com/

Deployment target:

- Google Cloud project: `mledis`
- VM: `mladis-test-1`
- Zone: `us-central1-a`
- App service: `mladis`
- App directory: `/home/pitergarcia/airbnb_agent`

Source state:

- Code commit before release documentation: `5185bcd989c161e14f179426ff7b3d0ed9083ece`
- Deployment commit: the final pushed HEAD used by `./deploy_mladis_vm.command`
- Branch used for deployment: `fix/recover-mock-pages-20260617-210747`
- Deploy command: `./deploy_mladis_vm.command`

## Scope

Version 3 deploys the current MLADIS ops frontend and Django application state,
including the restored and aligned ops workspace work up to the Calendar
workspace architecture pass.

Included operational surfaces:

- Command Center
- Reservations
- Calendar workspace and subpages
- Guests / Customers
- Properties
- Maintenance / Work Orders
- Payments
- Deposits
- Reports
- FairAgent
- Settings
- Admin

## Deployment Contract

Deploy through the root-level VM script only:

```bash
./deploy_mladis_vm.command
```

The script packages `airbnb_agent/`, builds the modern frontend into Django
static assets, uploads the archive to the VM, creates a runtime backup, runs
Django deploy steps, and restarts the `mladis` systemd service.

The deploy must remain non-destructive. It must not overwrite production
`.env`, `.venv`, `db.sqlite3`, `media/`, or collected runtime backup state.

## Validation Required

Before considering Version 3 deployed:

- Frontend build succeeds through `npm run build:django`.
- Django deployment checks pass through `python manage.py check`.
- Migrations complete through `python manage.py migrate --noinput`.
- The VM `mladis` service restarts successfully.
- Production responds at `https://mladis.com/`.
- Calendar routes remain available:
  - `/ops/calendar/`
  - `/ops/calendar/list/`
  - `/ops/calendar/rooms/`
  - `/ops/calendar/analytics/`

## Rollback Notes

If Version 3 fails after deployment, redeploy the previous known production code
commit or restore from the VM runtime backup created by the deployment script.
The previous app-code commit before the Calendar architecture pass was
`6ac32f28b0f06c868f560f03cc46f7d96e6b79b3`.
