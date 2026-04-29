# Drive Sources

This repo groups the reachable Google Drive source folders as private Git submodules.

| Source | Drive URL | GitHub repo | Submodule path | Notes |
|---|---|---|---|---|
| AIRBNB | https://drive.google.com/drive/folders/14hfw3c8s8QgYFNe9yGoiKHvUuK_LT_J5 | https://github.com/pzg8794/MLADIS-AIRBNB | `sources/AIRBNB` | Imported with files over 50 MiB listed in the source repo manifest. |
| SolOriens Apts | https://drive.google.com/drive/folders/1kc6RnaXLs3s7-7-YV8xA_4AZrEU_He6W | https://github.com/pzg8794/MLADIS-SolOriens-Apts | `sources/SolOriens-Apts` | Imported directly from Drive. |
| SolOriensV | https://drive.google.com/drive/folders/1BAwujmU1K9qFOSbU21o3606xDegy5n1i | https://github.com/pzg8794/MLADIS-SolOriensV | `sources/SolOriensV` | Initially unresolved in the Drive connector, then resolved through rclone and imported. |
| DR Apartments | https://drive.google.com/drive/folders/1-pzbXWgYmVRv5PkYH0JW9H-61PyGA0Jr | https://github.com/pzg8794/MLADIS-DR-Apartments | `sources/DR-Apartments` | The duplicate Drive URL was counted once. |

## Import Policy

- Repos are private under the `pzg8794` GitHub account.
- Google-native Docs, Sheets, and Slides are exported by rclone using `docx`, `xlsx`, `pptx`, or `svg` formats.
- `.gdoc`, `.gsheet`, and `.gslides` pointer files are not committed.
- Files larger than 50 MiB are not committed; they are listed in each source repo's `docs/large-files-manifest.md` with Drive links.
- Duplicate Drive objects with the same logical path are collapsed by rclone during import; Google Drive remains the source of truth for duplicate originals.
