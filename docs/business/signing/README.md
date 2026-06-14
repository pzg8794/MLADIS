# Signing Controls

Private signing-control note for MLADIS LLC.

## Policy

Do not commit reusable signature images, signature stamps, scans of IDs, EIN letters, SSNs, bank records, tax returns, or payment credentials to GitHub.

If a document needs a signature:

1. The owner must explicitly authorize signing that specific document in the current thread.
2. The exact document path, signer name, date, and signature method must be recorded.
3. Any reusable signature image must stay outside Git in a private local vault, password manager, or other secure storage.
4. The final signed copy should be stored in private business records and committed only if it does not expose sensitive identity, tax, bank, or reusable signature assets.

## Official E-Sign Workflow

For counterparty contracts and any document requiring more than the owner signature, use the MLADIS-owned Dropbox Sign account instead of typed `/s/` signatures.

- Account: `garcp37@mladis.com`
- Current ready-for-signature package: `docs/business/signing/ready-for-signature-2026-06-03/`
- Current Dropbox checkpoint: both signer entries were added, but the uploaded files must be replaced with the ready-for-signature PDFs before sending.
- Piter signer: `Piter Zacari Garcia Bautista <garcp37@mladis.com>`.
- Diana signer: `Diana Sori Garcia Bautista <garciabdianas@gmail.com>`.
- Required before sending: upload the ready-for-signature PDFs, place signature/date fields, and review the final recipients and fields in Dropbox Sign.

Typed `/s/` copies may be kept as interim internal records, but the preferred final execution package is the e-sign copy plus its audit trail from the signing platform.

## Polished Packet Generation

Use `docs/business/signing/scripts/generate_polished_signing_packet.py` to regenerate the branded DOCX files from the source Markdown records. Render the DOCX files to PDF/page PNGs, scan the generated files for leftover placeholder language, and visually inspect them before using them for signatures.

## Current Signature Source Note

The NYS DOS Articles packet contains a typed organizer signature line for Piter Zacari Garcia Bautista. It is part of the official filing receipt packet, but it is not a reusable handwritten signature asset.

Use the signature text only as evidence of the filed Articles of Organization. Do not extract it into a reusable signature stamp.

## Owner-Provided Drive Signature Source

The owner provided a Google Drive source file for future signing assistance. Metadata verified on 2026-06-03:

- Drive title: `MY SIGNATURE.jpg`
- Drive file ID: `0B6-Wz8uQfNpHVTZjTWdUY281Zm8`
- MIME type: `image/jpeg`
- Modified time: `2026-06-03T07:56:07.932Z`

Do not download, duplicate, transform, or apply this signature source unless the owner explicitly authorizes signing a specific document in the current thread. The long sharing URL and the image bytes should live in the future secure vault, not in Git.

## Diana Prior Signature Evidence

Diana's prior signature appears in the archived independent contractor agreement:

- `docs/business/source-documents/contractor-agreements/Diana_Sori_Garcia_Bautista_Independent_Contractor_Agreement_Signed.pdf`
- SHA-256: `43da771c435382c9590662dc1b8e54b28c5e7865d15c25bf8d5d4ad5539fc1fa`
- Signature dates recorded in the contractor record: Piter `2025-04-07`; Diana `2025-04-10`

Use this only as source evidence of the earlier contractor arrangement. Do not crop, extract, copy, or reuse Diana's signature for a new MLADIS document unless Diana separately authorizes that exact method for that exact document.
