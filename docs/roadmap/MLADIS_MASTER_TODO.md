# MLADIS Master TODO / Roadmap

Last status sweep: 2026-06-10

This is the central execution checklist for MLADIS. It consolidates the business/legal checklist, platform-account tracker, architecture roadmap, live-deployment notes, and current product/re-architecture priorities.

Sensitive values and official private records must stay in the private Google Drive business-record vault, not in GitHub.

---

## Status legend

| Status | Meaning |
| --- | --- |
| Done | Completed and supported by a repo-safe document, private Drive record, or live-system confirmation. |
| In progress | Started, partially completed, or waiting on an external response. |
| Todo | Not completed yet. |
| Deferred | Intentionally postponed until a safer dependency is ready. |
| Blocked | Cannot move until a dependency is completed. |

---

## 1. Business / legal foundation

| Priority | Item | Status | Evidence / notes |
| --- | --- | --- | --- |
| High | Form MLADIS LLC | Done | NY domestic LLC approved/issued on 2026-06-03. |
| High | Archive formation confirmation | Done | Stored in private business records. |
| High | Archive filing receipt and Articles packet | Done | Stored in private business records. |
| High | Capture filing receipt details | Done | DOS ID and filing details recorded in repo-safe business docs; official packet kept privately. |
| High | Apply for EIN through IRS | Done | EIN issued on 2026-06-03; exact value/CP 575 letter stored privately. |
| High | Save EIN confirmation letter in secure records | Done | Private Drive vault only. Do not copy into GitHub. |
| High | Draft operating agreement | Done | Governance package prepared. |
| High | Sign operating agreement | Done | Executed by Piter on 2026-06-03. |
| High | Sign initial written consent / member resolutions | Done | Executed by Piter on 2026-06-03. |
| Medium | Archive Diana contractor agreement | Done | Archived in private/source business records. |
| Medium | Prepare Diana operations acknowledgment | In progress | Piter/MLADIS-signed copy exists; Diana signature/acceptance remains pending unless later confirmed. |
| Medium | Prepare B-1 business visitor process package | Done | Prepared for future planning; not a guarantee or substitute for legal advice. |
| High | Start Queens/NY publication process | In progress | Designation request was sent; track clerk/newspaper response and publication run. |
| High | Complete NY publication requirement | Todo | Publish for six weeks, collect affidavits, file Certificate of Publication. |
| High | File Certificate of Publication with affidavits | Todo | Do after newspaper affidavits are received. |
| Medium | Evaluate BOI requirement status periodically | In progress | Current private tracker says domestic LLCs were exempt under 2025 interim final rule as reviewed on 2026-06-03; re-check before relying on it for future deadlines. |

---

## 2. Money infrastructure / finance operations

| Priority | Item | Status | Evidence / notes |
| --- | --- | --- | --- |
| High | Prepare bank account opening packet | Done | Packet exists; safe version does not include EIN/SSN/bank numbers. |
| High | Open MLADIS LLC business checking account | Todo | Needs bank/fintech selection and official documents. |
| High | Separate MLADIS income from personal funds | Blocked | Requires business account. |
| High | Use business account for direct-booking income, deposits, refunds, expenses, software, hosting, ads, repairs, and cleaning | Blocked | Requires business account and reconciliation process. |
| Medium | Keep reserve for refunds, chargebacks, and deposit timing | Todo | Add once bank account exists. |
| Medium | Export monthly bank statements to private records | Blocked | Requires business account. |
| Medium | Reconcile bank, payment processor, and booking records monthly | Blocked | Requires business account/payment processor flow. |
| Medium | Create bookkeeping starter chart of accounts | Done | Draft chart prepared; review with CPA before tax filing. |
| Medium | Implement bookkeeping system | In progress | Owner started a bookkeeping/booking system; final cleanup should align with MLADIS OOP Finance/Booking architecture. |
| Medium | Confirm tax/accounting treatment with CPA | Todo | Needed before first tax filing. |
| Medium | Confirm sales tax, hotel occupancy, short-term-rental, and local compliance obligations | Todo | Needed before direct bookings go live outside Airbnb. |
| Medium | Prepare financial forecast and business plan | Todo | Needs booking revenue, expenses, occupancy, and use-of-funds assumptions. |
| Medium | Build lender/grant/investor data room | Todo | Use funding-readiness checklist after bank/bookkeeping are further along. |
| Low | Register SAM.gov / UEI | Deferred | Do only if a federal grant/contract target is selected. |
| Low | Evaluate MWBE or other NY incentives | Deferred | Revisit after money infrastructure and records are stable. |

