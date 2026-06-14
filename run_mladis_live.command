#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="MLADIS Booking Platform"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/airbnb_agent"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
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
MLADIS_BUILD_FRONTEND="${MLADIS_BUILD_FRONTEND:-1}"
MLADIS_FORCE_NPM_INSTALL="${MLADIS_FORCE_NPM_INSTALL:-0}"
MLADIS_RESTART_EXISTING="${MLADIS_RESTART_EXISTING:-1}"
MLADIS_TUNNEL_MODE="${MLADIS_TUNNEL_MODE:-named}"
MLADIS_TUNNEL_NAME="${MLADIS_TUNNEL_NAME:-mladis-local}"
MLADIS_LOCAL_PUBLIC_HOSTNAME="${MLADIS_LOCAL_PUBLIC_HOSTNAME:-local.mladis.com}"
MLADIS_LOCAL_PUBLIC_ORIGIN="${MLADIS_LOCAL_PUBLIC_ORIGIN:-https://$MLADIS_LOCAL_PUBLIC_HOSTNAME}"
MLADIS_TUNNEL_STARTUP_TIMEOUT="${MLADIS_TUNNEL_STARTUP_TIMEOUT:-45}"
MLADIS_TUNNEL_LOG="${MLADIS_TUNNEL_LOG:-/private/tmp/mladis-tunnel.log}"
MLADIS_REUSE_TUNNEL="${MLADIS_REUSE_TUNNEL:-1}"
MLADIS_CLEANUP_TUNNEL="${MLADIS_CLEANUP_TUNNEL:-0}"

SERVER_PID=""
TUNNEL_PID=""
TUNNEL_TAIL_PID=""
TUNNEL_LOG="$MLADIS_TUNNEL_LOG"
PUBLIC_URL=""

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

cleanup() {
  if [[ -n "$TUNNEL_TAIL_PID" ]] && kill -0 "$TUNNEL_TAIL_PID" >/dev/null 2>&1; then
    kill "$TUNNEL_TAIL_PID" >/dev/null 2>&1 || true
    wait "$TUNNEL_TAIL_PID" >/dev/null 2>&1 || true
  fi
  if truthy "$MLADIS_CLEANUP_TUNNEL" && [[ -n "$TUNNEL_PID" ]] && kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
    echo
    echo "Stopping $APP_NAME public tunnel..."
    kill "$TUNNEL_PID" >/dev/null 2>&1 || true
    wait "$TUNNEL_PID" >/dev/null 2>&1 || true
  fi
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

install_frontend_dependencies_if_needed() {
  if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    echo "Missing frontend/package.json."
    exit 1
  fi

  if truthy "$MLADIS_FORCE_NPM_INSTALL" || [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    echo
    echo "Installing frontend dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
  else
    echo "Frontend dependencies found; skipping npm install."
  fi
}

build_frontend_if_needed() {
  if ! truthy "$MLADIS_BUILD_FRONTEND"; then
    echo
    echo "Skipping React build. Set MLADIS_BUILD_FRONTEND=1 to rebuild UI assets."
    return
  fi

  install_frontend_dependencies_if_needed
  echo
  echo "Building React UI into Django static files..."
  (cd "$FRONTEND_DIR" && npm run build:django)
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
  export SOCIAL_AUTH_CANONICAL_ORIGIN="${MLADIS_SOCIAL_AUTH_CANONICAL_ORIGIN:-}"
  export SOCIAL_AUTH_GOOGLE_ORIGIN="${SOCIAL_AUTH_GOOGLE_ORIGIN:-http://127.0.0.1:8000}"
  export SOCIAL_AUTH_GITHUB_ORIGIN="${SOCIAL_AUTH_GITHUB_ORIGIN:-http://127.0.0.1:8000}"
  case "$MLADIS_TUNNEL_MODE" in
    named)
      export ALLOWED_HOSTS="${ALLOWED_HOSTS:-localhost,127.0.0.1,$MLADIS_LOCAL_PUBLIC_HOSTNAME}"
      export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-$MLADIS_LOCAL_PUBLIC_ORIGIN}"
      export SOCIAL_AUTH_FACEBOOK_ORIGIN="${MLADIS_SOCIAL_AUTH_FACEBOOK_ORIGIN:-${SOCIAL_AUTH_FACEBOOK_ORIGIN:-$MLADIS_LOCAL_PUBLIC_ORIGIN}}"
      ;;
    quick)
      export ALLOWED_HOSTS="${ALLOWED_HOSTS:-localhost,127.0.0.1,.trycloudflare.com}"
      export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://*.trycloudflare.com}"
      ;;
    *)
      echo "Unknown MLADIS_TUNNEL_MODE=$MLADIS_TUNNEL_MODE. Use named or quick."
      exit 1
      ;;
  esac
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Creating Python virtual environment..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo
echo "Preparing $APP_NAME..."
install_requirements_if_needed
build_frontend_if_needed

