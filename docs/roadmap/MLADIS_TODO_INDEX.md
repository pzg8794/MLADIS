# MLADIS TODO Index

Last status sweep: 2026-06-10

This file is the **single source of truth for where MLADIS TODO lists live and what their current completion status is**.

Use this file first when asking: "What do we still need to do?"  
Use the linked/listed documents for the details inside each area.

Sensitive records and private evidence stay in the private Google Drive business-record vault. This index should reference private records by safe description only; do not paste EIN values, SSNs, bank numbers, identity-document numbers, private addresses, tax letters, or secret credentials into GitHub.

---

## Status legend

| Status | Meaning |
| --- | --- |
| Done | The checklist/list is complete or has no active open tasks. |
| Active | This is an actively maintained list with open tasks. |
| In progress | Significant work is complete, but important items remain. |
| Todo | The list exists as a needed area, but the concrete checklist has not been created yet. |
| Deferred | Intentionally postponed until a dependency or safer timing is ready. |
| Private | Source of truth lives outside GitHub because it contains sensitive records. |

---

## Master control rule

1. Start with this TODO index.
2. Use `docs/roadmap/MLADIS_MASTER_TODO.md` as the master execution checklist.
3. Use area-specific TODOs/checklists for details.
4. When an area-specific checklist changes, update this index and the master TODO status.
5. If a task is completed based on a private Drive record, mark it done here with a repo-safe note only.

---

## TODO source map

| Area | Source / tracker | Location | Status | Current summary | Update rule |
| --- | --- | --- | --- | --- | --- |
| Master execution roadmap | MLADIS Master TODO / Roadmap | `docs/roadmap/MLADIS_MASTER_TODO.md` | Active | Central checklist for business, architecture, product, deployment, and future neurons. | Update after every major planning or implementation sweep. |
| TODO index | MLADIS TODO Index | `docs/roadmap/MLADIS_TODO_INDEX.md` | Active | This file tracks all TODO lists and their completion state. | Update whenever a new checklist is created or an old one changes status. |
| Business/legal blueprint | MLADIS Business Blueprint | `docs/business/MLADIS_BUSINESS_BLUEPRINT.md` | In progress | Formation, EIN, operating agreement, and initial governance are done; publication, bank account, CPA/tax confirmation remain open. | Update after legal, tax, banking, publication, or business-account changes. |
| Universe architecture | ADR 0001: MLADIS Universe and Neuron Architecture | `docs/architecture/0001-mladis-universe-neuron-model.md` | Done / guiding | Core architecture accepted; future work should follow the neuron/composition model. | Update only through a deliberate architecture revision or a new ADR. |
| Operations workboard | ADR 0002: Operations Workboard and Gentelella Admin Shell | `docs/architecture/0002-operations-workboard-gentelella.md` + `/ops/workboard/` | In progress | Owner-only visual workboard MVP exists with seeded tasks, completion toggles, and Operations.WorkItem MVC/OOP structure. | Update after workboard model, API, UI, seed data, or owner-access changes. |
| Full-site rebrand | ADR 0003: Gentelella v4 Full-Site Rebrand Foundation | `docs/architecture/0003-gentelella-v4-full-site-rebrand.md` + active rebrand work | In progress | Gentelella v4 selected as View-system reference; APITable/Tabler/AdminLTE are references only. Old port `8010` preview is retired; use the canonical launcher/local origin. | Update after shell, theme tokens, shared components, mobile QA, or page migration changes. |
| Live deployment | MLADIS Live VM Deployment | `docs/live-vm-deployment.md` | Active | Live VM deployment/runbook exists; per-deploy checks still recur. | Update when VM, domain, deploy command, service, DB, static/media, or rollback behavior changes. |
| Admin business calendar | Admin Business Calendar | `docs/admin-business-calendar.md` | Active | Calendar documentation exists; continue smoke-testing after deploys. | Update when calendar UI, range helper, blocks, price overrides, or tests change. |
| Deposit operations | Deposit Admin Operations | `docs/deposit-admin-operations.md` | Active | Capture/release workflow documented; keep aligned with provider behavior. | Update when Stripe/PayPal deposit lifecycle or admin actions change. |
| Brand assets | MLADIS Brand Assets | `docs/brand/MLADIS_BRAND_ASSETS.md` | In progress | Parent and booking logos documented; audit live usage as pages evolve. | Update when logos, brand hierarchy, admin settings, or public materials change. |
| Platform/account migration | Platform Account Update Checklist | Private Drive tracker, repo-safe status summarized in business blueprint and master TODO | Private / In progress | Many account identity updates are done; bank, billing, payout, and deferred transfers remain. | Update private tracker first, then summarize repo-safe status here. |
| Owner action center | MLADIS Owner Action Center | Private Drive tracker | Private / In progress | Tracks signed governance, EIN, private vault, publication, Dropbox Sign/Diana items, and bank next steps. | Use as private evidence; do not copy sensitive details into Git. |
| Services and costs | Services & Costs Inventory | Private Drive tracker | Private / Active | Tracks subscriptions, ownership/migration status, costs, and deferred transfer backlog. | Update whenever a service, subscription, billing owner, migration, or cost changes. |
| Bank account checklist | Business Bank Account Checklist / Bank Account Opening Packet | Private Drive tracker and repo-safe summaries | Private / Todo | Required documents mostly prepared; actual bank account is not opened yet. | Update after bank choice, account open, funding, statement export setup, and reconciliation rules. |
| Google Workspace/storage policy | Not yet created | Recommended: `docs/business/google-workspace-storage-policy.md` | Todo | Business Standard trial active; user/storage/alias policy needs documentation before adding relatives or extra paid seats. | Create before adding non-business users or changing storage/billing structure. |
| Finance neuron design | Not yet created | Recommended: `docs/architecture/0002-finance-neuron-design.md` | Todo | Finance.Transaction, Invoice, Receipt, Ledger, TaxRecord need formal design. | Create before expanding payment/deposit/tax automation. |
| Booking cleanup plan | Not yet created | Recommended: `docs/architecture/0003-booking-neuron-cleanup-plan.md` | Todo | Current app needs mapping to Booking.Resource, Request, Reservation, Availability, Maintenance, Policy. | Create before large refactor or model rename. |
| Booking maintenance feature | Not yet created | Recommended: `docs/product/booking-maintenance-roadmap.md` | Todo | Maintenance needs title, cost, time, pictures, Finance expense link, Pyramid evidence, report/bill output. | Create before implementing maintenance models/UI/API. |
| Pyramid storage/memory plan | Not yet created | Recommended: `docs/architecture/0004-pyramid-storage-plan.md` | Todo | Need DB vs Pyramid boundaries, JSON schemas, evidence packets, artifacts, archive/search rules. | Create before storing operational JSON/artifacts at scale. |
| FairAgent/Fairgent design | Not yet created | Recommended: `docs/architecture/0005-fairagent-design.md` | Todo | Need code/domain naming, UI brand naming, audit/explanation/action rules. | Create before agentic automation expands. |
| Research migration | Not yet created | Recommended: `docs/research/research-neuron-migration.md` | Todo | Quantum MAB, EQUITAS, AI fairness, datasets, papers, and experiments need Research neuron mapping. | Create before moving research assets into MLADIS. |
| Education neuron | Not yet created | Recommended: `docs/architecture/education-neuron-design.md` | Deferred | Lower priority until Booking/Finance/Pyramid base is stable. | Create when Education becomes active product/research work. |
| Fitness neuron | Not yet created | Recommended: `docs/architecture/fitness-neuron-design.md` | Deferred | Lower priority until Booking/Finance/Pyramid base is stable. | Create when Fitness becomes active product work. |
| Portfolio neuron | Not yet created | Recommended: `docs/architecture/portfolio-neuron-design.md` | Deferred | Lower priority until core architecture is stable, but important for identity/showcase. | Create before public portfolio/product identity work expands. |
| Modern frontend/admin dashboard | Current frontend files + master TODO | `frontend/` and `docs/roadmap/MLADIS_MASTER_TODO.md` | In progress | Modern dashboard direction exists; auth-aware nav, polish, and integration path remain. | Update master TODO and create a frontend-specific roadmap if work becomes larger. |
| External service transfer backlog | Services & Costs Inventory + master TODO | Private Drive tracker + `docs/roadmap/MLADIS_MASTER_TODO.md` | Deferred | Do not transfer/cancel/rotate services while app is still stabilizing unless explicitly approved. | Resume one service at a time with export, smoke test, rollback, and evidence. |

