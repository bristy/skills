#!/usr/bin/env bash
set -euo pipefail

# OpenClaw 轻量版恢复脚本（本地恢复版）
#
# 用法：
#   bash scripts/openclaw-restore.sh --from <backup_dir>
#   bash scripts/openclaw-restore.sh --from <backup_dir> --decrypt-config
#   bash scripts/openclaw-restore.sh --from <backup_dir> --decrypt-config --dry-run
#
# 说明：
# - 默认恢复到 ~/.openclaw/
# - 会恢复 workspace / extensions
# - 如果存在 openclaw.json.enc，可选解密为 ~/.openclaw/openclaw.json
# - 默认不自动重启 gateway

BACKUP_DIR=""
DRY_RUN=0
DECRYPT_CONFIG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      BACKUP_DIR="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --decrypt-config)
      DECRYPT_CONFIG=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${BACKUP_DIR}" ]]; then
  echo "Usage: bash scripts/openclaw-restore.sh --from <backup_dir> [--decrypt-config] [--dry-run]" >&2
  exit 1
fi

BACKUP_DIR="$(cd "${BACKUP_DIR}" && pwd)"
HOME_DIR="${HOME}"
STATE_DIR="${HOME_DIR}/.openclaw"
WORKSPACE_TARGET="${STATE_DIR}/workspace"
EXTENSIONS_TARGET="${STATE_DIR}/extensions"
CONFIG_TARGET="${STATE_DIR}/openclaw.json"
if [[ -n "${OPENCLAW_WORKSPACE_DIR:-}" ]]; then
  ENV_FILE="${OPENCLAW_WORKSPACE_DIR}/.env.backup"
  SECRET_FILE="${OPENCLAW_WORKSPACE_DIR}/.env.backup.secret"
else
  BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
  ENV_FILE="${BASE_DIR}/.env.backup"
  SECRET_FILE="${BASE_DIR}/.env.backup.secret"
fi

log() { printf '[restore] %s\n' "$*"; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }
resolve_encrypt_pass() {
  if [[ -n "${BACKUP_ENCRYPT_PASS:-}" ]]; then
    return 0
  fi
  if [[ -f "${SECRET_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${SECRET_FILE}"
  fi
  if [[ -n "${BACKUP_ENCRYPT_PASS:-}" ]]; then
    export BACKUP_ENCRYPT_PASS
    return 0
  fi
  if [[ -t 0 ]]; then
    read -r -s -p 'Enter backup decryption password: ' BACKUP_ENCRYPT_PASS
    echo
    [[ -n "${BACKUP_ENCRYPT_PASS}" ]] || { echo "Empty decryption password" >&2; exit 1; }
    export BACKUP_ENCRYPT_PASS
    return 0
  fi
  echo "Missing BACKUP_ENCRYPT_PASS. Set env var, provide .env.backup.secret, or run interactively." >&2
  exit 1
}
run() {
  if [[ ${DRY_RUN} -eq 1 ]]; then
    printf '[restore] DRY RUN: %s\n' "$*"
  else
    eval "$@"
  fi
}

need_cmd tar
mkdir -p "${STATE_DIR}"

if [[ ! -f "${BACKUP_DIR}/workspace.tar.gz" ]]; then
  echo "Missing workspace.tar.gz in ${BACKUP_DIR}" >&2
  exit 1
fi

log "Preparing restore from ${BACKUP_DIR}"

run "mkdir -p '${WORKSPACE_TARGET}'"
log "Restoring workspace"
run "tar -xzf '${BACKUP_DIR}/workspace.tar.gz' -C '${WORKSPACE_TARGET}'"

if [[ -f "${BACKUP_DIR}/extensions.tar.gz" ]]; then
  log "Restoring extensions"
  run "mkdir -p '${STATE_DIR}'"
  run "tar -xzf '${BACKUP_DIR}/extensions.tar.gz' -C '${STATE_DIR}'"
fi

if [[ -f "${BACKUP_DIR}/openclaw.json" ]]; then
  log "Restoring plain config"
  run "cp '${BACKUP_DIR}/openclaw.json' '${CONFIG_TARGET}'"
elif [[ -f "${BACKUP_DIR}/openclaw.json.enc" ]]; then
  if [[ ${DECRYPT_CONFIG} -eq 1 ]]; then
    resolve_encrypt_pass
    : "${BACKUP_ENCRYPT_PASS:?BACKUP_ENCRYPT_PASS is required for config decryption}"
    need_cmd openssl
    log "Decrypting config"
    if [[ ${DRY_RUN} -eq 1 ]]; then
      printf '[restore] DRY RUN: decrypt %s -> %s\n' "${BACKUP_DIR}/openclaw.json.enc" "${CONFIG_TARGET}"
    else
      openssl enc -d -aes-256-cbc -pbkdf2 -in "${BACKUP_DIR}/openclaw.json.enc" -out "${CONFIG_TARGET}" -pass env:BACKUP_ENCRYPT_PASS >/dev/null 2>&1
    fi
  else
    log "Encrypted config found but not decrypted (use --decrypt-config if needed)"
  fi
fi

log "Restore flow completed"
log "Recommended next steps:"
log "  1. openclaw status"
log "  2. openclaw gateway restart"
log "  3. verify Telegram / Weixin / model / plugins.allow / memory"
