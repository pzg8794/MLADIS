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
| **Facebook Page** | garciapiterz@gmail.com | Free | Facebook Page | Public-facing business page for MLADIS | ✅ Renamed from `Body Transformation` to `Mladis LLC`; live URL = `facebook.com/mladis.connected` |

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
- **Facebook Page branding**: Page renamed live to `Mladis LLC` at `https://www.facebook.com/mladis.connected/`. Cover photo updated to the sunset pool image from Downloads on 2026-06-04. Profile picture is still the legacy image and should be replaced with an MLADIS logo next.
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
