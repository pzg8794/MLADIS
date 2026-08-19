# Airbnb Response Workflow Verification

This file records evidence for the guarded response workflow. Customer names,
messages, thread IDs, contact details, and raw exports must remain in the
private evidence store and never be copied here.

| Check | Status | Evidence | Last verified |
| --- | --- | --- | --- |
| Draft command accepts one private customer message | PASS | `draft_airbnb_response` run against a private real-thread message; output remained draft-only | 2026-08-18 |
| Draft is formatted into readable sections | PASS | Formatter regression test plus real-thread draft output; numbered steps and emphasis render without split markers | 2026-08-18 |
| Low-stakes topics are classified | PASS | Unit test for availability plus workflow classification path | 2026-08-18 |
| Escalation topics are not auto-sendable | PASS | Unit tests for financial questions and day-use/event requests | 2026-08-18 |
| Staff approval is required | PASS | `AirbnbResponseWorkflow.approve` test | 2026-08-18 |
| Durable authorization required | PASS | Authorization-ledger regression tests | 2026-08-19 |
| New guest message invalidates authorization | PASS | Hash-bound stale-message regression test | 2026-08-19 |
| Property-rule change invalidates authorization | PASS | Rule-digest regression test | 2026-08-19 |
| Duplicate or uncertain send is blocked | PASS | Idempotent claim/send regression test | 2026-08-19 |
| Real Airbnb unread discovery | PASS | Authorized inbox dry run; one platform event skipped and unread state preserved | 2026-08-19 |
| Live MLADIS model provider | PASS | Private local credential reused without disclosure; grounded response returned in `openai` mode | 2026-08-19 |
| Send-enabled Airbnb processor | PASS | Authorized inbox run used `send=true`; platform event was skipped, with zero sends and zero uncertain deliveries | 2026-08-19 |
| Fifteen-minute scheduler | PASS | Paused-until-commit heartbeat created as `mladis-airbnb-low-stakes-inbox-responder`; activated only after push | 2026-08-19 |
| One controlled real-customer draft reviewed | PASS | Private active thread; no name, message, or thread ID copied into Git | 2026-08-18 |
| Rules-first one-night/no-visitors interpretation | PASS | Property rule applied before conversation history; reservation-holder accountability included; no identity copied | 2026-08-18 |
| Practice edit/unsend handling | PASS | Practice messages were unsent; the composer was cleared; no customer-facing practice message remains | 2026-08-18 |
| Party prohibition is preserved | PASS | Workflow documentation distinguishes prohibited parties from an unconfirmed birthday/gathering and requires manual review | 2026-08-18 |
| One approved customer send | NOT RUN | No eligible unread low-stakes guest question was available | 2026-08-19 |
| Customer response observed | NOT RUN | Requires a verified provider send first | 2026-08-19 |

The associated lake import can be resumed independently with:

```bash
cd airbnb_agent
./scripts/resume_airbnb_data_lake.sh /private/path/airbnb-export.jsonl
```
