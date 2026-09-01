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
MLADIS_RELEASE_TAG="${MLADIS_RELEASE_TAG:-}"
MLADIS_ROLLBACK_TAG="${MLADIS_ROLLBACK_TAG:-}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEPLOY_LABEL="${MLADIS_DEPLOY_LABEL:-$STAMP}"
GIT_COMMIT="$(git -C "$PROJECT_ROOT" rev-parse --verify HEAD 2>/dev/null || true)"
LOCAL_ARCHIVE="$(mktemp "${TMPDIR:-/tmp}/mladis-release.${STAMP}.XXXXXX.tar.gz")"
PACKAGE_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/mladis-package.${STAMP}.XXXXXX")"
REMOTE_ARCHIVE="$MLADIS_REMOTE_USER_HOME/mladis-release-$STAMP.tar.gz"

file_checksum() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "A SHA-256 utility is required for deployment." >&2
    return 1
  fi
}

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

cleanup() {
  rm -f "$LOCAL_ARCHIVE"
  rm -rf "$PACKAGE_ROOT"
}

trap cleanup EXIT

if [[ ! -f "$APP_DIR/manage.py" ]]; then
  echo "Could not find manage.py in $APP_DIR" >&2
  exit 1
fi

if [[ -z "$GIT_COMMIT" ]]; then
  echo "Deployment blocked: the deployment commit cannot be identified." >&2
  exit 1
fi

if [[ -n "$(git -C "$PROJECT_ROOT" status --porcelain --untracked-files=all)" ]]; then
  echo "Deployment blocked: the working tree is not clean." >&2
  git -C "$PROJECT_ROOT" status --short
  exit 1
fi

if [[ -z "$MLADIS_RELEASE_TAG" || -z "$MLADIS_ROLLBACK_TAG" ]]; then
  echo "Deployment blocked: MLADIS_RELEASE_TAG and MLADIS_ROLLBACK_TAG are required." >&2
  exit 1
fi

if [[ ! "$MLADIS_RELEASE_TAG" =~ ^[A-Za-z0-9._/-]+$ || ! "$MLADIS_ROLLBACK_TAG" =~ ^[A-Za-z0-9._/-]+$ ]]; then
  echo "Deployment blocked: release and rollback tags contain unsupported characters." >&2
  exit 1
fi

RELEASE_COMMIT="$(git -C "$PROJECT_ROOT" rev-parse --verify "$MLADIS_RELEASE_TAG^{commit}" 2>/dev/null || true)"
ROLLBACK_COMMIT="$(git -C "$PROJECT_ROOT" rev-parse --verify "$MLADIS_ROLLBACK_TAG^{commit}" 2>/dev/null || true)"
if [[ "$RELEASE_COMMIT" != "$GIT_COMMIT" ]]; then
  echo "Deployment blocked: release tag $MLADIS_RELEASE_TAG does not point to HEAD $GIT_COMMIT." >&2
  exit 1
fi
if [[ -z "$ROLLBACK_COMMIT" || "$MLADIS_ROLLBACK_TAG" == "$MLADIS_RELEASE_TAG" ]]; then
  echo "Deployment blocked: rollback target is missing or invalid." >&2
  exit 1
fi

