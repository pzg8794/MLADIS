# MLADIS LLC Bank Account Verification And Control Packet

The first MLADIS LLC business bank account has already been approved. Use this
as the working packet for verification, funding, payment-platform linking, and
banking controls. This document is intentionally safe for Git: it does not
include the EIN value, SSN, bank account number, routing number, balance, or
identity-document numbers.

## Status

| Item | Status |
| --- | --- |
| LLC formed | Done, New York domestic LLC |
| Filing receipt / Articles | Done |
| Operating Agreement | Signed by Piter on 2026-06-03 |
| Initial Member Consent / banking authority | Signed by Piter on 2026-06-03 |
| EIN | Issued; value stored privately |
| EIN confirmation letter | Private CP 575 PDF, not committed to Git |
| Mercury business account | Approved 2026-06-19; funding, current use, and statements unverified |
| Stripe bank link | Bank-account addition notice received 2026-06-19; exact payout mapping unverified |
| Owner government ID | Provide directly only if Mercury requests reverification |

Private note: the Google Drive vault version of this bank packet includes the EIN value. This GitHub version intentionally does not.

## Bank-Ready Business Summary

| Field | Value |
| --- | --- |
| Legal name | MLADIS LLC |
| Entity type | Domestic Limited Liability Company |
| State formed | New York |
| Formation date | 2026-06-03 |
| DOS ID | 7932124 |
| County office location | Queens County |
| Sole member / authorized signer | Use the owner-only Operating Agreement and Initial Member Consent |
| Business phone | Use the owner-only business record |
| Current contact email | Use the owner-only account record |
| Domain | mladis.com |
| Principal address | Use the owner-only formation and tax records |
| Mailing address | Use the private IRS CP 575 / bank application address as needed |
| Industry | Vacation rentals, hospitality booking operations, and supporting software/automation for G-101 and G-102; disclose that the Dominican legal and accounting transition is in progress |
| Primary product/service | Vacation-rental lodging, booking, guest support, payments, reporting, and direct-booking automation for G-101 and G-102 under the documented transition to MLADIS LLC |

## Documents To Upload Or Bring

| Document | Current location | Notes |
| --- | --- | --- |
| NYS DOS filing receipt and Articles | Owner-only Drive record | Use `MLADIS_LLC-FilingReceipt-And-Articles.pdf`; historical public-repo copy requires privacy review. |
| Operating Agreement | Owner-only Drive record | Use the canonical executed PDF; historical public-repo copy requires privacy review. |
| Initial Member Consent | Owner-only Drive record | Use the canonical executed PDF showing banking and operational authority. |
| EIN confirmation letter | Private records only | Use IRS CP 575 PDF from private folder. Do not commit. |
| Owner government ID | Private records only | Upload directly to bank if required. Do not commit. |
| Proof of address, if required | Private records only | Utility bill, lease, bank statement, or accepted alternative. Do not commit unless intentionally redacted and private. |

## Suggested Application Answers

Use the bank's exact choices when available.

| Bank prompt | Suggested answer |
| --- | --- |
| Business type | LLC; use the bank's tax-classification choice only after checking the private tax record |
| Industry | Select the closest available vacation-rental, accommodation, hospitality, or property-operations category and disclose that the G-101/G-102 transition is being completed through Dominican counsel |
| Business description | MLADIS LLC was formed to formalize and grow the G-101 and G-102 Dominican Republic vacation-rental operations and their booking, guest-support, payment, reporting, and direct-booking systems. The company is completing the property/operating-authority and accounting transition. |
| Ownership | Enter member and percentage facts exactly as documented in the owner-only governance record |
| Employees | Enter the current count supported by payroll and contractor records; do not assume |
| Expected deposits | Owner contributions and supported payment-processor settlements now; G-101/G-102 lodging payouts after the counsel- and CPA-supported effective transition. Keep pre-formation payouts separately labeled. |
| Expected withdrawals | Enter only supported current categories, such as software, hosting, advertising, refunds, taxes, and documented contractor/vendor payments |
| International activity | Describe the confirmed plan accurately: MLADIS LLC is transitioning the G-101 and G-102 Dominican Republic vacation-rental operations into the company. State that the legal property/operating-authority and accounting transition is in progress; do not claim completed title, local registration, or licensed-operator status until documented. |
| Cash activity | Enter the actual expected amount and frequency; do not assume |
| Credit request | None at initial bank opening |

## Banking Controls

- Use the existing Mercury checking account as the primary business money lane
  after current status and funding are verified.
- Do not enable overdraft credit, credit line, business loan, merchant cash advance, or personal guarantee product without a separate written owner decision.
- Keep a reserve for refunds, chargebacks, damage-deposit release timing, taxes, and repairs.
- Reconcile bank statements monthly against Airbnb payouts, direct bookings, Stripe/PayPal, invoices, refunds, and vendor payments.
- Store bank statements outside Git in the private business-records vault.

## FinCEN / Beneficial Ownership Note

FinCEN's current public guidance says U.S.-formed domestic companies and U.S. persons are exempt from FinCEN BOI reporting under the current rule. Banks may still ask for beneficial-owner and control-person information for their own know-your-customer process. Provide that information directly to the bank; do not commit ID numbers, SSN, EIN, or identity documents to Git.

Sources:

- IRS EIN page: https://www.irs.gov/businesses/employer-identification-number
- FinCEN BOI page: https://www.fincen.gov/beneficial-ownership-information-reporting

## Private Drive Version

The bank-ready private version is stored outside Git as
`bank-account-opening-packet.md` in `05-banking` within the existing owner-only Drive record.
Use [private-records-manifest.md](private-records-manifest.md) to distinguish it
from the link-accessible AIRBNB mirror.
