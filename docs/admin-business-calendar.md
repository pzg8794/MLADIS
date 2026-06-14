# Business Calendar

This document covers the modern business calendar for stays, availability, manual holds, nightly pricing, and future Airbnb feed sync.

## Where It Lives

- Primary operator route: `/ops/calendar/`.
- Calendar subviews:
  - `/ops/calendar/list/`
  - `/ops/calendar/rooms/`
  - `/ops/calendar/analytics/`
- Django Admin fallback links under `Bookings` -> `Bookable items` redirect staff to the modern `/ops/calendar/` route.

The modern ops calendar is the main operator-facing calendar surface. The old admin calendar should remain only as a safe redirect/fallback while this surface is tested.

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
- `CalendarFeed`: Airbnb iCal and Google Calendar feed metadata for each stay.

## Airbnb iCal Sync Roadmap

MLADIS already stores Airbnb iCal URLs on `CalendarFeed.airbnb_ical_url`. The calendar UI must not pretend a stay is synced just because a URL exists. Treat these as separate states:

- `feed configured`: `CalendarFeed.airbnb_ical_url` exists and the feed record is active.
- `feed synced`: a backend sync job successfully imported or updated events from that feed.
- `calendar rendered`: imported reservations, manual blocks, and price overrides are shown through the existing calendar API.

Recommended implementation:

1. Add a backend service named `AirbnbICalSyncService`.
2. Add a management command named `sync_calendar_feeds`.
3. For each active `CalendarFeed` with an `airbnb_ical_url`, fetch the iCal feed, parse `VEVENT` records, and persist them through the booking domain.
4. Preserve external identity using Airbnb/iCal fields such as `UID`, `DTSTART`, `DTEND`, `SUMMARY`, and `LAST-MODIFIED`. Add explicit external-source fields or an `ExternalCalendarEvent` model before mutating reservations if the current `BookingInquiry` schema cannot safely store that identity.
5. Upsert records instead of blindly creating duplicates.
6. Store sync metadata on `CalendarFeed`: last sync time, last status, last error, and imported count.
7. Show sync warnings in `/ops/calendar/` notifications when a feed is missing, stale, or failed.

The source of truth for the rendered calendar remains:

- `BookingInquiry` for reservations.
- `AvailabilityBlock` for manual blocks.
- `DailyPriceOverride` for price overrides.
- `CalendarFeed` for external-feed configuration and health.

Do not fake imported Airbnb reservations in the UI. If a feed is not synced, the UI should say the feed is configured but awaiting sync.

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
