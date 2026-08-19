# Drive Sources

This repo groups the reachable Google Drive source folders as restricted Git
submodules mounted beneath a public engineering parent. The intended design is
public `pzg8794/MLADIS` plus source repositories whose contents remain
restricted to authorized collaborators.

| Source | Drive URL | GitHub repo | Submodule path | GitHub visibility | Data classification |
|---|---|---|---|---|
| AIRBNB | https://drive.google.com/drive/folders/14hfw3c8s8QgYFNe9yGoiKHvUuK_LT_J5 | https://github.com/pzg8794/MLADIS-AIRBNB | `sources/AIRBNB` | restricted | private source and business material |
| SolOriens Apts | https://drive.google.com/drive/folders/1kc6RnaXLs3s7-7-YV8xA_4AZrEU_He6W | https://github.com/pzg8794/MLADIS-SolOriens-Apts | `sources/SolOriens-Apts` | restricted | private property material |
| SolOriensV | https://drive.google.com/drive/folders/1BAwujmU1K9qFOSbU21o3606xDegy5n1i | https://github.com/pzg8794/MLADIS-SolOriensV | `sources/SolOriensV` | restricted | private property material |
| DR Apartments | https://drive.google.com/drive/folders/1-pzbXWgYmVRv5PkYH0JW9H-61PyGA0Jr | https://github.com/pzg8794/MLADIS-DR-Apartments | `sources/DR-Apartments` | restricted | private property material |

## Import Policy

- Source repositories listed above MUST have GitHub visibility `private`.
- `restricted` is the data classification, not a GitHub visibility value. The
  public MLADIS parent may remain public while restricted source submodules are
  private.
- Google-native Docs, Sheets, and Slides are exported by rclone using `docx`, `xlsx`, `pptx`, or `svg` formats.
- `.gdoc`, `.gsheet`, and `.gslides` pointer files are not committed.
- Files larger than 50 MiB are not committed; they are listed in each source repo's `docs/large-files-manifest.md` with Drive links.
- Duplicate Drive objects with the same logical path are collapsed by rclone during import; Google Drive remains the source of truth for duplicate originals.

Public/default CI and application deployments MUST NOT require restricted
source submodules. Jobs that genuinely need a restricted source repository
must use a dedicated read-only GitHub App or deploy credential scoped only to
the required repository, and must fail closed when that access is unavailable.
Do not use a broad personal PAT for deployment.

## Visibility Drift Check

The declared visibility above is an architectural intent, not proof of current
GitHub account configuration. Before cloning, CI setup, or deployment, an
authorized owner must verify each source repository's live GitHub visibility
and collaborator access. A mismatch is configuration drift to investigate; it
is not a reason to expose restricted source material in the public parent.

The check must record:

- repository name and current visibility;
- intended visibility and data classification;
- date and account that performed the check;
- whether local/CI/deployment credentials can initialize the submodule;
- remediation owner for any mismatch.

Do not place credentials, tokens, raw source records, or private Drive content
in this repository. Private Git submodules are versioned source boundaries,
not substitutes for the runtime Drive Object Lake.

See `docs/data-store/pyramid-data-lifecycle.md` for the privacy/Pyramid model.
