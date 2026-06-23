# Page Inventory

This inventory turns the mock-up booklet into a future platform roadmap.

## Public website

### Homepage / Landing Page

Purpose: introduce 809 Shipping, communicate trust, and drive quote/tracking actions.

Core objects:

- ShippingLane
- QuoteRequest
- TrackingSearch
- ServiceOffering
- CustomerReview

### Quote Calculator

Purpose: estimate package cost and create a quote workflow.

Core objects:

- QuoteRequest
- PackageItem
- ShippingRoute
- ShippingMethod
- RateEstimate

### Package Tracking

Purpose: let customers follow shipment progress.

Core objects:

- Shipment
- TrackingEvent
- RouteCheckpoint
- DeliveryEstimate
- SupportConversation

### How It Works / Services

Purpose: explain process, lanes, customs support, and service promises.

Core objects:

- ServiceOffering
- ShippingLane
- CustomsRequirement
- FAQItem

## Staff operations

### Shipment Command Center

Purpose: operational overview of shipments and pipeline health.

Core objects:

- Shipment
- TrackingEvent
- ShipmentPipelineStage
- Alert
- Carrier

### Customs Operations

Purpose: manage customs cases, missing documents, compliance statuses, and country-specific processing.

Core objects:

- CustomsCase
- ShippingDocument
- CustomsRequirement
- Shipment
- ComplianceNote

### Warehouse Management

Purpose: track inventory, package photos, storage zones, receiving, scanning, and dispatch.

Core objects:

- WarehouseItem
- PackageItem
- StorageZone
- BarcodeScan
- WarehouseWorkflow

### Delivery Routing

Purpose: manage drivers, routes, vehicles, stops, delivery exceptions, and completion.

Core objects:

- DeliveryRoute
- DeliveryStop
- Driver
- Vehicle
- Shipment

## Business operations

### Customer CRM

Purpose: manage customer profiles, communication, documents, shipping history, preferences, and value.

Core objects:

- Customer
- Shipment
- SupportConversation
- ShippingPreference
- ShippingDocument
- CustomerNote

### Payments & Invoices

Purpose: manage transactions, invoices, payments, refunds, reminders, and customer billing history.

Core objects:

- Invoice
- PaymentTransaction
- Shipment
- Customer
- Refund

### Analytics & Reports

Purpose: provide operational and business intelligence.

Core objects:

- Report
- ShipmentMetric
- RevenueMetric
- CustomsDelayMetric
- CarrierPerformanceMetric
- CustomerGrowthMetric

### Executive Command Center

Purpose: give owners/leaders a high-level view of revenue, operations, customer health, bottlenecks, and AI recommendations.

Core objects:

- ExecutiveSnapshot
- OperationalHealthMetric
- GrowthMetric
- Bottleneck
- AIRecommendation

## Future pages

Recommended next mockups/design docs:

- AI Shipping Agent
- Shipment creation wizard
- CustomsCase detail page
- Customer support inbox
- Driver mobile app
- Customer mobile app
- Admin/settings workspace
- Knowledge-base management
- Document upload portal
