# MLADIS LLC — Services & Costs Inventory

Last updated: 2026-06-04. Tracks every platform, subscription, and service used by MLADIS LLC operations.

---

## Legend

| Column | Meaning |
| --- | --- |
| Login email | Primary account login |
| Cost | Approximate recurring cost |
| Plan/Tier | Current subscription tier |
| Purpose | What the service is used for |
| Migration status | Identity updated to MLADIS LLC? |

---

## Critical Deferred Transfer Backlog

Status: **deferred until the MLADIS web application is robust/completed**.

This section is a critical future to-do list. Do not transfer, cancel, downgrade, rotate, or reconfigure external services while the web application is still being stabilized unless the owner explicitly approves that specific action in the current thread.

When this backlog is resumed, implement **one service transfer at a time**. Do not batch migrate accounts. Do not cancel cost items until the replacement path, backup/export, smoke test, rollback path, and evidence are complete.

### Required Transfer Checklist For Every Service

| Step | Requirement |
| --- | --- |
| 1 | Confirm the web app is stable enough for this specific account/service change. |
| 2 | Record the current owner/login, current billing owner, current plan/tier, renewal/cost trigger, and current admins. |
| 3 | Export or screenshot current settings, billing, users, domains, DNS, OAuth callbacks, webhooks, API keys metadata, recovery options, and other service-specific configuration. |
| 4 | Store private exports/screenshots in the MLADIS private business-record vault, not Git. |
| 5 | Add the MLADIS Workspace identity or alias as admin/owner before removing personal access. |
| 6 | Verify login/access from the MLADIS-owned identity. |
| 7 | Transfer ownership and/or billing only after access is confirmed. |
| 8 | Rotate secrets only after the new owner/control identity is confirmed. |
| 9 | Run the smoke test listed for that service. |
| 10 | Record rollback path and 24-72 hour monitoring result when the service touches production, payments, DNS, OAuth, email, or bookings. |
| 11 | Update this inventory with evidence before moving to the next service. |

### Deferred Transfer Queue

| Priority | Service group | Examples | Future action | Required smoke test | Status |
| --- | --- | --- | --- | --- | --- |
| Critical | Domains / DNS | Squarespace, Cloudflare, GoDaddy legacy domains | Centralize DNS/domain ownership under MLADIS-controlled identity; preserve mail records and OAuth callback domains. | `mladis.com`, `www.mladis.com`, `local.mladis.com`, Google Workspace mail, and OAuth callbacks still work. | Deferred |
| Critical | Hosting / infrastructure | Google Cloud project `mledis`, GCE VM, static IP, Caddy, systemd, future Cloud Run/Cloud SQL/Secret Manager/GCS | Move/administer cloud ownership and billing through MLADIS-controlled identity; do not disrupt live VM. | Site health check, admin login, deploy pipeline, static/media access, and VM service status pass. | Deferred |
| Critical | Code / CI | GitHub repos, private submodules, GitHub Actions, deploy credentials | Ensure MLADIS-controlled admins, protected branches, CI secrets, and submodule access are documented. | Clone/pull submodules, run sign-in contract CI, and deploy dry-run/check path still work. | Deferred |
| Critical | OAuth / sign-in | Google OAuth, Facebook Developer App, GitHub OAuth, Microsoft/Azure app | Transfer or re-create provider apps under MLADIS-controlled account only after callback inventory is complete. | Google, Facebook, GitHub, and any enabled Microsoft login flows pass local/production callback checks. | Deferred |
| Critical | Payments | Stripe, PayPal Developer, PayPal Business, webhooks | Move payment ownership/billing/tax profile after bank account and webhooks are ready; preserve deposit/donation behavior. | Deposit hold, release/capture admin flow, donation checkout, webhook verification, and payment admin records pass. | Deferred |
| High | Email / Workspace | Google Workspace, Gmail, SMTP sender, aliases/groups | Use Workspace aliases/groups for `admin@`, `billing@`, `support@`, `bookings@`, `legal@`, `finance@`, and `tech@` where possible to avoid extra paid seats. | Booking inquiry email, admin email, password/social auth email flow, and DNS mail records pass. | Deferred |
| High | Business records / documents | Google Drive private vault, source Drive folders, Dropbox Sign | Keep private records in Drive and public-safe tracker in Git; move document/e-sign ownership to MLADIS identity. | Signed-document retrieval, Drive folder access, and Dropbox Sign send/audit-trail workflow pass. | Deferred |
| High | Rental operations | Airbnb host, Ring, DR bank/payment support | Transfer what can safely move to MLADIS identity; keep platform access and property security uninterrupted. | Airbnb host access, payout/tax profile, listing visibility, message access, and Ring camera access pass. | Deferred |
| Medium | Marketing | Meta Business Suite, Facebook Page, Instagram/WhatsApp if connected | Keep Meta assets under MLADIS business control; complete WhatsApp/Instagram only when verification is available. | Facebook page loads, Meta app login works, ad/page access remains, and contact details are correct. | Deferred |
| Medium | Government / compliance | NYBE/NYS DOS, IRS, Queens publication, SAM.gov, Grants.gov, MWBE if later used | Track portal ownership/contact identity without exposing tax or identity data in Git. | Portal access verified and private records saved; no public docs expose EIN/SSN/bank/ID details. | Deferred |
| Medium | Legacy / cost cuts | GoDaddy hosting/PHP support, unused domains, duplicate subscriptions, mixed-use subscriptions | Aggressively cancel or downgrade only after confirming no active dependency and saving receipts/exports. | Domains still resolve as intended, no active website/email breaks, receipts saved, and cost summary updated. | Deferred |

