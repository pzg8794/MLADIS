# MLADIS LLC Bank Account Opening Packet

Use this as the working packet for opening the first MLADIS LLC business bank account. This document is intentionally safe for Git: it does not include the EIN value, SSN, bank account number, or identity-document numbers.

## Status

| Item | Status |
| --- | --- |
| LLC formed | Done, New York domestic LLC |
| Filing receipt / Articles | Done |
| Operating Agreement | Signed by Piter on 2026-06-03 |
| Initial Member Consent / banking authority | Signed by Piter on 2026-06-03 |
| EIN | Issued; value stored privately |
| EIN confirmation letter | Private CP 575 PDF, not committed to Git |
| Owner government ID | Needed at bank onboarding only |

## Bank-Ready Business Summary

| Field | Value |
| --- | --- |
| Legal name | MLADIS LLC |
| Entity type | Domestic Limited Liability Company |
| State formed | New York |
| Formation date | 2026-06-03 |
| DOS ID | 7932124 |
| County office location | Queens County |
| Sole member / authorized signer | Piter Zacari Garcia Bautista |
| Business phone | 631-575-4841 |
| Current contact email | garciapiterz@gmail.com |
| Domain | mladis.com |
| Principal address | 109-19 72nd Rd., Apt 5H, Forest Hills, NY 11375 |
| Mailing address | Use the private IRS CP 575 / bank application address as needed |
| Industry | Accommodations, vacation rentals, hospitality booking operations, and related software/AI systems |
| Primary product/service | Vacation-rental booking operations and MLADIS direct-booking platform |

## Documents To Upload Or Bring

| Document | Current location | Notes |
| --- | --- | --- |
| NYS DOS filing receipt and Articles | `docs/business/source-documents/MLADIS_LLC-FilingReceipt-And-Articles.pdf` | Safe formation record already in repo. |
| Operating Agreement | `docs/business/signing/execution-ready-2026-06-03/MLADIS_LLC_Operating_Agreement_EXECUTED_2026-06-03.pdf` | Signed by Piter. |
| Initial Member Consent | `docs/business/signing/execution-ready-2026-06-03/MLADIS_LLC_Initial_Member_Consent_EXECUTED_2026-06-03.pdf` | Shows banking and operational authority. |
| EIN confirmation letter | Private records only | Use IRS CP 575 PDF from private folder. Do not commit. |
| Owner government ID | Private records only | Upload directly to bank if required. Do not commit. |
| Proof of address, if required | Private records only | Utility bill, lease, bank statement, or accepted alternative. Do not commit unless intentionally redacted and private. |

## Suggested Application Answers

Use the bank's exact choices when available.

| Bank prompt | Suggested answer |
| --- | --- |
| Business type | LLC / Single-member LLC |
| Industry | Accommodations, hospitality, lodging, vacation rentals, or real estate rental/management depending on available choices |
| Business description | MLADIS LLC operates vacation-rental booking, guest-support, deposit, invoice, and direct-booking systems, supported by software and AI-agent infrastructure. |
| Ownership | Piter Zacari Garcia Bautista owns 100% as sole member |
| Employees | No W-2 employees at opening unless that changes |
| Expected deposits | Airbnb payouts, direct-booking payments, owner contributions, payment processor settlements |
| Expected withdrawals | Cleaning, repairs, software, hosting, advertising, refunds, deposit releases, taxes, contractor/vendor payments |
| International activity | Dominican Republic vacation-rental operations and related vendor/contractor coordination |
| Cash activity | Low / minimal cash if true |
| Credit request | None at initial bank opening |

## Banking Controls

- Open checking first.
- Do not enable overdraft credit, credit line, business loan, merchant cash advance, or personal guarantee product without a separate written owner decision.
- Keep a reserve for refunds, chargebacks, damage-deposit release timing, taxes, and repairs.
- Reconcile bank statements monthly against Airbnb payouts, direct bookings, Stripe/PayPal, invoices, refunds, and vendor payments.
- Store bank statements outside Git in the private business-records vault.

## FinCEN / Beneficial Ownership Note

FinCEN's current public guidance says U.S.-formed domestic companies and U.S. persons are exempt from FinCEN BOI reporting under the current rule. Banks may still ask for beneficial-owner and control-person information for their own know-your-customer process. Provide that information directly to the bank; do not commit ID numbers, SSN, EIN, or identity documents to Git.

Sources:

- IRS EIN page: https://www.irs.gov/businesses/employer-identification-number
- FinCEN BOI page: https://www.fincen.gov/beneficial-ownership-information-reporting
