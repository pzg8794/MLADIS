#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  cat <<'EOF'
Usage: restore_runtime_state.sh <archive.tar.gz>

Restores db.sqlite3 and media/ from a runtime backup archive.
Stop gunicorn or runserver before restoring.

Environment overrides:
- MLADIS_APP_DIR
- MLADIS_RESTORE_SAFETY_DIR
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit $([[ $# -lt 1 ]] && echo 1 || echo 0)
fi

ARCHIVE_PATH="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${MLADIS_APP_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
STAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/mladis-restore.XXXXXX")"
SAFETY_DIR="${MLADIS_RESTORE_SAFETY_DIR:-$APP_DIR/runtime_restore_safety/$STAMP}"

cleanup() {
  rm -rf "$STAGE_DIR"
}

trap cleanup EXIT

if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "Missing archive: $ARCHIVE_PATH" >&2
  exit 1
fi

mkdir -p "$SAFETY_DIR"
tar -xzf "$ARCHIVE_PATH" -C "$STAGE_DIR"

PAYLOAD_DIR="$(find "$STAGE_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

if [[ -z "$PAYLOAD_DIR" || ! -f "$PAYLOAD_DIR/db.sqlite3" ]]; then
  echo "Archive does not contain a valid MLADIS runtime payload." >&2
  exit 1
fi

if [[ -f "$APP_DIR/db.sqlite3" ]]; then
  mv "$APP_DIR/db.sqlite3" "$SAFETY_DIR/db.sqlite3"
fi

if [[ -d "$APP_DIR/media" ]]; then
  mv "$APP_DIR/media" "$SAFETY_DIR/media"
fi

cp "$PAYLOAD_DIR/db.sqlite3" "$APP_DIR/db.sqlite3"

if [[ -d "$PAYLOAD_DIR/media" ]]; then
  cp -R "$PAYLOAD_DIR/media" "$APP_DIR/media"
else
  mkdir -p "$APP_DIR/media"
fi

echo "Restored runtime state into: $APP_DIR"
echo "Previous runtime files were moved to: $SAFETY_DIR"