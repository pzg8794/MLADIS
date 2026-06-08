# ADR 0001: MLADIS Universe and Neuron Architecture

Status: Accepted as guiding architecture  
Scope: MLADIS platform, Viverse, re-architecture roadmap  
Primary purpose: Define the reusable domain layout that prevents MLADIS from being narrowed into a single vacation-rental application.

---

## 1. Context

MLADIS is not only a booking website, a vacation-home system, a tax tool, a research platform, a fitness system, or a portfolio.

MLADIS is the larger universe: a modular intelligence system where reusable domain capabilities, called **neurons**, cooperate to support many human-centered services.

The current production system began with vacation homes and booking operations. That was the first real-world expression of the platform, not the full identity of the platform.

Future MLADIS work will include:

- booking and reservation workflows,
- finance, taxes, ledgers, and expense intelligence,
- research workflows for quantum computing, AI, and AI fairness,
- education and learning support,
- fitness and wellness support,
- portfolio and identity representation,
- Pyramid-based memory, indexing, evidence, and archival structures,
- FairAgent-based ethical, fairness-aware, context-aware automation.

Because MLADIS is expected to grow across domains, its architecture must be object-oriented, reusable, composable, and resistant to premature narrowing.

---

## 2. Foundational Rule

A **MLADIS neuron** is a reusable intelligence structure that transforms data into meaning, decisions, coordination, or action.

A neuron is not just a database table or stored file.

A neuron must help the system understand, coordinate, decide, explain, automate, or improve something.

Examples of neurons:

- `Booking`
- `Finance`
- `Research`
- `Education`
- `Fitness`
- `Portfolio`
- `Pyramid`
- `FairAgent`

Examples of artifacts, not neurons:

- `Document`
- `Picture`
- `Receipt`
- `InvoicePDF`
- `Contract`
- `Report`
- `DatasetFile`
- `LegalNotice`

Artifacts are important, but they are outputs, evidence, memory, or files used by neurons. They do not become top-level neurons unless they gain intelligence behavior beyond storage and representation.

---

## 3. Notation

MLADIS uses this architecture notation:

```text
Neuron [uses: OtherNeuron]
- Neuron.SubNeuron
  - Neuron.SubNeuron.Object
    - Neuron.SubNeuron.Object.Specialization
```

### 3.1 Composition

Use `[uses: ...]` when one neuron collaborates with another neuron.

Example:

```text
Booking [uses: Finance, Pyramid, FairAgent]
```

Meaning:

- Booking is not Finance.
- Booking has access to Finance.
- Booking can create, reference, or request Finance objects.
- Booking can store memory/evidence through Pyramid.
- Booking can ask FairAgent for fairness-aware support, explanation, or automation.

### 3.2 Inheritance

Use inheritance only when a child object truly specializes a parent object inside the same neuron family.

Example:

```text
Booking.Request
- Booking.Request.GuestRequest
- Booking.Request.ClientRequest
```

`GuestRequest` is a specialized form of `Booking.Request`.

Do not use inheritance when the relationship is only collaboration.

### 3.3 Artifact references

Artifacts are referenced by neurons.

Example:

```text
Booking.Maintenance.Repair
  [uses Artifact.Picture]
  [uses Finance.Transaction.Expense]
  [uses Pyramid.Evidence]
  [can produce Artifact.Report]
```

The repair event is meaningful because it coordinates property readiness, cost, evidence, and future tax/document generation. The pictures and generated report are artifacts.

---

## 4. MLADIS Universe Layout