RELEASE_MANIFEST="$(grep -Rl --exclude-dir=.git -F "Release tag: \`$MLADIS_RELEASE_TAG\`" "$PROJECT_ROOT/docs/releases" 2>/dev/null | head -n 1 || true)"
if [[ -z "$RELEASE_MANIFEST" ]]; then
  echo "Deployment blocked: no release manifest identifies $MLADIS_RELEASE_TAG." >&2
  exit 1
fi
MANIFEST_COMMIT_REF="Deployment commit: \`$MLADIS_RELEASE_TAG^{commit}\`"
if { ! grep -Fq "$GIT_COMMIT" "$RELEASE_MANIFEST" && ! grep -Fq "$MANIFEST_COMMIT_REF" "$RELEASE_MANIFEST"; } ||
  ! grep -Fq "$MLADIS_ROLLBACK_TAG" "$RELEASE_MANIFEST"; then
  echo "Deployment blocked: release manifest does not identify the commit and rollback target." >&2
  exit 1
fi

if ! git -C "$PROJECT_ROOT" ls-remote --exit-code origin "refs/tags/$MLADIS_RELEASE_TAG" >/dev/null 2>&1; then
  echo "Deployment blocked: release tag $MLADIS_RELEASE_TAG is not visible on origin." >&2
  exit 1
fi
if ! git -C "$PROJECT_ROOT" ls-remote --exit-code origin "refs/tags/$MLADIS_ROLLBACK_TAG" >/dev/null 2>&1; then
  echo "Deployment blocked: rollback tag $MLADIS_ROLLBACK_TAG is not visible on origin." >&2
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

if [[ -f "$PROJECT_ROOT/frontend/package.json" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required to build the modern MLADIS frontend before deployment." >&2
    exit 1
  fi
  echo
  echo "Building modern MLADIS frontend into Django static assets..."
  (
    cd "$PROJECT_ROOT/frontend"
    if [[ -f package-lock.json ]]; then
      npm ci
    else
      npm install
    fi
    npm run build:django
  )
  if [[ -n "$(git -C "$PROJECT_ROOT" status --porcelain --untracked-files=all)" ]]; then
    echo "Deployment blocked: frontend packaging changed the committed tree." >&2
    git -C "$PROJECT_ROOT" status --short
    exit 1
  fi
fi

echo
echo "Packaging MLADIS app for deployment..."
cp -a "$APP_DIR" "$PACKAGE_ROOT/airbnb_agent"
cat > "$PACKAGE_ROOT/airbnb_agent/.mladis-release-source-identity" <<EOF
release_tag=$MLADIS_RELEASE_TAG
commit_sha=$GIT_COMMIT
rollback_target=$MLADIS_ROLLBACK_TAG
deployment_timestamp=$STAMP
EOF
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
  -C "$PACKAGE_ROOT" \
  airbnb_agent
ARTIFACT_SHA256="$(file_checksum "$LOCAL_ARCHIVE")"

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
  --command "bash -s -- '$REMOTE_ARCHIVE' '$MLADIS_REMOTE_APP_DIR' '$MLADIS_REMOTE_SERVICE' '$DEPLOY_LABEL' '$GIT_COMMIT' '$MLADIS_RELEASE_TAG' '$MLADIS_ROLLBACK_TAG' '$ARTIFACT_SHA256' '$STAMP' '$PRUNE_FLAG' '$RELOAD_CADDY_FLAG'" <<'REMOTE'
set -Eeuo pipefail

DEPLOY_ARCHIVE="$1"
REMOTE_APP_DIR="$2"
REMOTE_SERVICE="$3"
DEPLOY_LABEL="$4"
GIT_COMMIT="$5"
RELEASE_TAG="$6"
ROLLBACK_TAG="$7"
EXPECTED_ARTIFACT_SHA256="$8"
DEPLOYMENT_TIMESTAMP="$9"
PRUNE_FLAG="${10}"
RELOAD_CADDY_FLAG="${11}"

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

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL_ARTIFACT_SHA256="$(sha256sum "$DEPLOY_ARCHIVE" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
  ACTUAL_ARTIFACT_SHA256="$(shasum -a 256 "$DEPLOY_ARCHIVE" | awk '{print $1}')"
else
  echo "Deployment blocked: the VM has no SHA-256 utility." >&2
  exit 1
fi
if [[ "$ACTUAL_ARTIFACT_SHA256" != "$EXPECTED_ARTIFACT_SHA256" ]]; then
  echo "Deployment blocked: uploaded artifact hash does not match the packaged artifact." >&2
  exit 1
fi

tar -xzf "$DEPLOY_ARCHIVE" -C "$RELEASE_DIR"

SOURCE_DIR="$RELEASE_DIR/airbnb_agent"
if [[ ! -f "$SOURCE_DIR/manage.py" ]]; then
  echo "Release archive did not contain airbnb_agent/manage.py" >&2
  exit 1
fi
IDENTITY_FILE="$SOURCE_DIR/.mladis-release-source-identity"
if [[ ! -f "$IDENTITY_FILE" ]] || ! grep -Fxq "release_tag=$RELEASE_TAG" "$IDENTITY_FILE" || ! grep -Fxq "commit_sha=$GIT_COMMIT" "$IDENTITY_FILE" || ! grep -Fxq "rollback_target=$ROLLBACK_TAG" "$IDENTITY_FILE"; then
  echo "Deployment blocked: the artifact identity does not match the release arguments." >&2
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
bash scripts/ensure_agent_admin_credentials.sh
python manage.py collectstatic --noinput
python manage.py check

if [[ -f deploy/systemd/mladis-payment-lifecycle.service && -f deploy/systemd/mladis-payment-lifecycle.timer ]]; then
  echo "Installing payment lifecycle scheduler..."
  sudo install -m 0644 deploy/systemd/mladis-payment-lifecycle.service /etc/systemd/system/
  sudo install -m 0644 deploy/systemd/mladis-payment-lifecycle.timer /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable --now mladis-payment-lifecycle.timer
fi

echo "Restarting $REMOTE_SERVICE service..."
sudo systemctl restart "$REMOTE_SERVICE"
sudo systemctl --no-pager --full status "$REMOTE_SERVICE" | head -n 12
if ! sudo systemctl is-active --quiet "$REMOTE_SERVICE"; then
  echo "Deployment failed: $REMOTE_SERVICE is not active after restart." >&2
  exit 1
fi

cat > "$REMOTE_APP_DIR/.mladis-release-identity.json" <<EOF
{
  "release": "$RELEASE_TAG",
  "commit_sha": "$GIT_COMMIT",
  "deployment_timestamp": "$DEPLOYMENT_TIMESTAMP",
  "artifact_sha256": "$EXPECTED_ARTIFACT_SHA256",
  "rollback_target": "$ROLLBACK_TAG"
}
EOF

if truthy "$RELOAD_CADDY_FLAG"; then
  echo "Reloading Caddy..."
  sudo systemctl reload caddy
fi

echo
echo "Deploy label: $DEPLOY_LABEL"
echo "Git commit: $GIT_COMMIT"
echo "Release tag: $RELEASE_TAG"
echo "Artifact SHA-256: $EXPECTED_ARTIFACT_SHA256"
echo "Rollback target: $ROLLBACK_TAG"
echo "Production URL: https://mladis.com/"
REMOTE

echo
echo "Deploy finished for https://mladis.com/"
echo "Release tag: $MLADIS_RELEASE_TAG"
echo "Commit: $GIT_COMMIT"
echo "Artifact SHA-256: $ARTIFACT_SHA256"
echo "Rollback target: $MLADIS_ROLLBACK_TAG"
if truthy "$MLADIS_DEPLOY_PRUNE"; then
  echo "Remote prune mode was enabled for this deploy."
else
  echo "Remote prune mode is off by default. Set MLADIS_DEPLOY_PRUNE=1 only when you intentionally want remote code files deleted."
fi
