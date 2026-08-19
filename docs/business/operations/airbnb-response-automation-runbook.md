# Airbnb Response Automation Runbook

## Status

The current workflow is **draft-only**. It can use a real Airbnb customer
message as input and produce a real MLADIS response draft, but it cannot send
to Airbnb without a deliberately configured sender adapter and an immediate
staff confirmation at action time.

This is intentional. The collector is read-only, and the response workflow
must not silently represent MLADIS to a customer.

## Workflow

```mermaid
flowchart LR
  A[Authorized Airbnb DOM capture] --> B[Private combined export]
  B --> C[resume_airbnb_data_lake.sh]
  C --> D[BOOKINGS reservation snapshots]
  C --> E[INTERACTIONS anonymized learning lake]
  F[One customer message] --> G[AirbnbResponseWorkflow]
  G --> H[MLADIS agent draft]
  H --> I{Low-stakes and staff approved?}
  I -- no --> J[Escalate for manual handling]
  I -- yes --> K[Explicit send confirmation]
  K --> L[Future Airbnb sender adapter]
```

1. Capture only rendered Airbnb DOM through the authorized host session.
2. Run the new-only lake wrapper. It resumes from
   `BOOKINGS/.airbnb_capture_state.json` and skips completed source threads.
3. For a response test, pass one customer message to the draft command. The
   command stores the normal MLADIS agent conversation and prints only the
   structured draft result; the customer message is not written to Git.
4. Review the language, facts, promised actions, and escalation classification.
5. Obtain staff confirmation immediately before any future send action.
6. Record the result and evidence in the verification tracker.

## Draft command

From the repository:

```bash
cd airbnb_agent
.venv/bin/python manage.py draft_airbnb_response \
  --message "One private customer message" \
  --item-id 123
```

The command returns `send_status: "draft_only"`. It never sends a message.
The message argument must come from a private, authorized test flow and must
not be placed in shell history, logs, fixtures, commits, or issue text.

## Low-stakes gate

The workflow may classify a draft as low-stakes only for basic availability,
location, amenities, services, or general house-rule questions. Pricing,
deposits, payments, refunds, cancellations, damage, complaints, safety, legal
questions, discounts, guarantees, special exceptions, birthdays, events,
day-use requests, common-area use, contradictory guest counts, and unregistered
visitors always require manual handling. A small, normal gathering may be
allowed when it fits the applicable property rules, permitted hours, noise
limits, registered guest limits, visitor rules, and advance-notice or approval
requirements; the word "gathering" is a review trigger, not proof that every
gathering is prohibited. The response must distinguish registered overnight
guests from the total people proposing to use the property and must never
approve the request before staff confirms the conditions. A low-stakes
classification is not permission to send; the staff approval gate is still
required.

The detailed property-specific rules and service response ladder are maintained
in the [Customer Service Playbook](./customer-service-playbook.md).

When a reservation is discussed, the reservation holder must be treated as the
sole responsible party for everything that happens during the reservation,
regardless of who does what. This responsibility statement does not authorize
visitors or change a property's guest-count, day-use, or gathering rules.

## Actual-customer test protocol

For a controlled test, the host may designate one real customer thread and
confirm that the assigned staff member will not respond during the test
window. The operator must:

1. verify the exact thread and latest customer message in the authorized host
   browser;
2. run the draft workflow without sending;
3. compare the draft against the actual question, current listing facts, and
   MLADIS communication standards;
4. show the exact proposed reply, destination thread, and action to the owner;
5. obtain an immediate action-time confirmation before sending one message;
6. record whether the customer replied and whether the draft resolved the
   question.

Do not test against a customer who has not been identified by the host, and do
not send a response merely because a prior instruction authorized automation.
Do not expose the customer's name or message in Git documentation.

### Verified interpretation case

One controlled draft test used the private active Airbnb thread where a guest
first proposed a daytime birthday use for ten people, then clarified that only
five would sleep overnight. The workflow correctly kept the case in manual
review. For the one-night property involved, the rules-first interpretation is
that the reservation is for registered overnight guests only: it is not day use
and does not permit visitors or additional people to gather at the property.
The reservation holder is solely responsible for everything during the
reservation, regardless of who does what. The first permissive practice draft
was not sent; it was replaced with a corrected rules-first draft left unsent
for owner review.

When the platform supports editing or unsending a practice message, use that
instead of sending successive correction messages. A practice correction is
not customer-facing evidence unless the owner explicitly confirms a send and
the resulting customer-visible state is observed.

## Evidence and limitations

The workflow test is not a claim that Airbnb sending, provider callbacks,
scheduled jobs, or cancellation/payment actions work. Those require separate
safe tests. The current implementation has no active Airbnb sender adapter;
therefore any attempted send fails closed with a draft-only error.

Related records:

- [Airbnb collection runbook](../../data-store/airbnb-collection-runbook.md)
- [Anonymous interaction contract](../../data-store/anonymous-interaction-lake-contract.md)
- [Feature verification plan](../../qa/full-site-functional-verification-plan.md)
