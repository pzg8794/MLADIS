# Booking Neuron — Design Reference Images

Date: 2026-06-23

This directory contains generated design reference images created during Booking Neuron design planning.

These images are design references only.

Implementation must follow the object architecture documented in:

- `docs/architecture/0004-booking-neuron-homepage-design-system.md`
- `docs/architecture/booking-neuron/architecture/`

## Image inventory

### booking_homepage_bento_option_b.png

Approved homepage direction — Option B Neighborhood Bento layout.

Shows:
- Typography-first hero with warm ivory background
- Left-aligned headline (Santo Domingo Norte stays)
- Three-part bento grid: featured property card (tall), two stacked smaller cards, neighborhood map panel
- Trust strip below the grid
- Clean sans-serif throughout
- Warm light palette — ivory, white cards, deep teal accents

### booking_admin_settings_panel.png

Admin settings panel for Booking Neuron configuration inside OpsShell.

Shows:
- Two-column admin layout
- Left: tabbed Booking Neuron settings form (rate, minimum stay, deposit, advance window, AI toggles)
- Right: homepage section order control with drag-and-drop section visibility
- OpsShell sidebar with Booking Neuron highlighted
- Save button in teal

### booking_property_card_manager.png

Property Card Manager admin UI.

Shows:
- Grid of property card previews with edit controls
- Cover photo upload, crop, position options
- AI Enhance button (FairAgent action, human-approved)
- Published/Draft/Paused visibility toggles
- Live preview of card position in bento homepage layout

### booking_fairagent_settings_panel.png

FairAgent AI configuration panel for the Booking Neuron.

Shows:
- Agent behavior toggles (auto-draft replies, pricing suggestions, language detection)
- Guardrails section with human-approval requirements
- Max discount slider
- Live agent preview: guest query → AI draft → staff approval button
- FairAgent status badge: Active — Human-supervised mode
- Training & Knowledge Base section

## Generation context

These images were generated as part of the MLADIS design planning session on 2026-06-23.

They guided the homepage layout selection (Option B approved) and the admin control system design.
