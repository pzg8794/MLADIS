# MLADIS

MLADIS stands for **Machine Learning Advanced Information Systems**.

MLADIS is a private parent repository for the MLADIS source corpus, live booking platform, business documentation, and future Viverse-aligned intelligence systems.

The current production system began as a vacation-home / booking platform, but that is only the first product expression of the broader MLADIS architecture.

See:

- [MLADIS Universe and Neuron Architecture](docs/architecture/0001-mladis-universe-neuron-model.md)
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

It uses `airbnb_agent/.env`, prepares the Django app, starts the local site at:

```text
http://127.0.0.1:8000
```

and opens a temporary Cloudflare public URL when `cloudflared` is installed.

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
- `docs/business/` - repo-safe business/legal/brand trackers. Sensitive records stay outside Git.
- `docs/drive-sources.md` - Drive source inventory and import policy.
- `docs/live-vm-deployment.md` - live VM hosting and one-file deploy runbook.
- `sources/AIRBNB` - submodule for `pzg8794/MLADIS-AIRBNB`.
- `sources/SolOriens-Apts` - submodule for `pzg8794/MLADIS-SolOriens-Apts`.
- `sources/SolOriensV` - submodule for `pzg8794/MLADIS-SolOriensV`.
- `sources/DR-Apartments` - submodule for `pzg8794/MLADIS-DR-Apartments`.

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