```text
MLADIS
|
|-- Pyramid
|   |-- Pyramid.Memory
|   |-- Pyramid.Index
|   |-- Pyramid.Evidence
|   |-- Pyramid.Dataset
|   |-- Pyramid.Archive
|   `-- Pyramid.Search
|
|-- FairAgent [uses: Pyramid]
|   |-- FairAgent.Context
|   |-- FairAgent.Policy
|   |-- FairAgent.Decision
|   |-- FairAgent.Explanation
|   |-- FairAgent.Action
|   `-- FairAgent.Audit
|
|-- Finance [uses: Pyramid, FairAgent]
|   |-- Finance.Transaction
|   |   |-- Finance.Transaction.Payment
|   |   |-- Finance.Transaction.Deposit
|   |   |-- Finance.Transaction.Refund
|   |   |-- Finance.Transaction.Expense
|   |   |-- Finance.Transaction.Revenue
|   |   `-- Finance.Transaction.Transfer
|   |
|   |-- Finance.Invoice
|   |-- Finance.Receipt
|   |-- Finance.Ledger
|   |-- Finance.TaxRecord
|   |-- Finance.Budget
|   |-- Finance.Report
|   `-- Finance.Forecast
|
|-- Booking [uses: Finance, Pyramid, FairAgent]
|   |-- Booking.Resource
|   |   |-- Booking.Resource.Property
|   |   |-- Booking.Resource.Service
|   |   |-- Booking.Resource.Session
|   |   `-- Booking.Resource.Space
|   |
|   |-- Booking.Request
|   |   |-- Booking.Request.GuestRequest
|   |   |-- Booking.Request.ClientRequest
|   |   |-- Booking.Request.StudentRequest
|   |   `-- Booking.Request.ResearchRequest
|   |
|   |-- Booking.Reservation
|   |   |-- Booking.Reservation.StayReservation
|   |   |-- Booking.Reservation.AppointmentReservation
|   |   |-- Booking.Reservation.SessionReservation
|   |   `-- Booking.Reservation.ConsultationReservation
|   |
|   |-- Booking.Availability
|   |   |-- Booking.Availability.Window
|   |   |-- Booking.Availability.Block
|   |   |-- Booking.Availability.Override
|   |   `-- Booking.Availability.Calendar
|   |
|   |-- Booking.Maintenance
|   |   |-- Booking.Maintenance.Cleaning
|   |   |-- Booking.Maintenance.Repair
|   |   |-- Booking.Maintenance.Inspection
|   |   `-- Booking.Maintenance.Readiness
|   |
|   `-- Booking.Policy
|       |-- Booking.Policy.Cancellation
|       |-- Booking.Policy.Deposit
|       |-- Booking.Policy.Access
|       `-- Booking.Policy.Pricing
|
|-- Research [uses: Pyramid, FairAgent, Finance]
|   |-- Research.Question
|   |-- Research.Project
|   |-- Research.Experiment
|   |-- Research.Dataset
|   |-- Research.Model
|   |-- Research.Result
|   |-- Research.Publication
|   `-- Research.Review
|
|-- Education [uses: Booking, Portfolio, Pyramid, FairAgent]
|   |-- Education.Course
|   |-- Education.Lesson
|   |-- Education.Assessment
|   |-- Education.Accommodation
|   |-- Education.StudentRecord
|   |-- Education.Reflection
|   `-- Education.PortfolioArtifact
|
|-- Fitness [uses: Booking, Finance, Portfolio, Pyramid, FairAgent]
|   |-- Fitness.Routine
|   |-- Fitness.Session
|   |-- Fitness.Nutrition
|   |-- Fitness.Progress
|   |-- Fitness.Condition
|   `-- Fitness.Recommendation
|
`-- Portfolio [uses: Pyramid, FairAgent]
    |-- Portfolio.Identity
    |-- Portfolio.Project
    |-- Portfolio.Experience
    |-- Portfolio.Credential
    |-- Portfolio.Publication
    |-- Portfolio.Showcase
    `-- Portfolio.Narrative
```

---

## 5. Artifact Layer

Artifacts are not neurons. They are produced, stored, interpreted, linked, or transformed by neurons.

