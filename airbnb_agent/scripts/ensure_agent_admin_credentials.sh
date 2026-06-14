#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${MLADIS_ENV_FILE:-$APP_DIR/.env}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ROTATE_PASSWORD="${MLADIS_ROTATE_AGENT_ADMIN_PASSWORD:-0}"

touch "$ENV_FILE"
chmod 600 "$ENV_FILE" 2>/dev/null || true

"$PYTHON_BIN" - "$ENV_FILE" "$ROTATE_PASSWORD" <<'PY'
from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
rotate = sys.argv[2].strip().lower() in {"1", "true", "yes", "on"}

defaults = {
    "MLADIS_AGENT_ADMIN_EMAIL": "agent-admin@mladis.com",
    "MLADIS_AGENT_ADMIN_NAME": "MLADIS Automation Agent",
    "MLADIS_AGENT_ADMIN_PHONE": "",
    "MLADIS_AGENT_ADMIN_USERNAME": "mladis-agent",
}
secret_keys = {"MLADIS_AGENT_ADMIN_PASSWORD"}
pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")

lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
values: dict[str, str] = {}
positions: dict[str, int] = {}

for index, line in enumerate(lines):
    match = pattern.match(line)
    if not match:
        continue
    key = match.group(1)
    raw = line.split("=", 1)[1].strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        raw = raw[1:-1]
    values[key] = raw
    positions[key] = index

updates: dict[str, str] = {}
for key, default in defaults.items():
    if not values.get(key):
        updates[key] = default

if rotate or not values.get("MLADIS_AGENT_ADMIN_PASSWORD"):
    updates["MLADIS_AGENT_ADMIN_PASSWORD"] = secrets.token_urlsafe(36)

if updates:
    if lines and lines[-1].strip():
        lines.append("")
    if not any("MLADIS agent admin credentials" in line for line in lines):
        lines.append("# MLADIS agent admin credentials - generated locally; do not commit or print.")
    for key, value in updates.items():
        rendered = f"{key}={value!r}" if any(ch.isspace() for ch in value) else f"{key}={value}"
        if key in positions:
            lines[positions[key]] = rendered
        else:
            lines.append(rendered)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

public_updates = sorted(key for key in updates if key not in secret_keys)
secret_updates = sorted(key for key in updates if key in secret_keys)
if public_updates:
    print("Updated agent admin env keys: " + ", ".join(public_updates))
if secret_updates:
    print("Updated agent admin secret keys: " + ", ".join(secret_updates) + " (value hidden)")
if not updates:
    print("Agent admin env keys already present; no credential changes.")
PY

cd "$APP_DIR"
"$PYTHON_BIN" manage.py provision_agent_admin
