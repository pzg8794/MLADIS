# MLADIS Deployment Release Contract

## Purpose

Every MLADIS deployment must have a release version that can be identified, audited, and rolled back to.

This contract exists so a bad local or production change never leaves operators guessing which commit is live or which stable version should be restored.

```text
No release version, no deployment.
```

The deployment script enforces this contract. Production deployment is blocked
unless the source checkout is clean, the exact full commit SHA is known, the
release and rollback tags exist locally and on `origin`, and a release manifest
under `docs/releases/` identifies both the deployment commit and rollback
target.

## Release Requirement

Before any deployment, an agent must create or identify a release version for the exact commit being deployed.

A deployment may proceed only when all of the following are true:

- the working tree is clean;
- the deployment commit is known;
- the release version is known;
- the release notes identify the active object(s) changed;
- rollback instructions identify the previous stable release;
- required checks passed;
- Piter explicitly approved deployment in the current thread.

## Transaction Refactor Release Gate

Before implementing the simplified transaction refactor documented in
`docs/architecture/transactions/README.md`, create and push a v3.1 release tag
from the current stable commit.

The v3.1 release must exist before model, service, API, UI, or data migration
work begins for the transaction spine:

```text
Guest -> Transaction -> Reservation / Payment / DepositHold -> Invoice
```

Do not start the transaction refactor without a rollback tag.

Do not create the v3.1 tag during a documentation-only architecture task.

## Version Format

Use a simple monotonically increasing release tag:

```text
release/YYYY.MM.DD-N
```

Examples:

```text
release/2026.06.24-1
release/2026.06.24-2
release/2026.06.25-1
```

For urgent rollback/hotfix work, use:

```text
hotfix/YYYY.MM.DD-N
rollback/YYYY.MM.DD-N
```

Release tags must point to the exact commit deployed.

## Deployment Manifest

Each deployment must create a manifest under:

```text
docs/releases/
```

Use this filename pattern:

```text
docs/releases/YYYY-MM-DD-N.md
```

The manifest must include:

```text
Release tag:
Deployment commit:
Previous stable release:
Active object:
Files changed:
Checks run:
Manual verification:
Deployment target:
Deployment command:
Rollback command:
Known limitations:
Deployment approved by:
Deployment performed by:
Deployment timestamp:
```

The deployment commit may be recorded as the exact full SHA or as
`` `release/YYYY.MM.DD-N^{commit}` ``. The deploy script resolves the annotated
release tag, verifies that it points to `HEAD`, and accepts that exact tag
expression so a committed manifest is not required to contain its own
self-referential SHA.

The deploy script also stages a non-sensitive source identity file inside the
archive, computes the archive SHA-256 before upload, verifies the same hash on
the VM, and writes the successful deployment identity to:

```text
/home/pitergarcia/airbnb_agent/.mladis-release-identity.json
```

That record contains only the release tag, full commit SHA, deployment
timestamp, artifact SHA-256, and rollback target.

If more than one object is being deployed, the manifest must say why this is safe. Multi-object deploys require explicit approval.

## Required Pre-Deployment Checks

Before deployment, run the task-specific checks plus the deployment safety checks.

Default checks:

```bash
git status -sb
git rev-parse HEAD
git log -1 --oneline
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test bookings
```

If frontend files changed:

```bash
cd frontend
npm install
npm run build
```

If auth/login/OAuth files changed, or if the deployment could affect sign-in:

```bash
cd airbnb_agent
bash scripts/test_signin_contracts.sh
```

If provider/payment/email configuration changed:

```bash
cd airbnb_agent
bash scripts/check_provider_contract.sh
```

Do not deploy if any required check fails.

## Release Tag Creation

After checks pass and before deployment:

```bash
git tag -a release/YYYY.MM.DD-N -m "Release YYYY.MM.DD-N: <short summary>"
git push origin release/YYYY.MM.DD-N
```

The tag must be pushed before or as part of the deployment process.

Do not create a release tag after deploying as an afterthought.

## Deployment Rule

Production deployment requires the exact release and rollback tags:

```bash
MLADIS_RELEASE_TAG=release/YYYY.MM.DD-N \
MLADIS_ROLLBACK_TAG=release/YYYY.MM.DD-N-previous \
./deploy_mladis_vm.command
```

The release tag must point to `HEAD` and the release manifest must identify the
same full commit SHA. A clean checkout is mandatory. The existing non-pruning
sync and runtime-backup behavior remains unchanged.

A deployment report must include:

```text
Release tag:
Deployed commit:
Previous stable release:
Deployment target:
Checks passed:
Manual smoke tests:
Rollback plan:
```

A deployment is incomplete without this report.

## Rollback Rule

Every release must have a rollback target.

At minimum, record the previous known-good release tag and commit.

Rollback must prefer a known release tag over an untagged commit.

Example rollback command for the VM:

```bash
git fetch --tags origin
git checkout <previous-release-tag-or-commit>
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart mladis
sudo systemctl status mladis --no-pager
```

If rollback requires a database migration reversal, stop and ask Piter before proceeding.

## Forbidden Deployment Behavior

Do not deploy:

- directly from a dirty worktree;
- from an untagged/undocumented commit;
- from a temporary worktree;
- from a stale checkout;
- from `codex/dev` without an explicit release manifest and approval;
- without a rollback target;
- when tests failed;
- when sign-in is broken;
- when `/healthz` fails after restart;
- when `sudo systemctl status mladis` reports failure.

Do not claim deployment is complete until live smoke tests pass.

## Smoke Test Requirements

After deployment, verify at least:

```text
/healthz
/
/accounts/login/
/admin/
/ops/dashboard/
```

For object-specific deployments, also test the changed route, for example:

```text
/ops/payments/
/ops/customers/
/ops/calendar/
```

If a smoke test fails, capture logs and stop. Do not continue making unrelated fixes.

## Final Rule

```text
Every deployment must map to a release tag, a release manifest, and a rollback target.
```

No exceptions without explicit owner approval.
