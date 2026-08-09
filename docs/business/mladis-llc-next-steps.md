# MLADIS LLC Next Steps

Public-safe operating checklist. Private identifiers, signed filings, tax forms, affidavits, bank records, and personal financial information stay in the separate private Drive record. This is an implementation tracker, not legal, tax, accounting, or lending advice.

## Current State

- MLADIS LLC appears in New York Business Express as `Approved/Issued`.
- Articles of Organization application `DOS1336-2026-029778` was submitted and approved on 2026-06-03.
- The portal shows the $200 formation payment and transaction ID in the confirmation/status history.
- The NYBE status page says the Department of State item has been filed and approved.
- Canonical owner-only copies of the application confirmation, filing receipt,
  and Articles packet are secured in Drive. Historical public-repo copies
  require privacy review.
- No optional copies, certificate of status, optional registered agent, or optional service-of-process email were selected during formation.
- The MLADIS mailbox confirms that a Mercury business account was approved on
  2026-06-19. Stripe confirmed a bank account was added the same day. Current
  funding, transaction use, and statement availability remain unverified.

## Immediate Checklist

| Priority | Item | Target date | Status | Notes |
| --- | --- | --- | --- | --- |
| High | Save NYBE application confirmation | 2026-06-03 | Done | Canonical owner-only copy secured. This is not the filing acknowledgement; historical public-repo copy requires privacy review. |
| High | Verify portal filing status | 2026-06-03 | Done | NYBE status history shows `Approved/Issued` and says the Department of State item has been filed and approved. |
| High | Download or print the NYBE filing acknowledgement | 2026-06-03 | Done | Canonical owner-only copy secured; historical public-repo copy requires privacy review. |
| High | Verify the official Department of State filing receipt details | 2026-06-03 | Done | Receipt shows DOS ID `7932124`, file number `260603000036`, and authentication number `100010406121`. |
| High | Draft MLADIS LLC operating agreement package | 2026-06-03 | Done | Draft package is in `docs/business/operating-agreement/`. |
| High | Sign MLADIS LLC operating agreement and initial member consent | 2026-06-03 | Done | Executed copies are stored privately; historical public-repo copies require privacy review. |
| High | Secure private Drive records | Immediate | Critical security blocker | Canonical copies of the current legal/loan packet are in the existing flat owner-only Drive folder. The similarly named AIRBNB mirror reported `anyone with the link` writer access on 2026-08-08 and still contains legacy sensitive records. Remove that link permission, assess whether the link circulated, and verify file-level access before treating the archive as secure. |
| High | Prepare Queens publication package | 2026-06-03 | Done | Draft package is in `docs/business/publication/`. |
| High | Complete the New York publication process | 2026-10-01 | Partially complete / urgent | Daily News payment and a reviewed notarized affidavit establish six weekly insertions on 2026-06-10, 06-17, 06-24, 07-01, 07-08, and 07-15. The owner reports The Forum was paid and the record shows its requested card authorization was returned, but the paid receipt, dates, and notarized affidavit remain missing. Follow-ups were sent 2026-07-26 and 2026-08-08; Gmail confirmed the second message was sent. The unsigned Certificate of Publication draft must remain unsigned until The Forum affidavit passes review. See `docs/business/publication/publication-completion-checklist.md` and `publication-activity-log.md`. |
| High | File Certificate of Publication | 2026-10-01 | Blocked by The Forum | After The Forum affidavit passes review, review/sign the private draft, attach both affidavits, include the $50 Department of State fee, retain tracking, and archive the filing receipt. |
| High | Order fresh Certificate of Status | After publication filing | Todo | Order the current $25 Department of State certificate after the Certificate of Publication is accepted for the lender packet. |
| High | Prepare IRS EIN worksheet | 2026-06-03 | Done | Worksheet is in `docs/business/ein-and-banking/ein-worksheet.md`. |
| High | IRS EIN issued and CP 575 saved | 2026-06-03 | Done | EIN was issued on 2026-06-03. The CP 575 G letter and private EIN reference are in the existing flat owner-only Drive record. Do not copy the EIN value into Git or use the link-accessible AIRBNB mirror as the source. |
| High | Complete and submit NYS TR-570 response | Immediate | Overdue / ready to sign | The owner confirmed on 2026-08-08 that it was still not sent; no fax, mailing, or agency acknowledgment was found. The private five-page fax-ready response contains every supported non-signature answer. Owner review, signature, actual signing date, fax transmission, and delivery proof remain. |
| High | Update all business accounts/profiles with MLADIS LLC + EIN | 2026-06-03 | In progress | See `docs/business/platform-account-update-checklist.md` for Airbnb, Squarespace, Cloudflare, Dropbox Sign, Google Workspace, booking app, and bank. |
| High | Verify, fund, and use the Mercury business account | Immediate | Opened / activation evidence pending | Mercury approved the MLADIS LLC account on 2026-06-19 and Stripe recorded a bank account addition that day. Mercury reminders through 2026-07-24 still described the first deposit as pending; no monthly-statement email was found. Verify good standing, fund if still needed, route MLADIS activity through it, and archive bank-generated verification and statements privately. |
| High | Bind business and property-operation insurance | Before loan application / direct booking | Todo | No current insurance binder was found in the MLADIS packet. Review general liability, property, business interruption, cyber, host/short-term-rental, and lender requirements with a broker. |
| High | Remediate historical public-repo private data | Security review | In progress | This docs pass removed the exposed EIN and private contact values from the touched trackers. Other historical docs, signed/source files, code defaults, and Git history still contain personal contact or identity data. Coordinate a current-tree cleanup, secret/identifier exposure assessment, replacements in app configuration, and any required history rewrite before treating the public repo as privacy-clean. |
| Medium | Create bookkeeping starter chart of accounts | 2026-06-03 | Done | Draft chart is in `docs/business/ein-and-banking/bookkeeping-chart-of-accounts.md`; review with CPA before tax filing. |
| Medium | Implement bookkeeping system in selected tool | After OOP booking-system cleanup | In progress | Owner started a bookkeeping/booking system. Leave final cleanup for the MLADIS OOP integration phase, then track lodging revenue, deposits/holds, refunds, fees, cleaning, repairs, donations, software, hosting, advertising, taxes, and owner contributions/distributions. |
| Medium | Decide tax/accounting treatment with a CPA | Before first tax filing | Todo | A single-member LLC is often disregarded for federal tax by default, but verify based on MLADIS ownership and future plans. NY Form IT-204-LL depends on classification and New York-source items; do not assume Dominican lodging revenue is New York-source. |
| High | Complete the G-101/G-102 legal transition to MLADIS | Before a DR operating, asset, revenue, or lender claim | Counsel package prepared / outreach sent | MLADIS was formed to place these two Dominican Republic vacation-rental operations under the company. The private evidence binder and 13 unsigned counsel-review drafts are complete, and an engagement request was sent 2026-08-09. Await secure intake and counsel's current-title/structure plan; then obtain lender/Fiduciaria consent, RNC/Registro Mercantil and tax treatment, HOA confirmation, MITUR/RENATUR review, insurance, and platform/revenue assignment. See `docs/business/dominican-republic-apartment-transition.md`. |
| Medium | Archive Diana contractor agreement | 2026-06-03 | Done | Signed contractor agreement is archived in `docs/business/source-documents/contractor-agreements/`. |
| Medium | Prepare operations acknowledgment | 2026-06-03 | In progress | Owner/MLADIS signature exists; counterparty acceptance remains pending. Canonical copy is private. |
| Medium | Ratify/assign pre-formation contractor agreement to MLADIS LLC | After NY/DR legal-tax review | Draft prepared | Printable unsigned draft is stored in the owner-only Drive record; do not treat the assignment as effective until all required parties sign. |
| Medium | Prepare B-1 business visitor process package | 2026-06-03 | Done | Templates and official source links are in `docs/business/immigration/`; completed sensitive visa-history answers stay outside Git. |
| Medium | Configure `mladis.com` business email and DNS records | Before customer-facing launch | In progress | Keep Google Workspace MX/SPF/DKIM/DMARC stable before using a `@mladis.com` mailbox for production emails. |
| Medium | Store production secrets in a proper secret manager | Before live payments/agents | Todo | Stripe, OpenAI, SMTP, OAuth, and calendar credentials must stay out of Git. |
| Medium | Create funding-readiness tracker and data-room checklist | 2026-07-26 | Done | Public-safe trackers are in `docs/business/funding-readiness/`; the consolidated private legal/loan audit, current blank SBA forms, and unsigned borrowing resolution are in the flat owner-only Drive record. |
| Medium | Create financial-institution resume guide | 2026-06-04 | Done | Resume guide is in `docs/business/funding-readiness/financial-institution-resume-plan.md`; use it for Mercury verification, Airbnb exports, P&L, forecast, lender one-pager, use-of-funds, and lender/CDFI/SBA conversations. |
| Medium | Build lender/grant/investor data room | After Mercury verification and basic financial records | In progress | Use `docs/business/funding-readiness/data-room-index.md` as the checklist. Keep sensitive files outside public app assets. |
| Medium | Prepare first business plan and financial forecast | After bookkeeping setup | Todo | Needs revenue history, direct-booking plan, expense assumptions, and use-of-funds model. |
| Medium | Register SAM.gov / UEI only if a federal grant or contract target is selected | After bank/email readiness | Todo | EIN is ready, but do not register until there is a specific federal grant/contract target and the business email/responsible-party data are ready for official use. |
| Low | Evaluate MWBE certification or other NY business incentives | Later | Todo | NYBE links to MWBE and incentive resources; revisit once core operations are stable. |

