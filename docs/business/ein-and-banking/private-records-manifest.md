# Private EIN And Banking Records Manifest

This manifest records where sensitive records are stored without exposing the EIN, SSN, ID numbers, bank numbers, or tax-sensitive values in Git.

## Primary Private Google Drive Folder

Private records are now stored in the Google Drive-synced AIRBNB workspace, outside the Git repository:

`/Users/pitergarcia/Library/CloudStorage/GoogleDrive-garciapiterz@gmail.com/.shortcut-targets-by-id/1pY_fQ54nHKvFABNRGYAr5bQ3su_tUDAi/DataScience/AIRBNB/MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/`

Folder structure:

| Folder | Purpose |
| --- | --- |
| `01-formation/` | Formation receipt, Articles packet, and NYBE confirmation. |
| `02-tax-ein/` | IRS EIN confirmation letter. |
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
| `MLADIS_LLC-FilingReceipt-And-Articles.pdf` | Formation receipt and Articles copy for bank/publication use | Safe repo copy also exists |
| `MLADIS_LLC_Operating_Agreement_EXECUTED_2026-06-03.pdf` | Signed governance document | Repo copy exists; keep final signed copy private too |
| `MLADIS_LLC_Initial_Member_Consent_EXECUTED_2026-06-03.pdf` | Signed authority / banking consent | Repo copy exists; keep final signed copy private too |
| `MLADIS_Bookings_Founding_Operations_Pillar_Acknowledgment_PITER_SIGNED_PENDING_DIANA_2026-06-03.pdf` | Diana operations acknowledgment signed by Piter, pending Diana | Keep private copy with Diana records |
| Contractor agreement PDFs | Diana vacation-rental operations source records | Keep private copies with Diana records |
| `bank-account-opening-packet.md` | Bank onboarding guide | Safe Git copy also exists |
| `BANK_ACCOUNT_NEXT_STEPS_PRIVATE.md` | Private next-step checklist for opening the bank account | Do not commit unless sanitized first |
| `queens-publication-email-ready-to-send.md` | Sent publication request record | Safe Git copy also exists |

## Rules

- Do not commit EIN value, SSN/ITIN, bank account/routing numbers, ID images, tax returns, or unredacted bank statements.
- If a bank, payment processor, CPA, or government portal needs the EIN, enter it directly into that official system from the private CP 575 letter.
- If a future encrypted bookkeeping vault is created, move or mirror the private files there and update this manifest with the new storage location only, not the sensitive values.
