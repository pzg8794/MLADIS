# MLADIS Booking Agent

Django scaffold for the MLADIS booking website and future customer agent.

The app starts with three Santo Domingo Airbnb listings, direct booking inquiries,
an admin-managed `BookableItem` model for stays/services/transport/experiences,
an admin-managed `DamageDeposit` model for a $200 Stripe authorization hold,
mission donations, Airbnb image galleries, review summaries, admin-only calendar
setup, and an agent API boundary that can later connect to live booking logic.

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
- `/stays/<slug>/` gives every stay its own page with hero image, gallery, review summary, booking form, and deposit callout.
- `/about/` sells the Dominican Republic/Santo Domingo travel story and includes Stripe donation checkout for mission causes.
- `/ops/calendar/` is staff-only and supports the v1 manual Airbnb iCal setup path for Google Calendar.