---

## Current high-level completion snapshot

| Category | Status | Notes |
| --- | --- | --- |
| LLC formation | Done | Formation approved and official records archived privately. |
| EIN | Done | Issued and stored privately. Do not expose value in repo. |
| Governance docs | Done | Operating Agreement and Initial Written Consent executed by Piter. |
| Diana acknowledgment | In progress | Piter/MLADIS copy exists; Diana acceptance/signature still pending unless later confirmed. |
| NY publication | In progress | Request/designation path started; publication run/certificate still open. |
| Business bank account | Todo | Prepared but not opened. |
| Bookkeeping | In progress | Starter structure exists; final MLADIS Finance/Booking integration still needed. |
| Account identity updates | In progress | Many done; bank/billing/payout/deferred transfers remain. |
| MLADIS architecture | Done / guiding | ADR 0001 accepted as guide. |
| Operations workboard | In progress | Owner-only MVP exists at `/ops/workboard/`; continue improving search/filter and seeded task coverage. |
| Master roadmap | Active | Created and should be maintained. |
| README alignment | Done / monitor | Updated to universe framing; old code paths remain during transition. |
| Booking platform | In progress | Operational app exists; OOP cleanup still needed. |
| Finance neuron | Todo | Needs design and implementation. |
| Pyramid | Todo | Needs storage/memory plan. |
| FairAgent/Fairgent | Todo | Needs design before serious automation. |
| Research migration | Todo | Needs mapping plan. |
| Modern frontend | In progress | Prototype direction exists; not ready to replace live site. |
| Live deployment discipline | Active | Use deploy/check/restart rules every time. |

---

## Update checklist for future sweeps

When doing a TODO/status sweep, check in this order:

1. `docs/roadmap/MLADIS_TODO_INDEX.md`
2. `docs/roadmap/MLADIS_MASTER_TODO.md`
3. `docs/business/MLADIS_BUSINESS_BLUEPRINT.md`
4. Private Drive owner/action/platform/services/bank trackers
5. `docs/live-vm-deployment.md`
6. `docs/admin-business-calendar.md`
7. `docs/deposit-admin-operations.md`
8. `docs/architecture/0001-mladis-universe-neuron-model.md`
9. Current GitHub commits/branches/issues/PRs
10. Live system status only when explicitly checking deployment/runtime

Do not assume private/legal/financial tasks are done unless a tracker, file, or user confirmation supports it.
