# MLADIS LLC — Platform & Account Update Checklist

Created: 2026-06-03. Use this after LLC formation and EIN issuance to update every platform with the confirmed legal identity.

## Confirmed Entity Info (use exactly as shown)

| Field | Value |
| --- | --- |
| Legal business name | MLADIS LLC |
| EIN | 42-2932522 |
| Entity type | Domestic Limited Liability Company |
| State of formation | New York |
| Formation date | June 3, 2026 |
| DOS ID | 7932124 |
| Business address | 109-19 72nd Rd., Apt 5H, Forest Hills, NY 11375 |
| Business phone | 631-575-4841 |
| Current business email | garciapiterz@gmail.com |
| Future business email | garcp37@mladis.com (use once Google Workspace DNS is stable) |
| Domain | mladis.com |

Reference documents in the private vault:
- Articles / Filing Receipt: `MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/01-formation/MLADIS_LLC-FilingReceipt-And-Articles.pdf`
- EIN Confirmation (CP 575 G): `MLADIS-Private-Business-Records/2026-06-03-ein-banking-publication/02-tax-ein/MLADIS-EIN_CONFIRMATION-CP_575_G.pdf`

---

## 1. Airbnb Host Account

**What to update:** W-9 / tax info, payout recipient, and host profile display name.

