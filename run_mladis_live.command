#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="MLADIS Booking Platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/airbnb_agent"
VENV_DIR="$APP_DIR/.venv"

PYTHON_BIN="${PYTHON_BIN:-python3}"
MLADIS_HOST="${MLADIS_HOST:-127.0.0.1}"
MLADIS_PORT="${MLADIS_PORT:-8000}"
MLADIS_PUBLIC_TUNNEL="${MLADIS_PUBLIC_TUNNEL:-1}"
MLADIS_OPEN_BROWSER="${MLADIS_OPEN_BROWSER:-1}"
MLADIS_SERVER="${MLADIS_SERVER:-runserver}"
MLADIS_CHECK_ONLY="${MLADIS_CHECK_ONLY:-0}"
MLADIS_STARTUP_TIMEOUT="${MLADIS_STARTUP_TIMEOUT:-60}"
MLADIS_FORCE_INSTALL="${MLADIS_FORCE_INSTALL:-0}"
MLADIS_COLLECTSTATIC="${MLADIS_COLLECTSTATIC:-0}"

SERVER_PID=""

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    echo
    echo "Stopping $APP_NAME server..."
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}

on_error() {
  echo
  echo "Something stopped the launcher before the site could stay live."
  echo "Check the lines above for the exact error."
}

file_checksum() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    cksum "$1" | awk '{print $1}'
  fi
}

install_requirements_if_needed() {
  local stamp_file="$VENV_DIR/.requirements.sha256"
  local current_hash

  current_hash="$(file_checksum requirements.txt)"
  if ! truthy "$MLADIS_FORCE_INSTALL" && [[ -f "$stamp_file" ]] && [[ "$(cat "$stamp_file")" == "$current_hash" ]]; then
    echo "Python requirements unchanged; skipping install. Set MLADIS_FORCE_INSTALL=1 to force it."
    return
  fi

  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  printf "%s\n" "$current_hash" > "$stamp_file"
}

trap cleanup EXIT INT TERM
trap on_error ERR

cd "$APP_DIR"

if [[ ! -f manage.py ]]; then
  echo "Could not find manage.py in $APP_DIR"
  exit 1
fi

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "Created airbnb_agent/.env from .env.example. Add real secrets there when needed."
  else
    echo "Missing airbnb_agent/.env and .env.example."
    exit 1
  fi
fi

if truthy "$MLADIS_PUBLIC_TUNNEL"; then
  export USE_X_FORWARDED_PROTO="${USE_X_FORWARDED_PROTO:-True}"
  export ALLOWED_HOSTS="${ALLOWED_HOSTS:-localhost,127.0.0.1,.trycloudflare.com}"
  export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://*.trycloudflare.com}"
  export SOCIAL_AUTH_CANONICAL_ORIGIN="${MLADIS_SOCIAL_AUTH_CANONICAL_ORIGIN:-}"
  export SOCIAL_AUTH_GOOGLE_ORIGIN="${SOCIAL_AUTH_GOOGLE_ORIGIN:-http://127.0.0.1:8000}"
  export SOCIAL_AUTH_GITHUB_ORIGIN="${SOCIAL_AUTH_GITHUB_ORIGIN:-http://127.0.0.1:8000}"
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Creating Python virtual environment..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo
echo "Preparing $APP_NAME..."
install_requirements_if_needed

echo
echo "Applying database migrations..."
python manage.py migrate --noinput

echo
echo "Syncing social login apps from .env..."
python manage.py sync_socialapps

echo
echo "Provisioning optional agent admin from .env..."
python manage.py provision_agent_admin

echo
echo "Checking Django configuration..."
python manage.py check

if truthy "$MLADIS_COLLECTSTATIC"; then
  echo
  echo "Collecting static files..."
  python manage.py collectstatic --noinput --verbosity 0
else
  echo
  echo "Skipping collectstatic for local startup. Set MLADIS_COLLECTSTATIC=1 to collect static files."
