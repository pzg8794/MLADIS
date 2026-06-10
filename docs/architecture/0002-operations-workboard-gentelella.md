# ADR 0002: Operations Workboard and Gentelella Admin Shell

Status: Proposed for MVP implementation  
Scope: MLADIS internal management system, Operations neuron, Gentelella UI shell  
Related document: `docs/architecture/0001-mladis-universe-neuron-model.md`

---

## 1. Purpose

MLADIS needs a small internal management system so ongoing work does not disappear across chats, screenshots, commits, Google Drive files, browser tabs, and memory.

The first version should be a lightweight visual work-management board, not a full project-management product.

The purpose is to help us track:

- what we captured,
- what is planned,
- what is currently in progress,
- what is blocked,
- what is done,
- what the next tiny action is,
- which MLADIS neuron the work belongs to,
- which GitHub, Drive, or source links are connected to the work.

This system should be accessible through the MLADIS web app, likely at:

```text
/ops/workboard/
```

---

## 2. Decision

MLADIS will create an internal **Operations Workboard** using **Gentelella** as the visual admin/dashboard template.

Gentelella is allowed to provide:

- layout,
- dashboard shell,
- cards,
- tables,
- forms,
- sidebar/topbar structure,
- responsive admin UI patterns,
- visual polish.

Gentelella must not define:

- MLADIS domain logic,
- MLADIS neuron structure,
- model relationships,
- business rules,
- services,
- repositories,
- controller behavior,
- Pyramid storage rules,
- FairAgent logic.

The strict rule is:

> **Gentelella is the View layer only. MLADIS OOP/MVC architecture owns the system behavior.**

---

## 3. Architectural Position

The Workboard belongs under a new Operations neuron.

```text
Operations [uses: Pyramid, FairAgent, Portfolio]
- Operations.WorkItem
- Operations.WorkSession
- Operations.Decision
- Operations.Roadmap
- Operations.Release
```

For the MVP, only `Operations.WorkItem` is required.

Future objects may be added only after the WorkItem foundation is stable.

---

## 4. MVC / OOP Enforcement

The implementation must follow the MLADIS MVC/OOP process.

```text
Model       = operations/models.py
Service     = operations/services.py
Repository  = operations/repositories.py
Controller  = operations/views.py
View        = operations/templates/operations/*.html + Gentelella shell/assets
Routes      = operations/urls.py
Admin       = operations/admin.py
```

### 4.1 Model responsibilities

Models define persistent domain objects and field-level constraints.

The MVP model is:

```text
Operations.WorkItem
```

### 4.2 Service responsibilities

Services own business behavior that should not live in templates or views.

Examples:

- moving a work item between statuses,
- marking a work item complete,
- computing focus items,
- validating transitions,
- preparing Kanban column data,
- deciding which items appear in Today's Focus.

### 4.3 Repository responsibilities

Repositories own query patterns and data access abstraction.

Examples:

- list active work items,
- group work items by status,
- find blocked work,
- find recently updated work,
- find work by neuron,
- find today's focus candidates.

### 4.4 Controller responsibilities

Django views/controllers coordinate requests and responses.

They may call services and repositories, but they should not contain core business rules.

### 4.5 View responsibilities

Templates display data.

Gentelella assets may style the view, but templates should not contain domain decisions.

---

## 5. MVP Domain Model

### 5.1 WorkItem

Required fields:

```text
title
description
neuron
status
priority
next_action
created_at
updated_at
```

Useful optional fields:

```text
source_url
github_url
drive_url
completed_at
created_by
assigned_to
due_date
sort_order
```

### 5.2 Status choices

```text
captured      = Captured
planned       = Planned
in_progress   = In Progress
blocked       = Blocked
paused        = Paused
done          = Done
```

### 5.3 Priority choices

```text
low       = Low
medium    = Medium
high      = High
critical  = Critical
```

### 5.4 Neuron choices

```text
operations  = Operations
booking     = Booking
finance     = Finance
research    = Research
education   = Education
fitness     = Fitness
portfolio   = Portfolio
pyramid     = Pyramid
fair_agent  = FairAgent
```

---

## 6. MVP Page Layout

The first page should be simple and visual.

