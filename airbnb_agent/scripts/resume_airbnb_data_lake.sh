#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  printf 'Usage: %s /private/path/airbnb-export.json[.l]\n' "$0" >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
AIRBNB_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$AIRBNB_ROOT"

PYTHON_BIN="$AIRBNB_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

exec "$PYTHON_BIN" manage.py collect_airbnb_data_lake \
  --input "$1" \
  --new-only \
  "${@:2}"
