# Admin Business Calendar

This document covers the new business calendar inside Django Admin for MLADIS stays.

## Where It Lives

- Open Django Admin.
- Go to `Bookings` -> `Bookable items`.
- For a stay row, use the `Open calendar` link.

The calendar route is the custom admin view under `BookableItem` admin and is intended to be the main operator-facing calendar surface.

## What The Calendar Shows

For the selected stay and month, the calendar shows each day as one of these states:

- `booked`: at least one active `BookingInquiry` overlaps that night.
- `blocked`: a manual `AvailabilityBlock` closes that date and no active reservation already covers it.
- `available`: no active reservation or manual block covers that day.

Each day cell also shows pricing:

- Default nightly price comes from `BookableItem.starting_price`.
- If an active `DailyPriceOverride` covers that day, the override price is shown instead.

The calendar also includes a click-to-fill range helper:

- Click one day to start a range.
- Click another day to finish the range.
- The `Block days` and `Override nightly price` forms are both prefilled automatically.
- Use `Clear selected range` to reset the helper.
- Each day cell also has `Block day` and `Price day` quick actions that prefill a single-day range and jump to the matching form.
- Cells with existing records expose direct links to the related reservation, block, or price override admin record.

## Manage Availability

Use the `Block days` form on the right side of the calendar page to close a date range manually.

Fields:

- `Start date`
- `End date`
- `Reason`
- `Notes`

Saved blocks appear both on the calendar grid and in the `Manual blocks in view` panel, where they can also be removed. If a day is already blocked, the day cell also exposes an `Edit block` link.

## Manage Nightly Pricing

Use the `Override nightly price` form on the calendar page to apply a temporary nightly rate for a date range.

Fields:

- `Start date`
- `End date`
- `Nightly price`
- `Label`
- `Notes`

Saved overrides appear on the calendar grid and in the `Price overrides in view` panel, where they can also be removed. If a day already carries an override, the day cell also exposes an `Edit price` link.

## Reservation Visibility

The `Reservations in view` panel lists the reservation records that overlap the displayed month and links directly to the corresponding `BookingInquiry` admin pages. Day cells that belong to a reservation also expose an `Open booking` link for faster navigation.

That means the calendar is the visual scheduling surface, while the `BookingInquiry` record stays the source of truth for reservation details.

## Data Models Behind The Calendar

- `BookingInquiry`: active reservations shown as booked days.
- `AvailabilityBlock`: manual closures for owner holds, maintenance, or blackout dates.
- `DailyPriceOverride`: temporary nightly pricing for selected date ranges.

## Validation Commands

Focused calendar validation:

```bash
cd airbnb_agent
.venv/bin/python manage.py test bookings.tests.BookingCalendarServiceTests bookings.tests.BookableItemCalendarAdminTests
```

Broader relevant bookings slice:

```bash
cd airbnb_agent
.venv/bin/python manage.py test \
  bookings.tests.BookingInquiryFormTests \
  bookings.tests.BookingInquiryViewTests \
  bookings.tests.CalendarOpsTests \
  bookings.tests.BookingCalendarServiceTests \
  bookings.tests.BookableItemCalendarAdminTests \
  bookings.tests.DamageDepositTests \
  bookings.tests.DamageDepositAdminTests
```