```text
MLADIS Workboard

[Today's Focus]
Main focus: ...
Next tiny action: ...
Blocked: ...

[Captured] [Planned] [In Progress] [Blocked] [Done]
  card       card       card          card      card
```

Each card should show:

```text
title
neuron chip
priority chip
status
next action
last updated
GitHub / Drive / source links when available
```

The page should be mobile-friendly and readable on desktop.

---

## 7. Initial Seed Work Items

The MVP should seed or manually create these initial work items:

```text
1. Document MLADIS Universe Architecture
   Neuron: Operations / Pyramid
   Status: Done
   Link: docs/architecture/0001-mladis-universe-neuron-model.md

2. Document Operations Workboard + Gentelella Plan
   Neuron: Operations
   Status: Done
   Link: docs/architecture/0002-operations-workboard-gentelella.md

3. Build Operations Workboard MVP
   Neuron: Operations
   Status: Planned
   Next action: create operations Django app and WorkItem model

4. Integrate Gentelella as View Shell
   Neuron: Operations
   Status: Planned
   Next action: add Gentelella assets without importing domain logic

5. Update README with MLADIS Universe Architecture
   Neuron: Portfolio / Operations
   Status: Captured
   Next action: summarize ADR 0001 in README

6. Re-architect current bookings app toward Booking neuron
   Neuron: Booking
   Status: Captured
   Next action: map current models to Booking.Resource, Request, Reservation, Availability, Maintenance, Policy

7. Create Finance neuron foundation
   Neuron: Finance
   Status: Captured
   Next action: define Finance.Transaction, Invoice, Receipt, Ledger, TaxRecord

8. Create Pyramid storage/index foundation
   Neuron: Pyramid
   Status: Captured
   Next action: define JSON/evidence/archive storage strategy

9. Create FairAgent/Fairgent foundation
   Neuron: FairAgent
   Status: Captured
   Next action: define context, policy, explanation, audit objects

10. Connect maintenance events to Booking.Maintenance
    Neuron: Booking
    Status: Captured
    Next action: align maintenance model with architecture and finance links
```

---

## 8. Implementation To-Do List

### Phase 0: Safety

- [ ] Create branch: `feature/operations-workboard-gentelella`
- [ ] Do not deploy to production until local checks pass.
- [ ] Do not replace the existing Django admin.
- [ ] Do not replace the existing public site.
- [ ] Keep Gentelella isolated as a UI shell.

### Phase 1: Documentation

- [x] Add ADR 0001 for MLADIS Universe neuron model.
- [x] Add ADR 0002 for Operations Workboard and Gentelella plan.
- [ ] Add README link to both ADRs.
- [ ] Add a short implementation note under `docs/implementation/operations-workboard-mvp.md` if more technical detail is needed.

### Phase 2: Django app foundation

- [ ] Create `operations/` Django app.
- [ ] Add `operations` to `INSTALLED_APPS`.
- [ ] Create `operations/models.py` with `WorkItem`.
- [ ] Create `operations/admin.py` for admin management.
- [ ] Create and run migrations.
- [ ] Add tests for model defaults and status choices.

### Phase 3: OOP service/repository layer

- [ ] Create `operations/repositories.py`.
- [ ] Create `WorkItemRepository`.
- [ ] Add repository method: `list_active()`.
- [ ] Add repository method: `group_by_status()`.
- [ ] Add repository method: `list_blocked()`.
- [ ] Add repository method: `list_recently_updated()`.
- [ ] Create `operations/services.py`.
- [ ] Create `WorkboardService`.
- [ ] Add service method: `get_board_context()`.
- [ ] Add service method: `move_item()`.
- [ ] Add service method: `complete_item()`.
- [ ] Add service method: `get_today_focus()`.

### Phase 4: Views and URLs

- [ ] Create `operations/views.py`.
- [ ] Create `WorkboardView`.
- [ ] Create `operations/urls.py`.
- [ ] Register route: `/ops/workboard/`.
- [ ] Add authentication/staff protection.
- [ ] Add graceful empty state when no work items exist.

### Phase 5: Gentelella UI shell

