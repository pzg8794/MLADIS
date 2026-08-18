# MLADIS Customer Service Playbook

## Purpose

This is the customer-service source of truth for the temporary Airbnb-to-MLADIS
transition. It explains how MLADIS interprets customer intent, answers basic
questions, handles property rules, and decides when a draft must go to staff.

The playbook is based on read-only inspection of the Airbnb host listing editor,
arrival guidance, house rules, reservation details, and the existing host
conversation patterns. It is a policy and response guide, not a replacement for
the live property records.

## Non-negotiable service rules

1. Answer the customer's actual question first. Do not recite a generic script.
2. Separate the number of people staying overnight from the total number of
   people who would use the property.
3. Never treat a customer's first description as complete when a later message
   changes the dates, guest count, purpose, or use of common areas.
4. Never infer that a customer is telling the truth, or that a requested
   exception is approved, simply because they say what we want to hear.
5. A gathering is not automatically prohibited. A small, normal,
   rules-compliant gathering may be allowed only when the applicable property
   rules, permitted hours, noise limits, guest limits, visitor rules, and any
   advance-notice or approval requirements are satisfied.
6. Parties, disruptive events, unregistered visitors, and day-use arrangements
   that exceed the property's rules require manual review. Do not promise an
   approval in chat.
7. Before a reservation proceeds, require an explicit written confirmation that
   the guest count is accurate and that the customer will follow the property
   rules and any approved gathering conditions.
8. If Airbnb's listing summary and arrival guide conflict, stop guessing and
   escalate the answer to staff. A stale or contradictory source is not a valid
   basis for an automated promise.
9. Do not expose private Wi-Fi credentials, access codes, host phone numbers, or
   other operational secrets in public AI responses, Git, the anonymized
   interaction lake, or a public help page. Deliver those details only through
   the approved post-confirmation channel.
10. Do not promise availability, pricing, discounts, refunds, cancellation
    outcomes, or reservation confirmation without current system evidence and
    staff authorization.

## Response decision ladder

### Step 1: Identify the request

Extract only the facts needed for the next safe answer:

- property or stay requested;
- arrival and departure dates;
- overnight registered guest count;
- total people who will enter or use the property;
- visitors, event, birthday, gathering, pool, BBQ, filming, or day-use intent;
- the exact question still unanswered.

### Step 2: Compare facts against the property record

Use the current property object and its rule projection. Check capacity, stay
length, check-in/out, quiet hours, visitor policy, gathering conditions, and
amenity coordination. Treat missing or contradictory fields as an escalation,
not as permission to improvise.

### Step 3: Give a conditional answer

For a straightforward question, answer directly. For a gathering or exception,
state the condition that must be satisfied and the missing fact that staff must
confirm. Do not turn a conditional answer into a reservation approval.

### Step 4: Require written rule confirmation

Use a short confirmation before moving forward:

> Before we continue, please confirm the final number of people who will use
> the property, the number registered to stay overnight, and that everyone will
> follow the applicable house rules, quiet hours, visitor limits, and any
> gathering conditions approved by MLADIS. We will confirm the request before it
> is final.

For Spanish, preserve the same meaning and conditions rather than sending a
literal but weaker translation.

### Step 5: Escalate when needed

Escalate requests involving money, safety, complaints, damage, legal questions,
uncertain identity, contradictory guest counts, events, birthdays, day use,
common-area use, extra visitors, or a requested exception. A draft may still be
prepared, but it is not auto-sendable.

## Property rule matrix from Airbnb

The following is a normalized operational summary from the Airbnb host UI. It
is intentionally free of customer names, reservation identifiers, credentials,
door codes, and private contact values. The live listing record remains the
authority when a value changes.