```text
Artifact
|-- Document
|-- Picture
|-- Video
|-- Audio
|-- Receipt
|-- InvoicePDF
|-- Contract
|-- Report
|-- LegalNotice
|-- DatasetFile
|-- ResearchPaper
|-- LessonPlan
`-- EvidencePacket
```

An artifact can be powerful evidence, but it does not become a neuron merely because it exists.

The intelligence comes from the neuron that interprets or uses it.

Examples:

- Finance reads a receipt and classifies it.
- Booking uses pictures to support a maintenance record.
- Research produces a dataset file and uses Pyramid to index it.
- Education produces a lesson plan and stores it as an artifact.
- Portfolio uses documents, publications, projects, and narratives as identity evidence.

---

## 6. Important Naming Rules

### 6.1 Use singular object names

Domain objects should be singular.

Prefer:

```text
Booking
Reservation
Request
Resource
Finance
Transaction
Receipt
Research
Experiment
Education
Course
Portfolio
Project
```

Avoid singular object classes named as plural categories:

```text
Bookings
Reservations
Requests
Resources
Transactions
Documents
Profiles
Agents
Rentals
```

Plural names are acceptable for UI labels, folders, routes, and collections when appropriate. Domain concepts should remain singular.

### 6.2 Do not name neurons after one product expression

Avoid making a neuron too narrow.

Do not make the core neuron:

```text
Rental
Airbnb
VacationHome
GuestStayOnly
```

Use:

```text
Booking
Booking.Resource.Property
Booking.Reservation.StayReservation
Booking.Request.GuestRequest
```

The public product may say “Vacation Homes,” but the internal reusable neuron is `Booking`.

### 6.3 Product expressions are not neuron names

Examples:

| Product expression | Internal neuron structure |
|---|---|
| Vacation homes | Booking.Resource.Property + Booking.Reservation.StayReservation |
| Tax system | Finance.TaxRecord + Finance.Transaction + Finance.Report |
| Research platform | Research.Project + Research.Experiment + Research.Publication |
| Fitness coaching | Fitness.Routine + Fitness.Session + Booking.Reservation.SessionReservation |
| Education tools | Education.Course + Education.Lesson + Education.Assessment |
| Portfolio website | Portfolio.Identity + Portfolio.Project + Portfolio.Showcase |

---

## 7. Neuron Relationship Rules

### 7.1 Composition is the default

Most neuron relationships should be composition.

Example:

```text
Booking [uses: Finance, Pyramid, FairAgent]
```

Booking can reference Finance transactions, but Booking is not Finance.

### 7.2 Inheritance stays inside the neuron family

Example:

```text
Booking.Request
- Booking.Request.GuestRequest
```

GuestRequest inherits from Request because it is a specialized request.

Example:

```text
Finance.Transaction
- Finance.Transaction.Expense
```

Expense inherits from Transaction because it is a specialized financial transaction.

### 7.3 Cross-neuron interactions use references, events, services, or adapters

Example:

```text
Booking.Reservation.StayReservation
  -> creates/references Finance.Transaction.Payment
  -> creates/references Finance.Transaction.Deposit
  -> stores/references Pyramid.Evidence
  -> requests FairAgent.Explanation
```

This is not inheritance. It is collaboration.

---

## 8. Example: Vacation Homes Without Narrowing MLADIS

The public UI may say:

```text
Vacation Homes
```

Internally, the system should express this as:

```text
Booking.Resource.Property
Booking.Request.GuestRequest
Booking.Reservation.StayReservation
Booking.Maintenance.Cleaning
Booking.Maintenance.Repair
Finance.Transaction.Deposit
Finance.Transaction.Payment
Finance.Transaction.Expense
Pyramid.Evidence
FairAgent.Explanation
```

This keeps the current production system connected to the larger MLADIS brain.

The vacation-home system is not the identity of MLADIS. It is one expression of the Booking neuron.

---

## 9. Example: Maintenance Under Booking

Maintenance belongs under Booking for the current MLADIS vacation-home system because maintenance affects the readiness and availability of a bookable resource.

```text
Booking.Maintenance
- Booking.Maintenance.Cleaning
- Booking.Maintenance.Repair
- Booking.Maintenance.Inspection
- Booking.Maintenance.Readiness
```

A maintenance event should require at minimum:

- title,
- cost,
- time,
- pictures.

A maintenance event may then connect to:

```text
Finance.Transaction.Expense
Finance.Receipt
Finance.TaxRecord
Pyramid.Evidence
Artifact.Picture
Artifact.Report
```

This allows MLADIS to generate formal maintenance reports, bills, tax-support packets, and property-readiness records.

---

## 10. Example: Tax System

The tax system primarily belongs under Finance.

```text
Finance [uses: Pyramid, FairAgent]
|-- Finance.Transaction.Expense
|-- Finance.Transaction.Revenue
|-- Finance.Invoice
|-- Finance.Receipt
|-- Finance.TaxRecord
`-- Finance.Report
```