- [ ] Review Gentelella license and preserve attribution/notice.
- [ ] Add Gentelella source/reference in a controlled location if needed.
- [ ] Add compiled/customized assets under static assets.
- [ ] Create base shell template: `templates/layouts/ops_shell.html`.
- [ ] Create Workboard template: `operations/templates/operations/workboard.html`.
- [ ] Keep Gentelella as View-only.
- [ ] Do not put domain rules in JavaScript or templates.

### Phase 6: Workboard UX

- [ ] Add Today's Focus panel.
- [ ] Add Kanban columns.
- [ ] Add status cards.
- [ ] Add neuron chips.
- [ ] Add priority chips.
- [ ] Add next-action text.
- [ ] Add GitHub/Drive/source links.
- [ ] Add mobile-friendly layout.
- [ ] Add simple search/filter if time allows.

### Phase 7: Seed data

- [ ] Add management command or fixture for starter work items.
- [ ] Seed ADR/documentation tasks.
- [ ] Seed Booking re-architecture task.
- [ ] Seed Finance foundation task.
- [ ] Seed Pyramid foundation task.
- [ ] Seed FairAgent foundation task.
- [ ] Seed maintenance alignment task.

### Phase 8: Validation

- [ ] Run `python manage.py check`.
- [ ] Run `python manage.py makemigrations --check --dry-run`.
- [ ] Run migrations locally.
- [ ] Run tests.
- [ ] Verify `/ops/workboard/` loads locally.
- [ ] Verify staff-only access.
- [ ] Verify admin CRUD works.
- [ ] Verify board groups cards by status.
- [ ] Verify mobile layout is readable.

### Phase 9: PR and review

- [ ] Commit MVP implementation.
- [ ] Open PR.
- [ ] Include screenshots.
- [ ] Include local test results.
- [ ] Do not deploy until reviewed.

---

## 9. Suggested File Layout

```text
operations/
|-- __init__.py
|-- admin.py
|-- apps.py
|-- models.py
|-- repositories.py
|-- services.py
|-- urls.py
|-- views.py
|-- migrations/
|-- templates/
|   `-- operations/
|       `-- workboard.html
`-- tests/
    |-- test_work_item_model.py
    |-- test_workboard_service.py
    `-- test_workboard_view.py

templates/
`-- layouts/
    `-- ops_shell.html

static/
`-- operations/
    |-- css/
    |-- js/
    `-- vendor/
        `-- gentelella/
```

---

## 10. Acceptance Criteria

The MVP is acceptable when:

- `/ops/workboard/` exists and is staff-protected.
- Work items can be created and edited through Django admin.
- Work items appear grouped by status on the board.
- Each card shows title, neuron, priority, next action, and update time.
- Today's Focus appears at the top.
- Gentelella styling is visible but isolated to the view shell.
- Domain logic lives in `operations/services.py`, not templates.
- Query logic lives in `operations/repositories.py`, not templates.
- The implementation passes Django checks and migrations.
- The page works on desktop and mobile.

---

## 11. Non-Goals for MVP

The first version should not include:

- drag-and-drop persistence,
- real-time collaboration,
- notifications,
- calendar sync,
- Google Drive sync,
- ChatGPT conversation import,
- Pyramid archival automation,
- FairAgent decision automation,
- full project-management complexity.

These can come later.

The MVP must stay small, visual, and useful.

---

## 12. Future Extensions

After the MVP works, possible extensions include:

```text
Operations.WorkSession
Operations.Decision
Operations.Roadmap
Operations.Release
Operations.Note
Operations.Checklist
Operations.ArtifactLink
```

Future integrations:

- Archive completed work into Pyramid.
- Connect GitHub commits/PRs to WorkItems.
- Connect Google Drive docs to WorkItems.
- Add FairAgent summaries/explanations for project state.
- Add ADHD-friendly reminders and focus modes.
- Add release notes generation.
- Add roadmap views by neuron.

---

## 13. Guiding Principle

The Workboard exists to protect attention and memory.

It should help us answer:

```text
What are we doing?
Why are we doing it?
What neuron does it belong to?
What is the next tiny action?
What is blocked?
What is done?
```

The board should make MLADIS development visible without becoming another overwhelming system.
