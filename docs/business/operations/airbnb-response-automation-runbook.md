# Airbnb Response Automation Runbook

## Status

The workflow is **prepared and draft-only**. It can accept one private Airbnb
message as input and produce an internal MLADIS response draft, but it cannot
send to Airbnb and must not write directly to a customer. This preparation pass
does **not** test the workflow with a real customer.

This is intentional. The collector is read-only, and the response workflow
must not silently represent MLADIS to a customer.

## Prepared workflow artifacts

| Responsibility | Reusable artifact | Boundary |
|---|---|---|
| Response decision and draft | `airbnb_agent/bookings/airbnb_response_workflow.py` | Produces an internal draft; it has no sender. |
| One-message draft command | `airbnb_agent/bookings/management/commands/draft_airbnb_response.py` | Accepts one private structured message and returns a draft-only result. |
| Read-only Airbnb capture | `airbnb_agent/scripts/capture_airbnb_messages.mjs` | Reads rendered DOM through an already-authorized host session. |
| New-only lake resume | `airbnb_agent/scripts/resume_airbnb_data_lake.sh` | Imports only unseen conversation and reservation captures. |
| Customer-service rules | `docs/business/operations/customer-service-playbook.md` | Supplies rules-first response and escalation guidance. |
| Behavior mapping | `docs/business/operations/airbnb-platform-behavior-map.md` | Maps guest, staff, agent, and system behavior to MLADIS objects and capabilities. |
| Listing improvement | `docs/business/operations/airbnb-listing-improvement-runbook.md` | Turns recurring questions and outcomes into approved listing proposals. |

There is deliberately no Airbnb sender adapter in this workflow. A future
sender requires a separate implementation, staff approval gate, and an
explicitly authorized live test. The current prepared process ends at an
internal draft and review record.

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
3. For a future controlled test, pass one customer message to the draft
   command. The command stores the normal MLADIS agent conversation and prints
   only the structured draft result; the customer message is not written to
   Git. This preparation pass does not run the command against a real customer.
4. Review the language, facts, promised actions, and escalation classification.
5. Obtain staff confirmation immediately before any future send action.
6. Record the result and evidence in the verification tracker.

The response formatter must keep drafts concise: short paragraphs, one idea per
paragraph, and only the facts needed for the next decision. A greeting is fine
when it is its own paragraph; never combine it with the first substantive idea
or follow it with a wall of text. Before drafting from older guidance, compare
the rule wording with the current property record and correct grammar or
ambiguity.

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

## Future controlled test protocol

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
reservation, regardless of who does what. Parties are not allowed where the
property rules prohibit them. A birthday or gathering is not automatically a
party, but the agent must not infer approval; it must escalate when the facts
are unclear. The first permissive practice draft was not sent, the composer
was cleared, and no customer-facing draft remains.

When the platform supports editing or unsending a practice message, use that
instead of sending successive correction messages. The agent workflow should
produce an internal draft for staff review, not write directly to Airbnb. A
practice correction is not customer-facing evidence unless the owner explicitly
confirms a send and the resulting customer-visible state is observed.

## Evidence and limitations

The workflow test is not a claim that Airbnb sending, provider callbacks,
scheduled jobs, or cancellation/payment actions work. Those require separate
safe tests. The current implementation has no active Airbnb sender adapter;
therefore any attempted send fails closed with a draft-only error.

Related records:

- [Airbnb collection runbook](../../data-store/airbnb-collection-runbook.md)
- [Anonymous interaction contract](../../data-store/anonymous-interaction-lake-contract.md)
- [Airbnb-to-MLADIS behavior map](airbnb-platform-behavior-map.md)
- [Airbnb listing improvement runbook](airbnb-listing-improvement-runbook.md)
- [Feature verification plan](../../qa/full-site-functional-verification-plan.md)
