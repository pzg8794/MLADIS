# MLADIS LLC Next Steps

Private operating checklist. This is an implementation tracker for MLADIS LLC and not legal, tax, or accounting advice.

## Current State

- MLADIS LLC appears in New York Business Express as `Approved/Issued`.
- Articles of Organization application `DOS1336-2026-029778` was submitted and approved on 2026-06-03.
- The portal shows the $200 formation payment and transaction ID in the confirmation/status history.
- The NYBE status page says the Department of State item has been filed and approved.
- The downloaded application confirmation is archived at `docs/business/source-documents/MLADIS_LLC-Confirmation.pdf`.
- No optional copies, certificate of status, optional registered agent, or optional service-of-process email were selected during formation.

## Immediate Checklist

| Priority | Item | Target date | Status | Notes |
| --- | --- | --- | --- | --- |
| High | Save NYBE application confirmation | 2026-06-03 | Done | Archived at `docs/business/source-documents/MLADIS_LLC-Confirmation.pdf`. This is not the filing acknowledgement. |
| High | Verify portal filing status | 2026-06-03 | Done | NYBE status history shows `Approved/Issued` and says the Department of State item has been filed and approved. |
| High | Download or print the NYBE filing acknowledgement | ASAP | Todo | Use NYBE Recent Activity or the `View Acknowledgement` link from the profile/status page. Keep a copy outside the repo if it contains sensitive/payment details. |
| High | Verify the official Department of State filing receipt details | ASAP | Todo | NY DOS says the filing receipt is proof of filing and no duplicate receipt is issued to replace a lost or destroyed one. The acknowledgement/receipt file still needs to be saved. |
| High | Draft MLADIS LLC operating agreement package | 2026-06-03 | Done | Draft package is in `docs/business/operating-agreement/`. |
| High | Sign MLADIS LLC operating agreement and initial member consent | 2026-09-01 | Todo | NY DOS says members must adopt a written operating agreement before, at, or within 90 days after filing Articles of Organization. |
| High | Prepare Queens publication package | 2026-06-03 | Done | Draft package is in `docs/business/publication/`. |
| High | Start the New York publication process | 2026-10-01 | Todo | Send the filing acknowledgement/receipt to Queens County Clerk, receive newspaper designations, publish for six weeks, collect affidavits, then file Certificate of Publication. |
| High | Prepare IRS EIN worksheet | 2026-06-03 | Done | Worksheet is in `docs/business/ein-and-banking/ein-worksheet.md`. |
| High | Apply for an IRS EIN | After filing receipt is saved | Todo | Use the official IRS EIN Assistant. Do not use third-party EIN services. |
| High | Open a business bank account | After EIN | Todo | Keep MLADIS income, deposits, reimbursements, and expenses separate from personal accounts. |
| Medium | Create bookkeeping starter chart of accounts | 2026-06-03 | Done | Draft chart is in `docs/business/ein-and-banking/bookkeeping-chart-of-accounts.md`; review with CPA before tax filing. |
| Medium | Implement bookkeeping system in selected tool | After bank account | Todo | Track lodging revenue, deposits/holds, refunds, platform fees, cleaning, repairs, charitable donations, software, hosting, advertising, taxes, and owner contributions/distributions. |
| Medium | Decide tax/accounting treatment with a CPA | Before first tax filing | Todo | A single-member LLC is often disregarded for federal tax by default, but verify based on MLADIS ownership and future AI/business plans. |
| Medium | Confirm sales tax, hotel occupancy, short-term rental, and local compliance obligations | Before direct bookings go live | Todo | Airbnb platform compliance does not automatically cover direct-booking obligations. |
| Medium | Archive Diana contractor agreement | 2026-06-03 | Done | Signed contractor agreement is archived in `docs/business/source-documents/contractor-agreements/`. |
| Medium | Prepare MLADIS LLC contractor ratification/assignment | 2026-06-03 | Done | Draft bridge document is in `docs/business/operations/contractor-ratification-and-assignment-draft.md`; signing still pending. |
| Medium | Configure `mladis.com` business email and DNS records | Before customer-facing launch | In progress | Keep Google Workspace MX/SPF/DKIM/DMARC stable before using a `@mladis.com` mailbox for production emails. |
| Medium | Store production secrets in a proper secret manager | Before live payments/agents | Todo | Stripe, OpenAI, SMTP, OAuth, and calendar credentials must stay out of Git. |
| Low | Evaluate MWBE certification or other NY business incentives | Later | Todo | NYBE links to MWBE and incentive resources; revisit once core operations are stable. |

## Publication Workplan

1. Contact the Queens County Clerk for the two newspapers designated for the LLC publication requirement.
2. Publish the Articles of Organization or a formation notice in both newspapers for six consecutive weeks.
3. Collect affidavits of publication from both newspapers.
4. File the Certificate of Publication with the affidavits attached.
5. Pay the current Department of State filing fee.
6. Store the filed Certificate of Publication and affidavits in the private business records folder, not in public website assets.

Target deadline from 2026-06-03 plus 120 days: 2026-10-01.

## How To Check Whether Filing Happened

The downloaded `MLADIS_LLC-Confirmation.pdf` alone means the application was submitted and paid. It does not by itself mean the Department of State accepted the filing.

The filing is considered approved in NYBE when the status page shows:

- `Approved/Issued`
- `Approved Date: 06/03/2026`
- `An item submitted using the New York Business Express portal to the New York Department of State has been filed and approved.`

The remaining evidence task is to save the filing acknowledgement or filing receipt from the `View Acknowledgement` link.

## Operating Agreement Workplan

Draft the agreement before the 90-day target of 2026-09-01. The first MLADIS agreement should at least cover:

- Member and ownership information.
- Whether the LLC is member-managed or manager-managed.
- Authority to sign contracts, open bank accounts, manage booking platforms, and hire vendors.
- Capital contributions and owner reimbursements.
- Profit/loss allocation and distributions.
- Treatment of customer deposits, refunds, damages, chargebacks, and platform fees.
- Rules for using AI agents, customer data, OAuth integrations, calendars, and email automation.
- Recordkeeping, tax classification, and bookkeeping responsibilities.
- How to admit future members or investors.
- Dissolution, dispute resolution, and amendment process.

## Direct-Booking Compliance Notes

Before MLADIS takes direct reservations outside Airbnb, confirm:

- Applicable lodging, hotel occupancy, sales, local, or tourism taxes.
- Required short-term rental permits or local restrictions for each property location.
- Payment processor rules for security deposits, holds, refunds, and chargebacks.
- Customer-data consent language for email/SMS promotions.
- Cancellation/refund terms shown before payment.
- Insurance and liability coverage for direct bookings.

## Federal BOI Status

As of the official FinCEN quick reference reviewed on 2026-06-03, entities created in the United States, including domestic LLCs, are exempt from federal BOI reporting under FinCEN's 2025 interim final rule. Re-check FinCEN before relying on this for a future deadline because BOI rules have changed rapidly.

## Official Source Links

- NY DOS Articles of Organization for Domestic LLC: https://dos.ny.gov/node/35506
- NY DOS Certificate of Publication for Domestic LLC: https://dos.ny.gov/node/16241
- NY Senate LLC Law records requirement, Section 1102: https://www.nysenate.gov/legislation/laws/LLC/1102
- IRS EIN online application: https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online
- FinCEN BOI quick reference: https://www.fincen.gov/boi/quick-reference
