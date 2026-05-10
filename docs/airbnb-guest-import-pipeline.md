# Airbnb Guest Import Pipeline

This pipeline imports Airbnb reservation/message history into MLADIS without committing private guest data to git.

## What It Stores

- Guest name, optional email, optional phone
- Airbnb listing title and listing ID
- Check-in/check-out dates and guest count
- Airbnb thread URL/source email metadata
- Message excerpt and feedback notes
- Marketing consent status on the linked customer profile

Airbnb usually hides direct guest email/phone behind platform messaging. Imported Airbnb-only contacts default to `Unknown` marketing consent, so promotions are not sent until an admin records opt-in.

## Run It

Put export files in `airbnb_agent/imports/`, which is ignored by git.

```bash
cd airbnb_agent
.venv/bin/python manage.py import_airbnb_guests imports/airbnb-guests.json --dry-run
.venv/bin/python manage.py import_airbnb_guests imports/airbnb-guests.json
```

Accepted formats:

- Gmail connector JSON with a top-level `responses` or `messages` array
- CSV with columns like `id`, `subject`, `body`, `email_ts`, `guest_email`, `guest_phone`, `feedback_summary`

## Admin Workflow

- Go to `Dashboard > Reservations` or `/ops/reservations/` to see booked Airbnb guests linked to stay history, feedback, contact path, and customer group.
- Use the group filters for `Favorite`, `VIP`, `Average`, and `Blacklisted`.
- Export the reservation/customer list from that page as `mladis-airbnb-customers.csv`.
- Go to `Admin > Bookings > Airbnb guest records > Import Airbnb guests`.
- Upload a `.json` or `.csv` export and run it with `Dry run only` checked first.
- If the counts look right, upload the same file again with `Dry run only` unchecked.
- Review imported records in `Admin > Bookings > Airbnb guest records`.
- Review linked customer profiles in `Admin > Bookings > Customer profiles`.
- Use the customer-profile admin action to send permission request emails.
- Mark a customer `Opted in` only after permission is received.
- Promotions only build/send recipients for opted-in customer profiles.
