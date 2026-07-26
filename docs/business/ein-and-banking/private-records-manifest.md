# Private EIN And Banking Records Manifest

This manifest records where sensitive records are stored without exposing the EIN, SSN, ID numbers, bank numbers, or tax-sensitive values in Git.

## Primary Private Google Drive Folder

Private records are stored in the existing Google Drive-synced AIRBNB workspace,
outside this Git repository, under:

`MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/`

Direct Drive URLs are intentionally omitted from public Git. Authorized users
should open the existing private MLADIS record through their Drive account.

Folder structure:

| Folder | Purpose |
| --- | --- |
| `01-formation/` | Formation receipt, Articles packet, and NYBE confirmation. |
| `02-tax-ein/` | IRS EIN confirmation letter, private EIN reference file, and NYS TR-570 response packet. |
| `03-governance/` | Signed operating agreement and signed initial member consent. |
| `04-diana-operations/` | Diana operations acknowledgment and contractor/source agreements. |
| `05-banking/` | Bank/lender packet, current blank SBA forms, borrowing-resolution draft, and consolidated readiness audit. |
| `06-publication/` | Designation, paid-order evidence, unsigned Certificate of Publication draft, and closeout record. |

## Local Backup Folder

An offline backup may be maintained outside the repository. Its absolute path is
not recorded publicly.

## Current Private Files

| File | Purpose | Git status |
| --- | --- | --- |
| `MLADIS-EIN_CONFIRMATION-CP_575_G.pdf` | IRS EIN confirmation letter | Do not commit |
| `MLADIS_EIN_INFO_PRIVATE.md` | Private EIN reference for bank, tax, CPA, payment processor, and government forms | Do not commit |
| `MLADIS_LLC-FilingReceipt-And-Articles.pdf` | Formation receipt and Articles copy for bank/publication use | Safe repo copy also exists |
| `MLADIS_LLC_Operating_Agreement_EXECUTED_2026-06-03.pdf` | Signed governance document | Repo copy exists; keep final signed copy private too |
| `MLADIS_LLC_Initial_Member_Consent_EXECUTED_2026-06-03.pdf` | Signed authority / banking consent | Repo copy exists; keep final signed copy private too |
| `MLADIS_Bookings_Founding_Operations_Pillar_Acknowledgment_PITER_SIGNED_PENDING_DIANA_2026-06-03.pdf` | Diana operations acknowledgment signed by Piter, pending Diana | Keep private copy with Diana records |
| Contractor agreement PDFs | Diana vacation-rental operations source records | Keep private copies with Diana records |
| `bank-account-opening-packet.md` | Bank onboarding guide | Safe Git copy also exists |
| `BANK_ACCOUNT_NEXT_STEPS_PRIVATE.md` | Private next-step checklist for opening the bank account | Do not commit unless sanitized first |
| `queens-publication-email-ready-to-send.md` | Sent publication request record | Safe Git copy also exists |
| `MLADIS_LLC_Legal_and_Loan_Readiness_Status_2026-07-26.md` | Consolidated legal and lender-readiness audit | Do not commit; public tracker only |
| `MLADIS_LLC_Borrowing_Resolution_DRAFT_UNSIGNED_2026-07-26.pdf` | Printable lender-resolution draft | Keep private until lender terms are known |
| Current blank SBA Forms 1919 and 413 | Lender application source forms | Keep completed copies private |
| `MLADIS_LLC_Publication_Closeout_Status_2026-07-26.md` | Publication evidence and filing-control record | Do not commit; public tracker only |
| `MLADIS_LLC_Certificate_of_Publication_DRAFT_UNSIGNED_2026-07-26.pdf` | Unsigned state filing draft | Keep private; do not sign before both affidavits |
| `MLADIS_LLC_Contractor_Ratification_and_Assignment_DRAFT_UNSIGNED_2026-07-26.pdf` | Printable cross-border contract-assignment draft | Keep private until legal/tax review and signatures |

## NYS TR-570 Response Packet

The New York Taxation and Finance LLC/LLP Request for Information packet is stored privately in the existing tax/EIN Drive folder above. These files contain private tax identifiers and must not be copied into Git.

| Private Drive file | Purpose | Status |
| --- | --- | --- |
| `MLADIS_TR-570_original-notice_2026-06-17.pdf` | Original NYS LLC/LLP Request for Information notice | Source |
| `MLADIS_TR-570_private-business-values_2026-07-05.txt` | Authoritative private values and hand-entry controls | Source |
| `MLADIS_TR-570_corrected-response-draft_UNSIGNED_2026-07-26.pdf` | Corrected draft using only supported values | Current draft |
| `MLADIS_TR-570_field-plan_and_submission-log_2026-07-26.txt` | Field plan, blank-field review, exact notice submission methods, and proof controls | Current log |
| `MLADIS_TR-570_filled-response-draft_2026-07-05.pdf` and duplicate | Earlier work containing unresolved selections and a stale date | Historical; do not submit |

TR-570 draft status as of 2026-07-26:

- No fax confirmation, mailing receipt, or agency acknowledgment was found.
- The corrected draft fills only values explicitly supported by the private
  source record.
- NAICS remains blank for owner/CPA review.
- Owner, member, and officer identifier fields remain blank for hand entry as
  directed by the private values source.
- Signer title, signature, and date remain blank.
- The private submission log records the exact fax and mailing methods printed
  on the notice.
- The notice date is 2026-06-17 and requested return within 15 days; treat the
  response as overdue and submit promptly after review.

## Private EIN Path For Agents

When an authorized MLADIS agent needs the EIN for a bank, CPA, tax, payroll,
payment processor, or government workflow, use the private Drive vault file:

`02-tax-ein/MLADIS_EIN_INFO_PRIVATE.md`

Do not copy the EIN value into GitHub, app fixtures, screenshots, chat logs, public documents, or customer-facing systems.

The private bank packet that includes the EIN value is:

`05-banking/bank-account-opening-packet.md`

## Rules

- Do not commit EIN value, SSN/ITIN, bank account/routing numbers, ID images, tax returns, or unredacted bank statements.
- If a bank, payment processor, CPA, or government portal needs the EIN, enter it directly into that official system from the private CP 575 letter.
- For official tax forms, keep completed PDFs and private value files in the private Drive folder; Git stores only this filename-level manifest.
- Do not place direct private Drive file URLs in public Git.
- If a future encrypted bookkeeping vault is created, move or mirror the private files there and update this manifest with the new storage location only, not the sensitive values.
