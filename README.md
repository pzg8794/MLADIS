# MLADIS

Private parent repository for the MLADIS source corpus and future Airbnb agent work.

## One-File Live Launcher

Run `./run_mladis_live.command` from this folder, or double-click it in Finder.
It uses `airbnb_agent/.env`, prepares the Django app, starts the local site at
`http://127.0.0.1:8000`, and opens a temporary Cloudflare public URL when
`cloudflared` is installed.

## One-File VM Deploy

Run `./deploy_mladis_vm.command` from this folder to push the current
`airbnb_agent/` code to the live Google Compute Engine VM.

The deploy command uploads the app code, creates a runtime backup on the VM,
runs the Django deploy steps, and restarts the `mladis` service.

See [docs/live-vm-deployment.md](docs/live-vm-deployment.md) for the current
live architecture, domain notes, OAuth alignment, recovery steps, and deploy
options.

## Layout

- `airbnb_agent/` - workspace for the Airbnb agent implementation.
- `sources/AIRBNB` - submodule for `pzg8794/MLADIS-AIRBNB`.
- `sources/SolOriens-Apts` - submodule for `pzg8794/MLADIS-SolOriens-Apts`.
- `sources/SolOriensV` - submodule for `pzg8794/MLADIS-SolOriensV`.
- `sources/DR-Apartments` - submodule for `pzg8794/MLADIS-DR-Apartments`.
- `docs/drive-sources.md` - Drive source inventory and import policy.
- `docs/live-vm-deployment.md` - live VM hosting and one-file deploy runbook.

Each source repo contains its own `docs/import-summary.md`, `docs/google-native-exports.md`, and `docs/large-files-manifest.md`.