---

## 3. Platform account migration / business identity

| Priority | Platform / area | Status | Notes |
| --- | --- | --- | --- |
| High | Airbnb W-9 / tax profile | In progress | Business W-9 submitted; validation pending. Payout method still depends on LLC bank account. |
| High | Airbnb payout method | Blocked | Requires MLADIS LLC bank account. |
| Medium | Airbnb display/preferred name | Done | Preferred name set to MLADIS LLC. |
| Medium | Squarespace WHOIS registrant | In progress | WHOIS organization updated; confirmation/billing details still need final check. |
| Medium | Squarespace billing contact | Todo | Update billing name/contact when safe. |
| Medium | Cloudflare account name | Done | Account renamed to MLADIS LLC. |
| Medium | Dropbox Sign company name | Done | Company name set to MLADIS LLC; free-tier limits remain. |
| High | MLADIS Django SiteSettings | Done | Live DB site name/contact email updated to MLADIS LLC / MLADIS email. |
| High | Google Workspace organization name | Done | Workspace profile name set to MLADIS LLC. |
| Medium | Google Workspace Business Standard trial/storage | In progress | Trial active; document user/storage policy before adding relatives/non-business users. |
| Medium | Google Workspace aliases/groups | Todo | Prefer aliases/groups for admin@, billing@, support@, bookings@, legal@, finance@, tech@ when possible to avoid unnecessary paid seats. |
| Medium | Meta Business Suite | Done | Business portfolio renamed to Meta-accepted title-case form. |
| Medium | Facebook Page | Done | Page renamed, bio/about/contact and cover updated; WhatsApp remains pending phone verification. |
| High | Google Cloud/GCE ownership and billing | Deferred | Keep current working production VM stable; migrate only with export, smoke test, rollback path. |
| High | GitHub ownership/protected branches/secrets | Deferred | Preserve current access; document MLADIS-controlled admins and CI/deploy secret path later. |
| High | OAuth provider app ownership | Deferred | Do not change until callback inventory and auth smoke tests are ready. |
| High | Payment platform ownership/webhooks | Deferred | Do after bank account, reconciliation, webhook checks, and rollback plan. |
| Medium | Ring/property security systems | Deferred | Do not migrate until access/smoke test path is clear. |
| Low | Legacy GoDaddy domains/hosting | Deferred | Review after app and domain strategy are stable; do not cancel without exports and dependency check. |

---

## 4. Documentation and architecture alignment

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Document MLADIS universe / neuron architecture | Done | See `docs/architecture/0001-mladis-universe-neuron-model.md`. |
| High | Build owner-only Operations Workboard MVP | In progress | `Operations.WorkItem` model/API/UI exists at `/ops/workboard/`; continue search/filter and broader seed coverage after MVP verification. |
| High | Prototype Gentelella v4 full-site rebrand | In progress | See `docs/architecture/0003-gentelella-v4-full-site-rebrand.md`; old port `8010` preview is retired, and active rebrand testing uses the canonical launcher/local origin. |
| High | Create master TODO / roadmap | Done | This file. |
| High | Update business blueprint statuses | Done | `docs/business/MLADIS_BUSINESS_BLUEPRINT.md` refreshed with latest status sweep. |
| High | Update README to describe MLADIS as universe / connected intelligence platform | Done | README now links to architecture and roadmap. |
| High | Stop describing MLADIS as only Airbnb/vacation-rental work | In progress | README/business docs improved; remaining old app/folder names stay during transition. |
| Medium | Document Google Workspace/storage/business-infrastructure setup | Todo | Capture plan, users, storage policy, aliases, and private records strategy. |
| Medium | Document Pyramid storage design | Todo | Need practical schema/folder/index/archive/evidence plan. |
| Medium | Document Finance neuron design | Todo | Define Transaction, Expense, Revenue, Deposit, Refund, Payment, Invoice, Receipt, Ledger, TaxRecord. |
| Medium | Document Booking neuron cleanup plan | Todo | Map current Django objects to Booking.Resource, Request, Reservation, Availability, Maintenance, Policy. |
| Medium | Document FairAgent/Fairgent design | Todo | Define code name vs UI/brand name and fairness-aware action rules. |
| Medium | Document Research migration plan | Todo | Map Quantum MAB, EQUITAS, AI fairness, datasets, papers, and experiments into Research neuron. |

