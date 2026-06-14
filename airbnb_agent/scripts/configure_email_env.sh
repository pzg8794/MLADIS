#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$APP_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$APP_DIR/.env.example" ]]; then
    cp "$APP_DIR/.env.example" "$ENV_FILE"
    echo "Created $ENV_FILE from .env.example."
  else
    echo "Missing $ENV_FILE and .env.example."
    exit 1
  fi
fi

read_default() {
  local prompt="$1"
  local default="$2"
  local value
  read -r -p "$prompt [$default]: " value
  printf "%s" "${value:-$default}"
}

env_value() {
  local key="$1"
  python3 - "$ENV_FILE" "$key" <<'PY'
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
target = sys.argv[2]
for line in env_path.read_text(encoding="utf-8").splitlines():
    if "=" not in line or line.lstrip().startswith("#"):
        continue
    key, value = line.split("=", 1)
    if key == target:
        print(value)
        break
PY
}

read_secret() {
  local prompt="$1"
  local value
  read -r -s -p "$prompt: " value
  echo >&2
  printf "%s" "$value"
}

AGENT_EMAIL="$(env_value "MLADIS_AGENT_ADMIN_EMAIL")"
if [[ -z "$AGENT_EMAIL" ]]; then
  AGENT_EMAIL="agent-admin@mladis.com"
fi

STORED_AGENT_MAIL_PASSWORD="${MLADIS_AGENT_EMAIL_PASSWORD:-$(env_value "MLADIS_AGENT_EMAIL_PASSWORD")}"
STORED_GMAIL_APP_PASSWORD="${GMAIL_SMTP_APP_PASSWORD:-$(env_value "GMAIL_SMTP_APP_PASSWORD")}"
STORED_SMTP_PASSWORD="${EMAIL_HOST_PASSWORD:-$(env_value "EMAIL_HOST_PASSWORD")}"

EMAIL_HOST="$(read_default "SMTP host" "smtp.gmail.com")"
EMAIL_PORT="$(read_default "SMTP port" "587")"
EMAIL_HOST_USER="$(read_default "SMTP username/email" "$AGENT_EMAIL")"

if [[ -n "$STORED_AGENT_MAIL_PASSWORD" ]]; then
  EMAIL_HOST_PASSWORD="$STORED_AGENT_MAIL_PASSWORD"
  echo "Using stored MLADIS_AGENT_EMAIL_PASSWORD from $ENV_FILE (value hidden)."
elif [[ -n "$STORED_GMAIL_APP_PASSWORD" ]]; then
  EMAIL_HOST_PASSWORD="$STORED_GMAIL_APP_PASSWORD"
  echo "Using stored GMAIL_SMTP_APP_PASSWORD from $ENV_FILE (value hidden)."
elif [[ -n "$STORED_SMTP_PASSWORD" ]]; then
  EMAIL_HOST_PASSWORD="$STORED_SMTP_PASSWORD"
  echo "Using existing EMAIL_HOST_PASSWORD from $ENV_FILE (value hidden)."
else
  EMAIL_HOST_PASSWORD="$(read_secret "SMTP password or app password for $EMAIL_HOST_USER")"
fi

DEFAULT_FROM_EMAIL="$(read_default "Default from email" "MLADIS Bookings <$EMAIL_HOST_USER>")"
BOOKING_INQUIRY_RECIPIENTS="$(read_default "Admin recipient emails, comma-separated" "garciapiterz@gmail.com")"

if [[ -z "$EMAIL_HOST_PASSWORD" ]]; then
  echo "No SMTP password entered; not updating .env."
  exit 1
fi

export EMAIL_HOST EMAIL_PORT EMAIL_HOST_USER EMAIL_HOST_PASSWORD DEFAULT_FROM_EMAIL BOOKING_INQUIRY_RECIPIENTS

python3 - "$ENV_FILE" <<'PY'
import os
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
updates = {
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": os.environ["EMAIL_HOST"],
    "EMAIL_PORT": os.environ["EMAIL_PORT"],
    "EMAIL_HOST_USER": os.environ["EMAIL_HOST_USER"],
    "EMAIL_HOST_PASSWORD": os.environ["EMAIL_HOST_PASSWORD"],
    "EMAIL_USE_TLS": "True",
    "EMAIL_USE_SSL": "False",
    "DEFAULT_FROM_EMAIL": os.environ["DEFAULT_FROM_EMAIL"],
    "BOOKING_INQUIRY_RECIPIENTS": os.environ["BOOKING_INQUIRY_RECIPIENTS"],
}

lines = env_path.read_text(encoding="utf-8").splitlines()
seen = set()
output = []
for line in lines:
    if "=" not in line or line.lstrip().startswith("#"):
        output.append(line)
        continue
    key, _value = line.split("=", 1)
    if key in updates:
        output.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        output.append(line)

for key, value in updates.items():
    if key not in seen:
        output.append(f"{key}={value}")

env_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
PY

echo "Email SMTP settings saved to $ENV_FILE."
echo "Restart with ./run_mladis_live.command so Django loads the new email backend."
