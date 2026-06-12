# ADR 0003: Gentelella v4 Full-Site Rebrand Foundation

Status: Accepted for isolated prototype branch  
Branch: `feature/gentelella-v4-rebrand`  
Preview: `http://127.0.0.1:8010/`  
Related:

- `docs/architecture/0001-mladis-universe-neuron-model.md`
- `docs/architecture/0002-operations-workboard-gentelella.md`
- `docs/engineering/oop-mvc-contract.md`

---

## 1. Decision

MLADIS will use **Gentelella v4** as the primary visual direction for the next full-site rebrand.

This does not mean importing Gentelella as business logic or replacing the current Django/React architecture.

The rule is:

```text
Gentelella v4 = View system reference.
MLADIS OOP/MVC = Model, service, repository, controller, and domain behavior.
```

The implementation path is a **design-system adaptation**:

- keep Django models/controllers as the backend MVC layer,
- keep React domain/application/infrastructure/ui objects as the modern frontend layer,
- map Gentelella v4 visual patterns into reusable MLADIS shell, card, table, form, modal, command, and mobile components,
- avoid page-by-page one-off styling.

---

## 2. Why Gentelella v4

Gentelella v4 is the best rebrand base because it is modern enough for the current MLADIS operational UI while staying view-layer focused.

Useful Gentelella v4 ideas:

- compact admin shell,
- clear sidebar and command navigation,
- dashboard cards,
- data tables,
- forms,
- charts,
- calendar/app pages,
- settings/profile/inbox-style surfaces,
- responsive admin layout,
- Vite-era frontend workflow,
- no need to move MLADIS into Vue or Angular.

This aligns with MLADIS because the system needs:

- booking operations,
- reservation and maintenance tables,
- calendar work,
- reports and analytics,
- business task/workboard tracking,
- agent/admin configuration,
- future AI-assisted operational workflows.

---

## 3. Reference Framework Roles

### 3.1 Primary: Gentelella v4

Use for:

- main shell direction,
- dashboard density,
- admin navigation,
- data-heavy pages,
- reusable card/table/form styles,
- mobile admin layout decisions.

Do not use for:

- domain models,
- backend services,
- permissions,
- data lake rules,
- agent behavior,
- payment logic.

### 3.2 Reference: APITable

Use APITable as a long-term reference for:

- operational data grids,
- collaborative data surfaces,
- spreadsheet-like record management,
- advanced filtering,
- future AI/data workspace concepts.

Do not use APITable as the main site framework right now because it is a full platform, not a lightweight UI shell for the current Django/React app.

### 3.3 Reference: Tabler

Use Tabler as a reference for:

- clean Bootstrap-like component anatomy,
- simple responsive utility patterns,
- icons and spacing sanity checks.

Do not use it to override the chosen Gentelella direction.

### 3.4 Reference: AdminLTE

Use AdminLTE only as a legacy admin comparison.

It may help with traditional admin patterns, but MLADIS should not inherit an outdated visual language from it.

### 3.5 Do Not Adopt as Primary: Vue Element Admin / ngx-admin

Do not adopt these as the primary framework because they force Vue or Angular stack decisions that do not match the current MLADIS React/Django implementation path.

---

## 4. MLADIS Rebrand Principles

The full site must feel:

- clean,
- compact,
- operational,
- premium,
- mobile-usable,
- color-coded,
- easy to scan,
- ready for AI-assisted workflows.

The site must avoid:

- announcing framework names in the UI,
- large decorative padding,
- inconsistent page-specific menus,
- duplicated card implementations,
- old-template fragments,
- random one-off colors,
- nested card chaos,
- mobile overflow,
- buttons that do nothing.

---

## 5. OOP/MVC Enforcement

Every feature must remain in the proper layer.

```text
Model:
  Django models or frontend domain classes.

Repository:
  Query/data access objects.

Service:
  Business workflow and domain behavior.

Controller:
  Django views/API endpoints or route-level coordinators.

View:
  React components and CSS only.
```

Gentelella-inspired UI code belongs in the View layer.

If a page needs a new table, record card, metric, modal, or property card, create or reuse a shared component. Do not duplicate the same object view across pages.

---

## 6. First Rebrand Foundation

The isolated prototype branch starts with:

- a reusable `opsTheme` object in `frontend/src/ui/theme/opsTheme.ts`,
- a `data-theme-reference="gentelella-v4"` shell marker,
- tighter dashboard shell spacing,
- cleaner topbar/header surfaces,
- more compact metric cards,
- crisper shell/card borders and shadows,
- improved mobile rail density,
- Gentelella-style left accent rails on metric cards.

This is the foundation, not the final full rebrand.

---

## 7. Mobile Contract

Before this branch can replace the current production UI:

- public home page must be checked on mobile,
- ops shell must not overflow horizontally,
- admin/settings forms must fit mobile width,
- calendar must remain usable on mobile,
- reservation and maintenance tables must use reusable list/modal behavior,
- nav must remain one consistent menu,
- logo must render everywhere,
- text must not overlap or distort.

Mobile can use smaller fonts and horizontal chips when needed, but it must not distort content.

---

## 8. Rollout Plan

### Phase 1: Prototype branch

- Branch: `feature/gentelella-v4-rebrand`
- Preview: `http://127.0.0.1:8010/`
- Keep production/current local branch untouched.

### Phase 2: Shared component layer

Create or improve shared components:

- `OpsShell`
- `OpsMetricCard`
- `OpsRecordTable`
- `OpsListModal`
- `OpsPropertyCard`
- `OpsSettingsPanel`
- `OpsActionButton`
- `OpsStatusBadge`

### Phase 3: Page migration

Migrate pages into the shared system:

- public site,
- dashboard,
- admin/settings,
- reservations,
- calendar,
- stay portfolio,
- reports,
- customers,
- deposits,
- maintenance,
- agent,
- workboard,
- business profile.

### Phase 4: Advanced references

Use APITable-style concepts for:

- advanced operational tables,
- spreadsheet-like editing,
- AI-auditable record views,
- future Pyramid/search workspaces.

Use Tabler/AdminLTE only for component sanity checks when useful.

### Phase 5: Approval and deployment

Do not deploy the rebrand branch over production until:

- desktop smoke checks pass,
- mobile smoke checks pass,
- Django checks pass,
- frontend build passes,
- local preview is approved.

---

## 9. Acceptance Criteria

The rebrand direction is acceptable when:

- the whole site uses one visual system,
- the left menu is consistent everywhere,
- all pages inherit the shared shell,
- tables/lists use reusable components,
- object cards are not duplicated,
- mobile views are decent and readable,
- framework names are kept out of visible UI,
- OOP/MVC boundaries remain intact,
- the site is easier to operate than the current version.

---

## 10. Guiding Principle

The rebrand is not decoration.

It is the operational skin for the MLADIS brain.

The UI must make the system easier to reason about, easier to automate, and easier to grow into Booking, Finance, Research, Education, Fitness, Portfolio, Pyramid, and FairAgent neurons.
