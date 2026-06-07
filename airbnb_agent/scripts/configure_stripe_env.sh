#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python3"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$APP_DIR/.env.example" ]]; then
    cp "$APP_DIR/.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE" || true
  else
    touch "$ENV_FILE"
    chmod 600 "$ENV_FILE" || true
  fi
fi

echo "Stripe local setup for MLADIS"
echo "Paste a Stripe secret key from Stripe Dashboard > Developers > API keys."
echo "Use a test key for local testing. It should start with sk_test_ or sk_live_."
echo

read -rsp "STRIPE_SECRET_KEY: " STRIPE_SECRET_KEY_VALUE
echo

if [[ -z "${STRIPE_SECRET_KEY_VALUE// }" ]]; then
  echo "No key entered. Leaving $ENV_FILE unchanged."
  exit 1
fi

case "$STRIPE_SECRET_KEY_VALUE" in
  sk_test_*|sk_live_*) ;;
  *)
    echo "That does not look like a Stripe secret key. Expected sk_test_... or sk_live_..."
    exit 1
    ;;
esac

read -rsp "STRIPE_WEBHOOK_SECRET (optional, press Enter to skip): " STRIPE_WEBHOOK_SECRET_VALUE
echo

export STRIPE_SECRET_KEY_VALUE
export STRIPE_WEBHOOK_SECRET_VALUE
export ENV_FILE

"$PYTHON_BIN" - <<'PY'
import os
from pathlib import Path

env_file = Path(os.environ["ENV_FILE"])
updates = {
    "STRIPE_SECRET_KEY": os.environ["STRIPE_SECRET_KEY_VALUE"],
}
webhook = os.environ.get("STRIPE_WEBHOOK_SECRET_VALUE", "").strip()
if webhook:
    updates["STRIPE_WEBHOOK_SECRET"] = webhook

lines = env_file.read_text().splitlines() if env_file.exists() else []
seen = set()
next_lines = []

for line in lines:
    if not line or line.lstrip().startswith("#") or "=" not in line:
        next_lines.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in updates:
        next_lines.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        next_lines.append(line)

for key, value in updates.items():
    if key not in seen:
        next_lines.append(f"{key}={value}")

env_file.write_text("\n".join(next_lines) + "\n")
PY

chmod 600 "$ENV_FILE" || true
echo
echo "Stripe values saved to $ENV_FILE."
echo "Restart Django so settings reload the new key."
