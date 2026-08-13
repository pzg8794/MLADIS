# MLADIS Feature Verification Ledger

Status: active quality record

Machine-readable ledger: [`feature-verification-ledger.csv`](feature-verification-ledger.csv)

GitHub tracker: [Full Functionality Verification](https://github.com/pzg8794/MLADIS/milestone/1)

## Purpose

This ledger prevents an implementation, build, route smoke, or prior production
canary from being summarized as "everything works." Each user-visible function
has independent implementation and verification states. A feature is fully
verified only when all applicable states are `PASS` for the same release.

## Verification States

| State | Meaning |
| --- | --- |
| `IMPLEMENTED` | Source code exists and the control is wired to a real service, route, or honestly unavailable state. |
| `PARTIAL` | Some required behavior exists, but one or more paths remain incomplete. |
| `UNKNOWN` | The implementation has not been audited. |
| `PASS` | The expected result and applicable persisted/external effect were observed. |
| `FAIL` | The function was executed and did not meet its contract. |
| `BLOCKED` | Verification cannot run because a named dependency, credential, or environment is unavailable. |
| `NOT_TESTED` | No valid execution evidence exists. |
| `NOT_APPLICABLE` | This verification axis does not apply to the function. |

The verification axes are:

1. `implementation_status`: code and wiring audit.
2. `local_dev_status`: automated checks against the canonical local environment.
3. `local_user_status`: browser execution as the named user role with visible expected-result checks.
4. `production_dev_status`: production-safe health, API, provider, or database evidence.
5. `production_user_status`: production browser/canary execution as the named user role.

## Evidence Rules

- Every `PASS` must include a durable evidence reference and verification date.
- State-changing tests must verify both the visible result and the database or
  provider effect.
- A prior release canary is valid only for that release and function scope.
- `BLOCKED` must name the missing dependency. It is not a pass.
- Fake buttons, dead links, visual-only filters, and fake pagination are
  `FAIL`, not `IMPLEMENTED`.
- Hidden or disabled controls with an honest reason may be recorded as
  `UNAVAILABLE` in `notes`, but must not be counted as working.
- When code changes a feature, reset affected verification cells to
  `NOT_TESTED` until they are rerun.

## Required Workflow

1. Add or update the function row before implementation.
2. Implement the feature using real records and real service boundaries.
3. Run automated local checks and update `local_dev_status`.
4. Drive the function through the browser as each applicable role and update
   `local_user_status`.
5. Deploy only after approval, then run production-safe checks and update the
   production columns.
6. Link defects in `defect` and do not overwrite failures with narrative text.
7. Update the ledger in the same pull request or commit series as the verified
   feature.

## Current Agent Verification

The 2026-08-13 booking-agent readability pass verified the real local homepage
as an authenticated guest. A live `gpt-5.4-nano` response was returned through
the configured OpenAI provider and rendered as a compact paragraph without raw
Markdown emphasis markers. The response was 40 words. The browser contained no
MLADIS application errors; one unrelated Google Maps widget request failed.

Evidence:

- [`agent-readability-local.png`](evidence/2026-08-13-agent-readability/agent-readability-local.png)
- [`agent-live-openai-local.png`](evidence/2026-08-13-agent-readability/agent-live-openai-local.png)
- [`agent-live-openai-production.png`](evidence/2026-08-13-agent-readability/agent-live-openai-production.png)
- [`browser-observation.md`](evidence/2026-08-13-agent-readability/browser-observation.md)
- `bookings.tests.AgentAPITests`: 13 passing tests.

## Full-Site Claim

MLADIS may be described as fully functional only when every enabled function in
the CSV has `PASS` for all applicable verification axes on one immutable release
and no open P0/P1 defect. Until then, reports must state the verified scope and
the remaining `FAIL`, `BLOCKED`, and `NOT_TESTED` rows.
