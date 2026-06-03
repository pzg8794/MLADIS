# MLADIS Business Operations

Private operating documents for the legal and administrative setup behind MLADIS.

These records are meant to give the MLADIS app, agents, and future automation work a reliable business source of truth. Do not copy this directory into public frontend content, public documentation, marketing pages, or generated customer emails without reviewing privacy first.

## Current Records

- [MLADIS LLC profile](mladis-llc-profile.md): legal identity, portal references, filing facts, responsible people, and operational contact information.
- [MLADIS LLC next steps](mladis-llc-next-steps.md): post-formation checklist, deadlines, and source links.

## Data Handling Rules

- Keep EINs, SSNs, tax IDs, bank information, payment card data, and government login credentials out of this repo.
- Store production secrets in the deployment provider, `.env` files, or GitHub Actions secrets.
- Treat home addresses, legal transaction IDs, and government portal references as private business operations data.
- If these facts are later needed by the app, create explicit admin-only models or environment configuration rather than reading directly from these docs.