**Steps:**
1. Go to [airbnb.com](https://www.airbnb.com) → log in as host.
2. **Tax info (W-9):** Account → Taxes → Add/Edit tax info.
   - Taxpayer type: **Business**
   - Legal name: `MLADIS LLC`
   - EIN: `42-2932522`
   - Business address: `109-19 72nd Rd., Apt 5H, Forest Hills, NY 11375`
   - Save and submit the W-9.
3. **Payout method:** Account → Payments & Payouts → Payout methods.
   - If a payout is tied to a personal name, update the payee name to `MLADIS LLC` or add a new business payout method once the MLADIS LLC bank account is open.
   - Note: Airbnb may require an official bank account in the LLC name to set the payee as MLADIS LLC.
4. **Host profile name:** Account → Personal info → Name.
   - Consider using `MLADIS LLC` or `MLADIS Vacation Rentals` as the display name. This is visible to guests.
5. **Status:**
   - ✅ W-9 submitted (2026-06-03) — IRS validation pending (up to 10 business days)
   - ☐ Payout method — pending LLC bank account
   - ✅ Preferred first name set to `MLADIS LLC` (2026-06-04)

---

## 2. Squarespace (Domain Registrar for mladis.com)

**What to update:** Billing/account contact name; domain registrant name for WHOIS.

**Steps:**
1. Go to [account.squarespace.com](https://account.squarespace.com) → log in.
2. **Billing info:** Account → Billing → Update billing name and address to `MLADIS LLC`, address `109-19 72nd Rd., Apt 5H, Forest Hills, NY 11375`.
3. **Domain contact / WHOIS registrant:** Domains → mladis.com → Edit contact info.
   - Organization: `MLADIS LLC`
   - Name: `Piter Zacari Garcia Bautista`
   - Address: `109-19 72nd Rd., Apt 5H, Forest Hills, NY 11375`
   - Email: `garciapiterz@gmail.com` (update to `garcp37@mladis.com` after Workspace DNS is verified)
   - Phone: `631-575-4841`
4. **Status:**
   - ✅ WHOIS registrant updated (2026-06-03) — Organization: MLADIS LLC, Phone: 631-575-4841, Address: 109-19 72nd Rd. APT 5H, Forest Hills, NY 11375; confirmation email pending from Squarespace/ICANN
   - ☐ Billing info — not done

---

## 3. Cloudflare (DNS for mladis.com)

**What to update:** Account/organization name shown in the Cloudflare dashboard.

**Steps:**
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → log in.
2. Click the account name (top left) → Account Settings → Name.
   - Update to `MLADIS LLC` if currently set to a personal name or placeholder.
3. Billing profile: My Profile → Billing → update billing name to `MLADIS LLC`.
4. No DNS record changes are required for the LLC update itself — the nameservers (`olof.ns.cloudflare.com`, `ophelia.ns.cloudflare.com`) stay the same.
5. **Status:** ✅ Done — 2026-06-04 — Account renamed to `MLADIS LLC` via Cloudflare API (`PUT /accounts/{id}`) using a custom token with `Account Settings:Edit` permission. API confirmed `"success": true, "name": "MLADIS LLC"`.

---

## 4. Dropbox Sign (E-signature platform)

**What to update:** Organization/team name and billing name.

**Account:** `garcp37@mladis.com`

**Steps:**
1. Go to [sign.dropbox.com](https://sign.dropbox.com) → log in with `garcp37@mladis.com`.
2. Settings → Account → Organization name → set to `MLADIS LLC`.
3. Billing → confirm billing name is `MLADIS LLC`.
4. Confirm both signers are set correctly for the pending Diana acknowledgment:
   - Piter: `Piter Zacari Garcia Bautista <garcp37@mladis.com>`
   - Diana: `Diana Sori Garcia Bautista <garciabdianas@gmail.com>`
5. **Status:** ✅ Done — 2026-06-04 — Profile → Company name set to `MLADIS LLC` (saved successfully). Receipt address requires paid plan (Free account — skipped). Billing: no card on file (Free plan).

---

## 5. MLADIS Booking App — Django SiteSettings (mladis.com)

**What to update:** `SiteSettings.site_name` (currently `"MLADIS"` → `"MLADIS LLC"`) and `contact_email`.

**Via Django Admin (recommended for live/deployed instance):**
1. Go to `https://mladis.com/admin/` → log in as staff.
2. Navigate to Bookings → Site Settings → (pk=1 record).
3. Update:
   - **Site name:** `MLADIS LLC`
   - **Contact email:** `garcp37@mladis.com` (once Google Workspace DNS is stable; otherwise keep `garciapiterz@gmail.com`)
4. Save.

**Source code — model default and seed migration were also updated** (see `bookings/models.py` `site_name` default and migration `0007_seed_booking_platform.py`) to `"MLADIS LLC"` so fresh databases reflect the correct name.

5. **Status:** ✅ Done — 2026-06-04 — Live DB updated via Django shell over SSH: `site_name` → `'MLADIS LLC'`, `contact_email` → `'garcp37@mladis.com'` (SiteSettings pk=1, confirmed).

---

## 6. Google Workspace Admin (garcp37@mladis.com)

**What to update:** Organization name in Google Workspace admin console.

**Steps:**
1. Go to [admin.google.com](https://admin.google.com) → log in with `garcp37@mladis.com`.
2. Account → Account settings → Organization name → set to `MLADIS LLC`.
3. Contact info → Primary domain contact → update address and phone to match MLADIS LLC info above.
4. **Status:** ✅ Done — 2026-06-04 — Account settings → Profile → Name changed from 'MLADIS' to 'MLADIS LLC' (saved successfully, toast confirmed).

---

## 7. Bank Account (when opened)

The LLC bank account has not been opened yet. When opening:
- Account name: **MLADIS LLC** (exactly as shown on Articles)
- EIN: `42-2932522`
- Bring: Articles / Filing Receipt, Signed Operating Agreement, Signed Initial Member Consent, EIN confirmation letter (CP 575 G), owner ID.
- Reference: `docs/business/ein-and-banking/bank-account-opening-packet.md`
- **Status:** ☐ Not done — pending

---

## 8. Meta Business Suite + Facebook Page

**What to update:** Business portfolio name and public Facebook Page branding.

**Account:** `garciapiterz@gmail.com`  
**Business Portfolio ID:** `2115472558905606`

**Steps:**
1. Go to [business.facebook.com](https://business.facebook.com/latest/settings/business_info?business_id=2115472558905606).
2. Under **Business portfolio info** → click **Edit**.
3. Business name field → set to `Mladis LLC` (Meta policy requires title-case; all-caps "MLADIS LLC" is rejected).
4. Click **Save**.
5. Open the linked **Primary Page** and switch into the Page profile.
6. Facebook Settings → Page setup → **Name** → change the Page name from `Body Transformation` to `Mladis LLC`.
7. Update the Page bio to MLADIS umbrella branding and fill the public About/contact fields.
   - Bio: `MLADIS LLC is a connected business ecosystem where hospitality, fitness and technology learn from each other to grow smarter together.`
   - Address: `109-19 72nd Rd Apt 5H, Queens, NY, United States, 11375`
   - Phone: `+1 631-575-4841`
   - Public email: `garcp37@mladis.com`
   - Website: `https://mladis.com/`
   - Languages: `English language (United States)` and `Spanish language`
   - Founding date: `3 June 2026`
8. Update the cover photo to the MLADIS Connected Intelligence artwork (brain / neuron network concept).
9. Keep the current MLADIS profile picture/logo.
10. WhatsApp connection remains optional until the phone verification code can be completed from the device receiving `+1 631-575-4841`.
11. Optionally update the Legal business name field under **Business details** once Meta's business verification is completed.
12. **Status:** ✅ Done — 2026-06-04 — Business portfolio name changed from "Body Transformation" to `Mladis LLC`. Primary Facebook Page also changed from `Body Transformation` to `Mladis LLC`, now live at `https://www.facebook.com/mladis.connected/`. Page bio and About/contact info were updated with the MLADIS business details, and the cover photo was changed to the MLADIS Connected Intelligence artwork. WhatsApp setup is still pending phone verification. Note: Meta requires title-case — "MLADIS LLC" was rejected by Meta naming policy; "Mladis LLC" was accepted.

---

## 9. Future Platforms (add as needed)

When adding Stripe, PayPal, Airbnb direct-deposit, Booking.com, VRBO, or any payment/OTA platform:
- Always use **MLADIS LLC** as the legal business name.
- Always use EIN **42-2932522** for W-9 / tax forms.
- Always use the business address: **109-19 72nd Rd., Apt 5H, Forest Hills, NY 11375**.
- Keep the signed Operating Agreement and EIN letter on hand — most platforms will ask for them during business verification.

---

## Update Log

| Date | Platform | Action | Done by |
| --- | --- | --- | --- |
| 2026-06-03 | Booking app (code) | `site_name` default + seed updated to "MLADIS LLC" | Copilot |
| 2026-06-03 | Airbnb | W-9 Form submitted — MLADIS LLC, EIN 42-2932522, Queens NY 11375; IRS validation pending | Copilot |
| | Airbnb | Payout method update — pending LLC bank account | |
| 2026-06-04 | Airbnb | Preferred first name set to `MLADIS LLC` (Account → Personal Info) | Copilot |
| 2026-06-03 | Squarespace | WHOIS registrant updated — Organization: MLADIS LLC, Phone: 631-575-4841, Address corrected; ICANN confirmation email pending | Copilot |
| | Squarespace | Billing contact name — not done | |
| 2026-06-04 | Cloudflare | Account name renamed to `MLADIS LLC` via API (PUT /accounts/{id}, token: MLADIS Account Rename) | Copilot |
| ✅ | Dropbox Sign | Company name (Profile) | 2026-06-04 |
| ✅ | Google Workspace | Org name (Profile → Name) | 2026-06-04 |
| ✅ | Django live DB | SiteSettings pk=1: site_name → 'MLADIS LLC', contact_email → 'garcp37@mladis.com' | 2026-06-04 |
| 2026-06-04 | Meta Business Suite | Business portfolio name changed from "Body Transformation" → `Mladis LLC` (title-case required by Meta policy) | Copilot |
| 2026-06-04 | Facebook Page | Public Page renamed from `Body Transformation` → `Mladis LLC`; live URL now `facebook.com/mladis.connected` | Copilot |
| 2026-06-04 | Facebook Page | Public bio refreshed; address, phone, email, website, languages, and founding date added to About/contact info | Copilot |
| 2026-06-04 | Facebook Page | Cover photo updated to MLADIS Connected Intelligence artwork; current MLADIS profile image retained | Copilot |
| 2026-06-04 | Facebook Page | WhatsApp setup opened but left pending because Meta requires a phone verification code | Copilot |
| | Bank account | Open + fund | |
