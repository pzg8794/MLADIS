# MLADIS Agent Repository Hygiene

## Required Preflight

Before any AI agent edits files, run from the canonical repository root:

```bash
git status -sb
git branch --show-current
git rev-parse HEAD
git worktree list
git stash list
```

Report:

```text
Active branch:
Active object:
Allowed files:
Forbidden files:
Required tests:
Worktree status:
Stash status:
Stop condition:
Proceeding: yes/no
```

Do not proceed when the branch is wrong, the tree is dirty, a stash is
unexpected, a worktree is unexpected, or an untracked source file is
unexplained.

## Branch Discipline

The normal AI branch is `codex/dev`.

```bash
git checkout main
git pull --ff-only origin main
git checkout -B codex/dev
git push -u origin codex/dev
```

- Do not edit directly on `main`.
- Do not push directly to `main`.
- Do not force-push `main`.
- Use a separate feature branch only with explicit approval from Piter.

## Worktree Policy

Worktrees are forbidden unless Piter explicitly approves one for the current
task.

Do not create a temporary worktree for convenience. Do not leave a worktree
behind after a task. Never remove a dirty worktree or one containing
unpreserved work.

Before completion:

```bash
git status -sb
git worktree list
git stash list
```

Expected final state:

```text
clean working tree
expected branch only
no unexpected worktrees
no unexpected stashes
no untracked source files
```

## Stash Policy

Stashes are not a substitute for task boundaries. Do not hide unrelated dirty
state in a new stash just to begin work.

If preflight finds an unexpected stash:

1. stop;
2. identify its source and object;
3. preserve it through an owner-approved recovery path;
4. do not apply it into an unrelated task;
5. proceed only after the repository has an understood clean state.

No task is complete with an unexplained stash.

## Runtime Hygiene

For a local-site task:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
ps -p <PID> -o pid,ppid,command
lsof -p <PID> | awk '$4 == "cwd" {print $9}'
```

The server current working directory must be the canonical checkout. If not,
stop the stale runtime and use the documented launcher. Do not start random
`runserver`, Vite, preview, or alternate-port processes.

## Dependency Hygiene

Use the existing environment and caches. Install only when missing or when
dependency declarations changed:

```bash
cd airbnb_agent
python -m pip install --upgrade pip
pip install -r requirements.txt
cd ../frontend
npm install
cd ..
```

Never commit virtual environments, `node_modules`, `.env`, generated logs, or
temporary output.

## Validation

Default task validation:

```bash
cd airbnb_agent
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test bookings
cd ../frontend
npm run build
```

For auth tasks only:

```bash
cd airbnb_agent
bash scripts/test_signin_contracts.sh
```

For a documentation-only task, run the validation explicitly requested by the
task. Do not add unrelated build work.

## Documentation-Only Guardrail

For documentation-only tasks:

- edit only the declared documentation files;
- do not touch `airbnb_agent/`, `frontend/src/`, templates, static assets,
  migrations, `.env`, settings, middleware, or launchers;
- do not create release tags unless the task explicitly says to create one;
- run `git diff --name-only` before validation and stop if non-documentation
  files appear.

Documentation may clarify architecture, but it must not sneak in app behavior,
auth, payment, deposit, reservation, guest, frontend, or deployment changes.

## Staging and Commit Review

Before committing:

```bash
git status -sb
git diff --check
git diff --name-only
git diff --cached --name-only
```

Confirm every changed and staged file belongs to the active object. Stage files
explicitly; do not use `git add .` when unrelated files could exist.

Commit messages must identify one object:

```text
ops/payments: fix pagination and invoice links
ops/guests: fix row selection toggle
docs: add codex environment contract
```

Push the focused commit to `origin/codex/dev`.

## Final Report

Every task report must include:

```text
Environment:
Canonical repository:
Active branch:
Active object:
Commit:
Files changed:
Tests run:
Final git status:
Final worktree list:
Final stash list:
Deployment performed: yes/no
```

Do not claim completion while repository hygiene checks are unresolved.