fi

if truthy "$MLADIS_CHECK_ONLY"; then
  echo
  echo "$APP_NAME setup check completed."
  exit 0
fi

LOCAL_URL="http://$MLADIS_HOST:$MLADIS_PORT"
HEALTH_URL="$LOCAL_URL/healthz"

is_server_live() {
  python - "$HEALTH_URL" <<'PY'
import sys
from urllib.request import urlopen

try:
    with urlopen(sys.argv[1], timeout=2) as response:
        raise SystemExit(0 if response.status < 500 else 1)
except Exception:
    raise SystemExit(1)
PY
}

wait_for_server() {
  local deadline=$((SECONDS + MLADIS_STARTUP_TIMEOUT))
  while (( SECONDS < deadline )); do
    if is_server_live; then
      return 0
    fi
    if [[ -n "$SERVER_PID" ]] && ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
      return 1
    fi
    sleep 1
  done
  return 1
}

start_server() {
  case "$MLADIS_SERVER" in
    gunicorn)
      gunicorn config.wsgi:application --bind "$MLADIS_HOST:$MLADIS_PORT"
      ;;
    runserver)
      python manage.py runserver "$MLADIS_HOST:$MLADIS_PORT"
      ;;
    *)
      echo "Unknown MLADIS_SERVER=$MLADIS_SERVER. Use runserver or gunicorn."
      exit 1
      ;;
  esac
}

open_local_browser() {
  if truthy "$MLADIS_OPEN_BROWSER" && command -v open >/dev/null 2>&1; then
    open "$LOCAL_URL" >/dev/null 2>&1 || true
  fi
}

if is_server_live; then
  echo
  echo "$APP_NAME is already running at $LOCAL_URL"
else
  echo
  echo "Starting $APP_NAME at $LOCAL_URL..."
  if truthy "$MLADIS_PUBLIC_TUNNEL"; then
    start_server &
    SERVER_PID="$!"
    if ! wait_for_server; then
      echo "The Django server did not answer at $HEALTH_URL within ${MLADIS_STARTUP_TIMEOUT}s."
      exit 1
    fi
  else
    open_local_browser
    echo
    echo "Local site: $LOCAL_URL"
    echo "Press Ctrl-C to stop."
    start_server
    exit 0
  fi
fi

open_local_browser

echo
echo "Local site: $LOCAL_URL"

if truthy "$MLADIS_PUBLIC_TUNNEL" && command -v cloudflared >/dev/null 2>&1; then
  echo
  echo "Starting public Cloudflare tunnel..."
  echo "Look for the https://...trycloudflare.com URL below. Press Ctrl-C to stop."
  cloudflared tunnel --url "$LOCAL_URL" 2>&1 | while IFS= read -r line; do
    echo "$line"
    if [[ "$line" =~ https://[A-Za-z0-9.-]+\.trycloudflare\.com ]]; then
      PUBLIC_URL="${BASH_REMATCH[0]}"
      echo
      echo "Public live URL: $PUBLIC_URL"
      echo "For Facebook OAuth, add this callback in Meta while the tunnel is running:"
      echo "$PUBLIC_URL/oauth/facebook/login/callback/"
      echo "Then set SOCIAL_AUTH_FACEBOOK_ORIGIN=$PUBLIC_URL in airbnb_agent/.env and restart this launcher."
      if truthy "$MLADIS_OPEN_BROWSER" && command -v open >/dev/null 2>&1; then
        open "$PUBLIC_URL" >/dev/null 2>&1 || true
      fi
    fi
  done
else
  echo
  echo "Cloudflared is not available or public tunnel is disabled."
  echo "The site is live locally at $LOCAL_URL"
  echo "Press Ctrl-C to stop if this script started the server."
  if [[ -n "$SERVER_PID" ]]; then
    wait "$SERVER_PID"
  fi
fi
