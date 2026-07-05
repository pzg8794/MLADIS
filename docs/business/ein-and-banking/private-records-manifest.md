# Private EIN And Banking Records Manifest

This manifest records where sensitive records are stored without exposing the EIN, SSN, ID numbers, bank numbers, or tax-sensitive values in Git.

## Primary Private Google Drive Folder

Private records are now stored in the Google Drive-synced AIRBNB workspace, outside the Git repository:

`/Users/pitergarcia/Library/CloudStorage/GoogleDrive-garciapiterz@gmail.com/.shortcut-targets-by-id/1pY_fQ54nHKvFABNRGYAr5bQ3su_tUDAi/DataScience/AIRBNB/MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/`

Drive access path for the tax/EIN folder:

`https://drive.google.com/drive/folders/1rzUcroTiAbdjkurvy_kP8pPI_e9bE58d`

Folder structure:

| Folder | Purpose |
| --- | --- |
| `01-formation/` | Formation receipt, Articles packet, and NYBE confirmation. |
| `02-tax-ein/` | IRS EIN confirmation letter, private EIN reference file, and NYS TR-570 response packet. |
| `03-governance/` | Signed operating agreement and signed initial member consent. |
| `04-diana-operations/` | Diana operations acknowledgment and contractor/source agreements. |
| `05-banking/` | Bank account opening packet and private next-step checklist. |
| `06-publication/` | Queens publication request sent record and publication tracking checklist. |

## Local Backup Folder

`/Users/pitergarcia/Documents/MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/`

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

## NYS TR-570 Response Packet

The New York Taxation and Finance LLC/LLP Request for Information packet is stored privately in the existing tax/EIN Drive folder above. These files contain private tax identifiers and must not be copied into Git.

| Private Drive file | Purpose | Drive URL |
| --- | --- | --- |
| `MLADIS_TR-570_original-notice_2026-06-17.pdf` | Original NYS LLC/LLP Request for Information notice | https://drive.google.com/file/d/1uq86PmpbC_rg1X0DsRWxA8N5mbiW4vvr/view |
| `MLADIS_TR-570_filled-response-draft_2026-07-05.pdf` | Completed draft response with private identifiers filled; signature line remains for owner handwriting | https://drive.google.com/file/d/1QhYCu6O4meaSnArz4u_4I6yFB7ZvN4Jk/view |
| `MLADIS_TR-570_submission-log_2026-07-05.txt` | Field-by-field log, source notes, submission methods, and final review notes without printing private identifier values | https://drive.google.com/file/d/1eH9kCxMjjIj58etntHnrfoo7RH6M0Fsg/view |
| `MLADIS_TR-570_private-business-values_2026-07-05.txt` | Private values source used for the draft response | https://drive.google.com/file/d/18DkS2yk87NvUSmVSH3RHrdxuvhlWQXW9/view |

TR-570 draft status as of 2026-07-05:

- Entity type, owner/member/officer facts, EIN, SSN-backed owner/member/officer identifier fields, address, phone, start date, ownership percentage, NAICS, and prior-business classification are filled in the private draft PDF.
- NAICS `721199` was used for the current principal activity because MLADIS records describe the active operating branch as vacation lodging/direct-booking hospitality, and New York Publication 910 lists `721199 All Other Traveler Accommodation`.
- Signature line is intentionally not machine-signed. The owner must hand-sign the printed final copy before fax or mail submission.
- Notice date is 2026-06-17. The notice says to return the completed form within 15 days by fax or mail, so submit immediately if not already submitted.

## Private EIN Path For Agents

When an authorized MLADIS agent needs the EIN for a bank, CPA, tax, payroll, payment processor, or government workflow, use the private Google Drive vault file:

`/Users/pitergarcia/Library/CloudStorage/GoogleDrive-garciapiterz@gmail.com/.shortcut-targets-by-id/1pY_fQ54nHKvFABNRGYAr5bQ3su_tUDAi/DataScience/AIRBNB/MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/02-tax-ein/MLADIS_EIN_INFO_PRIVATE.md`

Do not copy the EIN value into GitHub, app fixtures, screenshots, chat logs, public documents, or customer-facing systems.

The private bank packet that includes the EIN value is:

`/Users/pitergarcia/Library/CloudStorage/GoogleDrive-garciapiterz@gmail.com/.shortcut-targets-by-id/1pY_fQ54nHKvFABNRGYAr5bQ3su_tUDAi/DataScience/AIRBNB/MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/05-banking/bank-account-opening-packet.md`

## Rules

- Do not commit EIN value, SSN/ITIN, bank account/routing numbers, ID images, tax returns, or unredacted bank statements.
- If a bank, payment processor, CPA, or government portal needs the EIN, enter it directly into that official system from the private CP 575 letter.
- For official tax forms, keep completed PDFs and private value files in the private Drive folder; Git stores only the manifest and Drive access path.
- If a future encrypted bookkeeping vault is created, move or mirror the private files there and update this manifest with the new storage location only, not the sensitive values.
