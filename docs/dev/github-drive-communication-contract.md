# MLADIS GitHub and Drive Communication Contract

## Source-of-truth split

MLADIS uses two complementary communication and evidence surfaces:

| Surface | Stores | Does not store |
|---|---|---|
| GitHub (`pzg8794/MLADIS`) | Code, architecture, contracts, decisions, sanitized workflows, agent feedback, verification status, issue/PR handoffs, commit history | Raw customer data, credentials, private exports, production database files, unredacted screenshots |
| Google Drive MLADIS Object Lake | Private JSON/JSONL object records, raw or restricted capture evidence, approved data-lake exports, private QA artifacts | Source-code decisions that future agents need to recover, secrets in unapproved locations, customer data in public/shared docs |

GitHub is the durable engineering communication record. Drive is the private
data and evidence record. Neither surface replaces the Django database as the
transactional source of truth.

## Required workflow

1. Declare the active object and scope in the repository task record.
2. Store private customer, Airbnb, reservation, or conversation material in
   the approved Drive location only.
3. Store the sanitized schema, workflow, decision, and evidence reference in
   GitHub.
4. Commit and push the change to `codex/dev` with a focused message.
5. Record local and production verification status in the GitHub feature
   ledger; do not claim a pass from an intention or screenshot alone.
6. When an external agent such as Viber reviews the work, send only the
   sanitized GitHub context needed for review. Record its feedback and the
   accepted, rejected, or deferred disposition back in GitHub.

## Handoff template

```text
Repository: pzg8794/MLADIS
Branch/commit: codex/dev/<commit>
Active object: <object>
GitHub documents: <paths or issue/PR>
Drive evidence reference: <non-sensitive identifier only>
Review questions: <specific questions>
Known limitations: <explicit list>
```

Never put a Drive URL containing private customer data, raw messages, contact
values, credentials, or private identifiers into a public GitHub document.
Use a non-sensitive evidence ID and keep the private mapping in the approved
Drive area.

## External-agent feedback

For each Viber or other-agent review, GitHub must record:

```text
Reviewer: <agent or reviewer name>
Source: <issue, PR, or sanitized handoff ID>
Feedback: <sanitized summary>
Disposition: accepted | rejected | deferred
Reason: <technical, safety, or business reason>
Follow-up commit: <hash or none>
```

An external-agent suggestion is not an MLADIS decision until it is reviewed in
context and recorded in GitHub. Private source material remains in Drive.

## Privacy and action boundaries

- Do not commit names, emails, phone numbers, addresses, thread IDs, booking
  IDs, raw conversation bodies, credentials, API keys, cookies, or payment data.
- Do not use Drive as a substitute for Git history or architecture documents.
- Do not use GitHub as a data lake.
- Do not send customer messages, edit Airbnb, change reservations, or alter
  permissions merely because an external review suggested it. Those actions
  require their own explicit approval and evidence.
- Keep draft-only AI response workflows and customer-facing sender workflows
  clearly separated.

## Completion standard

A task is complete only when the relevant GitHub docs/code and verification
state are pushed, private evidence is stored in the approved Drive location,
the handoff is recoverable from GitHub, and the working tree is clean.
