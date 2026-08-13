# Private EIN And Banking Records Manifest

This manifest records where sensitive records are stored without exposing the EIN, SSN, ID numbers, bank numbers, or tax-sensitive values in Git.

## Canonical Owner-Only Google Drive Folder

The canonical private record is the existing owner-only Google Drive folder:

`MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/`

Drive metadata was rechecked on 2026-08-13. The current Dominican counsel packet
and its four control records reported `not_shared`; direct Drive URLs and file
IDs are intentionally omitted from public Git. The mounted record uses the
existing numbered `01-formation` through `06-publication` subdirectories. Per
the owner's storage instruction, use those directories and do not create a new
MLADIS directory or parallel data-room tree. Use filenames, not public links,
to identify records.

## Security Warning: Legacy AIRBNB Mirror

The similarly named folder beneath the Drive-synced `DataScience/AIRBNB`
workspace is **not** the canonical private vault. On 2026-08-08 its folder
metadata showed an `anyone with the link` writer permission. It contains legacy
copies of sensitive records and must be treated as exposed until that link
permission is removed and the files are rechecked.

- Do not add new private material to the AIRBNB mirror.
- Do not publish a link to either Drive location in Git.
- Canonical owner-only copies of the current legal/loan packet were secured in
  the existing numbered owner-only record before this tracker was updated.
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
| `MLADIS_Mercury_Business_Account_Verification_2026-08-08.md` | Mailbox-based account-opening evidence and verification limits | Do not commit; public status only |
| `MLADIS_G101_G102_Legal_Transition_Audit_2026-08-08.md` | Source-by-source apartment transition audit | Do not commit; public tracker only |
| `Mercury_MLADIS_LLC_Account_Approval_Email_2026-06-19.pdf` | Private account-approval evidence; includes sensitive bank details | Do not commit |
| `MLADIS_TR-570_Fax_Transmission_Report_OK_2026-08-11.jpeg` | UPS fax proof showing five of five pages and successful transmission | Do not commit |
| `Forum_Newsgroup_Affidavit_MLADIS_LLC_2026-07-27.pdf` | Publication affidavit received with expired-notary defect | Do not file; do not commit |
| `MLADIS_Lender_Readiness_Packet_2026-08-11.md` | Detailed private legal, financial, and lender-readiness control | Do not commit |
| `MLADIS_Lender_Readiness_Cover_2026-08-11.pdf` | Printable private readiness cover and release checklist | Do not commit |
| `MLADIS_Lender_Core_Document_Packet_DRAFT_PRIVATE_2026-08-11.pdf` | 22-page private core packet with verified formation, EIN, governance, account, fax, and Daily News evidence | Do not commit or submit as a complete application |

## Dominican Republic G-101/G-102 Counsel Package

The following current files were assembled, uploaded to the existing owner-only
folder, and verified as `not_shared` on 2026-08-13. They contain private
corporate, property, identity, financial, and contract evidence.

| Private Drive file | Purpose | Status |
| --- | --- | --- |
| `MLADIS_DR_Counsel_Submission_Packet_2026-08-13.pdf` | Verified 89-page counsel packet: brief, core evidence, and Photos annex | Ready for owner review and counsel delivery; not yet sent |
| `MLADIS_DR_Google_Photos_Evidence_Annex_2026-08-13.pdf` | 13-page annex containing 12 distinct retained records | Verified private supporting record |
| `MLADIS_DR_Google_Photos_Evidence_Register_2026-08-13.txt` | Source facts, limits, hashes, duplicates, and exclusions | Verified private control |
| `MLADIS_DR_Source_Audit_2018-2026_2026-08-13.txt` | Git/Drive/Photos source matrix, findings, access limitations, and exact legal gaps | Verified private control |
| `MLADIS_DR_Counsel_Packet_Control_Log_2026-08-13.txt` | Page map, checksum, verification, outstanding documents, and transmission status | Verified private control |

The source audit covered the AIRBNB repository and four apartment submodules,
accessible RIT and personal Drive records, and indexed RIT/personal Photos
searches from 2018-2026. The MLADIS Google account was signed out and is recorded
as an access limitation. No counsel transmission is recorded; the packet should
be sent in the existing counsel email thread with a request for receipt and the
outstanding official products.

## NYS TR-570 Response Packet

The New York Taxation and Finance LLC/LLP Request for Information packet is
stored in `02-tax-ein` within the owner-only Drive record above. These files
contain private tax identifiers and must not be copied into Git.

| Private Drive file | Purpose | Status |
| --- | --- | --- |
| `MLADIS_TR-570_original-notice_2026-06-17.pdf` | Original NYS LLC/LLP Request for Information notice | Source |
| `MLADIS_TR-570_fax-ready_SIGN-AND-DATE_2026-07-26.pdf` | Complete five-page response with every non-signature field filled | Current fax-ready file |
| `MLADIS_TR-570_field-plan_and_submission-log_2026-07-26.txt` | Field plan, source rationale, owner review, exact notice submission methods, and proof controls | Current log |
| `MLADIS_TR-570_submission-status_2026-08-08.txt` | Current overdue status and fax/mail proof controls | Current submission control |

TR-570 status as of 2026-08-11:

- The owner faxed the response. The UPS report shows the notice destination,
  five of five pages, and `Result OK`; agency acknowledgment is pending.
- The fax machine printed an incorrect 2021 date. Retain original file metadata
  and UPS context, and archive the exact signed transmitted packet if available.
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
