# Public guest guide and voluntary offers

## Pages

- `/airbnb-stay-guide/`: multilingual supplemental guide for the three overnight Airbnb listings. No checkout clock time, payment/deposit link, acceptance button, signup, or direct-booking promotion. Existing reservation terms remain authoritative; earlier bookings keep their original terms.
- `/offers/`: independent public offers form. It must not be promoted through Airbnb listings/messages or linked from the Airbnb stay guide. Use independently acquired public audiences and MLADIS's own marketing channels.
- `/offers/privacy/`: purpose, storage and withdrawal notice.

The legacy `/property-rules/` document and direct-booking payment flow are unchanged. The new guide addresses their conflicting checkout/deposit language by providing a separate, informational URL.

## Language selection

The guide, offers form, privacy notice, status/confirmation/unsubscribe pages and verification email support English, Spanish, French and Portuguese. An explicit `?lang=en|es|fr|pt` choice takes priority, followed by the feature's saved language cookie, then the browser's weighted `Accept-Language` preferences (including regional variants such as `fr-CA` or `pt-BR`). Unsupported preferences fall back to English. No location or translation service receives visitor data.

The visible switcher works without JavaScript and saves the explicit preference for one year in an HttpOnly, SameSite=Lax cookie (Secure on HTTPS). Language links retain the current route/token but drop unrelated query parameters. Responses declare Content-Language and vary by Accept-Language and Cookie. Other site pages and global language settings are unchanged.

Signup snapshots the exact translated choices and consent version. Confirmation records that original language even if the confirmation page is viewed in another language; each confirmation appends the exact evidence to protected consent history. Earlier seasonal consent remains recorded after a later discount-only request. Pre-localization consent evidence is retained on reconfirmation. Verified seasonal signups set the existing customer profile's preferred language for future audience selection. This does not translate arbitrary future campaign copy or enable/send campaigns. The existing delivery gate remains disabled.

## Audience state

`AudienceSubscription` is separate from reservation contact data. The form offers two independent, initially unchecked purposes: a welcome discount and occasional seasonal offers. Neither a booking email nor an imported guest record is consent.

The email is normalized and validated. A signed confirmation capability expires after 48 hours; GET does not activate it, and CSRF-protected POST confirms the selected purposes. Pending requests cannot receive promotions. Repeated requests have a persisted per-address 15-minute resend cooldown and a database-backed 30-per-hour source cap. Source hashes expire after a day; raw IP addresses are not stored by this feature.

Confirmed seasonal consent links to the existing customer profile. A discount-only confirmation does not opt into recurring marketing. Tokens contain a random public ID and nonce, not the email. The object lake stores the protected audience state under CUSTOMERS; nonce fields are redacted. Short-lived anti-abuse counters are intentionally excluded from object-lake export.

## Welcome discount

Confirmation can issue one high-entropy 10% percentage coupon with a one-redemption limit. It is tied to the confirmed email, reserved when an eligible direct booking request is created, and bound to that inquiry. Checkout can reprice that same inquiry without redeeming again. Reuse on another inquiry/email is rejected. A failed inquiry save rolls back coupon reservation. Existing unrelated coupons retain their prior behavior. No automatic expiry was invented.

The discount applies to the existing lodging subtotal; taxes, separate fees and deposits are excluded. Availability and the final quote apply. It is not applied to existing reservations or combined with another code. This feature does not change nightly prices, fee settings, booking calendars or reservation terms.

## Withdrawal and campaign sends

Each confirmation page/email supplies a stable, signed unsubscribe URL. GET displays a confirmation; POST suppresses recurring offers and invalidates pending confirmations. It also suppresses matching legacy profile duplicates. An already issued welcome code is not revoked by unsubscribing.

The existing promotion sender rechecks both profile and public subscription consent at send time. For this audience it requires a verified public business mailing address configured under the Django admin's **Audience campaign settings / Offers email footer**, and adds that address, promotional identification and the self-service unsubscribe link. No campaigns are sent by installation or deployment. Do not publish a private legal address as the mailing address without authorization.

## Delivery gate and current mailbox blocker

Public signup defaults to disabled (`AudienceCampaignSettings.signup_enabled=False`). The page explicitly says signup is temporarily unavailable and accepts no email submission while disabled. Enable only after delivering a confirmation email and verifying its arrival through the documented agent mailbox.

The October 29, 2026 preflight found SMTP configured on production, but the existing agent mailbox credential was rejected by both IMAP and SMTP (535 BadCredentials). The approved local, reference and prior runtime envs contain no replacement, and the configured Cloud Secret Manager has no mailbox secret. No password was guessed, generated, printed, committed or reset. The web-app agent password is a different credential and must not be tried against the mailbox.

Recovery follows `docs/environment-provider-contract.md` and `docs/agent-admin-login.md`: reuse the dedicated mailbox's approved runtime secret path; preserve other production env values. A human principal must complete any required password/app-password creation step under the browser credential policy. After restoration, authenticate SMTP, deliver and retrieve a verification email privately, and only then enable signup in the admin. Keep the mailing-address field empty until a verified public business address is supplied; this independently blocks future promotional campaign sends.

## Verification

Focused tests cover the delivery gate, purpose separation, honeypot/throttling, duplicate response, pending state, signature expiry/tampering/replacement, CSRF, read-only GETs, unsubscribe suppression, exact coupon value/email binding, one-use claims and rollback, bound-inquiry repricing, existing coupon compatibility, postal footer gate, and guide/marketing separation.

Desktop and narrow-browser rendering were inspected through the canonical launcher. The browser constrained the requested narrow viewport to 582px; no horizontal overflow or broken image was observed. No 390px visual claim is made. Preview used an isolated task database, reused the canonical env/venv through temporary symlinks, and sent no real mail. The symlinks and preview runtime were removed after inspection. Auth source/configuration, payment providers and the original dirty checkout are outside this feature's edit scope.
