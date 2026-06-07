#!/usr/bin/env bash
set -Eeuo pipefail

LOCAL_URL="${MLADIS_LOCAL_URL:-http://127.0.0.1:8000}"
PUBLIC_URL="${MLADIS_PUBLIC_URL:-https://local.mladis.com}"
PORT="${MLADIS_PORT:-8000}"
TUNNEL_NAME="${MLADIS_TUNNEL_NAME:-mladis-local}"

failures=()
warnings=()

check_url() {
  local label="$1"
  local url="$2"
  local curl_args=(-s --max-time 8)
  if [[ "$url" == https://* ]]; then
    curl_args=(-sk --max-time 8)
  fi

  local response
  response="$(curl "${curl_args[@]}" "$url/healthz" 2>/dev/null || true)"
  if [[ "$response" == "ok" ]]; then
    echo "PASS: $label answers at $url/healthz"
  else
    failures+=("$label is not live at $url/healthz")
  fi
}

check_url "Local Django origin" "$LOCAL_URL"
check_url "Stable public tunnel" "$PUBLIC_URL"

listen_lines="$(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -z "$listen_lines" ]]; then
  failures+=("No process is listening on TCP port $PORT.")
else
  echo "$listen_lines"
  if echo "$listen_lines" | grep -Eq "TCP (\\*|0\\.0\\.0\\.0):$PORT"; then
    failures+=("Port $PORT is bound to 0.0.0.0 or *. Use 127.0.0.1 through ./run_mladis_live.command.")
  else
    echo "PASS: Port $PORT is not bound to 0.0.0.0."
  fi
fi

if pgrep -f "cloudflared.*tunnel.*run.*$TUNNEL_NAME" >/dev/null 2>&1 || pgrep -f "^cloudflared tunnel run$" >/dev/null 2>&1; then
  echo "PASS: Cloudflare named tunnel process appears to be running."
else
  failures+=("Cloudflare named tunnel '$TUNNEL_NAME' is not running.")
fi

if pgrep -f "vite|127\\.0\\.0\\.1:5173|localhost:5173" >/dev/null 2>&1; then
  warnings+=("A Vite/dev preview process may be running. Do not use it for Django/allauth testing.")
fi

if (( ${#warnings[@]} )); then
  for warning in "${warnings[@]}"; do
    echo "WARN: $warning"
  done
fi

if (( ${#failures[@]} )); then
  for failure in "${failures[@]}"; do
    echo "FAIL: $failure"
  done
  exit 1
fi

echo "Local runtime contract check passed."
