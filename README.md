# MLADIS

MLADIS stands for **Machine Learning Advanced Information Systems**.

MLADIS is a private parent repository for the MLADIS source corpus, live booking platform, business documentation, and future Viverse-aligned intelligence systems.

The current production system began as a vacation-home / booking platform, but that is only the first product expression of the broader MLADIS architecture.

See:

- [MLADIS Universe and Neuron Architecture](docs/architecture/0001-mladis-universe-neuron-model.md)
- [Operations Workboard ADR](docs/architecture/0002-operations-workboard-gentelella.md)
- [MLADIS Master TODO / Roadmap](docs/roadmap/MLADIS_MASTER_TODO.md)
- [MLADIS Business Blueprint](docs/business/MLADIS_BUSINESS_BLUEPRINT.md)

---

## Current production expression

The current live app is the first expression of the **Booking** neuron:

```text
Booking [uses: Finance, Pyramid, FairAgent]
- Booking.Resource
- Booking.Request
- Booking.Reservation
- Booking.Availability
- Booking.Maintenance
- Booking.Policy
```

The existing Django app still lives under `airbnb_agent/` during the transition. Do not rename or break working production code just to satisfy the target architecture. Refactor gradually.

---

## One-file live launcher

Run `./run_mladis_live.command` from this folder, or double-click it in Finder.

This is the only normal way to run the local MLADIS site. It uses
`airbnb_agent/.env`, builds the React UI into Django static assets, prepares the
Django app, stops stale Django/tunnel processes on the same port, starts Django
at `http://127.0.0.1:8000`, and opens the stable Cloudflare named-tunnel URL
`https://local.mladis.com` when `cloudflared` is installed and authorized. It
exports `SOCIAL_AUTH_FACEBOOK_ORIGIN=https://local.mladis.com` for the Django
process it starts, so normal UI/Django restarts do not rotate the Facebook
callback URL.

During active development, keep the launcher running so the site stays testable.
If an agent has to restart the app after migrations, frontend builds, env
changes, or a server failure, the agent should restart it through this same
launcher immediately and verify `/healthz` before saying the work is ready.
Do not use or share `http://0.0.0.0:8000` as a MLADIS test URL; it is only a
bind address. Owner-facing testing uses `https://local.mladis.com` and internal
local checks use `http://127.0.0.1:8000`.

Use `https://local.mladis.com` for browser testing when Facebook sign-in
matters. Use `http://127.0.0.1:8000` as the internal local
Django origin and for Google/GitHub local callbacks. Do not use the Vite dev
server at `http://127.0.0.1:5173` for Django/allauth sign-in testing. If the
Terminal scrollback moves, the named-tunnel output is in
`/private/tmp/mladis-tunnel.log`.

One-time Cloudflare setup for the stable local URL:

```bash
cloudflared tunnel login
cloudflared tunnel create mladis-local
cloudflared tunnel route dns mladis-local local.mladis.com
```

Cloudflare must manage the `mladis.com` DNS zone for `local.mladis.com` to
resolve publicly. For this zone, Cloudflare assigned
`olof.ns.cloudflare.com` and `ophelia.ns.cloudflare.com`.

If the Google Drive checkout is slow, clone this repo to a fast local path such
as `~/Documents/MLADIS-dev` and copy only `airbnb_agent/.env` from the Drive
checkout. Use GitHub branches as the source of truth between the two locations.

For social sign-in work, the run/sign-in contract and anti-regression tests live in
[docs/sign-in-contract.md](docs/sign-in-contract.md). Run the contract locally
with:

```bash
bash airbnb_agent/scripts/test_signin_contracts.sh
```

For local runtime and provider setup, read:

- [docs/local-runtime-contract.md](docs/local-runtime-contract.md)
- [docs/environment-provider-contract.md](docs/environment-provider-contract.md)

Verify the contracts with:

```bash
airbnb_agent/scripts/check_local_runtime_contract.sh
airbnb_agent/scripts/check_provider_contract.sh
```

For implementation work, the OOP/MVC architecture contract lives in
[docs/engineering/oop-mvc-contract.md](docs/engineering/oop-mvc-contract.md).
MLADIS features must keep model/domain objects, controller payloads, and rendered
views separated.

---

## One-file VM deploy

Run:

```bash
./deploy_mladis_vm.command
```

to push the current `airbnb_agent/` code to the live Google Compute Engine VM.

The deploy command uploads the app code, creates a runtime backup on the VM, runs the Django deploy steps, and restarts the `mladis` service.

See [docs/live-vm-deployment.md](docs/live-vm-deployment.md) for the current live architecture, domain notes, OAuth alignment, recovery steps, and deploy options.

Important deploy rule:

> Do not deploy if `python manage.py check` fails, migrations fail, or `sudo systemctl status mladis` shows the service failed after restart. Capture logs first and stop.

---

## Layout

- `airbnb_agent/` - current Django implementation for the live MLADIS booking platform.
- `frontend/` - modern frontend/dashboard direction under local-first development.
- `docs/architecture/` - MLADIS universe, neuron model, and re-architecture decisions.
- `docs/roadmap/` - execution roadmap and master TODO list.
- `docs/business/` - repo-safe business/legal/brand trackers, LLC formation records, and operations checklists. Sensitive records stay outside Git.
- `docs/drive-sources.md` - Drive source inventory and import policy.
- `docs/live-vm-deployment.md` - live VM hosting and one-file deploy runbook.
- `sources/AIRBNB` - submodule for `pzg8794/MLADIS-AIRBNB`.
- `sources/SolOriens-Apts` - submodule for `pzg8794/MLADIS-SolOriens-Apts`.
- `sources/SolOriensV` - submodule for `pzg8794/MLADIS-SolOriensV`.
- `sources/DR-Apartments` - submodule for `pzg8794/MLADIS-DR-Apartments`.
- `docs/sign-in-contract.md` - social sign-in setup, callback rules, and CI contract.

Each source repo contains its own `docs/import-summary.md`, `docs/google-native-exports.md`, and `docs/large-files-manifest.md`.

---

## Architecture rule

The guiding MLADIS pattern is:

```text
Neuron [uses: OtherNeuron]
- Neuron.SubNeuron
  - Neuron.SubNeuron.Object
    - Neuron.SubNeuron.Object.Specialization
```

A MLADIS neuron is a reusable intelligence structure that transforms data into meaning, decisions, coordination, or action. Neurons may use other neurons through composition. Specialized objects inherit within their neuron family. Artifacts are evidence, memory, or outputs used by neurons.
