# MLADIS Stable Dev Environment

## Purpose

This contract defines the permanent Codex-ready development environment for
MLADIS:

```text
One environment.
One clean development branch.
One object per task.
No cross-object edits.
No lingering worktrees.
No direct main edits.
```

## Canonical Identity

| Setting | Required value |
|---|---|
| Environment name | `MLADIS Stable Dev Environment` |
| Repository | `pzg8794/MLADIS` |
| Stable branch | `main` |
| AI development branch | `codex/dev` |
| Working directory | Repository root |

`main` is stable and human-approved. AI agents must not edit, commit, or push
directly on `main`. Start from current `main`, then work on `codex/dev` unless
Piter explicitly approves a separate feature branch.

## Branch Initialization

Use the canonical checkout:

```bash
git checkout main
git pull --ff-only origin main
git checkout -B codex/dev
git push -u origin codex/dev
```

Never force-push `main`. Never push an AI task directly to `main`.

## Dependency Setup

Run setup from the repository root:

```bash
cd airbnb_agent
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ../frontend
npm install
cd ..
```

Reuse the existing virtual environment and dependency caches. Reinstall only
when the environment is missing, a lockfile or requirements file changed, or a
task explicitly requires a clean dependency verification.

## Standard Verification

Every task must be able to run:

```bash
cd airbnb_agent
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test bookings
cd ../frontend
npm run build
```

For an auth task only, also run:

```bash
cd airbnb_agent
bash scripts/test_signin_contracts.sh
```

Auth tests do not authorize auth edits during a non-auth task.

## Secrets Policy

- Never print secrets.
- Never commit `.env`.
- Never create OAuth credentials as part of routine development.
- Never change OAuth callback origins unless the active object is `auth` and
  the sign-in contract explicitly requires it.
- Use only the existing approved `.env` handling.
- Do not expose secret values in logs, commits, documentation, screenshots, or
  comments.

## Runtime Source Verification

For tasks involving the local site, verify the process serving port `8000`:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
ps -p <PID> -o pid,ppid,command
lsof -p <PID> | awk '$4 == "cwd" {print $9}'
```

The process working directory must match the canonical checkout. If it does
not, stop the stale runtime and restart with the documented launcher. Do not
start an ad hoc `runserver` or a second MLADIS service.

## Task Declaration

Before editing, every task must declare:

```text
Active object:
Allowed files:
Forbidden files:
Required tests:
Stop condition:
```

The detailed scope rules are in `docs/dev/object-scope-rules.md`. Repository
preflight and completion rules are in
`docs/dev/agent-repository-hygiene.md`.

## Architecture Contracts

Before changing Guests, Reservations, Payments, DepositHolds, Invoices, booking
checkout, or financial/admin transaction views, read:

```text
docs/architecture/transactions/README.md
```

The governing model is:

```text
Guest -> Transaction -> Reservation / Payment / DepositHold -> Invoice
```

Normal local and production behavior must use real database records. Fallback
or sample data is allowed only in tests or explicitly marked fixtures.

The transaction refactor must not begin until a v3.1 release tag exists from
the current stable commit. Do not create that tag during documentation-only
tasks.

## Completion Standard

A task is complete only when:

- its required tests pass or failures are reported accurately;
- only the active object's files changed;
- the working tree is clean after commit;
- the expected branch is active;
- no unexpected worktrees remain;
- no unexpected stashes remain;
- no unexplained untracked source files remain;
- the focused commit is pushed to `origin/codex/dev`;
- no deployment occurred unless Piter explicitly requested one.
