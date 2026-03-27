#!/usr/bin/env bash
set -euo pipefail

UPLOAD=0
DRY_RUN=0
ENCRYPT_CONFIG=0
LOCAL_KEEP="${LOCAL_KEEP:-7}"
REMOTE_KEEP="${REMOTE_KEEP:-7}"

for arg in "$@"; do
  case "$arg" in
    --upload) UPLOAD=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --encrypt-config) ENCRYPT_CONFIG=1 ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${OPENCLAW_WORKSPACE_DIR:-}" ]]; then
  WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR}"
else
  WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
fi
HOME_DIR="${HOME}"
STATE_DIR="${HOME_DIR}/.openclaw"
CONFIG_FILE="${STATE_DIR}/openclaw.json"
EXTENSIONS_DIR="${STATE_DIR}/extensions"
BACKUP_ROOT="${WORKSPACE_DIR}/backups/openclaw"
TS="$(date +%F-%H%M%S)"
RUN_DIR="${BACKUP_ROOT}/${TS}"
LATEST_LINK="${BACKUP_ROOT}/latest"

# === Rotation Functions (defined before use) ===

rotate_local_backups() {
  local root="$1"
  local keep="$2"
  [[ -d "$root" ]] || return 0
  mapfile -t dirs < <(find "$root" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
  local count=${#dirs[@]}
  if (( count <= keep )); then
    return 0
  fi
  local remove_count=$((count - keep))
  for d in "${dirs[@]:0:remove_count}"; do
    rm -rf "$root/$d"
  done
}

webdav_list_dirs() {
  local url="$1"
  curl --silent --show-error -u "${WEBDAV_USER}:${WEBDAV_PASS}" -X PROPFIND -H 'Depth: 1' "$url" || return 1
}

webdav_delete_dir() {
  local url="$1"
  if [[ ${DRY_RUN} -eq 1 ]]; then
    log "DRY RUN delete remote dir: ${url}"
    return 0
  fi
  curl --silent --show-error -u "${WEBDAV_USER}:${WEBDAV_PASS}" -X DELETE "$url" >/dev/null
}

rotate_remote_backups() {
  local root="$1"
  local keep="$2"
  local xml
  xml=$(webdav_list_dirs "$root") || return 0
  mapfile -t names < <(printf '%s' "$xml" | grep -oP '(?<=<d:href>)[^<]+' | sed 's#/$##' | awk -F'/' 'NF{print $NF}' | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{6}$' | sort -u)
  local count=${#names[@]}
  if (( count <= keep )); then
    return 0
  fi
  local remove_count=$((count - keep))
  for d in "${names[@]:0:remove_count}"; do
    webdav_delete_dir "$root/$d"
  done
}

# === End Rotation Functions ===

mkdir -p "${RUN_DIR}"

WORKSPACE_ARCHIVE="${RUN_DIR}/workspace.tar.gz"
EXTENSIONS_ARCHIVE="${RUN_DIR}/extensions.tar.gz"
CONFIG_COPY="${RUN_DIR}/openclaw.json"
CONFIG_ENC="${RUN_DIR}/openclaw.json.enc"
RESTORE_NOTE="${RUN_DIR}/RESTORE-NOTES.txt"
MANIFEST="${RUN_DIR}/manifest.txt"
NOTIFY_SUMMARY="${RUN_DIR}/notify.txt"
NOTIFY_SCRIPT="${WORKSPACE_DIR}/skills/openclaw-webdav-backup/scripts/openclaw-backup-notify.impl.sh"
FAILED_STAGE="initializing"

log() { printf '[backup] %s\n' "$*"; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }

send_notify() {
  local status="$1"
  [[ -x "$NOTIFY_SCRIPT" || -f "$NOTIFY_SCRIPT" ]] || return 0
  /usr/bin/bash "$NOTIFY_SCRIPT" "$status" "$NOTIFY_SUMMARY" || true
}

write_success_summary() {
  cat > "$NOTIFY_SUMMARY" <<EOF
✅ OpenClaw backup succeeded
Time: ${TS}
Local dir: ${RUN_DIR}
Encrypted config: $([[ ${ENCRYPT_CONFIG} -eq 1 ]] && echo yes || echo no)
WebDAV upload: $([[ ${UPLOAD} -eq 1 ]] && echo yes || echo no)
Retention: local ${LOCAL_KEEP}, remote ${REMOTE_KEEP}
EOF
}

write_failure_summary() {
  cat > "$NOTIFY_SUMMARY" <<EOF
❌ OpenClaw backup failed
Time: ${TS}
Stage: ${FAILED_STAGE}
Local dir: ${RUN_DIR}
Encrypted config: $([[ ${ENCRYPT_CONFIG} -eq 1 ]] && echo yes || echo no)
WebDAV upload: $([[ ${UPLOAD} -eq 1 ]] && echo yes || echo no)
Hint: check cron log or rerun manually for details
EOF
}

on_error() {
  write_failure_summary
  send_notify failure
}

trap on_error ERR

resolve_encrypt_pass() {
  if [[ -n "${BACKUP_ENCRYPT_PASS:-}" ]]; then
    return 0
  fi
  local secret_file="${WORKSPACE_DIR}/.env.backup.secret"
  if [[ -f "${secret_file}" ]]; then
    # shellcheck disable=SC1090
    source "${secret_file}"
  fi
  if [[ -n "${BACKUP_ENCRYPT_PASS:-}" ]]; then
    export BACKUP_ENCRYPT_PASS
    return 0
  fi
  if [[ -t 0 ]]; then
    read -r -s -p 'Enter backup encryption password: ' BACKUP_ENCRYPT_PASS
    echo
    [[ -n "${BACKUP_ENCRYPT_PASS}" ]] || { echo "Empty encryption password" >&2; exit 1; }
    export BACKUP_ENCRYPT_PASS
    return 0
  fi
  echo "Missing BACKUP_ENCRYPT_PASS. Set env var, provide .env.backup.secret, or run interactively." >&2
  exit 1
}

need_cmd tar
need_cmd curl

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "Config file not found: ${CONFIG_FILE}" >&2
  exit 1
fi

FAILED_STAGE="creating workspace archive"
log "Creating workspace archive"
tar --exclude='node_modules' --exclude='.git' --exclude='backups/openclaw' --exclude='.env.backup' --exclude='.env.backup.secret' -czf "${WORKSPACE_ARCHIVE}" -C "${WORKSPACE_DIR}" .

if [[ -d "${EXTENSIONS_DIR}" ]]; then
  FAILED_STAGE="creating extensions archive"
log "Creating extensions archive"
  tar -czf "${EXTENSIONS_ARCHIVE}" -C "${STATE_DIR}" extensions
fi

FAILED_STAGE="copying config"
log "Copying config"
cp "${CONFIG_FILE}" "${CONFIG_COPY}"

if [[ ${ENCRYPT_CONFIG} -eq 1 ]]; then
  ENV_FILE="${WORKSPACE_DIR}/.env.backup"
  [[ -f "${ENV_FILE}" ]] || { echo "Missing ${ENV_FILE}" >&2; exit 1; }
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  resolve_encrypt_pass
  : "${BACKUP_ENCRYPT_PASS:?BACKUP_ENCRYPT_PASS is required when --encrypt-config is used}"
  need_cmd openssl
  FAILED_STAGE="encrypting config"
log "Encrypting config copy"
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "${CONFIG_COPY}" -out "${CONFIG_ENC}" -pass env:BACKUP_ENCRYPT_PASS >/dev/null 2>&1
  rm -f "${CONFIG_COPY}"
fi

cat > "${RESTORE_NOTE}" <<NOTE
OpenClaw restore notes
Generated at: ${TS}
Security note: openclaw.json may contain secrets/tokens/API keys.
If encrypted backup is used, decrypt openclaw.json.enc before restore.
NOTE

{
  echo "timestamp=${TS}"
  echo "workspace_archive=$(basename "${WORKSPACE_ARCHIVE}")"
  [[ -f "${EXTENSIONS_ARCHIVE}" ]] && echo "extensions_archive=$(basename "${EXTENSIONS_ARCHIVE}")"
  if [[ -f "${CONFIG_ENC}" ]]; then
    echo "config_encrypted=$(basename "${CONFIG_ENC}")"
  else
    echo "config_copy=$(basename "${CONFIG_COPY}")"
  fi
} > "${MANIFEST}"

ln -sfn "${RUN_DIR}" "${LATEST_LINK}"
log "Backup set created at: ${RUN_DIR}"
FAILED_STAGE="applying local retention"
log "Applying local retention: keep ${LOCAL_KEEP}"
rotate_local_backups "${BACKUP_ROOT}" "${LOCAL_KEEP}"

if [[ ${UPLOAD} -eq 1 ]]; then
  ENV_FILE="${WORKSPACE_DIR}/.env.backup"
  [[ -f "${ENV_FILE}" ]] || { echo "Missing upload env file: ${ENV_FILE}" >&2; exit 1; }
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  : "${WEBDAV_URL:?WEBDAV_URL is required}"
  : "${WEBDAV_USER:?WEBDAV_USER is required}"
  : "${WEBDAV_PASS:?WEBDAV_PASS is required}"

  mkcol_if_needed() {
    local url="$1"
    if [[ ${DRY_RUN} -eq 1 ]]; then
      log "DRY RUN MKCOL ${url}"
      return 0
    fi
    local code
    code=$(curl --silent --show-error -u "${WEBDAV_USER}:${WEBDAV_PASS}" -o /dev/null -w '%{http_code}' -X MKCOL "$url")
    case "$code" in
      201|301|405) return 0 ;;
      *) echo "MKCOL failed for $url (HTTP $code)" >&2; return 1 ;;
    esac
  }

  upload_file() {
    local local_file="$1"
    local remote_url="$2"
    if [[ ${DRY_RUN} -eq 1 ]]; then
      log "DRY RUN upload: ${local_file} -> ${remote_url}"
      return 0
    fi
    curl --fail --silent --show-error -u "${WEBDAV_USER}:${WEBDAV_PASS}" -T "${local_file}" "$remote_url" >/dev/null
  }

  REMOTE_ROOT="${WEBDAV_URL%/}/openclaw-backup"
  REMOTE_RUN="${REMOTE_ROOT}/${TS}"

  FAILED_STAGE="creating remote directories"
  log "Ensuring remote directories exist"
  mkcol_if_needed "${REMOTE_ROOT}"
  mkcol_if_needed "${REMOTE_RUN}"

  FAILED_STAGE="uploading to WebDAV"
  log "Uploading backup files to WebDAV"
  upload_file "${WORKSPACE_ARCHIVE}" "${REMOTE_RUN}/$(basename "${WORKSPACE_ARCHIVE}")"
  [[ -f "${EXTENSIONS_ARCHIVE}" ]] && upload_file "${EXTENSIONS_ARCHIVE}" "${REMOTE_RUN}/$(basename "${EXTENSIONS_ARCHIVE}")"
  [[ -f "${CONFIG_COPY}" ]] && upload_file "${CONFIG_COPY}" "${REMOTE_RUN}/$(basename "${CONFIG_COPY}")"
  [[ -f "${CONFIG_ENC}" ]] && upload_file "${CONFIG_ENC}" "${REMOTE_RUN}/$(basename "${CONFIG_ENC}")"
  upload_file "${RESTORE_NOTE}" "${REMOTE_RUN}/$(basename "${RESTORE_NOTE}")"
  upload_file "${MANIFEST}" "${REMOTE_RUN}/$(basename "${MANIFEST}")"
  log "Upload finished"
  FAILED_STAGE="applying remote retention"
  log "Applying remote retention: keep ${REMOTE_KEEP}"
  rotate_remote_backups "${REMOTE_ROOT}" "${REMOTE_KEEP}"
else
  log "Upload skipped (use --upload to enable)"
fi

write_success_summary
send_notify success
log "Done"
