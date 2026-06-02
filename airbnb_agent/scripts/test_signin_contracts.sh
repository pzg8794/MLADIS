#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${APP_DIR}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
fi

export SECRET_KEY="${SECRET_KEY:-signin-contract-ci-secret}"
export DEBUG="${DEBUG:-True}"
export DATABASE_URL="${DATABASE_URL:-}"
export DATABASE_NAME="${DATABASE_NAME:-}"
export DATABASE_USER="${DATABASE_USER:-}"
export DATABASE_PASSWORD="${DATABASE_PASSWORD:-}"
export DATABASE_HOST="${DATABASE_HOST:-}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-localhost,127.0.0.1,testserver,.trycloudflare.com}"
export ACCOUNT_DEFAULT_HTTP_PROTOCOL="${ACCOUNT_DEFAULT_HTTP_PROTOCOL:-http}"
export SOCIAL_AUTH_CANONICAL_ORIGIN="${SOCIAL_AUTH_CANONICAL_ORIGIN:-}"
export SOCIAL_AUTH_GOOGLE_ORIGIN="${SOCIAL_AUTH_GOOGLE_ORIGIN:-http://127.0.0.1:8000}"
export SOCIAL_AUTH_GITHUB_ORIGIN="${SOCIAL_AUTH_GITHUB_ORIGIN:-http://127.0.0.1:8000}"
export SOCIAL_AUTH_FACEBOOK_ORIGIN="${SOCIAL_AUTH_FACEBOOK_ORIGIN:-https://facebook-contract.trycloudflare.com}"
export SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS="${SOCIAL_AUTH_HIDDEN_UNCONFIGURED_PROVIDERS:-microsoft}"
export SITE_DOMAIN="${SITE_DOMAIN:-127.0.0.1:8000}"
export SITE_NAME="${SITE_NAME:-MLADIS Local}"

"${PYTHON_BIN}" manage.py check
"${PYTHON_BIN}" manage.py makemigrations --check --dry-run
"${PYTHON_BIN}" manage.py test bookings.test_signin_contracts.SignInContractTests

bash -n ../run_mladis_live.command
test ! -e ../preview_mladis_ui.command
grep -q 'MLADIS_PUBLIC_TUNNEL="${MLADIS_PUBLIC_TUNNEL:-1}"' ../run_mladis_live.command
grep -q 'MLADIS_BUILD_FRONTEND="${MLADIS_BUILD_FRONTEND:-1}"' ../run_mladis_live.command
grep -q 'MLADIS_RESTART_EXISTING="${MLADIS_RESTART_EXISTING:-1}"' ../run_mladis_live.command
grep -q 'MLADIS_TUNNEL_STARTUP_TIMEOUT="${MLADIS_TUNNEL_STARTUP_TIMEOUT:-45}"' ../run_mladis_live.command
grep -q 'MLADIS_TUNNEL_LOG="${MLADIS_TUNNEL_LOG:-/private/tmp/mladis-tunnel.log}"' ../run_mladis_live.command
grep -q 'MLADIS_STARTUP_TIMEOUT="${MLADIS_STARTUP_TIMEOUT:-60}"' ../run_mladis_live.command
grep -q 'MLADIS_COLLECTSTATIC="${MLADIS_COLLECTSTATIC:-0}"' ../run_mladis_live.command
grep -q 'install_requirements_if_needed' ../run_mladis_live.command
grep -q 'start_public_tunnel_if_needed' ../run_mladis_live.command
grep -q 'grep -aEo' ../run_mladis_live.command
grep -q 'npm run build:django' ../run_mladis_live.command
grep -q 'export SOCIAL_AUTH_FACEBOOK_ORIGIN="$facebook_origin"' ../run_mladis_live.command
grep -q 'Use the public URL printed below for browser testing when Facebook login matters.' ../run_mladis_live.command
grep -q 'Tunnel log: $TUNNEL_LOG' ../run_mladis_live.command
