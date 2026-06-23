# Booking Neuron — Homepage Layout Specification

Date: 2026-06-23  
Status: Approved — Option B selected  
Related ADR: `docs/architecture/0004-booking-neuron-homepage-design-system.md`

## Decision

**Option B — Neighborhood Bento** is the approved homepage layout.

It was selected over a cinematic/hero-image approach because it makes the page immediately operational.

## Layout sections

### Section 1 — Warm Text Hero

```text
Background:   warm ivory (#f7f6f2)
Layout:       left-aligned, two columns (text left, subtle image right)
Headline:     Cabinet Grotesk display, --text-2xl, near-black charcoal
Subline:      Satoshi body, --text-base, muted gray
CTAs:         2 buttons — primary teal "Book your stay" + ghost "View all apartments"
```

Copy direction:

```text
Headline: "Vacation stays in Santo Domingo Norte"
Subline:  "Pool-ready apartments, human support, and AI-guided booking to save you money."
```

No generic marketing copy. No "Empowering your journey" filler.

### Section 2 — Neighborhood Bento Grid

```text
Grid:         3-column desktop, 1-column mobile (stacked cards)
Left cell:    OpsPropertyCard (tall, featured — set by admin in settings)
Center cell:  2x OpsPropertyCard (small, stacked)
Right cell:   MapPanel (neighborhood pins + compact legend)
```

Each bento cell has exactly one job. The map supports decision-making, it does not dominate the inventory.

Data source: `Booking.Resource.Property` objects via `PropertyRepository`.

### Section 3 — Trust Strip

```text
Layout:   horizontal row, 4 trust signals
Signals:  Average guest rating | Deposit clarity | Human support | AI booking
Style:    compact badges, muted gold accent for ratings, no decorative icons in colored circles
```

### Section 4 — Neighborhood Cards

```text
Layout:   2–3 horizontal cards
Content:  Area name + short description + ambient photo
Purpose:  Build confidence about the neighborhood before booking
```

### Section 5 — Rules + Stay Rhythm

```text
Layout:   single column, clear list
Content:  Check-in/out times, quiet hours, house rules, what to expect
Tone:     Transparent, warm, not legal-disclaimer language
```

### Section 6 — AI Booking Panel

```text
Layout:   full-width panel, teal accent surface
Content:  FairAgent booking assistant entry point
Behavior: Guest enters dates + preferences → AI suggests availability + rate
Approval: All AI suggestions reviewed by staff before confirming
Label:    "Powered by FairAgent" (not a generic chatbot)
```

### Section 7 — Mission Section

```text
Layout:   2-column (text + image)
Content:  MLADIS human story, named in honor of Mladis, what the system stands for
Tone:     Warm, personal, real — not corporate boilerplate
```

## Admin controls

Admins control this layout from `Booking Neuron > Homepage Settings` in OpsShell:

- reorder sections via drag-and-drop
- toggle section visibility (show/hide)
- set featured property card
- enable/disable AI Booking Panel
- preview changes before publishing

See: `docs/architecture/booking-neuron/design/admin-control-panels.md`

## Mobile behavior

```text
Desktop (1024px+):  3-column bento grid
Tablet (768px):     2-column grid (map moves below property cards)
Mobile (375px):     1-column stacked: featured card → small cards → map
```

The page must feel complete on mobile. Bento collapse is not a degraded experience — it is the mobile-first default.