---

## 5. Core re-architecture foundation

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Preserve current live booking app while re-architecting | In progress | Avoid risky rewrites until clear migration path exists. |
| High | Create/formalize `core.Neuron` | Todo | Base reusable intelligence structure. |
| High | Create/formalize `core.Artifact` | Todo | Evidence/output/file abstraction; artifacts are not neurons. |
| High | Create/formalize `core.ValueObject` | Todo | Money, TimeWindow, Address, Contact, etc. |
| High | Create/formalize `core.Event` | Todo | Cross-neuron communication without improper inheritance. |
| High | Create/formalize `core.Registry` | Todo | Track neurons, artifacts, product expressions, and references. |
| Medium | Define composition notation in code conventions | Todo | `Neuron [uses: OtherNeuron]` should map to services/references/adapters. |
| Medium | Define singular naming rules in code conventions | Todo | Domain objects singular; plural only for collections/routes/UI sections. |

---

## 6. Booking neuron

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Keep current reservation/customer/admin workflows usable | In progress | Existing Django app remains operational path. |
| High | Map current `BookableItem` to `Booking.Resource` | Todo | Preserve behavior while reducing rental-specific naming in reusable layers. |
| High | Map current inquiry/reservation logic to `Booking.Request` and `Booking.Reservation` | Todo | Need clear distinction between request, offer, reservation, and financial event. |
| High | Map calendar/blocks/pricing to `Booking.Availability` and `Booking.Policy` | Todo | Admin calendar exists; OOP cleanup still pending. |
| High | Build `Booking.Maintenance` | Todo | Required fields: title, cost, time, pictures; types: Cleaning, Repair, Inspection, Readiness. |
| Medium | Connect Booking maintenance costs to Finance expenses | Todo | Use Finance.Transaction.Expense reference/event. |
| Medium | Connect maintenance pictures/reports to artifacts and Pyramid evidence | Todo | Avoid storing evidence only as loose uploads. |
| Medium | Generate maintenance report/bill/tax-support packet | Todo | Future formal document generation. |
| Medium | Improve mobile-friendly operator workflow | Todo | Needed for property managers/cleaners on phone. |
| Medium | Keep calendar/admin docs updated | In progress | Existing admin calendar doc covers current behavior. |

---

## 7. Finance neuron

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Define Finance neuron design doc | Todo | Must guide payments, deposits, invoices, receipts, bookkeeping, taxes. |
| High | Define `Finance.Transaction` | Todo | Parent for Payment, Deposit, Refund, Expense, Revenue, Transfer. |
| High | Define `Finance.Invoice` and `Finance.Receipt` | Todo | Current Invoice exists in booking app; future home should be Finance. |
| High | Define `Finance.Ledger` and `Finance.TaxRecord` | Todo | Needed before direct-booking/tax automation matures. |
| Medium | Map current `DamageDeposit` to Finance concepts | Todo | Current deposit admin workflow exists; architecture mapping pending. |
| Medium | Map current `Invoice` to Finance concepts | Todo | Avoid Booking owning too much finance logic long-term. |
| Medium | Design reconciliation process | Todo | Bank/payment processor/booking records monthly. |
| Medium | Payment processor integration expansion | Deferred | Do only after bank and reconciliation plan are stable. |

---

## 8. Pyramid memory / records / evidence

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Define Pyramid storage plan | Todo | Replace generic “data lake” thinking with MLADIS Pyramid. |
| High | Decide DB vs Pyramid responsibilities | Todo | DB = operational source of truth; Pyramid = memory/evidence/archive/search/intelligence. |
| High | Define JSON schema conventions | Todo | Need stable naming, metadata, references, privacy levels. |
| Medium | Define evidence packet structure | Todo | Useful for maintenance, legal/property, taxes, research, customer issues. |
| Medium | Define artifact metadata structure | Todo | Documents, pictures, receipts, reports, datasets. |
| Medium | Define backup/sync policy | Todo | Private records in Drive, code-safe trackers in Git, future object storage as needed. |
| Medium | Connect Pyramid to Booking, Finance, Research, FairAgent | Todo | Use events/references/services. |

---

