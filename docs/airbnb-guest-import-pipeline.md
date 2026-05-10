# Airbnb Guest Import Pipeline

This pipeline imports Airbnb reservation/message history into MLADIS without committing private guest data to git.

## What It Stores

- Guest name, optional email, optional phone
- Airbnb listing title and listing ID
- Check-in/check-out dates and guest count
- Airbnb thread URL/source email metadata
- Message excerpt and feedback notes
- A linked customer feedback entry tied to the customer profile, stay, and Airbnb reservation record
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
- Structured Airbnb contact JSON with a top-level `guest_contact_list` array
- CSV with columns like `id`, `subject`, `body`, `email_ts`, `guest_email`, `guest_phone`, `feedback_summary`
- CSV/JSON contact columns like `guest_name`, `email`, `phone_number`, `listing_apartment`, `airbnb_thread_url`, `check_in_date`, `check_out_date`, `number_of_guests`, `message_summary`, `feedback_or_review_summary`, `consent_status`, and `promotion_permission_notes`

For structured Airbnb contact exports, the importer:

- Normalizes `https://www.airbnb.com/hosting/messages/<id>` to `https://www.airbnb.com/hosting/thread/<id>` so duplicate imports update the same record.
- Maps known listing titles to Airbnb listing IDs.
- Infers the current year for month/day dates without a year, while preserving explicit historical years.
- Keeps email/phone blank when Airbnb does not expose them.
- Stores consent as `Unknown` unless the export explicitly provides a valid MLADIS consent status.
- Stores promotion/contact permission notes on the Airbnb guest record.
- Copies message feedback/rating context into `Customer feedback` so admins can review it from the guest profile, the Airbnb record, reporting, and the reservations screen.

## Admin Workflow

- Go to `Dashboard > Reservations` or `/ops/reservations/` to see booked Airbnb guests linked to stay history, feedback, contact path, and customer group.
- Use the group filters for `Favorite`, `VIP`, `Average`, and `Blacklisted`.
- Export the reservation/customer list from that page as `mladis-airbnb-customers.csv`.
- Go to `Admin > Bookings > Airbnb guest records > Import Airbnb guests`.
- Upload a `.json` or `.csv` export and run it with `Dry run only` checked first.
- If the counts look right, upload the same file again with `Dry run only` unchecked.
- Review imported records in `Admin > Bookings > Airbnb guest records`.
- Review linked feedback in `Admin > Bookings > Customer feedback`.
- Review linked customer profiles in `Admin > Bookings > Customer profiles`.
- Use the customer-profile admin action to send permission request emails.
- Mark a customer `Opted in` only after permission is received.
- Promotions only build/send recipients for opted-in customer profiles.

## Agent Training Notes From Airbnb Threads

Use these notes to improve the live booking agent and public FAQ copy. When a note conflicts with current Airbnb/email source data, confirm the rule before hard-coding it into the public agent.

- Pricing and discounts: guests ask about returning-guest discounts and feedback offers. The agent should say offers may be sent to past guests, but should not promise a discount unless an active offer exists for that guest.
- Availability and guest count: guests ask if dates are available and whether they can add people. The agent should say availability is real-time/admin-confirmed and the booking must match the true guest count.
- Check-in/check-out: guests ask about arrival and departure times. Imported Airbnb messages show check-in as 3:00 p.m.; several imported Airbnb messages show check-out as 11:00 a.m., while a draft training note says 12:00 noon. Confirm the correct public check-out time before changing the agent or listing copy.
- Location and transportation: guests ask for full address and directions. The agent should give neighborhood-level guidance and say full arrival details are shared through Airbnb/confirmed booking channels.
- Pool/shared amenities: guests ask whether the pool is private and about pool rules. The agent should say the pool is shared unless an admin explicitly says otherwise, and should not promise exclusive pool access.
- House rules: guests ask about visitors, parties, smoking, pets, and noise. The agent should not waive rules. It can summarize no smoking inside, no parties, visitor limits by stay length, and visitors leaving by 11 p.m. when those rules match the active listing rules.
- Safety/security: guests ask about keys, doors, and access. The agent should give practical guidance without guaranteeing safety, including keeping doors/windows closed and using gate access only for registered guests.
