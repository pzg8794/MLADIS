# Local AI PDF Form-Fill Instructions

Last updated: 2026-07-05

Use this when asking a local AI agent to help fill an official PDF form for MLADIS LLC.

## Safety rule

Do not put the completed PDF, private identifier values, personal address details, owner identity numbers, bank data, portal credentials, or fax confirmations in Git. Keep those files in the private business-record vault.

## Goal

Ask the local AI to create a completed draft copy of the official PDF response, using private records stored locally, then stop for human review before signature and submission.

## Files to prepare locally

Create a private working folder outside the repo, for example:

```text
MLADIS-Private-Business-Records/current-response/
```

Put these files there:

```text
original-notice.pdf
private-business-values.txt
filled-response-draft.pdf
submission-log.txt
```

The `private-business-values.txt` file should contain only the values needed for the form, such as business address, business phone, owner/member facts, classification choice, business activity code, and the federal business identifier from the private vault.

## Prompt to give the local AI

```text
You are helping me prepare a draft response to an official LLC/LLP information-request PDF for MLADIS LLC.

Use a PDF form-filling skill or equivalent PDF editing tool. Work only on local private files. Do not upload the PDF or private values to any external service. Do not store completed forms, private identifiers, addresses, or owner identity values in Git.

Input files:
- original PDF: ./original-notice.pdf
- private values: ./private-business-values.txt

Tasks:
1. Inspect all pages of the PDF and identify every field that needs an answer.
2. Produce a field-by-field fill plan before modifying the PDF.
3. Fill only fields supported by the private values file.
4. For any uncertain field, leave it blank and list it in a review section.
5. Do not guess classification, business activity code, member facts, prior-business status, or registration-transfer status.
6. Output a draft PDF named ./filled-response-draft.pdf.
7. Output a plain-text review checklist named ./submission-log.txt listing:
   - fields filled,
   - fields left blank,
   - assumptions used,
   - questions requiring human or CPA review,
   - exact submission methods shown on the notice.
8. Stop before signature. The owner must review, sign, date, and submit.

After creating the draft, tell me exactly what I need to review before printing/signing/faxing.
```

## Field-review checklist

Before signing, manually confirm:

- Legal entity name is correct.
- Mailing address is correct.
- Physical address is correct.
- Business phone is correct.
- Entity type is correct.
- Single-member or multi-member status is correct.
- Owner/member legal name is correct.
- Ownership percentage is correct.
- Federal identifier is correct and not stored in Git.
- Business activity code matches the real primary activity.
- Business start date is correct.
- Prior-business/successor status is correct.
- Any transfer of prior registrations is correctly handled.
- Signature title is correct.
- Signature date is current.

## Submission workflow

1. Review the filled draft page by page.
2. Print the final draft.
3. Sign and date it manually.
4. Fax it using the number shown on the notice.
5. Save the fax confirmation in the private vault.
6. Optionally mail the signed copy as backup.
7. Confirm receipt with the agency.
8. Update the repo-safe tracker with dates only, not private values.

## Good local command pattern

If the local AI can run shell commands, ask it to keep outputs in the private folder:

```bash
mkdir -p ~/MLADIS-Private-Business-Records/current-response
cd ~/MLADIS-Private-Business-Records/current-response
```

Then place `original-notice.pdf` and `private-business-values.txt` there before running any PDF tool.

## Completion note for the repo

After submission, update the repo-safe compliance tracker with only:

```text
Sent by fax: YYYY-MM-DD
Fax confirmation saved privately: yes/no
Mailed backup copy: yes/no
Receipt confirmed: yes/no
Follow-up required: yes/no
```