## 9. FairAgent / Fairgent

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| Medium | Decide final brand/code naming | In progress | `FairAgent` for code/domain; `Fairgent` may be UI/brand name. |
| Medium | Define FairAgent.Context, Policy, Decision, Explanation, Action, Audit | Todo | Must not become generic chatbot wrapper. |
| Medium | Connect FairAgent to Pyramid evidence | Todo | Explanations/actions need grounding and audit trail. |
| Medium | Use FairAgent first in high-impact workflows | Todo | Property management, finance, customer decisions, student/education, research fairness. |

---

## 10. Research neuron

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| Medium | Create Research neuron design doc | Todo | Structure: Question, Project, Experiment, Dataset, Model, Result, Publication, Review. |
| Medium | Map Quantum MAB work into Research.Project/Experiment/Model/Result | Todo | Preserve existing paper/project logic. |
| Medium | Map EQUITAS / AI fairness work into Research and FairAgent | Todo | Keep fairness architecture consistent. |
| Medium | Define research artifact handling through Pyramid | Todo | Papers, datasets, figures, logs, results, notebooks. |
| Low | Build research dashboard/product expression | Deferred | After core Research/Pyramid structure is defined. |

---

## 11. Education, Fitness, Portfolio neurons

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| Low | Education design doc | Todo | Course, Lesson, Assessment, Accommodation, StudentRecord, Reflection, PortfolioArtifact. |
| Low | Fitness design doc | Todo | Routine, Session, Nutrition, Progress, Condition, Recommendation. |
| Low | Portfolio design doc | Todo | Identity, Project, Experience, Credential, Publication, Showcase, Narrative. |
| Low | Connect Education/Fitness/Portfolio to Booking/Finance/Pyramid/FairAgent | Deferred | After Booking/Finance/Pyramid base is stable. |

---

## 12. Frontend / admin / UX

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Keep current Django admin usable | In progress | Existing admin controls remain primary operational surface. |
| High | Continue modern frontend/dashboard direction locally first | In progress | Do not replace live site until local version is polished/tested. |
| High | Make frontend nav auth-aware | Todo | Account page showed signed-in info while menu still showed Sign in. |
| Medium | Improve modern homepage/dashboard layout | In progress | Soft UI / SaaS direction started. |
| Medium | Improve admin command center | In progress | `/ops/admin/` route/page work started; needs local/live verification. |
| Medium | Verify reports UI | In progress | Search/chips/chart cards/expand/highlight should stay tested. |
| Medium | Verify homepage motion | In progress | Motion CSS/JS should remain functional with no console errors. |
| Medium | Maintain admin branding | In progress | MLADIS Admin header, CSS, quick links, brand assets. |

---

## 13. Live deployment / release checklist

Run before serious deploys:

```bash
cd /home/pitergarcia/airbnb_agent
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart mladis
sudo systemctl status mladis --no-pager
```

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Do not deploy if `python manage.py check` fails | Active rule | Capture logs and stop. |
| High | Do not deploy if migrations fail | Active rule | Capture logs and stop. |
| High | Do not deploy if `systemctl status mladis` shows failed after restart | Active rule | Capture logs and stop. |
| Medium | Keep runtime backup before sync | Active rule | Deployment script should backup SQLite/media/runtime state. |
| Medium | Confirm live admin login after deploy | Todo per deploy | Manual/browser check. |
| Medium | Confirm calendar after deploy | Todo per deploy | Range select, auto-submit, loading links, bulk/selection actions. |
| Medium | Confirm reports after deploy | Todo per deploy | `/ops/reports/`. |
| Medium | Confirm homepage after deploy | Todo per deploy | motion.css/motion.js and console. |
| Medium | Confirm chatbot/AgentFAQ after deploy | Todo per deploy | AgentFAQ admin exists; runtime behavior still should be smoke-tested. |

---

## 14. Deferred transfer backlog rule

Do not transfer, cancel, downgrade, rotate, or reconfigure external services while the MLADIS web application is still being stabilized unless Piter explicitly approves that exact action in the current thread.

When resumed, transfer one service at a time:

1. Record current owner/login/billing/admins.
2. Export screenshots/settings/receipts privately.
3. Add MLADIS-controlled identity before removing personal access.
4. Verify login from MLADIS identity.
5. Transfer ownership/billing.
6. Rotate secrets only after ownership is confirmed.
7. Run service-specific smoke test.
8. Record rollback path and monitor 24-72 hours for production/payment/DNS/OAuth/email changes.
9. Update this roadmap and private evidence records.
