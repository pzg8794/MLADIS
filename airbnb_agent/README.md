# MLADIS Booking Agent

Django scaffold for the MLADIS booking website and future customer agent.

The app starts with three Santo Domingo Airbnb listings, direct admin-confirmed
reservation requests, customer accounts, coupons, client segmentation, invoices,
promotion emails, admin-test reservations, admin-managed site content/logo/rules,
a $200 Stripe authorization hold, mission donations, Airbnb image galleries,
review highlights, owner analytics, admin-only calendar setup, and an agent API
boundary that can later connect to live booking logic.

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Visit `http://localhost:8000`.

## Deployment

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Required environment variables: `SECRET_KEY`, `ALLOWED_HOSTS`
- Optional environment variables: `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- Email variables: `DEFAULT_FROM_EMAIL`, `BOOKING_INQUIRY_RECIPIENTS`, `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`
- Deposit settings: `DEPOSIT_AMOUNT_CENTS=20000`, `DEPOSIT_CURRENCY=usd`
- Donation setting: `DONATION_CURRENCY=usd`
- Health check path: `/healthz`

The app currently returns an agent-ready setup/stub response. Replace
`BookingAgentService` in `bookings/services.py` when the real booking logic is ready.

## Damage Deposit Flow

The deposit flow uses Stripe Checkout with manual capture, so MLADIS can authorize
the $200 damage deposit without capturing it immediately. Stripe displays eligible
safe payment methods from the Stripe account configuration; methods that cannot
support a hold may not appear.

Webhook endpoint:

```txt
/stripe/webhook/
```

## Initial Airbnb Listings

- `588632365342578374`: 6 Bedrooms Vacation Home & Pool, 4.69 rating, 26 reviews, 6 bedrooms, 8 beds, 4 private baths
- `587194328968598250`: 3 Bedrooms Vacation Home & Pool G-102, 4.88 rating, 24 reviews, 3 bedrooms, 4 beds, 2 private baths
- `582161420407543691`: 3 Bedrooms Vacation Home & Pool G-101, 4.93 rating, 42 reviews, 3 bedrooms, 4 beds, 2 private baths

## Marketing Pages

- `/` is the travel-forward homepage with stay cards, Airbnb-hosted images, review proof, booking, deposit, mission, and agent sections.
- `/stays/<slug>/` gives every stay its own page with hero image, gallery, review summary, guest highlights, apartment rules, booking form, and deposit callout.
- `/about/` sells the Dominican Republic/Santo Domingo Norte travel story and includes Stripe donation checkout plus an agent panel.
- `/accounts/` lets customers see and manage their reservation requests and invoices.
- `/ops/dashboard/` gives staff reservation, cancellation, inquiry, visit, and agent-question analytics.
- `/ops/calendar/` is staff-only and supports the v1 manual Airbnb iCal setup path for Google Calendar.

## Admin Workflow

- Use `/admin/` to manage stays, galleries, guest highlights, rules, coupons,
  cancellation policies, customer profiles, invoices, extra bill templates,
  promotions, donations, deposits, logo/site settings, and content blocks.
- Booking requests are emailed to `BOOKING_INQUIRY_RECIPIENTS` and stored in admin.
- Admin-test reservations can be created by staff from the public booking form
  and are recorded with zero cost.
- Promotions can target all clients or favorite/VIP/average/blacklisted segments.
