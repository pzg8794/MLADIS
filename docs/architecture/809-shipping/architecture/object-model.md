# Object Model

809 Shipping should use an object-first architecture from the beginning.

## Core rule

```text
Each page is a projection of platform objects.
Objects own business meaning.
Pages render object state.
Services coordinate workflows.
Repositories manage data sources.
```

## Primary objects

### Shipment

The central object of the platform.

Responsibilities:

- tracking number
- customer link
- origin and destination
- route/lane
- package items
- current status
- tracking events
- customs case link
- invoice/payment link
- warehouse location
- delivery route link
- ETA and delivery outcome

### Customer

Relationship and identity object.

Responsibilities:

- name, email, phone
- country/location
- preferred language
- shipping history
- communication history
- documents
- invoices/payments
- preferences
- VIP/repeat/business status
- support notes

### CustomsCase

A first-class object for customs and compliance work.

Responsibilities:

- shipment link
- missing documents
- customs status
- inspection state
- fees/duties
- country-specific requirements
- compliance notes
- updates and timeline
- AI customs guidance

This may become one of the most valuable objects in the platform because many shipping systems treat customs as notes instead of structured workflow state.

### WarehouseItem

Operational inventory object.

Responsibilities:

- SKU/package identifier
- shipment link
- storage zone
- barcode
- package photo references
- receiving status
- dispatch status
- exception state

### DeliveryRoute

Delivery execution object.

Responsibilities:

- driver
- vehicle
- route number
- delivery stops
- shipment assignments
- route status
- ETA per stop
- completion state
- exception handling

### PaymentTransaction

Money movement object.

Responsibilities:

- transaction number
- customer link
- shipment link
- invoice link
- method/provider
- amount
- status
- refund/chargeback link
- reconciliation state

### Invoice

Billing document object.

Responsibilities:

- invoice number
- shipment/customer link
- line items
- fees
- taxes
- customs charges
- total due
- status
- due date
- document URL

### Carrier

External or internal transport provider.

Responsibilities:

- carrier name
- route coverage
- service type
- reliability metrics
- cost/performance signals

### TrackingEvent

Timeline event object for shipment movement.

Responsibilities:

- shipment link
- event type
- location
- timestamp
- visibility to customer
- source/provider
- note

### ShippingDocument

Document object for customs, customer verification, invoices, and package evidence.

Responsibilities:

- shipment/customer/customs case link
- document type
- file URL
- verification status
- required/optional flag
- uploaded by
- reviewed by
- timestamps

### SupportConversation

Communication object.

Responsibilities:

- customer link
- shipment link
- channel
- messages
- suggested replies
- staff notes
- status

### ShippingAgent

AI assistant/automation object.

Responsibilities:

- customer questions
- knowledge sources
- FAQ training
- customs guidance
- suggested replies
- operational recommendations
- confidence/guardrails

## Suggested frontend object structure

```text
frontend/src/domain/shipments.ts
frontend/src/domain/customers.ts
frontend/src/domain/customsCases.ts
frontend/src/domain/warehouseItems.ts
frontend/src/domain/deliveryRoutes.ts
frontend/src/domain/paymentTransactions.ts
frontend/src/domain/invoices.ts
frontend/src/domain/trackingEvents.ts
frontend/src/domain/shippingDocuments.ts
frontend/src/domain/supportConversations.ts
```

## Suggested backend service structure

```text
shipping/services/shipments.py
shipping/services/customers.py
shipping/services/customs_cases.py
shipping/services/warehouse.py
shipping/services/delivery_routes.py
shipping/services/payments.py
shipping/services/invoices.py
shipping/services/tracking.py
shipping/services/documents.py
shipping/services/agent.py
```

## Data strategy

Use the MLADIS real-first rule:

```text
Use real data wherever available.
Use fallback/sample/seed data only where real fields/endpoints are missing.
Keep fallback data isolated behind repositories, mappers, fixtures, or domain factories.
Never mix data scaffolding directly into page behavior.
```
