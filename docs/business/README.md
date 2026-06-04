# MLADIS Business Operations

Private operating documents for the legal and administrative setup behind MLADIS.

These records are meant to give the MLADIS app, agents, and future automation work a reliable business source of truth. Do not copy this directory into public frontend content, public documentation, marketing pages, or generated customer emails without reviewing privacy first.

## Current Records

- [MLADIS LLC profile](mladis-llc-profile.md): legal identity, portal references, filing facts, responsible people, and operational contact information.
- [MLADIS LLC next steps](mladis-llc-next-steps.md): post-formation checklist, deadlines, and source links.
- [Owner action center](owner-action-center-2026-06-03.md): current read/sign/click status page.
- [Brand assets](brand-assets/README.md): official MLADIS logo/image assets copied from Downloads for business and product use.
- [Operating agreement package](operating-agreement/README.md): single-member operating agreement draft, initial member consent, and future member notes.
- [Operations roles](operations/README.md): private operating-role notes for people helping run MLADIS business branches.
- [Business visitor package](immigration/README.md): B-1-aligned planning process, Diana visit policy, invitation template, travel packet checklist, and official source links.
- [Publication package](publication/README.md): Queens County Clerk publication workflow, email draft, notice draft, and completion checklist.
- [EIN and banking package](ein-and-banking/README.md): EIN worksheet, bank checklist, and bookkeeping starter categories.
- [Funding readiness package](funding-readiness/README.md): fundable-company goal, resume plan, todo list, data-room index, and lender/grant/certification readiness notes.
- [Signing controls](signing/README.md): rules for signing assistance and why reusable signature assets stay outside Git.

## Data Handling Rules

- Keep EINs, SSNs, tax IDs, bank information, payment card data, and government login credentials out of this repo.
- Store production secrets in the deployment provider, `.env` files, or GitHub Actions secrets.
- Treat home addresses, legal transaction IDs, and government portal references as private business operations data.
- If these facts are later needed by the app, create explicit admin-only models or environment configuration rather than reading directly from these docs.