echo
echo "Applying database migrations..."
python manage.py migrate --noinput

echo
echo "Syncing social login apps from .env..."
python manage.py sync_socialapps

echo
echo "Ensuring dedicated agent admin credentials and access..."
bash scripts/ensure_agent_admin_credentials.sh

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

stop_existing_processes() {
  if ! truthy "$MLADIS_RESTART_EXISTING"; then
    return
  fi

  local pids
  pids="$(lsof -tiTCP:"$MLADIS_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo
    echo "Stopping existing Django server on $LOCAL_URL..."
    kill $pids >/dev/null 2>&1 || true
    sleep 1
    pids="$(lsof -tiTCP:"$MLADIS_PORT" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      kill -9 $pids >/dev/null 2>&1 || true
    fi
  fi

  if truthy "$MLADIS_PUBLIC_TUNNEL" && [[ "$MLADIS_TUNNEL_MODE" == "quick" ]]; then
    pids="$(pgrep -f "cloudflared tunnel --url $LOCAL_URL" || true)"
    if [[ -n "$pids" ]]; then
      if truthy "$MLADIS_REUSE_TUNNEL"; then
        echo "Existing Cloudflare tunnel found; keeping it so the Facebook callback URL does not rotate."
      else
        echo "Stopping existing Cloudflare tunnel for $LOCAL_URL..."
        kill $pids >/dev/null 2>&1 || true
      fi
    fi
  fi
}

