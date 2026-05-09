#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: backup_runtime_state.sh [output_dir]

Creates a point-in-time archive of the Django runtime state for a pilot setup:
- db.sqlite3
- media/

Environment overrides:
- PYTHON_BIN
- MLADIS_DB_PATH
- MLADIS_MEDIA_DIR
- MLADIS_BACKUP_DIR
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DB_PATH="${MLADIS_DB_PATH:-$APP_DIR/db.sqlite3}"
MEDIA_DIR="${MLADIS_MEDIA_DIR:-$APP_DIR/media}"
BACKUP_DIR="${1:-${MLADIS_BACKUP_DIR:-$APP_DIR/runtime_backups}}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/mladis-backup.XXXXXX")"
PAYLOAD_DIR="$WORK_DIR/mladis-runtime-$STAMP"
ARCHIVE_PATH="$BACKUP_DIR/mladis-runtime-$STAMP.tar.gz"

cleanup() {
  rm -rf "$WORK_DIR"
}

trap cleanup EXIT

if [[ ! -f "$DB_PATH" ]]; then
  echo "Missing SQLite database: $DB_PATH" >&2
  exit 1
fi

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python executable not found: $PYTHON_BIN" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR" "$PAYLOAD_DIR"

"$PYTHON_BIN" - "$DB_PATH" "$PAYLOAD_DIR/db.sqlite3" <<'PY'
import pathlib
import sqlite3
import sys

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])

source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
target_connection = sqlite3.connect(target)
try:
    with target_connection:
        source_connection.backup(target_connection)
finally:
    source_connection.close()
    target_connection.close()
PY

if [[ -d "$MEDIA_DIR" ]]; then
  cp -R "$MEDIA_DIR" "$PAYLOAD_DIR/media"
else
  mkdir -p "$PAYLOAD_DIR/media"
fi

cat > "$PAYLOAD_DIR/manifest.txt" <<EOF
created_at_utc=$STAMP
app_dir=$APP_DIR
db_path=$DB_PATH
media_dir=$MEDIA_DIR
git_commit=$(git -C "$APP_DIR" rev-parse HEAD 2>/dev/null || echo unknown)
EOF

tar -C "$WORK_DIR" -czf "$ARCHIVE_PATH" "$(basename "$PAYLOAD_DIR")"

echo "Created runtime backup: $ARCHIVE_PATH"