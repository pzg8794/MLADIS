# Private EIN And Banking Records Manifest

This manifest records where sensitive records are stored without exposing the EIN, SSN, ID numbers, bank numbers, or tax-sensitive values in Git.

## Canonical Owner-Only Google Drive Folder

The canonical private record is the existing owner-only Google Drive folder:

`MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/`

Drive metadata was rechecked on 2026-08-08. The canonical folder was owner-only,
and all 30 files listed in it reported `not_shared`; direct Drive URLs and file
IDs are intentionally omitted from public Git. Per the owner's storage
instruction, this folder is flat and no new subdirectories should be created.
Use filenames, not public links, to identify records.

## Security Warning: Legacy AIRBNB Mirror

The similarly named folder beneath the Drive-synced `DataScience/AIRBNB`
workspace is **not** the canonical private vault. On 2026-08-08 its folder
metadata showed an `anyone with the link` writer permission. It contains legacy
copies of sensitive records and must be treated as exposed until that link
permission is removed and the files are rechecked.

- Do not add new private material to the AIRBNB mirror.
- Do not publish a link to either Drive location in Git.
- Canonical owner-only copies of the current legal/loan packet were secured in
  the existing flat owner-only folder before this tracker was updated.
- Permission removal and a review of whether the exposed link circulated remain
  required security actions.

## Local Backup Folder

An offline backup may be maintained outside the repository. Its absolute path is
not recorded publicly.

## Current Private Files

| File | Purpose | Git status |
| --- | --- | --- |
| `MLADIS-EIN_CONFIRMATION-CP_575_G.pdf` | IRS EIN confirmation letter | Do not commit |
| `MLADIS_EIN_INFO_PRIVATE.md` | Private EIN reference for bank, tax, CPA, payment processor, and government forms | Do not commit |
| `MLADIS_LLC-FilingReceipt-And-Articles.pdf` | Formation receipt and Articles copy for bank/publication use | Canonical owner-only copy secured; historical repo copy requires privacy review |
| `MLADIS_LLC_Operating_Agreement_EXECUTED_2026-06-03.pdf` | Signed governance document | Canonical owner-only copy secured; historical repo copy requires removal/privacy review |
| `MLADIS_LLC_Initial_Member_Consent_EXECUTED_2026-06-03.pdf` | Signed authority / banking consent | Canonical owner-only copy secured; historical repo copy requires removal/privacy review |
| `MLADIS_Bookings_Founding_Operations_Pillar_Acknowledgment_PITER_SIGNED_PENDING_DIANA_2026-06-03.pdf` | Diana operations acknowledgment signed by Piter, pending Diana | Keep private copy with Diana records |
| Contractor agreement PDFs | Diana vacation-rental operations source records | Keep private copies with Diana records |
| `bank-account-opening-packet.md` | Bank onboarding guide | Safe Git copy also exists |
| `BANK_ACCOUNT_NEXT_STEPS_PRIVATE.md` | Private next-step checklist for opening the bank account | Do not commit unless sanitized first |
| `MLADIS_LLC_Legal_and_Loan_Readiness_Status_2026-08-08.md` | Current consolidated legal and lender-readiness audit | Do not commit; public tracker only |
| `Airbnb_2025_Earnings_PreFormation_Operating_History.pdf` | Historical operating evidence predating LLC formation | Do not commit; not MLADIS financial statements |
| `MLADIS_LLC_Borrowing_Resolution_DRAFT_UNSIGNED_2026-07-26.pdf` | Printable lender-resolution draft | Keep private until lender terms are known |
| Current blank SBA Forms 1919 and 413 | Lender application source forms | Keep completed copies private |
| `MLADIS_LLC_Publication_Closeout_Status_2026-08-08.md` | Current closeout record reflecting Daily News affidavit and Forum blocker | Do not commit; public tracker only |
| `NY_Daily_News_Affidavit_Order_87497_2026-07-27.pdf` | Reviewed notarized six-week publication affidavit | Do not commit |
| `MLADIS_LLC_Certificate_of_Publication_DRAFT_UNSIGNED_2026-07-26.pdf` | Unsigned state filing draft | Keep private; do not sign before both affidavits |
| `MLADIS_LLC_Contractor_Ratification_and_Assignment_DRAFT_UNSIGNED_2026-07-26.pdf` | Printable cross-border contract-assignment draft | Keep private until legal/tax review and signatures |

## NYS TR-570 Response Packet

The New York Taxation and Finance LLC/LLP Request for Information packet is
stored directly in the existing flat owner-only Drive folder above. These files
contain private tax identifiers and must not be copied into Git.

| Private Drive file | Purpose | Status |
| --- | --- | --- |
| `MLADIS_TR-570_original-notice_2026-06-17.pdf` | Original NYS LLC/LLP Request for Information notice | Source |
| `MLADIS_TR-570_fax-ready_SIGN-AND-DATE_2026-07-26.pdf` | Complete five-page response with every non-signature field filled | Current fax-ready file |
| `MLADIS_TR-570_field-plan_and_submission-log_2026-07-26.txt` | Field plan, source rationale, owner review, exact notice submission methods, and proof controls | Current log |
| `MLADIS_TR-570_submission-status_2026-08-08.txt` | Current overdue status and fax/mail proof controls | Current submission control |

TR-570 draft status as of 2026-08-08:

- The owner confirmed it remains unsent. No fax confirmation, mailing receipt, or agency acknowledgment was found.
- The fax-ready private response fills every supported non-signature field.
- NAICS `721199` is supported by MLADIS's documented active vacation-stay and
  direct-booking operation and the official short-term traveler-accommodation
  classification.
- Owner, member, and officer identifier fields are filled from private source
  records under the owner's July 26 instruction. No values are copied to Git.
- Signer title is filled; only the owner's signature and actual signing date
  remain blank.
- The private submission log records the exact fax and mailing methods printed
  on the notice.
- The notice date is 2026-06-17 and requested return within 15 days; treat the
  response as overdue and submit promptly after review.

## Private EIN Path For Agents

When an authorized MLADIS agent needs the EIN for a bank, CPA, tax, payroll,
payment processor, or government workflow, use the canonical owner-only Drive
file `MLADIS_EIN_INFO_PRIVATE.md` or the IRS CP 575 letter.

Do not copy the EIN value into GitHub, app fixtures, screenshots, chat logs, public documents, or customer-facing systems.

The private bank packet filename is `bank-account-opening-packet.md`. Confirm
that the opened copy comes from the owner-only folder, not the AIRBNB mirror.

## Rules

- Do not commit EIN value, SSN/ITIN, bank account/routing numbers, ID images, tax returns, or unredacted bank statements.
- If a bank, payment processor, CPA, or government portal needs the EIN, enter it directly into that official system from the private CP 575 letter.
- For official tax forms, keep completed PDFs and private value files in the private Drive folder; Git stores only this filename-level manifest.
- Do not place direct private Drive file URLs in public Git.
- Do not rely on a folder name alone to establish privacy; verify that Drive
  reports the file and parent as not shared before placing sensitive material.
- If a future encrypted bookkeeping vault is created, move or mirror the private files there and update this manifest with the new storage location only, not the sensitive values.