| Property | Stay/capacity | Rule signals | Customer-service handling |
| --- | --- | --- | --- |
| 3BR G-101 | 1-90 nights; up to 7 guests; check-in 3:00 PM; listing summary checkout 11:00 AM | Parties not allowed in the apartment/recreation area; small gatherings allowed with advance notice; loud noise limited after 5:00 PM; no noise after 11:00 PM; one-night reservations have no visitors; 2+ night reservations allow one visitor per guest, who must leave before 11:00 PM; pool/BBQ requires coordination | Confirm total people, overnight count, dates, and gathering details. Do not approve a birthday/day-use request without staff confirmation. |
| 3BR G-102 | 1-365 nights; up to 7 guests; check-in 3:00 PM; listing summary checkout 11:00 AM | Parties not allowed; small gatherings allowed with advance notice; same core noise, visitor, guest-count, pool, and BBQ rules as the 3BR set; the current custom text is missing one visitor-rule line, so do not assume it is different | Use the current listing record and escalate if visitor terms matter. Require accurate registration and written rule acceptance. |
| 6BR G-102 | 2-1125 nights; up to 14 guests; check-in 3:00 PM; checkout 11:00 AM | Airbnb control shows events off and smoking off; quiet hours on; parties not allowed; small gatherings allowed with advance notice; two pets shown in the host editor; guest count must match the reservation | The larger capacity does not remove the gathering, noise, visitor, or registration checks. Confirm the final total and overnight count. |
| Vacation Day Apartment with Pool | 1-night stay; up to 7 guests; check-in 10:00 AM; checkout 12:00 AM | Airbnb control shows events on, smoking on, quiet hours off, and pets off, while the additional rules still prohibit parties and allow small gatherings with advance notice; guest count must match the reservation | Treat the listing as a day-use product, but still require staff confirmation of the purpose, total people, hours, and rule-compliant use. Do not infer that “events on” permits a party. |

### Known source conflicts

The Airbnb arrival guidance currently contains shared text that refers to G-102
even when shown from another listing, says checkout is at 12:00 PM while the
listing summary says 11:00 AM, and contains a G-101 entry instruction for both
units. These are captured as source-quality issues. MLADIS must not repeat them
as confirmed facts until a staff member reconciles the property records.

The 3BR and day-use listings also show broad Airbnb controls that can appear to
permit events or smoking while their custom rules prohibit parties and smoking
inside the apartment. The custom property rules and an explicit staff review
control the response. The agent must describe the conflict and escalate rather
than choose the permissive interpretation.

## The real-thread interpretation pattern

An anonymized controlled test contained this sequence:

1. The customer first asked about day use for ten people without an overnight
   stay.
2. The customer clarified that it was a birthday and later said ten people
   would use the common area while five would sleep overnight.
3. The correct interpretation is not “ten overnight guests,” and it is not
   “all gatherings are forbidden.” It is a request for a possible
   rules-compliant gathering with a mismatch between total people and registered
   overnight guests.
4. The draft must ask for the dates, property, final overnight count, total
   people present, and written agreement to the rules. It must say that MLADIS
   will confirm whether the proposed gathering fits the applicable limits.
5. The case remains manual review until staff confirms the gathering, visitor
   conditions, hours, and property-specific rules. No message was sent in the
   controlled test.

## Response quality checklist

Before a staff member approves a draft, verify:

- The first sentence answers the current question.
- Overnight guests and total people present are separate fields.
- The property and dates are not guessed.
- A conditional rule is stated as conditional.
- No availability, price, discount, exception, or approval is invented.
- The customer is asked only for the missing facts needed to proceed.
- Written rule acceptance is requested before the reservation continues.
- The message uses short paragraphs or numbered steps and is easy to read.
- Any conflict or risky topic is marked for staff review.

## Source and maintenance record

Current source surfaces inspected on 2026-08-18:

- Airbnb host listing editor for the four active MLADIS listings;
- per-listing House rules panel;
- per-listing Arrival guide panel;
- a current inquiry's reservation details and message history;
- existing host response patterns in the authorized Messages workspace.

When a listing changes, update the structured MLADIS property/rule source first,
then update this playbook's summary and the response tests. Keep raw Airbnb
captures in the private local evidence/data-lake area. Do not paste raw HTML,
customer identities, reservation IDs, Wi-Fi values, access codes, or private
phone numbers into Git documentation.

Related documents:

- [Airbnb response automation runbook](./airbnb-response-automation-runbook.md)
- [Airbnb collection runbook](../../data-store/airbnb-collection-runbook.md)
- [Anonymous interaction lake contract](../../data-store/anonymous-interaction-lake-contract.md)
- [Feature verification plan](../../qa/full-site-functional-verification-plan.md)
