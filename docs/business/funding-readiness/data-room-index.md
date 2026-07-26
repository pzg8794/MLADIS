# MLADIS Data Room Index

Public-safe index for a private lender data room. Private identifiers, signed
forms, affidavits, bank records, tax returns, owner financial information, and
completed loan applications stay outside Git.

## Folder 1 - Formation And Governance

| Document | Status | Storage guidance |
| --- | --- | --- |
| Articles / NYBE application confirmation | Done | Archived in `docs/business/source-documents/MLADIS_LLC-Confirmation.pdf`. |
| NY filing acknowledgement / filing receipt | Done | Archived in `docs/business/source-documents/MLADIS_LLC-FilingReceipt-And-Articles.pdf`. |
| Operating agreement | Executed | Canonical executed copy is in private `03-governance`; public-repo historical copies require privacy review. |
| Initial member consent | Executed | Canonical executed copy is in private `03-governance`; public-repo historical copies require privacy review. |
| Operations acknowledgment | Owner signed; counterparty pending | Obtain counterparty review/acceptance, then store the fully executed copy privately. |
| Business visitor process package | Template ready | Keep blank templates in Git; completed visa-history answers stay outside Git. |
| Certificate of Publication and affidavits | Blocked | Both papers were paid, but no affidavit was found and Daily News evidence appears to show an incorrect consecutive-day schedule. Unsigned draft is private. |
| Certificate of Status | Todo | Order a fresh certificate after the publication filing is accepted. |
| EIN confirmation letter | Done | Stored outside Git in private business records. Do not commit EIN value or CP 575 letter. |
| NYS TR-570 response | Overdue / unsigned | Corrected draft and field plan are in private `02-tax-ein`; retain submission proof and agency response. |
| Recurring compliance calendar | CPA review | Track biennial statement, IT-204-LL/annual filing fee, tax returns, assumed name, and ownership-disclosure rule changes. |

## Folder 2 - Ownership, Identity, And Authority

| Document | Status | Storage guidance |
| --- | --- | --- |
| Owner resume / founder bio | Todo | Public-safe version can be committed later. |
| Owner ID documents | Todo | Never commit. |
| Proof of address if required | Todo | Never commit unless redacted and intentionally private. |
| Bank signature card / bank letter | Todo | Bank package is prepared in `docs/business/ein-and-banking/`; final bank records can only exist after the account is opened and must stay outside Git. |
| Admin/agent authority notes | In progress | Keep non-sensitive summaries in `AGENTS.md` and admin docs. |

## Folder 3 - Financial Records

| Document | Status | Storage guidance |
| --- | --- | --- |
| Business bank statements | Todo | Store outside Git. |
| Airbnb payout reports | Todo | Private data room; summaries may be committed if anonymized. |
| Direct-booking revenue reports | Todo | Generate after platform has live transactions. |
| Expense ledger | Todo | Bookkeeping tool preferred. |
| Receipts and invoices | Todo | Store outside Git by year/vendor. |
| Monthly P&L | Todo | Private data room; public-safe summaries only if approved. |
| Balance sheet | Todo | Private data room. |
| Cash-flow forecast | Todo | Draft can be committed if it contains no sensitive account numbers. |
| Tax returns | Todo | Never commit. |

## Folder 4 - Operations And Traction

| Document | Status | Storage guidance |
| --- | --- | --- |
| Airbnb listing summary | In progress | Public listing metadata is fine; private guest info must be protected. |
| Reviews / guest feedback summaries | In progress | Avoid exposing guest contact data or non-public messages. |
| Reservation history metrics | Todo | Summaries can be committed if anonymized. |
| Customer list / consent status | In progress | Keep direct contact info private and consent-tracked. |
| Contractor/vendor list | In progress | Summaries okay; sensitive payment details private. |
| Insurance documents | Todo | Store outside Git. |
| DR property-control documents | Source archive identified | Attorney must curate current title/lease/authority, HOA permission, disputes/liens, and assignment rights into a lender packet. |
| DR tax/tourism/business registrations | Todo / not verified | Store current RNC, Registro Mercantil, RENATUR/MITUR, tax, invoicing, and local authorization evidence privately. |
| Contractor ratification/assignment | Draft ready | Unsigned printable draft is private; execute only after NY/DR legal-tax review. |

## Folder 5 - Funding Materials

| Document | Status | Storage guidance |
| --- | --- | --- |
| Business plan | Draft materials exist | Finalize one borrower/operating model and lender-ready narrative. |
| Use-of-funds plan | Todo | Can be committed after approval. |
| 3-year financial forecast | Todo | Can be committed after assumptions are approved. |
| Lender one-page summary | Todo | Public-safe version can be committed. |
| Pitch deck | Todo | Store versioned export and source file. |
| Capability statement | Todo | Public-safe version can be committed. |
| SBA Form 1919 | Current blank archived | Complete only after lender, amount, use, ownership, and legal answers are final. |
| SBA Form 413 | Current blank archived | Completed personal financial statement stays private and is sent only through the lender's secure channel. |
| Borrowing resolution | Unsigned draft ready | Complete only after lender, amount, purpose, collateral, guaranty, and final terms are known. |
| Grant-specific narratives | Todo | One folder per grant/agency/program. |

## Folder 6 - Government And Certifications

| Document | Status | Storage guidance |
| --- | --- | --- |
| SAM.gov UEI confirmation | Todo | Store outside Git or summarize non-sensitive UEI status only. |
| Grants.gov account notes | Todo | Do not commit passwords or recovery codes. |
| NYC M/WBE application packet | Todo | Private application docs. |
| NYS MWBE application packet | Todo | Private application docs. |
| SBA lender correspondence | Todo | Store private copies; summarize status only. |
| CDFI/bank correspondence | Todo | Store private copies; summarize status only. |