### Future Inventory Columns To Add Before Migration Starts

Before any transfer begins, expand the tables below or create a dedicated transfer table with:

- Current owner/login.
- Desired MLADIS owner/login.
- Billing owner/payment method.
- Renewal date or cost trigger.
- MFA/recovery status.
- Data/export location.
- Backup/export required.
- Smoke test required.
- Rollback path.
- Risk level.
- Transfer status.
- Evidence link.

---

## 1. Core Business & Hosting

| Service | Login email | Cost | Plan/Tier | Purpose | Migration status |
| --- | --- | --- | --- | --- | --- |
| **Google Workspace** | garcp37@mladis.com (admin) | ~$6/user/mo | Business Starter | Business email (`@mladis.com`), Google Drive, Docs, admin console | ✅ Org name = MLADIS LLC |
| **Google Cloud (GCE)** | garciapiterz@gmail.com | ~$30–50/mo | Pay-as-you-go | Hosts MLADIS Django booking app on `mladis-test-1` VM (static IP `34.63.199.174`) | ⬜ Not renamed — personal account |
| **Cloudflare** | garciapiterz@gmail.com | Free | Free | DNS for `mladis.com` (NS: olof / ophelia.ns.cloudflare.com) | ✅ Account name = MLADIS LLC |
| **Squarespace** | garciapiterz@gmail.com | ~$22/yr (domain only) | Domain registration | `mladis.com` domain registration (not a website builder — DNS delegated to Cloudflare) | Partial — WHOIS org ✅, billing contact ☐ |
| **GoDaddy** | pzg8794@rit.edu | ~$22.17/yr per domain | Domain registration | `garciapiterz.com` and `mledistech.com` domains; also web hosting for `mledistech.com` ($119.88/yr + PHP support $39.06/yr) | ⬜ Not migrated — legacy domains |
| **MLADIS Booking App (Django)** | garcp37@mladis.com (staff/admin) | Included in GCE | Custom Django app | Guest management, booking requests, rental contracts at `mladis.com` | ✅ site_name = MLADIS LLC, contact_email = garcp37@mladis.com |

---

## 2. Property & Rental Platforms

| Service | Login email | Cost | Plan/Tier | Purpose | Migration status |
| --- | --- | --- | --- | --- | --- |
| **Airbnb (host)** | garciapiterz@gmail.com | 3% host fee per booking | Host | Short-term rental listings for G-101 and G-102 (DR properties) | Partial — W-9 ✅ (MLADIS LLC, EIN 42-2932522), payout pending LLC bank account, preferred name = MLADIS LLC ✅ |
| **Ring** | garciapiterz@gmail.com | ~$10–20/mo | Ring Protect | Security cameras for DR rental properties | ⬜ Not migrated — see `Taxes/Ring Invoice/` |

---

## 3. Contracts & Documents

| Service | Login email | Cost | Plan/Tier | Purpose | Migration status |
| --- | --- | --- | --- | --- | --- |
| **Dropbox Sign** (fka HelloSign) | garcp37@mladis.com | Free | Free (3 docs/mo) | Digital signatures for guest rental contracts | ✅ Company name = MLADIS LLC |

---

## 4. Marketing

| Service | Login email | Cost | Plan/Tier | Purpose | Migration status |
| --- | --- | --- | --- | --- | --- |
| **Meta Business Suite** | garciapiterz@gmail.com | Ad spend variable (no fixed fee) | Free (organic) + Ads | Business portfolio, ad settings, Instagram/Facebook business management | ✅ Portfolio name = Mladis LLC (2026-06-04) |
| **Facebook Page** | garciapiterz@gmail.com | Free | Facebook Page | Public-facing business page for MLADIS | ✅ Renamed from `Body Transformation` to `Mladis LLC`; live URL = `facebook.com/mladis.connected`; bio/contact info updated; cover = MLADIS Connected Intelligence artwork |

---

## 5. Payments & Banking

| Service | Login email | Cost | Plan/Tier | Purpose | Migration status |
| --- | --- | --- | --- | --- | --- |
| **PayPal Developer** | garciapiterz@gmail.com | Per-transaction (2.9% + $0.30 standard) | Developer / Sandbox+Live | Payment processing integration for booking app | ⬜ Not migrated — check dashboard at developer.paypal.com |
| **Western Union** | garciapiterz@gmail.com | Per-transfer fee | N/A | International remittances to DR | N/A (personal transfers) |
| **Remitly** | garciapiterz@gmail.com | Per-transfer fee | N/A | International remittances to DR | N/A (personal transfers) |
| **Scotiabank (DR)** | In-person | Variable | Business/Personal | DR bank account for property-related expenses | ⬜ In-person visit required — statements in `Taxes/scotia statements/` |
| **MLADIS LLC Bank Account (US)** | N/A | TBD | Business checking | US LLC operating account (not yet opened) | ⬜ Pending — need Articles + EIN + ID |