If tax meetings or appointments are needed, Finance can use Booking:

```text
Booking.Reservation.ConsultationReservation
```

Taxes should not be hacked into Booking. Taxes are a Finance expression that may use Booking for scheduling.

---

## 11. Example: Research System

The research system belongs under Research.

```text
Research [uses: Pyramid, FairAgent, Finance]
|-- Research.Question
|-- Research.Project
|-- Research.Experiment
|-- Research.Dataset
|-- Research.Model
|-- Research.Result
`-- Research.Publication
```

For quantum MAB, AI fairness, and EQUITAS-style work, the structure may include:

```text
Research.Experiment.QuantumMABExperiment
Research.Model.EXPNeuralUCBModel
Research.Model.ICMABModel
Research.Result.RegretCurve
Research.Result.FairnessMetric
Research.Publication.PaperDraft
```

Research stores and indexes artifacts through Pyramid:

```text
Pyramid.Dataset
Pyramid.Index
Pyramid.Archive
```

Research can use FairAgent for explanation, audit, fairness review, and ethical interpretation:

```text
FairAgent.Explanation
FairAgent.Audit
FairAgent.Decision
```

---

## 12. Example: Education System

Education is broader than teaching.

```text
Education [uses: Booking, Portfolio, Pyramid, FairAgent]
|-- Education.Course
|-- Education.Lesson
|-- Education.Assessment
|-- Education.Accommodation
|-- Education.StudentRecord
|-- Education.Reflection
`-- Education.PortfolioArtifact
```

Education can use Booking when scheduling classes, tutoring, office hours, meetings, or advising.

Education can use Portfolio when student work or teaching evidence becomes part of a portfolio.

Education can use FairAgent when decisions involve access, accommodation, equity, bias, or inclusive design.

---

## 13. Example: Fitness System

Fitness is a neuron because it can transform routines, health signals, progress, nutrition, and user context into guidance and action.

```text
Fitness [uses: Booking, Finance, Portfolio, Pyramid, FairAgent]
|-- Fitness.Routine
|-- Fitness.Session
|-- Fitness.Nutrition
|-- Fitness.Progress
|-- Fitness.Condition
`-- Fitness.Recommendation
```

Fitness may use Booking for coaching sessions, Finance for paid plans or subscriptions, Portfolio for public transformation/content identity, Pyramid for health/progress memory, and FairAgent for safe/context-sensitive recommendations.

---

## 14. Example: Portfolio System

Portfolio is broader than Profile.

A profile is often too narrow because it only stores user attributes.

Portfolio can represent identity, projects, credentials, public presence, work history, narratives, publications, and service offerings.

```text
Portfolio [uses: Pyramid, FairAgent]
|-- Portfolio.Identity
|-- Portfolio.Project
|-- Portfolio.Experience
|-- Portfolio.Credential
|-- Portfolio.Publication
|-- Portfolio.Showcase
`-- Portfolio.Narrative
```

A user account can reference a Portfolio, but the Portfolio is more than an account profile.

---

## 15. Pyramid

Pyramid is the MLADIS memory and structured knowledge system.

It replaces the generic idea of a “data lake” in MLADIS language.

Pyramid should manage:

- durable memory,
- archival records,
- evidence structures,
- indexing,
- searchable JSON objects,
- datasets,
- generated reports,
- cross-neuron references,
- audit trails,
- future retrieval and AI grounding.

Pyramid does not erase the operational database. The operational database remains the source of truth for current application state. Pyramid supports archival, search, evidence, analysis, cross-domain learning, and future intelligence.

---

## 16. FairAgent and Fairgent

`FairAgent` is the code/domain name.

`Fairgent` may be used as a brand or UI name.

FairAgents are fairness-aware, context-aware, ethically constrained agentic structures that help MLADIS reason, explain, recommend, and act.