## Publication Workplan

1. Preserve the reviewed Daily News affidavit and its six weekly dates privately.
2. Obtain The Forum's paid receipt, exact six weekly dates, completion confirmation, and notarized affidavit.
3. Review The Forum affidavit against the designation, entity name, schedule, notice, and notarization.
4. Review and sign the private Certificate of Publication draft only after both affidavits pass.
5. File the certificate with both affidavits and the current $50 Department of State fee.
6. Store the complete signed packet, tracking, payment proof, and filing receipt privately.
7. Verify the filing history and order a fresh Certificate of Status.

Target deadline from 2026-06-03 plus 120 days: 2026-10-01.

## How To Check Whether Filing Happened

The downloaded `MLADIS_LLC-Confirmation.pdf` alone means the application was submitted and paid. It does not by itself mean the Department of State accepted the filing.

The filing is considered approved in NYBE when the status page shows:

- `Approved/Issued`
- `Approved Date: 06/03/2026`
- `An item submitted using the New York Business Express portal to the New York Department of State has been filed and approved.`

That evidence is secured in the owner-only Drive record. The historical
public-repo source copy requires privacy review.

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

## NYS TR-570 Response Notes

The private NYS TR-570 packet is stored in the existing MLADIS private tax/EIN Drive folder, not in Git. See `docs/business/ein-and-banking/private-records-manifest.md` for filenames and storage rules.

