# Document Archive Sharding And Rehydration

Status: Adopted for MLADIS document-heavy workflows  
Effective: 2026-08-12

## Decision

MLADIS uses Google Drive as the durable document archive and small, private GitHub repositories as fast working segments. The production application and the public MLADIS code repository store metadata and retrieval references only; they do not store private document payloads.

This pattern applies to any document category that becomes slow because of file count, binary size, cloud hydration, or Git history. The first implementation is the private `pzg8794/MLADIS-Invoices-2026` repository.

## Storage Tiers

1. **Google Drive: canonical archive**
   - Holds the durable copy, organized by business area and period.
   - Stores the original document and its immutable metadata record.
   - Remains the source of truth after a Git working segment is closed.

2. **Private GitHub segment: fast active window**
   - Contains only the current, frequently accessed period for one document category.
   - Must be private before any document is added.
   - Must not contain credentials, recovery codes, government identity scans, signatures, full bank or card numbers, guest identity files, or documents whose disclosure would create material legal risk.
   - Legal/property packets remain in the private Drive legal archive unless counsel transmission requires a controlled copy.

3. **MLADIS application: metadata index**
   - Stores document identifiers, category, dates, status, hashes, and authorized retrieval references.
   - Does not scan archive repositories or mounted Drive folders during application startup.
   - Retrieves a document only when a user explicitly requests it.

4. **Disposable local checkout: archive rehydration**
   - Used to inspect one closed private GitHub segment.
   - Lives under an existing local temporary workspace, never inside the production checkout.
   - Is deleted after the needed files are verified or restored.

## Segmentation

Use a separate private repository family for each high-volume category. Do not mix unrelated records merely to reduce repository count.

Examples:

- `MLADIS-Invoices-2026`
- `MLADIS-Receipts-2026`
- `MLADIS-Statements-2026`
- `MLADIS-Operations-Documents-2026`

Legal, property, identity, tax-return, guest-private, and credential material needs a stricter review and is not automatically eligible for GitHub storage.

## Default Limits

Close the active segment when any threshold is reached:

- 250 MB repository working size
- 1,000 files
- 10 MB for an individual document
- Observable clone, status, index, or application latency that exceeds the team's normal workflow

At 80% of a limit, mark the segment `ROLLOVER_DUE`. Do not rely on a GitHub release to reduce size: releases and tags do not reset repository history.

The successor is a new private repository, for example `MLADIS-Invoices-2026-Q4-02`. The old repository is finalized and archived; it is never emptied and reused.

## Required Index Record

Every archived document record should contain:

- stable document ID
- category
- document date
- vendor or counterparty
- amount and currency when applicable
- source filename
- canonical Drive location identifier
- private working-segment repository and path, when present
- SHA-256 hash
- verification status
- payment, filing, or response status
- retention class
- sensitivity class
- superseding document ID, when applicable

Indexes must mask account numbers and personal identifiers. Do not publish Drive share URLs or private repository links in public documentation.

## Rollover Procedure

1. Stop writes to the active segment.
2. Verify that every document has a canonical Drive copy.
3. Export the final metadata index and SHA-256 manifest.
4. Check repository visibility and collaborator access.
5. Scan tracked content for secrets and restricted identifiers.
6. Tag the final state with `archive-YYYY-MM-DD`.
7. Archive the private GitHub repository.
8. Create the next private segment from an empty repository.
9. Copy only the index schema, policy, and current-period files into the new segment.
10. Update the MLADIS application index to point new writes to the successor.

## Temporary Rehydration Procedure

Use this only when an old working segment is needed.

```bash
cd <existing-MLADIS-temp-workspace>
git clone --filter=blob:none --no-checkout <private-archive-url> temp-git-repo
cd temp-git-repo
git sparse-checkout init --cone
git sparse-checkout set <needed-period-or-path>
git checkout <archive-tag-or-default-branch>
```

After inspection:

1. Verify the selected file against the archive SHA-256 manifest.
2. Copy an actively needed document only to its canonical Drive location or the current eligible private segment.
3. Update the metadata index with the restoration event.
4. Do not merge the old archive branch into the live repository.
5. Remove the disposable checkout from the temporary workspace.

A future MLADIS archive-retrieval command may automate this process. It must require the archive name and exact path, verify private visibility, use sparse checkout, validate the hash, and clean up the temporary checkout.

## Application Performance Contract

- Production code must not include document binaries.
- Application startup must not hydrate mounted Drive files.
- List views query metadata, not filesystem trees.
- Preview and download are explicit user actions.
- Background indexing is incremental and resumes from a cursor.
- Closed segments are excluded from routine sync and CI.
- Large files stay in Drive and are represented by verified metadata records.
- Git LFS is not the default archive mechanism because its quota and transfer behavior do not solve repository-history growth.

## Privacy And Access

- Public repositories contain this policy and sanitized status only.
- Private repositories use least-privilege collaborators.
- A private repository is still an external service; restricted documents remain Drive-only unless an owner-approved workflow explicitly permits them.
- Deleting a tracked file does not erase it from Git history. A mistaken sensitive upload requires incident handling and history remediation.
- Secrets and authentication artifacts are never document archives.

## Current Implementation

- Private active segment: `pzg8794/MLADIS-Invoices-2026`
- Durable source: MLADIS private Google Drive archive
- Current segment content: policy only; no invoice documents added as of 2026-08-12
- Public MLADIS repository: architecture and sanitized operational status only
