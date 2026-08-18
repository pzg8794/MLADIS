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
| No sender adapter means send fails closed | PASS | Unit test and command evidence | 2026-08-18 |
| One controlled real-customer draft reviewed | PASS | Private active thread; no name, message, or thread ID copied into Git | 2026-08-18 |
| One approved customer send | NOT RUN | Requires action-time owner confirmation |  |
| Customer response observed | NOT RUN | Requires approved send and private observation |  |

The associated lake import can be resumed independently with:

```bash
cd airbnb_agent
./scripts/resume_airbnb_data_lake.sh /private/path/airbnb-export.jsonl
```
