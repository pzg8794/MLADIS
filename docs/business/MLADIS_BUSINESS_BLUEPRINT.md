# MLADIS Business Blueprint

Last updated: 2026-06-03  
Last status sweep: 2026-08-08

This document tracks the public-safe business foundation for MLADIS LLC. It intentionally avoids sensitive tax, banking, address, identity, and account-secret values.

---

## Status legend

| Status | Meaning |
| --- | --- |
| Done | Completed and supported by a repo-safe document, private Drive record, or live-system confirmation. |
| In progress | Started, partially completed, or waiting for an external response. |
| Todo | Not completed yet. |
| Deferred | Intentionally postponed until a safer dependency is ready. |

---

## Legal entity

| Field | Status / value |
| --- | --- |
| Legal name | MLADIS LLC |
| Entity type | Domestic Limited Liability Company |
| Formation state | New York |
| County | Queens |
| File date / existence date | 2026-06-03 |
| DOS ID | 7932124 |
| NYBE Business ID | 727480853 |
| Articles of Organization Application ID | DOS1336-2026-029778 |
| Initial filing fee paid | $200.00 |
| Formation status | Done — NYBE/DOS filing approved and archived privately. |
| EIN status | Done — EIN issued and IRS confirmation letter stored in the private business-record vault outside Git. Do not copy the EIN into this repo. |
| Governance status | Done — Operating Agreement and Initial Written Consent executed by Piter on 2026-06-03. |

Do not store sensitive personal address details, EIN values, SSNs, identity-document numbers, bank account numbers, tax letters, or private portal screenshots in this repository. Keep official PDFs, filing receipts, EIN letters, banking documents, tax documents, and signed private records in the secure private Google Drive business-record vault.

---

## Core meaning

MLADIS stands for:

**Machine Learning Advanced Information Systems**

MLADIS is the umbrella company for connected intelligence systems, automation, booking tools, research frameworks, education tools, finance/tax support, fitness/wellness systems, portfolio systems, and future Viverse-aligned business branches.

The current vacation-home platform is the first production expression of the broader **Booking** neuron. It is not the full identity of MLADIS.

---

## Mission

MLADIS was born from love, technical creativity, and the desire to make a positive impact. The company should be built carefully, with financial discipline, personal-credit protection, modular architecture, privacy-aware records, and systems that can grow without creating chaos.

---

## Brand architecture

### Parent umbrella

**MLADIS LLC**

Public-facing parent brand:

**MLADIS Connected Intelligence**

Purpose:

- Parent intelligence/technology brand.
- Owns the MLADIS identity, software, frameworks, and future business units.
- Represents the broader Viverse direction: connected systems, intelligent support, ethical technology, modular infrastructure, and human-centered automation.

Primary logo file:

- `airbnb_agent/bookings/static/bookings/brand/mladis-connected-intelligence.png`

Status:

- Done — parent brand asset documented and archived.
- Done — Django admin/site settings support uploaded logo and logo URL.
- In progress — continue replacing old narrow booking-only language with the parent MLADIS universe identity.

### First production product expression

**Booking neuron / MLADIS booking platform**

Current public/product expression:

**MLADIS Bookings**

Purpose:

- Vacation stays and booking workflows.
- Customer reservation flow.
- Admin dashboard and reporting.
- Invoices, deposits, donations, customer information, promotions, and guest communication.
- First practical business branch under MLADIS LLC.

Primary logo file:

- `airbnb_agent/bookings/static/bookings/brand/mladis-bookings.png`

Status:

- Done — booking brand asset documented and archived.
- In progress — keep the current product usable while gradually migrating language and architecture toward the reusable Booking neuron.

---

## Operating principle

MLADIS should grow as a parent company with internal product lines first. Avoid creating separate LLCs until a branch has enough revenue, liability exposure, partners, employees/contractors, or operational complexity to justify separate legal structure.

Recommended structure for now:

```text
MLADIS LLC
|-- MLADIS Connected Intelligence   # Parent brand / umbrella identity
|-- Booking neuron                  # Current vacation-home booking platform is first expression
|-- Finance neuron                  # Transactions, invoices, receipts, ledgers, taxes
|-- Pyramid                         # Memory, evidence, indexing, archive, datasets
|-- FairAgent / Fairgent            # Fairness-aware action/explanation layer
|-- Future: Research                # Quantum/AI/AI-fairness research systems
|-- Future: Education               # Learning, course, teaching, accommodation systems
|-- Future: Fitness                 # Fitness/wellness and progress systems
`-- Future: Portfolio               # Identity, projects, credentials, showcase
```

---

## Credit-safe financial rules

The company must protect Piter's personal credit.

1. Avoid loans during the early validation phase.
2. Avoid personal guarantees unless intentionally reviewed and approved.
3. Use business checking before business credit.
4. Keep personal and business money separate.
5. Track owner contributions and owner draws.
6. Pay business expenses from the business account when possible.
7. Do not scale spending before revenue, booking demand, and operating workflows are proven.
8. Every expense should connect to one of these categories:
   - Compliance
   - Revenue generation
   - Customer experience
   - Platform infrastructure
   - Legal/tax protection
   - Brand asset development
   - Research/product development
9. Do not let excitement, branding, or launch energy create debt pressure.
10. Build MLADIS as a clean, modular system before expanding.

---

## Current business/legal priorities

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Form MLADIS LLC | Done | NY domestic LLC approved/issued on 2026-06-03. |
| High | Archive NYBE application confirmation | Done | Stored in private business records. |
| High | Archive NYS DOS filing receipt and Articles packet | Done | Stored in private business records. |
| High | Apply for EIN directly through IRS | Done | EIN issued on 2026-06-03; IRS confirmation letter stored privately outside Git. |
| High | Save EIN confirmation letter in secure business records | Done | Confirmed in private Google Drive vault. Do not copy EIN value into Git. |
| High | Draft operating agreement | Done | Agreement package prepared. |
| High | Sign single-member operating agreement | Done | Executed by Piter on 2026-06-03. |
| High | Sign initial written consent / member resolutions | Done | Executed by Piter on 2026-06-03. |
| High | Prepare Queens publication package | Done | Draft package prepared. |
| High | Start New York publication process | Done | Daily News payment and affidavit are documented. The owner reports The Forum was paid and the record shows its requested card authorization was returned, but the paid receipt and completion evidence are still missing. |
| High | Complete New York publication requirement | In progress / urgent | Daily News affidavit is complete. Obtain The Forum receipt, six dates, and affidavit, then file by the 2026-10-01 working deadline. |
| High | File Certificate of Publication with affidavits | Blocked by The Forum | Private unsigned draft exists. Sign only after both affidavits pass, then file with the $50 fee and tracking. |
| High | Submit NYS TR-570 response | Overdue / ready to sign | Owner confirmed 2026-08-08 that the private five-page response remains unsent. Review, sign, date, fax, and retain proof. |
| High | Open business checking account | Todo | Bank packet is prepared; actual business account still pending and needed to clear Stripe/Airbnb payout dependencies. |
| Medium | Start bookkeeping | In progress | Starter chart of accounts is prepared; owner started a bookkeeping/booking system; final integration should wait for the OOP Finance/Booking cleanup. |
| Medium | Confirm tax/accounting treatment with CPA | Todo | Confirm before first tax filing and before relying on any tax treatment assumptions. |
| Medium | Confirm direct-booking tax/compliance obligations | Todo | Needed before direct bookings go live outside Airbnb. |
| Medium | Decide whether MLADIS Bookings needs a DBA/assumed name | Todo | Revisit after parent/Booking naming settles and before public marketing relies on a separate assumed name. |
| Medium | Connect Stripe/payment processor | In progress | Stripe account has an action-required status email requesting a valid bank account; final readiness is blocked on business checking account setup. |
| Medium | Build lender/grant/investor data room | In progress | Formation, EIN, governance, blank SBA forms, and pre-formation 2025 Airbnb history are private; bank statements, 2026 exports, financials, insurance, and DR compliance remain open. |
| Low | Evaluate MWBE certification or incentives | Deferred | Revisit after money infrastructure and records are stable. |

---

## Platform/account status sweep

| Platform / area | Status | Notes |
| --- | --- | --- |
| Airbnb W-9 / tax profile | In progress | Business W-9 submitted; IRS/platform validation pending. Payout method still depends on LLC bank account. |
| Airbnb display identity | Done | Preferred first name updated to MLADIS LLC. |
| Squarespace domain registrant / WHOIS | In progress | WHOIS organization updated; billing contact still pending. |
| Cloudflare account name | Done | Account renamed to MLADIS LLC. |
| Dropbox Sign company name | Done | Company name set to MLADIS LLC; free tier limits remain. |
| MLADIS Booking App SiteSettings | Done | Live DB site name/contact email updated to MLADIS LLC / MLADIS business email. |
| Google Workspace organization name | Done | Workspace org name updated to MLADIS LLC. |
| Google Workspace storage/plan | In progress | Business Standard trial is active; document user/storage policy separately before adding non-business users. |
| Meta Business Suite | Done | Business portfolio renamed to the Meta-accepted title-case form. |
| Facebook Page | Done | Page renamed, public URL and About/contact/cover updated. WhatsApp setup remains pending phone verification. |
| Google Cloud / GCE billing ownership | Deferred | Current production VM remains working; ownership/billing transfer should happen only after export/smoke-test/rollback checklist. |
| GitHub / code ownership and secrets | Deferred | Keep current access stable; later document MLADIS-controlled admins, protected branches, and CI/deploy secret handling. |
| PayPal / Stripe / payment platforms | Deferred | Do not migrate/connect serious payment ownership until bank account, webhook checks, and reconciliation are ready. |
| Ring / property security systems | Deferred | Do not migrate until production/support access can be smoke-tested. |
| Legacy GoDaddy domains/hosting | Deferred | Review only after MLADIS app and domain strategy are stable. |

---

## Platform/product priorities

| Priority | Item | Status | Notes |
| --- | --- | --- | --- |
| High | Document MLADIS universe/neuron architecture | Done | See `docs/architecture/0001-mladis-universe-neuron-model.md`. |
| High | Create master roadmap / TODO | Done | See `docs/roadmap/MLADIS_MASTER_TODO.md`. |
| High | Update README to stop describing MLADIS as only future Airbnb work | Done | README now points to the universe architecture and master roadmap. |
| High | Keep booking platform modular for future generic booking framework | In progress | Current app remains usable; re-architecture must move toward Booking.Resource, Booking.Request, Booking.Reservation, Booking.Availability, Booking.Maintenance, and Booking.Policy. |
| High | Track reservations, invoices, deposits, donations, page visits, promotions, and customer profiles | In progress | Current Django models/admin support these records; future Finance/Pyramid integration still needed. |
| Medium | Add parent logo to admin/site settings as default MLADIS umbrella identity | Done | SiteSettings supports logo upload/URL and preview. |
| Medium | Add bookings logo to MLADIS Bookings pages/customer materials | In progress | Asset exists; usage should be audited as public/customer pages evolve. |
| Medium | Document decisions as business evolves | In progress | Continue keeping repo-safe docs in Git and sensitive evidence in private Drive. |
| Medium | Build Booking.Maintenance workflow | Todo | Needs model/admin/API/UI for title, cost, time, pictures, Finance expense link, Pyramid evidence, and generated report/bill. |
| Medium | Formalize Finance neuron | Todo | Move payment/deposit/invoice/accounting thinking toward Finance.Transaction, Finance.Invoice, Finance.Receipt, Finance.Ledger, and Finance.TaxRecord. |
| Medium | Formalize Pyramid storage plan | Todo | Define safe JSON/evidence/artifact/index/archive structure and connection to Booking, Finance, Research, and FairAgent. |
| Medium | Continue modern frontend/admin dashboard | In progress | New frontend direction exists; still needs local polishing, auth-aware navigation, and gradual integration path. |

---

## Future Viverse direction

MLADIS is the first formal business/legal foundation for the Viverse. The goal is not just one Airbnb-style booking site. The goal is a modular, ethical, intelligent ecosystem that can support business, research, education, health/fitness, finance/taxes, portfolio, and automation systems over time.

The first priority is stability:

- legal stability,
- financial stability,
- operational clarity,
- customer trust,
- data/privacy discipline,
- personal-credit protection,
- architecture discipline,
- and careful product expansion.
