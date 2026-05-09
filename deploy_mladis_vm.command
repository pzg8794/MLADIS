#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
APP_DIR="$PROJECT_ROOT/airbnb_agent"

MLADIS_GCP_PROJECT_ID="${MLADIS_GCP_PROJECT_ID:-mledis}"
MLADIS_GCE_INSTANCE="${MLADIS_GCE_INSTANCE:-mladis-test-1}"
MLADIS_GCE_ZONE="${MLADIS_GCE_ZONE:-us-central1-a}"
MLADIS_REMOTE_APP_DIR="${MLADIS_REMOTE_APP_DIR:-/home/pitergarcia/airbnb_agent}"
MLADIS_REMOTE_SERVICE="${MLADIS_REMOTE_SERVICE:-mladis}"
MLADIS_REMOTE_USER_HOME="${MLADIS_REMOTE_USER_HOME:-/home/pitergarcia}"
MLADIS_DEPLOY_PRUNE="${MLADIS_DEPLOY_PRUNE:-0}"
MLADIS_RELOAD_CADDY="${MLADIS_RELOAD_CADDY:-0}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEPLOY_LABEL="${MLADIS_DEPLOY_LABEL:-$STAMP}"
GIT_COMMIT="$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo working-tree)"
LOCAL_ARCHIVE="$(mktemp "${TMPDIR:-/tmp}/mladis-release.${STAMP}.XXXXXX.tar.gz")"
REMOTE_ARCHIVE="$MLADIS_REMOTE_USER_HOME/mladis-release-$STAMP.tar.gz"

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

cleanup() {
  rm -f "$LOCAL_ARCHIVE"
}

trap cleanup EXIT

if [[ ! -f "$APP_DIR/manage.py" ]]; then
  echo "Could not find manage.py in $APP_DIR" >&2
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required for deployment." >&2
  exit 1
fi

if ! command -v tar >/dev/null 2>&1; then
  echo "tar is required for deployment." >&2
  exit 1
fi

echo
echo "Packaging MLADIS app for deployment..."
tar \
  --exclude='airbnb_agent/.env' \
  --exclude='airbnb_agent/.venv' \
  --exclude='airbnb_agent/db.sqlite3' \
  --exclude='airbnb_agent/media' \
  --exclude='airbnb_agent/staticfiles' \
  --exclude='airbnb_agent/runtime_backups' \
  --exclude='airbnb_agent/runtime_restore_safety' \
  --exclude='airbnb_agent/.pytest_cache' \
  --exclude='airbnb_agent/.mypy_cache' \
  --exclude='airbnb_agent/__pycache__' \
  --exclude='airbnb_agent/*/__pycache__' \
  -czf "$LOCAL_ARCHIVE" \
  -C "$PROJECT_ROOT" \
  airbnb_agent

echo
echo "Uploading release archive to $MLADIS_GCE_INSTANCE..."
gcloud compute scp \
  --project "$MLADIS_GCP_PROJECT_ID" \
  --zone "$MLADIS_GCE_ZONE" \
  "$LOCAL_ARCHIVE" \
  "$MLADIS_GCE_INSTANCE:$REMOTE_ARCHIVE"

PRUNE_FLAG=0
RELOAD_CADDY_FLAG=0
if truthy "$MLADIS_DEPLOY_PRUNE"; then
  PRUNE_FLAG=1
fi
if truthy "$MLADIS_RELOAD_CADDY"; then
  RELOAD_CADDY_FLAG=1
fi

echo
echo "Deploying on VM $MLADIS_GCE_INSTANCE..."
gcloud compute ssh \
  "$MLADIS_GCE_INSTANCE" \
  --project "$MLADIS_GCP_PROJECT_ID" \
  --zone "$MLADIS_GCE_ZONE" \
  --command "bash -s -- '$REMOTE_ARCHIVE' '$MLADIS_REMOTE_APP_DIR' '$MLADIS_REMOTE_SERVICE' '$DEPLOY_LABEL' '$GIT_COMMIT' '$PRUNE_FLAG' '$RELOAD_CADDY_FLAG'" <<'REMOTE'
set -Eeuo pipefail

DEPLOY_ARCHIVE="$1"
REMOTE_APP_DIR="$2"
REMOTE_SERVICE="$3"
DEPLOY_LABEL="$4"
GIT_COMMIT="$5"
PRUNE_FLAG="$6"
RELOAD_CADDY_FLAG="$7"

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

RELEASE_DIR="$(mktemp -d /tmp/mladis-release.XXXXXX)"

cleanup() {
  rm -rf "$RELEASE_DIR"
  rm -f "$DEPLOY_ARCHIVE"
}

trap cleanup EXIT

if [[ ! -d "$REMOTE_APP_DIR" ]]; then
  echo "Remote app directory does not exist: $REMOTE_APP_DIR" >&2
  exit 1
fi

tar -xzf "$DEPLOY_ARCHIVE" -C "$RELEASE_DIR"

SOURCE_DIR="$RELEASE_DIR/airbnb_agent"
if [[ ! -f "$SOURCE_DIR/manage.py" ]]; then
  echo "Release archive did not contain airbnb_agent/manage.py" >&2
  exit 1
fi

cd "$REMOTE_APP_DIR"

if [[ -x scripts/backup_runtime_state.sh ]]; then
  echo "Creating runtime backup before deploy..."
  bash scripts/backup_runtime_state.sh
fi

echo "Syncing code into $REMOTE_APP_DIR..."
if command -v rsync >/dev/null 2>&1; then
  RSYNC_ARGS=(-a)
  if truthy "$PRUNE_FLAG"; then
    RSYNC_ARGS+=(--delete)
  fi
  RSYNC_ARGS+=(
    --exclude=.env
    --exclude=.venv
    --exclude=db.sqlite3
    --exclude=media/
    --exclude=staticfiles/
    --exclude=runtime_backups/
    --exclude=runtime_restore_safety/
  )
  rsync "${RSYNC_ARGS[@]}" "$SOURCE_DIR/" "$REMOTE_APP_DIR/"
else
  if truthy "$PRUNE_FLAG"; then
    echo "MLADIS_DEPLOY_PRUNE=1 requires rsync on the VM." >&2
    exit 1
  fi
  tar -C "$SOURCE_DIR" -cf - . | tar -C "$REMOTE_APP_DIR" -xf -
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating remote virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Running Django deploy steps..."
python manage.py migrate --noinput
python manage.py sync_socialapps
python manage.py provision_agent_admin
python manage.py collectstatic --noinput
python manage.py check

echo "Restarting $REMOTE_SERVICE service..."
sudo systemctl restart "$REMOTE_SERVICE"
sudo systemctl --no-pager --full status "$REMOTE_SERVICE" | head -n 12

if truthy "$RELOAD_CADDY_FLAG"; then
  echo "Reloading Caddy..."
  sudo systemctl reload caddy
fi

echo
echo "Deploy label: $DEPLOY_LABEL"
echo "Git commit: $GIT_COMMIT"
echo "Production URL: https://mladis.com/"
REMOTE

echo
echo "Deploy finished for https://mladis.com/"
if truthy "$MLADIS_DEPLOY_PRUNE"; then
  echo "Remote prune mode was enabled for this deploy."
else
  echo "Remote prune mode is off by default. Set MLADIS_DEPLOY_PRUNE=1 only when you intentionally want remote code files deleted."
fi
