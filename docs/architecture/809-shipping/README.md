# 809 Shipping Platform Design Documentation

Date: 2026-06-22
Status: concept design / future platform reference

This directory documents the 809 Shipping mock-up booklet and platform direction created during MLADIS design planning.

809 Shipping is treated as a future platform built from the same design and architecture philosophy as MLADIS: real-first data, fallback-safe development, object-driven frontend/backend design, modern SaaS operations screens, and a clean command-center experience.

## Design premise

809 Shipping should not be designed as a basic courier website.

It should be designed as:

```text
A MLADIS-style command-center platform for international shipping, customs, warehouse, delivery, payments, CRM, and business intelligence.
```

## Visual direction

The visual style should align with MLADIS while adapting to the 809 Shipping brand:

- deep navy command surfaces
- ocean blue and Caribbean teal accents
- white workspace cards
- clean tables and operational dashboards
- rounded cards and soft shadows
- premium SaaS typography
- status badges for shipping, customs, delivery, and payment states
- map-based logistics visuals
- customer-facing tracking and quote flows

## Generated image assets

The generated mock-up booklet currently includes three image boards:

```text
images/809_shipping_platform_mock_up_layout.png
images/809_shipping_platform_mock_up_overview.png
images/809_shipping_platform_overview_mockup.png
```

These images are design references only. They should guide layout, visual direction, and feature imagination, but implementation should follow the object architecture documented here.

## Documentation map

```text
docs/architecture/809-shipping/
├── README.md
├── design/
│   ├── mockup-booklet.md
│   ├── theme-and-ux-direction.md
│   └── page-inventory.md
├── architecture/
│   ├── object-model.md
│   └── implementation-notes.md
└── images/
    ├── README.md
    ├── 809_shipping_platform_mock_up_layout.png
    ├── 809_shipping_platform_mock_up_overview.png
    └── 809_shipping_platform_overview_mockup.png
```

## Core platform objects

The platform should eventually revolve around these first-class objects:

```text
Shipment
Customer
CustomsCase
WarehouseItem
DeliveryRoute
PaymentTransaction
Invoice
Carrier
TrackingEvent
ShippingDocument
SupportConversation
ShippingAgent
```

## MLADIS architecture alignment

The future implementation should follow the same structure used for MLADIS objects:

```text
frontend/src/domain/<object>.ts
frontend/src/application/<Object>Service.ts
frontend/src/application/<Object>Factory.ts
frontend/src/infrastructure/<Object>Repository.ts
frontend/src/ui/pages/<Object>WorkspacePage.tsx
frontend/src/ui/components/<object>/...
```

The page should not own business truth. Pages render object projections.
