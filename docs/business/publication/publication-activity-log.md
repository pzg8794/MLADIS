# Publication Activity Log

Operational log for the MLADIS LLC New York publication requirement. This file records what was verified, what was only attempted, and what still needs owner action.

## 2026-06-10 - Status Sweep

- NY Daily News is no longer an open placement/payment task. Order #87497 was placed and paid on 2026-06-08, with first run scheduled for 2026-06-10 and affidavit delivery expected by email after the run completes.
- The Forum remains open. Two emails were sent on 2026-06-08; cost, payment method, and first publication date are still waiting on newspaper reply.
- The overall NY publication requirement remains in progress until both papers complete publication, both affidavits are collected, and the Certificate of Publication is filed with NY DOS.

## 2026-06-03 - Queens County Clerk Designation Request Sent

- Account used: `garcp37@mladis.com`.
- Thread subject: `Request for LLC Newspaper Publication Designation - MLADIS LLC`.
- Visible email details verified in Gmail on 2026-06-08:
  - Sent by Piter Garcia from `garcp37@mladis.com`.
  - Sent to `QCC-LLC`.
  - Timestamp visible in Gmail: June 3, 2026, 7:23 AM.
  - LLC name: `MLADIS LLC`.
  - Entity type: Domestic Limited Liability Company.
  - Department of State application ID: `DOS1336-2026-029778`.
  - DOS ID: `7932124`.
  - DOS file number: `260603000036`.
  - Date filed/approved: June 3, 2026.
  - County office location: Queens County.
  - Contact name: Piter Zacari Garcia Bautista.
  - Contact email used in the email body: `garciapiterz@gmail.com`.
  - Contact phone: `631-575-4841`.
  - Attachment visible in Gmail: filing receipt / Articles packet.

## 2026-06-08 - Queens County Clerk Designation Received

- Gmail thread summary visible on 2026-06-08 states:
  - MLADIS requested LLC publication designation for Queens County.
  - `QCC-LLC` designated NY Daily News for daily publication.
  - `QCC-LLC` sent `MLADIS LLC.pdf`.
- The designation letter is archived in the repo at:
  - `docs/business/source-documents/MLADIS_LLC-Publication-Designation-Letter-2026-06-08.pdf`
- The archived letter should remain the source of truth for newspaper names and contact details.
- The letter says to submit the raised-seal designation letter to each designated newspaper.

## 2026-06-08 - Designated Newspapers

Daily newspaper:

- `NEW YORK DAILY NEWS`
- 270c Duffy Avenue
- Hicksville, NY 11801
- Phone: `212-210-2111`
- Placement site: `placeanad.nydailynews.com`

Weekly newspaper:

- `THE FORUM`
- Howard Beach, NY 11414
- Phone: `718-845-3221`
- Email: `forumsouth@gmail.com`
- Note: the address line extracted from the PDF is difficult to read. Use the official PDF and the newspaper reply before mailing anything physical.

## 2026-06-08 - Forum Email Status

- Repo documentation says an email was sent to `forumsouth@gmail.com` from `garcp37@mladis.com` on 2026-06-08.
- The documented subject is: `LLC Publication Notice Request - MLADIS LLC`.
- The email asks for:
  - cost,
  - accepted payment methods,
  - earliest first publication date,
  - any format requirements.
- Status as of this log:
  - Follow-up sent on 2026-06-08 through the configured MLADIS SMTP account.
  - Follow-up subject: `Follow-up: LLC Publication Notice Request - MLADIS LLC`.
  - Sent to: `forumsouth@gmail.com`.
  - CC: `garcp37@mladis.com`.
  - Reply-To: `garcp37@mladis.com`.
  - Attachment included: `MLADIS_LLC-Publication-Designation-Letter-2026-06-08.pdf`.
  - SMTP result: `sent_count=1`.
  - Awaiting reply from The Forum with cost, payment method, and first publication date.

## 2026-06-08 - NY Daily News Pre-Order Navigation

- NY Daily News placement flow was identified:
  - Legal Notices
  - LLC / registering an LLC package
  - URL documented in the checklist.
- This section is superseded by the later 2026-06-08 order record below. NY Daily News is now placed and paid.

## 2026-06-08 - Browser / Tooling Audit

- Chrome profile that contains the MLADIS Gmail session:
  - Profile name: `mladis.com`
  - Chrome profile directory: `Profile 8`
  - Account: `garcp37@mladis.com`
- The Chrome plugin was explicitly attempted after the user requested `@chrome`.
- The Chrome plugin connection returned no claimable user tabs even when the Gmail tab was visibly open.
- A direct visible-screen check confirmed the MLADIS Gmail inbox and the QCC thread.
- Low-level local screen interaction was used only to open the already-visible QCC thread; no new email was sent and no payment was submitted.
- Future agents must not claim the mailbox was fully searched unless the Chrome tab is actually claimable or a screenshot/connector result proves the search.

## 2026-06-08 - Session Wrap / Docs Sync

Session completed by owner and agent (2026-06-08 evening).

What was fully accomplished this session:

- Queens County Clerk designation letter received and archived.
- Both newspapers identified and recorded: NY Daily News (daily) and The Forum (weekly).
- Initial notice email sent to The Forum at `forumsouth@gmail.com`.
- Follow-up sent to The Forum with designation letter PDF attached.
- NY Daily News LLC notice order flow navigated to: Legal Notices → LLC package at `advertising.nydailynews.com`. Owner later completed the order/payment; see the order record below.
- Activity log, README, checklist, next-steps, and owner action center all updated and committed.
- Stale "wait for designation" instructions removed from docs so future agents follow correct post-designation workflow.
- Commits on `feature/signin-contracts-ci`: `b78bf6f`, `574cb21`, `51d6165`, `882f34c`, `d0f5052`.

What is explicitly NOT done yet:

- The Forum reply: awaiting response to the two emails sent. Once they reply with cost and first date, pay and record the start date.
- No Dropbox Sign sends have been made — Diana signature on the Founding Operations Pillar Acknowledgment is still pending.

## 2026-06-08 - NY Daily News Order Placed

- Order placed by owner after agent navigated all 5 steps of the ad configuration wizard.
- Order number: **87497**
- Account number: 15494
- Package: Legal - LLC
- Publications: New York Daily News Classified, NDN Public Notices, New York Daily News Affidavit
- Run dates: 06/10/2026 – 06/15/2026 (6 consecutive days)
- Amount paid: **$235.00** (credit card)
- Affidavit delivery: Email to garcp37@mladis.com, contact: Piter Garcia
- Status at order time: **Pending Approval**
- Confirmation URL: `https://advertising.nydailynews.com/manage-orders`

Save the order confirmation email when it arrives at garcp37@mladis.com.

## Current Next Actions

1. **[Waiting]** NY Daily News order approval — watch garcp37@mladis.com for confirmation email. Save it.
2. **[Waiting]** The Forum reply — confirm cost, payment, and first publication date.
3. Record The Forum's first publication date once confirmed.
4. Track all six weekly runs in the table in `publication-completion-checklist.md`.
5. Collect affidavit of publication from each newspaper after final run.
6. File Certificate of Publication with NY DOS, attach both affidavits, pay $50 filing fee, save confirmation.
