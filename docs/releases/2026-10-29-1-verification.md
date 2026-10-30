# Production verification — public guest resources

Verified release: `release/2026.10.29-1`

Deployed application commit: `b56e922a51a6e97bacf9057835c9e84abb504e1a`

Deployment timestamp: `2026-10-30T03:41:48Z` (October 29, 2026, 11:41:48 p.m. EDT).

Artifact SHA-256: `11dde05b96cea0c7111ec5285dfc024e46739688a58d5feebf953aaca8861224`

Rollback target: `release/2026.09.27-1`

Runtime backup retained: `/home/pitergarcia/airbnb_agent/runtime_backups/mladis-runtime-20261030T034216Z.tar.gz`

## Verified

- Existing non-pruning deployment script completed; service active/running. Production env, database, media and runtime backups were preserved.
- Additive migrations `0029_public_guest_resources` and `0030_offer_signup_delivery_gate` applied; Django check clean; static collection succeeded.
- Live browser rendered `https://mladis.com/airbnb-stay-guide/` in English and Spanish. No broken images or horizontal overflow at the default viewport. The page links only to its language anchors and the three Airbnb listings; no payment, deposit or marketing link.
- Live browser rendered `https://mladis.com/offers/` with the explicit email-delivery-unavailable notice and no active form. This is the intended disabled state, not an enabled signup claim.
- Origin HTTP checks: health, home, account login, guide, offers and offers privacy returned 200; admin and ops dashboard correctly redirected unauthenticated requests to login.
- Mac urllib requests were rejected by the existing Cloudflare rule (403 / error 1010). Native browser checks and authenticated server-origin diagnostics succeeded. No Cloudflare rule was changed.
- Production-code integration smoke used the actual production schema inside a deliberately rolled-back transaction, in-memory email backend, and disabled object-lake writes. Pending state, read-only confirmation GET, confirmation POST, exact 10% coupon, unsubscribe GET/POST and suppression passed. All synthetic audience/coupon/config rows were rolled back, with counts unchanged. No real email was sent.
- Source validation: 309 full bookings tests and 15 focused feature tests passed; migration drift clean; frontend build passed with unchanged compiled outputs.
- Existing build warnings: Node 23 is outside several frontend tooling engine ranges; dependency audit reported 9 pre-existing vulnerabilities (7 high). No package declaration or lockfile was changed by this feature and no unrelated dependency repair was attempted.

## Still blocked

The dedicated automation mailbox's saved credential is rejected by Google (IMAP authentication failure; SMTP 535 / BadCredentials). The existing MLADIS runbooks, canonical/reference/prior runtime env paths and configured Cloud Secret Manager were checked; no valid replacement was found. The web-app admin password was not tried as a mailbox password. No authentication credential was reset or generated.

The signup gate must remain disabled until mailbox delivery is restored and a real confirmation email is received/verified. A verified public business postal address must also be configured before sending promotional campaigns. No Airbnb guest list was imported and no marketing campaign was sent.

Overall feature status: guide published and verified; audience/coupon/consent/unsubscribe implementation deployed and tested, but public signup NOT ACTIVE because confirmation delivery is unavailable.

The approved marketing checkout is clean after committing this verification note. Existing unrelated worktrees and the original dirty checkout were preserved; no new worktree or stash was created. Task-created preview and authentication tabs/processes were closed. The two final production pages remain for review; local temporary env/venv symlinks were removed. The canonical launcher populated its missing agent phone metadata during local setup; no stored password was changed.
