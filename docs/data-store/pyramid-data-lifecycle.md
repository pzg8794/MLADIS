# MLADIS Pyramid Data Lifecycle

The MLADIS information lifecycle is:

```text
COLLECT -> CLEAN -> PREPARE -> LEARN -> USE
```

The Pyramid is a data-maturity and access-boundary model. It is not a license
to build a giant procedural ETL function, replace domain objects with JSON
dictionaries, or bypass authorization. `ACTION` is outside the Pyramid and
must remain behind an explicit authorized workflow.

## Stage Contract

| Stage | Purpose | Primary object responsibility |
|---|---|---|
| COLLECT | Preserve source evidence | Source/evidence objects retain origin, capture time, and source scope. |
| CLEAN | Normalize and protect | Normalization, validation, conflict, and redaction objects preserve evidence status and privacy. |
| PREPARE | Establish MLADIS truth candidates | Domain objects, aggregates, identity resolvers, and reconciliation objects establish relationships and invariants. |
| LEARN | Derive knowledge safely | Signal/knowledge objects retain provenance, confidence, and the evidence used to derive them. |
| USE | Serve a bounded use case | DTOs and projections expose complete, purpose-specific context to controllers and views. |

## OOP/MVC Integration

OOP and MVC remain authoritative at every stage:

- Domain objects own identity, state, relationships, invariants, and domain
  decisions.
- Services coordinate cross-object workflows without becoming a substitute for
  the object model.
- Repositories/adapters own storage and external-system boundaries.
- Controllers coordinate use cases and return explicit domain/projection
  payloads.
- Templates and UI components render projections and do not reconstruct
  relationships or business rules.

The Pyramid answers **where information is in its lifecycle**. OOP answers
**what the information is**. Relationships answer **how objects connect**. MVC
answers **how application requests consume those objects**. The canonical
engineering rules are in `docs/engineering/oop-mvc-contract.md`.

## Relationship-First Preparation

Preparation must resolve relationships rather than duplicate strings across
unrelated records:

```text
Guest
  -> Reservations
Reservation
  -> Property
  -> Guest
  -> Payments
  -> DepositHolds
  -> Invoices
  -> Messages
  -> WorkOrders
  -> Timeline
```

Important reconciliation boundaries are explicit and reviewable:

```text
AirbnbReservationSnapshot
  -> ReservationReconciliation
  -> unmatched | candidate_match | confirmed_match | imported | rejected
  -> Reservation / BookingInquiry

AirbnbGuestRecord
  -> GuestIdentityResolver
  -> unmatched | candidate | confirmed | conflict
  -> Guest / CustomerProfile
```

No inferred signal may silently overwrite a source-backed fact. Conflicts must
remain visible until an authorized workflow resolves them.

## Privacy Is a Separate Dimension

Repository visibility and Pyramid stage are independent. A COLLECT record can
be private, and public application code can implement a LEARN algorithm without
making the learned data public.

MLADIS uses three practical privacy tiers:

1. **Tier 1: raw/private capture** - source messages, reservation evidence,
   private source documents, and capture metadata.
2. **Tier 2: protected operational objects** - normalized guest, reservation,
   property, transaction, and event objects needed for operations.
3. **Tier 3: anonymized learning objects** - identity-free interactions,
   themes, outcomes, and derived signals used for learning and evaluation.

Public GitHub code and sanitized architecture documentation must not contain
Tier 1 or Tier 2 records. The Drive/Object Lake and approved transactional
stores remain the data boundary for private runtime material.

## Evidence Escalation

When remote and local evidence disagree, investigate in this order:

```text
remote contract
  -> remote implementation/diff
  -> local implementation
  -> local tests/runtime
  -> private Drive/source documents
  -> data-lake state
  -> production evidence, when authorized and available
```

Absence from GitHub is not evidence of absence. Record whether a state is
committed, local-only, experimental, verified, or unavailable before changing
architecture.

## Agent Handoff Minimum

Every architecture handoff should include:

- goal and active object;
- repository, branch, commit, and local dirty-state;
- architecture objects and relationships affected;
- Pyramid stages touched;
- OOP/MVC boundaries touched;
- tests and runtime evidence;
- private source material available locally but not copied into GitHub;
- known uncertainty and questions requiring evidence.

This keeps Viber, Codex, local runtime agents, and human decisions aligned
without making any one surface the entire system of record.
