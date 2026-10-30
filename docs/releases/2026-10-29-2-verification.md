# Guest resource languages — release verification

Status: production language update VERIFIED. Authorized stakeholder email sent and read back; WhatsApp send result remains unverified after a macOS capture failure at the Send action.

## Deployment identity

- Release: `release/2026.10.29-2`.
- Commit: `bbaecfb05286bd5c7688bea8e75aa73deddddf8f`.
- VM identity timestamp: `20261030T035746Z` (October 29, 2026, 11:57:46 p.m. EDT); service restarted at 03:58:33 UTC.
- Archive SHA-256: `3940fbc827ce5ab12f77b25664b651ebf7835783d6dc4a5899588f617bc754d9`.
- Rollback: `release/2026.10.29-1`.
- Target: existing `mladis-test-1`, project `mledis`, zone `us-central1-a`.
- Runtime backup retained: `/home/pitergarcia/airbnb_agent/runtime_backups/mladis-runtime-20261030T035815Z.tar.gz`.
- Additive migrations 0031 and 0032 applied successfully. Existing runtime secrets, database records and media were preserved. Existing signup delivery gate remains disabled.

## Live verification

- Public browser rendered the guide in English, Spanish, French and Portuguese using the actual visible switch links. The selected language and page text changed correctly.
- A Portuguese manual selection carried to `/offers/` without a language query, proving the saved preference works across feature routes.
- Spanish privacy notice rendered with the language disclosure and Spanish return link.
- The guide retained accurate reservation counts, occupancy 7/7/14, visitor and care guidance, prior-reservation protection and the three exact Airbnb links. No marketing/payment/deposit link was introduced.
- At the actual 1280px viewport, no horizontal overflow or broken images was observed. The viewport override did not change the actual page width; no narrow/mobile visual-verification claim is made for this release. Temporary override was reset.
- Production origin checks: `/healthz`, `/`, `/accounts/login/`, `/offers/`, `/offers/privacy/` returned 200; `/admin/` and `/ops/dashboard/` redirected to their normal sign-in destinations.
- Actual production Accept-Language requests selected Spanish for `es-DO, en;q=0.8`, French for `fr-CA;q=0.9, es;q=0.4`, Portuguese for `pt-BR` and English fallback for unsupported German/Chinese. Responses declared the correct Content-Language and `Vary: Accept-Language, Cookie`.
- No production signup, coupon, confirmation email or marketing campaign was created by verification. The separate operator-requested stakeholder email used the already authenticated Gmail connection.

## Tests and source hygiene

- Django check passed and migration drift check reported no changes.
- Full bookings suite: 316 passed before the final pre-localization consent fallback was added.
- Final focused public resources/localization suite: 23 passed, including the new fallback and multilingual consent-history regressions.
- TypeScript/Vite Django build passed; generated tracked bundles remained unchanged. Existing runtime stay-image warning and Node/npm dependency warnings were not changed by this feature.
- `git diff --check` passed. Source commit and immutable release tag were pushed before deploying.
- Environment: MLADIS Stable Dev Environment; repository `pzg8794/MLADIS`; approved branch `codex/marketing-funnel-unblocker`; active object public guest resources. Fifteen source/documentation files changed in the deployment commit; exact list is available in its Git diff.
- No auth, global locale configuration, provider credentials, reservation, price, calendar or Airbnb listing setting was changed by this release.
- No new worktree or stash was created. The two pre-existing other worktrees, their commits and unrelated modifications were preserved. Deployment archive/package paths were cleaned by the deployment script; runtime backup is intentionally retained.

## Evidence and stakeholder updates

Private browser proof is retained in the existing private business-records folder under `airbnb-house-rules-2026-10-29/language-release-2026-10-29/`; it includes the Spanish screenshot and browser text, without publishing customer data to Git.

Piter explicitly requested a Spanish update to Diana by email and WhatsApp after completion. The email was sent from the authenticated MLADIS account and read back with the SENT label, correct recipients, subject and guide URL. Its text clearly distinguishes the published guide from the still-disabled audience signup. The WhatsApp message was composed in Diana's existing native chat; macOS capture failed at the Send action. Browser fallbacks required device linking, so no new account/session was linked and no duplicate was sent. User-visible access is needed to determine the native send result.

## Remaining limitation

The automated confirmation-email credential remains rejected. Signup remains disabled until delivery is restored and independently verified. Future promotional campaign copy is not automatically translated by this feature; preferred language is recorded for audience selection. Supported public-resource translations are English, Spanish, French and Portuguese, with English fallback.