```text
FairAgent [uses: Pyramid]
|-- FairAgent.Context
|-- FairAgent.Policy
|-- FairAgent.Decision
|-- FairAgent.Explanation
|-- FairAgent.Action
`-- FairAgent.Audit
```

FairAgent must not be a generic chatbot wrapper. It must preserve MLADIS values: fairness, consent, context, human dignity, evidence, accountability, and explainability.

---

## 17. Target Code Layout

This is the long-term target architecture. It does not require immediate renaming of every current app.

```text
mladis/
|
|-- core/
|   |-- neuron.py
|   |-- artifact.py
|   |-- value_object.py
|   |-- event.py
|   `-- registry.py
|
|-- pyramid/
|   |-- models.py
|   |-- services.py
|   |-- repositories.py
|   `-- schemas/
|
|-- fair_agent/
|   |-- models.py
|   |-- policies.py
|   |-- services.py
|   `-- audit.py
|
|-- finance/
|   |-- models.py
|   |-- services.py
|   |-- repositories.py
|   |-- serializers.py
|   `-- views.py
|
|-- booking/
|   |-- models.py
|   |-- request.py
|   |-- reservation.py
|   |-- resource.py
|   |-- availability.py
|   |-- maintenance.py
|   |-- policy.py
|   |-- services.py
|   |-- repositories.py
|   `-- views.py
|
|-- research/
|-- education/
|-- fitness/
`-- portfolio/
```

Current code may continue to use existing Django app names during transition. The architecture should guide gradual refactoring rather than force risky renaming.

---

## 18. Re-Architecture Roadmap

### Phase 1: Documentation and naming alignment

- Add this architecture document.
- Update the README to describe MLADIS as a universe/intelligence platform.
- Stop describing MLADIS as only a vacation-rental or booking website.
- Define vacation homes as the first expression of the Booking neuron.

### Phase 2: Core abstractions

Create or formalize:

```text
core.Neuron
core.Artifact
core.ValueObject
core.Event
core.Registry
```

### Phase 3: Booking cleanup

Gradually map existing booking code into:

```text
Booking.Resource
Booking.Request
Booking.Reservation
Booking.Availability
Booking.Maintenance
Booking.Policy
```

Avoid Airbnb-specific or rental-specific naming in reusable logic.

### Phase 4: Finance neuron

Formalize:

```text
Finance.Transaction
Finance.Invoice
Finance.Receipt
Finance.Ledger
Finance.TaxRecord
```

Connect Booking events to Finance through references/events/services.

### Phase 5: Pyramid integration

Create a Pyramid-backed storage/indexing structure for:

- JSON records,
- artifacts,
- evidence packets,
- generated reports,
- search indexes,
- research datasets,
- audit records.

### Phase 6: Research migration

Create the Research neuron and migrate research assets into:

```text
Research.Question
Research.Project
Research.Experiment
Research.Dataset
Research.Model
Research.Result
Research.Publication
```

### Phase 7: FairAgent integration

Add FairAgent as the fairness-aware action and explanation layer.

Use it first where decisions affect users, customers, students, guests, property management, finance, or research fairness.

---

## 19. Decision

MLADIS will be documented and developed as a universe of composable neurons.

The current booking/vacation-home system is the first production expression of the Booking neuron.

Future work must preserve the distinction between:

- neuron,
- sub-neuron,
- object,
- specialization,
- artifact,
- product expression.

This architecture is accepted as the guiding model for MLADIS re-architecture and future development.

---

## 20. Summary

The winning MLADIS pattern is:

```text
Neuron [uses: OtherNeuron]
- Neuron.SubNeuron
  - Neuron.SubNeuron.Object
    - Neuron.SubNeuron.Object.Specialization
```

The guiding sentence is:

> A MLADIS neuron is a reusable intelligence structure that transforms data into meaning, decisions, coordination, or action. Neurons may use other neurons through composition. Specialized objects inherit within their neuron family. Artifacts are evidence, memory, or outputs used by neurons.

This protects MLADIS from being narrowed into a single app and gives the system a durable OOP foundation for Booking, Finance, Research, Education, Fitness, Portfolio, Pyramid, and FairAgent.