Current response status as of 2026-08-08:

- The owner confirmed the form was not sent. No submission proof or agency acknowledgment was found; treat the response as overdue and unsubmitted.
- Fax-ready unsigned five-page response prepared from the 2026-06-17 notice.
- Entity, tax treatment, start, member, officer, identifier, and
  not-a-successor facts are filled from the private formation, tax,
  governance, identity, and prior-response records.
- NAICS `721199` is filled because the documented current production activity
  is vacation stays and direct booking, and the official classification covers
  other short-term traveler accommodation.
- Signer title is filled from the executed governance record.
- Only the owner's signature and actual signing date remain blank.
- Exact fax and mailing methods from the notice are recorded only in the private field plan and August 8 submission-control log.

## Ownership Disclosure And Recurring Filing Status

- Current FinCEN rules exempt entities created in the United States from federal BOI reporting.
- Current New York beneficial-ownership rules apply to LLCs formed under foreign-country law and authorized in New York, not MLADIS LLC as a domestic New York LLC.
- First New York Biennial Statement is expected in June 2028; verify current rules before filing.
- Form IT-204-LL applies only if the applicable classification and New York-source income, gain, loss, or deduction tests are met. A CPA must determine the 2026 obligation; if applicable for a calendar-year entity, the normal deadline is the 15th day of the third month after year-end.
- No assumed-name filing was found. Use `MLADIS LLC` on legal, tax, banking, and lending documents unless an assumed-name certificate is filed and accepted.
- Public Git is not yet privacy-clean. Do not add any completed form, private
  Drive URL, affidavit, signed filing, tax ID, home address, personal contact
  value, bank record, or owner financial statement while the remediation item
  remains open.
- The legacy AIRBNB Drive mirror is also not private while its link-access
  permission remains active. Use only the owner-only Drive record named in the
  private records manifest.

## Official Source Links

- NY DOS Articles of Organization for Domestic LLC: https://dos.ny.gov/node/35506
- NY DOS Certificate of Publication for Domestic LLC: https://dos.ny.gov/certificate-publication-domestic-limited-liability-company-0
- NY DOS Certificate of Status: https://dos.ny.gov/certificate-status
- NY DOS LLC FAQs / Biennial Statement: https://dos.ny.gov/node/35461
- NY LLC annual filing fee: https://www.tax.ny.gov/pit/efile/annual_filing_fee.htm
- NY Senate LLC Law records requirement, Section 1102: https://www.nysenate.gov/legislation/laws/LLC/1102
- IRS EIN online application: https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online
- FinCEN BOI FAQs: https://www.fincen.gov/boi-faqs
- NY beneficial ownership FAQs: https://dos.ny.gov/beneficial-ownership-disclosure-frequently-asked-questions
- SBA Lender Match: https://www.sba.gov/funding-programs/loans/lender-match-connects-you-lenders
- NY Tax Publication 910, NAICS Codes for Principal Business Activity: https://www.tax.ny.gov/pdf/publications/general/pub910.pdf
- U.S. Census NAICS 721199, All Other Traveler Accommodation: https://www.census.gov/naics/?details=721199&input=721199&year=2022
