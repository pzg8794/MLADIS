# MLADIS Brand Assets

Last updated: 2026-06-03

## Asset files

### Parent brand: MLADIS Connected Intelligence

- File: `airbnb_agent/bookings/static/bookings/brand/mladis-connected-intelligence.png`
- Type: PNG
- Size: 1254 x 1254 px
- Purpose: Top-level MLADIS umbrella brand.
- Recommended use:
  - Parent company pages.
  - Admin brand settings.
  - Business documentation.
  - Future MLADIS ecosystem identity.
  - Viverse / Connected Intelligence materials.

### Child brand: MLADIS Bookings

- File: `airbnb_agent/bookings/static/bookings/brand/mladis-bookings.png`
- Type: PNG
- Size: 1254 x 1254 px
- Purpose: Vacation stays and booking product line under MLADIS LLC.
- Recommended use:
  - Bookings landing pages.
  - Customer information packet.
  - Invoices / booking documents.
  - Reservation confirmations.
  - Admin booking dashboard.

## Brand hierarchy

```text
MLADIS LLC
└── MLADIS Connected Intelligence  # parent / umbrella
    └── MLADIS Bookings            # first business/product line
```

## Implementation notes

For the Django app, these images should be committed into:

```text
airbnb_agent/bookings/static/bookings/brand/
```

After deploy, run:

```bash
python manage.py collectstatic --noinput
```

Then open Django Admin and upload the desired logo under Site Settings.

Use:

- Parent/company context: `mladis-connected-intelligence.png`
- Booking/customer context: `mladis-bookings.png`

If the app supports multiple brand contexts later, keep both logos available and expose settings for:

```text
Parent brand logo
Product/Bookings logo
```

## Accessibility notes

When using these logos in templates, use clear alt text:

```html
<img src="{{ logo_url }}" alt="MLADIS Connected Intelligence">
<img src="{{ bookings_logo_url }}" alt="MLADIS Bookings">
```

Do not rely on the logo alone to communicate brand identity; keep visible text where appropriate.
