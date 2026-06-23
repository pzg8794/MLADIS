# Implementation Notes

These notes explain how the 809 Shipping design should eventually be implemented using the MLADIS process.

## Development sequence

### Phase 1 - Public website shell

Start with customer-facing pages:

- Homepage
- Quote calculator
- Tracking page
- How it works / services

The initial implementation can use fallback-safe sample data while the backend objects are being created.

### Phase 2 - Shipment object foundation

Build the `Shipment` object first.

A Shipment should connect:

- Customer
- PackageItem
- TrackingEvent
- ShippingLane
- CustomsCase
- Invoice
- PaymentTransaction
- WarehouseItem
- DeliveryRoute

### Phase 3 - CustomsCase foundation

Build `CustomsCase` as a first-class object, not a notes field.

This is strategically important because customs workflows create delays, documents, fees, customer questions, and operational risk.

### Phase 4 - Operations command center

Implement:

- Shipment Command Center
- Customs Operations
- Warehouse Management
- Delivery Routing

Each page should render object snapshots and detail panels.

### Phase 5 - Business layer

Implement:

- Customer CRM
- Payments & Invoices
- Analytics & Reports
- Executive Command Center

### Phase 6 - AI Shipping Agent

Add AI assistant features after object workflows exist.

The AI agent should read structured objects and suggest actions. It should not replace staff approval for consequential workflows.

## Frontend architecture pattern

Each major object should follow the MLADIS pattern:

```text
Domain object
Application service
Factory
Repository
Page
Components
```

Example for Shipment:

```text
frontend/src/domain/shipments.ts
frontend/src/application/ShipmentService.ts
frontend/src/application/ShipmentFactory.ts
frontend/src/infrastructure/ShipmentRepository.ts
frontend/src/ui/pages/ShipmentWorkspacePage.tsx
frontend/src/ui/components/shipments/ShipmentTable.tsx
frontend/src/ui/components/shipments/ShipmentDetailPanel.tsx
```

## Backend architecture pattern

The backend should expose object-centered APIs:

```text
GET    /api/shipping/shipments/
POST   /api/shipping/shipments/
GET    /api/shipping/shipments/<id>/
PATCH  /api/shipping/shipments/<id>/
GET    /api/shipping/shipments/<id>/timeline/
POST   /api/shipping/shipments/<id>/tracking-events/
POST   /api/shipping/shipments/<id>/documents/
POST   /api/shipping/shipments/<id>/customs-case/
```

## Shared with MLADIS

Potentially shared patterns:

- dashboard shell
- status badges
- card/grid/table primitives
- payment/invoice object approach
- customer/guest relationship management concepts
- AI assistant training interface concepts
- real-first/fallback-safe data strategy
- data-lake/event logging philosophy

## Important warning

Do not implement 809 Shipping by copying static mock screens directly.

The screenshots are design references. The platform should be built from objects and services so the UI can grow without being rewritten.