---

## 6. Personal / Mixed-Use Subscriptions (tracked for taxes)

| Service | Login email | Cost | Plan/Tier | Purpose | Notes |
| --- | --- | --- | --- | --- | --- |
| **Uber One** | garciapiterz@gmail.com | ~$9.99/mo | Member | Ride share & Uber Eats membership | Receipts in `Taxes/uberonemembership/` — monthly auto-renewal |
| **Mobile / Phone plan** | garciapiterz@gmail.com | See `Taxes/Mobile Cost/` | Carrier plan | Business phone line (631-575-4841) | Receipts in `Taxes/Mobile Cost/` |

---

## 7. Legacy / Inactive

| Service | Notes |
| --- | --- |
| **mledistech.com (GoDaddy hosting)** | Old brand — `mledistech.com` domain + web hosting on GoDaddy. $119.88/yr hosting + $39.06/yr PHP support + $22.17/yr domain renewal. Consider discontinuing if not in use. |
| **garciapiterz.com (GoDaddy)** | Personal domain — $22.17/yr renewal. Not tied to MLADIS LLC operations. |

---

## Cost Summary (approximate recurring)

| Category | Approx. monthly | Approx. annual |
| --- | --- | --- |
| Google Workspace | $6/user | $72/user |
| Google Cloud (GCE) | $30–50 | $360–600 |
| Cloudflare | $0 | $0 |
| Squarespace (domain) | ~$1.83 | ~$22 |
| GoDaddy (mledistech hosting) | ~$13.25 | ~$159 |
| GoDaddy (domains x2) | ~$3.70 | ~$44 |
| Ring Protect | ~$10–20 | ~$120–240 |
| Uber One | $9.99 | ~$120 |
| Airbnb host fee | 3% per booking | Variable |
| **Total fixed (approx.)** | **~$75–105/mo** | **~$900–1,260/yr** |

> Airbnb host fee and PayPal transaction fees are variable — not included in the fixed total.

---

## Notes

- **GCE billing account**: Linked to `garciapiterz@gmail.com` Google account. To migrate billing to MLADIS LLC, create a billing account under the Google Workspace org (`garcp37@mladis.com`) and transfer the project.
- **Meta naming policy**: Meta rejects all-caps business names (e.g., "MLADIS LLC"). Use "Mladis LLC" in Meta Business Suite and on the Facebook Page. Legal name remains MLADIS LLC everywhere else.
- **Facebook Page branding**: Page renamed live to `Mladis LLC` at `https://www.facebook.com/mladis.connected/`. Bio updated to the MLADIS umbrella positioning, public contact info now shows the MLADIS address / phone / email / website, languages are set to English + Spanish, founding date is set to 3 June 2026, and the cover photo now uses the MLADIS Connected Intelligence artwork. WhatsApp remains pending because Meta requires a verification code sent to `+1 631-575-4841`.
- **GoDaddy login**: Uses `pzg8794@rit.edu` — receipts paid via PayPal. Consider migrating billing to `garciapiterz@gmail.com` or a MLADIS LLC email.
- **Dropbox Sign free tier**: 3 documents/month. If rental contract volume increases, upgrade to a paid plan and update billing to MLADIS LLC.

---

## Direct Access URLs

| Service | URL | Notes |
| --- | --- | --- |
| Google Workspace Admin | `https://admin.google.com/` | Admin login: `garcp37@mladis.com` |
| Google Drive | `https://drive.google.com/` | Workspace + personal storage |
| Google Cloud Console | `https://console.cloud.google.com/` | Billing/account currently under `garciapiterz@gmail.com` |
| Airbnb Host Account | `https://www.airbnb.com/account-settings/` | Tax/W-9 and payouts |
| Cloudflare Dashboard | `https://dash.cloudflare.com/` | Account renamed to MLADIS LLC |
| Squarespace Account | `https://account.squarespace.com/settings/profile` | Domain registrar for `mladis.com` |
| Dropbox Sign | `https://app.hellosign.com/` | Login: `garcp37@mladis.com` |
| Meta Business Suite | `https://business.facebook.com/latest/settings/business_info?business_id=2115472558905606` | Portfolio = `Mladis LLC` |
| Facebook Page | `https://www.facebook.com/mladis.connected/` | Public Page = `Mladis LLC` |
| PayPal Developer | `https://developer.paypal.com/dashboard/applications/live` | Payment integration dashboard |
| MLADIS Booking App | `https://mladis.com/` | Public site |
| MLADIS Booking Admin | `https://mladis.com/admin/` | Django admin |