wait_for_public_url() {
  local deadline=$((SECONDS + MLADIS_TUNNEL_STARTUP_TIMEOUT))
  local url=""

  while (( SECONDS < deadline )); do
    if [[ -n "$TUNNEL_PID" ]] && ! kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
      return 1
    fi
    url="$(grep -aEo 'https://[A-Za-z0-9.-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -n 1 || true)"
    if [[ -n "$url" ]]; then
      PUBLIC_URL="$url"
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_named_tunnel() {
  local deadline=$((SECONDS + MLADIS_TUNNEL_STARTUP_TIMEOUT))

  while (( SECONDS < deadline )); do
    if [[ -n "$TUNNEL_PID" ]] && ! kill -0 "$TUNNEL_PID" >/dev/null 2>&1; then
      return 1
    fi
    if grep -aqE 'Registered tunnel connection|Connection .* registered|serving tunnel' "$TUNNEL_LOG" 2>/dev/null; then
      return 0
    fi
    sleep 1
  done

  [[ -n "$TUNNEL_PID" ]] && kill -0 "$TUNNEL_PID" >/dev/null 2>&1
}

start_named_tunnel() {
  PUBLIC_URL="$MLADIS_LOCAL_PUBLIC_ORIGIN"

  if ! cloudflared tunnel info "$MLADIS_TUNNEL_NAME" >/dev/null 2>&1; then
    echo
    echo "The stable Cloudflare tunnel '$MLADIS_TUNNEL_NAME' is not ready yet."
    echo "Complete Cloudflare login, then run these once:"
    echo "  cloudflared tunnel create $MLADIS_TUNNEL_NAME"
    echo "  cloudflared tunnel route dns $MLADIS_TUNNEL_NAME $MLADIS_LOCAL_PUBLIC_HOSTNAME"
    echo
    echo "Do not switch back to a random trycloudflare URL for normal Facebook testing."
    exit 1
  fi

  local existing_named_pids
  existing_named_pids="$(pgrep -f "cloudflared.*tunnel.*run.*$MLADIS_TUNNEL_NAME" || true)"
  local existing_bare_pids
  existing_bare_pids="$(pgrep -f "^cloudflared tunnel run$" || true)"
  existing_named_pids="$(printf "%s\n%s\n" "$existing_named_pids" "$existing_bare_pids" | awk 'NF' | sort -u)"
  if [[ -n "$existing_named_pids" ]]; then
    if truthy "$MLADIS_RESTART_EXISTING"; then
      echo
      echo "Stopping existing stable Cloudflare tunnel '$MLADIS_TUNNEL_NAME' before restart..."
      kill $existing_named_pids >/dev/null 2>&1 || true
      sleep 1
      existing_named_pids="$(printf "%s\n%s\n" "$(pgrep -f "cloudflared.*tunnel.*run.*$MLADIS_TUNNEL_NAME" || true)" "$(pgrep -f "^cloudflared tunnel run$" || true)" | awk 'NF' | sort -u)"
      if [[ -n "$existing_named_pids" ]]; then
        kill -9 $existing_named_pids >/dev/null 2>&1 || true
      fi
    else
      echo
      echo "Reusing stable Cloudflare tunnel '$MLADIS_TUNNEL_NAME'."
      echo "Public live URL: $PUBLIC_URL"
      echo "Facebook OAuth origin for this run: $SOCIAL_AUTH_FACEBOOK_ORIGIN"
      echo "Facebook callback URL does not rotate:"
      echo "$SOCIAL_AUTH_FACEBOOK_ORIGIN/oauth/facebook/login/callback/"
      return
    fi
  fi

  : > "$TUNNEL_LOG"
  echo
  echo "Starting stable Cloudflare tunnel '$MLADIS_TUNNEL_NAME'..."
  echo "Public live URL: $PUBLIC_URL"
  echo "Tunnel log: $TUNNEL_LOG"
  tail -n +1 -f "$TUNNEL_LOG" &
  TUNNEL_TAIL_PID="$!"
  cloudflared tunnel run --url "$LOCAL_URL" "$MLADIS_TUNNEL_NAME" >> "$TUNNEL_LOG" 2>&1 &
  TUNNEL_PID="$!"

  if ! wait_for_named_tunnel; then
    echo
    echo "The stable Cloudflare tunnel did not start within ${MLADIS_TUNNEL_STARTUP_TIMEOUT}s."
    echo "Check $TUNNEL_LOG. If Cloudflare is not authorized yet, run cloudflared tunnel login."
    exit 1
  fi

  echo
  echo "Facebook OAuth origin for this run: $SOCIAL_AUTH_FACEBOOK_ORIGIN"
  echo "Facebook callback URL does not rotate:"
  echo "$SOCIAL_AUTH_FACEBOOK_ORIGIN/oauth/facebook/login/callback/"
}

start_quick_tunnel() {
  if ! truthy "$MLADIS_PUBLIC_TUNNEL"; then
    return
  fi

  if ! command -v cloudflared >/dev/null 2>&1; then
    echo
    echo "Cloudflared is not available. The site will run local-only at $LOCAL_URL."
    echo "Facebook OAuth will not work from local-only mode."
    return
  fi

  local existing_tunnel_pids
  existing_tunnel_pids="$(pgrep -f "cloudflared tunnel --url $LOCAL_URL" || true)"
  if truthy "$MLADIS_REUSE_TUNNEL" && [[ -n "$existing_tunnel_pids" ]]; then
    PUBLIC_URL="$(grep -aEo 'https://[A-Za-z0-9.-]+\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | tail -n 1 || true)"
    if [[ -n "$PUBLIC_URL" ]]; then
      local facebook_origin
      facebook_origin="${MLADIS_SOCIAL_AUTH_FACEBOOK_ORIGIN:-${SOCIAL_AUTH_FACEBOOK_ORIGIN:-$PUBLIC_URL}}"
      export SOCIAL_AUTH_FACEBOOK_ORIGIN="$facebook_origin"
      echo
      echo "Reusing existing Cloudflare tunnel."
      echo "Public live URL: $PUBLIC_URL"
      echo "Facebook OAuth origin for this run: $SOCIAL_AUTH_FACEBOOK_ORIGIN"
      echo "For Facebook OAuth, the Meta callback must allow:"
      echo "$SOCIAL_AUTH_FACEBOOK_ORIGIN/oauth/facebook/login/callback/"
      return
    fi
    echo
    echo "Existing Cloudflare tunnel found, but $TUNNEL_LOG does not contain a public URL."
    echo "Starting a fresh tunnel so the launcher can recover the active callback."
  fi

  : > "$TUNNEL_LOG"
  echo
  echo "Starting public Cloudflare tunnel..."
  echo "Quick tunnel mode is an emergency fallback. It is not the normal Facebook OAuth contract."
  echo "Tunnel log: $TUNNEL_LOG"
  tail -n +1 -f "$TUNNEL_LOG" &
  TUNNEL_TAIL_PID="$!"
  cloudflared tunnel --url "$LOCAL_URL" >> "$TUNNEL_LOG" 2>&1 &
  TUNNEL_PID="$!"

  if ! wait_for_public_url; then
    echo
    echo "Cloudflare tunnel did not print a public URL within ${MLADIS_TUNNEL_STARTUP_TIMEOUT}s."
    echo "Check the cloudflared output above."
    exit 1
  fi

  local facebook_origin
  facebook_origin="${MLADIS_SOCIAL_AUTH_FACEBOOK_ORIGIN:-${SOCIAL_AUTH_FACEBOOK_ORIGIN:-$PUBLIC_URL}}"
  export SOCIAL_AUTH_FACEBOOK_ORIGIN="$facebook_origin"

  echo
  echo "Public live URL: $PUBLIC_URL"
  echo "Facebook OAuth origin for this run: $SOCIAL_AUTH_FACEBOOK_ORIGIN"
  echo "For Facebook OAuth, the Meta callback must allow:"
  echo "$SOCIAL_AUTH_FACEBOOK_ORIGIN/oauth/facebook/login/callback/"
}

start_public_tunnel_if_needed() {
  if ! truthy "$MLADIS_PUBLIC_TUNNEL"; then
    return
  fi

  if ! command -v cloudflared >/dev/null 2>&1; then
    echo
    echo "Cloudflared is not available. The site will run local-only at $LOCAL_URL."
    echo "Facebook OAuth will not work from local-only mode."
    return
  fi

  case "$MLADIS_TUNNEL_MODE" in
    named) start_named_tunnel ;;
    quick) start_quick_tunnel ;;
    *)
      echo "Unknown MLADIS_TUNNEL_MODE=$MLADIS_TUNNEL_MODE. Use named or quick."
      exit 1
      ;;
  esac
}

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

echo
echo "Starting $APP_NAME at $LOCAL_URL..."
stop_existing_processes
start_public_tunnel_if_needed

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
  echo "Local-only site: $LOCAL_URL"
  echo "Facebook OAuth requires MLADIS_PUBLIC_TUNNEL=1."
  echo "Press Ctrl-C to stop."
  start_server
  exit 0
fi

echo
if [[ -n "$PUBLIC_URL" ]]; then
  echo "Public site: $PUBLIC_URL"
  echo "Local Django origin: $LOCAL_URL"
  if truthy "$MLADIS_OPEN_BROWSER" && command -v open >/dev/null 2>&1; then
    open "$PUBLIC_URL" >/dev/null 2>&1 || true
  fi
else
  echo "Local-only site: $LOCAL_URL"
  echo "Facebook OAuth requires the public tunnel URL."
  open_local_browser
fi
echo "Press Ctrl-C to stop."

if [[ -n "$SERVER_PID" ]]; then
  wait "$SERVER_PID"
fi
