# Publication Activity Log

Operational log for the MLADIS LLC New York publication requirement. This file records what was verified, what was only attempted, and what still needs owner action.

## 2026-07-26 - Compliance Audit And Newspaper Follow-Ups

- The private publication record now contains the Queens designation letter, NY Daily News order proof, approval/invoice, and email confirmation.
- NY Daily News order #87497 was paid for $235. The invoice identifies a classified run from 2026-06-10 through 2026-06-15. That appears to be six consecutive days, not one insertion in each week for six successive weeks, so it is not accepted as proof of statutory completion.
- The Forum quoted $375 in advance, including notarized-affidavit processing. The private email record shows that payment authorization was returned on 2026-06-19. No final receipt, six weekly dates, or notarized affidavit was found.
- No notarized affidavit from either newspaper was found in the connected private Drive, local records, or connected MLADIS mailbox.
- Follow-up sent to The Forum on 2026-07-26 requesting the exact six weekly dates, completion status, paid receipt, and notarized affidavit.
- Compliance-correction request sent to NY Daily News on 2026-07-26 requesting every insertion date, confirmation of the six-successive-weeks schedule, a no-charge correction or rerun if needed, and the final notarized affidavit. No new charge was authorized.
- An unsigned Certificate of Publication draft and a private closeout checklist were prepared in the existing private `06-publication` folder. The certificate must remain unsigned until both affidavits establish compliant publication.
- Calculated 120-day deadline from the 2026-06-03 formation date: **2026-10-01**.
- Public filing-history review found the Articles filing but no Certificate of Publication as of this audit.

## 2026-06-10 - Status Sweep

- NY Daily News is no longer an open placement/payment task. Order #87497 was placed and paid on 2026-06-08, with first run scheduled for 2026-06-10 and affidavit delivery expected by email after the run completes.
- The Forum remains open. Two emails were sent on 2026-06-08; cost, payment method, and first publication date are still waiting on newspaper reply.
- The overall NY publication requirement remains in progress until both papers complete publication, both affidavits are collected, and the Certificate of Publication is filed with NY DOS.

## 2026-06-03 - Queens County Clerk Designation Request Sent

- Account used: private MLADIS company mailbox.
- Thread subject: `Request for LLC Newspaper Publication Designation - MLADIS LLC`.
- Visible email details verified in Gmail on 2026-06-08:
  - Sent by the owner from the private MLADIS company mailbox.
  - Sent to `QCC-LLC`.
  - Timestamp visible in Gmail: June 3, 2026, 7:23 AM.
  - LLC name: `MLADIS LLC`.
  - Entity type: Domestic Limited Liability Company.
  - Department of State application ID: `DOS1336-2026-029778`.
  - DOS ID: `7932124`.
  - DOS file number: `260603000036`.
  - Date filed/approved: June 3, 2026.
  - County office location: Queens County.
  - Owner contact details: stored in the private business record.
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

- Repo documentation says an email was sent to `forumsouth@gmail.com` from the private MLADIS company mailbox on 2026-06-08.
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
  - Account: private MLADIS company mailbox
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
- Package: Legal - LLC
- Publications: New York Daily News Classified, NDN Public Notices, New York Daily News Affidavit
- Run dates: 06/10/2026 – 06/15/2026 (6 consecutive days)
- Amount paid: **$235.00** (credit card)
- Affidavit delivery: private MLADIS company mailbox
- Status at order time: **Pending Approval**
- Confirmation URL: `https://advertising.nydailynews.com/manage-orders`

Save the order confirmation email when it arrives at garcp37@mladis.com.

## Current Next Actions

1. **[Urgent correction]** Obtain NY Daily News written confirmation of a compliant once-per-week schedule or a no-charge six-week correction/rerun.
2. **[Waiting]** Obtain The Forum's paid receipt, exact six weekly dates, completion confirmation, and notarized affidavit.
3. Record only affidavit-supported weekly publication dates in `publication-completion-checklist.md`.
4. Review both affidavits for exact entity name, designated paper, six successive weeks, and notarization.
5. Complete and sign the private Certificate of Publication draft only after both affidavits pass review.
6. File the certificate with both affidavits and the $50 Department of State fee; retain tracking, a full packet copy, and the filing receipt.
7. Order a fresh Certificate of Status after the publication filing is accepted for the lender packet.
