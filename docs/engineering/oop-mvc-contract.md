# MLADIS OOP and MVC Contract

OOP and MVC are the engineering bible for MLADIS. Every feature must preserve this contract.

## Required Shape

- **Model/domain objects** own state, identity, invariants, and business rules.
- **Controllers/API views** coordinate requests, call model/domain objects, and return explicit payloads.
- **Views/templates/components** render model state. They do not invent business rules or keep duplicate truth.

## User and Agent State

Every visitor is represented as a user/session context object:

- Anonymous visitor: internal `anon:<session>` context.
- Authenticated visitor: internal `user:<id>` context.
- Signed-out visitor: still a visitor context, but `is_authenticated` is false.

The booking agent is also an object:

- `AgentInstance` represents the shared public booking agent and its policy.
- `AgentUserContext` attaches that agent to the current visitor/user.
- `AgentAccessContext` answers whether that user context can ask that agent.

The frontend mirrors this with `PublicUserContext`, which owns the current auth state and its `AgentAccessStatus`.

## Reservation and Payment Objects

Reservation requests are objects, not form blobs:

- `BookingInquiry` is the reservation request object and owns request identity through `request_key`.
- `ReservationRequestService` prepares and creates reservation requests from validated form/controller input.
- `DamageDeposit` is the deposit object tied back to the reservation request through `inquiry`.
- `ReservationPaymentHold` is the reservation payment object tied back to the reservation request through `inquiry`.
- `PaymentAuthorization` is the provider-return payment object. It owns the `successful` decision.
- Payment services create provider checkout state from payment objects; views do not assemble payment records by hand.
- Payment confirmation rule: `if payment.successful: send confirmation emails; else: do not send`.

## Non-Negotiables

- Do not keep separate login/agent state in unrelated components.
- Do not let the nav say one thing while the agent panel says another.
- Do not check raw auth booleans in several views when one user context model can own the decision.
- Do not hide backend enforcement behind frontend-only behavior.
- Do not patch views around a broken model/controller boundary.
- Do not create customer, reservation, request, payment, invoice, promotion, or agent objects without a data-store export/log path.

## Correct Flow

1. Browser visits the site.
2. Backend controller builds a user/session context object.
3. Backend attaches the shared agent object to that user context.
4. Backend returns the current context payload.
5. Frontend controller stores that payload as a `PublicUserContext`.
6. Nav, booking, and agent views all render from that one context.

For the agent button:

- If `PublicUserContext.agent.isAuthenticated` is false, render `Sign in to ask agent`.
- If true and `canAsk` is true, render `Ask agent`.
- If true and limit is reached, render the limit message.

## Regression Test Rule

Any change that touches login, logout, public agent access, booking permissions, reservations, payments, or account state must include a focused test proving the model/controller/view flow still agrees.

Any change that creates or mutates a durable business object must also prove one of these is true:

- the object is covered by a data lake export collection,
- the workflow appends a live `object_events` record when `MLADIS_DATASTORE_ROOT` is configured,
- or the feature documentation records why logging is intentionally deferred.
