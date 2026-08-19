# Historical Data Runbook

This runbook is for the protected Airbnb historical-data sidecar. It is a
manual, low-frequency operation and is not part of normal MLADIS startup or
request processing.

## Preconditions

1. Use a protected local directory or mounted Drive segment. Never use a Git
   checkout for real data.
2. Confirm the COLLECT root is an existing MLADIS Object Lake export and keep
   it read-only.
3. Choose a separate output root. The preparation service rejects nested or
   overlapping roots.
4. Keep the `--private-working-segment` acknowledgement explicit.
5. Do not put credentials, tokens, card data, access secrets, raw messages, or
   unredacted screenshots in the input/output path used for a public Git task.

## Prepare or resume

From `airbnb_agent/`:

```bash
python manage.py prepare_airbnb_history \
  --collect-root /protected/MLADIS-DATASTORE \
  --output-root /protected/MLADIS-HISTORY \
  --hot-policy current-year \
  --as-of 2026-08-19 \
  --private-working-segment
```

For a repeatable rerun with the same source hashes and policy:

```bash
python manage.py prepare_airbnb_history \
  --collect-root /protected/MLADIS-DATASTORE \
  --output-root /protected/MLADIS-HISTORY \
  --hot-policy current-year \
  --as-of 2026-08-19 \
  --resume \
  --private-working-segment
```

The command reports CLEAN counts, duplicates, conflicts, and PREPARE context
and index counts. It does not alter Django transactional records.

## Targeted historical lookup

```bash
python manage.py rehydrate_airbnb_history \
  --history-root /protected/MLADIS-HISTORY \
  --guest-id customer_profile:42 \
  --year 2024 \
  --temporary-output /protected/temporary/guest-42-2024.json \
  --private-working-segment
```

The lookup checks the active transactional store first. If it misses, it reads
only the exact indexed guest/year archive after verifying its size and SHA-256.
The temporary output is mode `0600` and should be deleted according to the
protected retention policy after the use case is complete.

## Promotion

Promotion is not performed by either management command. A future authorized
workflow must:

1. review the prepared context and unresolved conflicts;
2. reconcile Guest and Reservation identity against current domain services;
3. approve explicit promotion keys;
4. write through transactional repositories in one auditable operation;
5. rely on the promotion key to make retries idempotent.

Do not use prepared JSON as a substitute for a Django domain write, and do not
silently overwrite a current operational record.

## Failure handling

Stop and preserve evidence when:

- a source collection is malformed or declares the wrong collection;
- the output path overlaps the COLLECT root;
- a history index reference is missing;
- the indexed archive is missing, unreadable, has the wrong size, or has a
  different SHA-256;
- conflicting facts have no approved resolution;
- the private-segment acknowledgement is absent.

Do not bypass these failures by selecting another year, changing a source key,
or manually editing an archive. Rebuild CLEAN/PREPARE from COLLECT after the
source issue is resolved.

## Retention and authority

Drive/Object Lake is the durable private archive. The Django transactional
store is current operational truth. Public GitHub contains only the code,
sanitized fixtures, and this documentation. No private Git working segment is
used by the initial implementation.

## Scope boundary

This process is historical preparation and targeted lookup only. It does not
send customer messages, enable an Airbnb live sender, accept or cancel a
reservation, charge or refund a payment, capture or release a deposit, or
change authentication.
