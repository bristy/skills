#!/usr/bin/env bash
set -euo pipefail

STATUS="${1:-}"
MSG_FILE="${2:-}"

[[ -n "$STATUS" ]] || { echo "Usage: $0 <success|failure> <message-file>" >&2; exit 1; }
[[ -f "$MSG_FILE" ]] || { echo "Message file not found: $MSG_FILE" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${OPENCLAW_WORKSPACE_DIR:-}" ]]; then
  WORKSPACE_DIR="${OPENCLAW_WORKSPACE_DIR}"
else
  WORKSPACE_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
fi
STATE_DIR="${HOME}/.openclaw"
CONFIG_FILE="${STATE_DIR}/openclaw.json"
NOTIFY_ENV_FILE="${WORKSPACE_DIR}/.env.backup.notify"

BACKUP_NOTIFY="${BACKUP_NOTIFY:-0}"
BACKUP_NOTIFY_CHANNEL="${BACKUP_NOTIFY_CHANNEL:-telegram}"
BACKUP_NOTIFY_TELEGRAM_CHAT_ID="${BACKUP_NOTIFY_TELEGRAM_CHAT_ID:-}"
BACKUP_NOTIFY_TELEGRAM_BOT_TOKEN="${BACKUP_NOTIFY_TELEGRAM_BOT_TOKEN:-}"

log() { printf '[backup-notify] %s\n' "$*" >&2; }
need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 1; }; }

if [[ -f "$NOTIFY_ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$NOTIFY_ENV_FILE"
fi

[[ "${BACKUP_NOTIFY:-0}" == "1" ]] || exit 0

send_telegram() {
  local text
  text="$(cat "$MSG_FILE")"
  if [[ -z "${BACKUP_NOTIFY_TELEGRAM_BOT_TOKEN:-}" && -f "$CONFIG_FILE" ]]; then
    need_cmd jq
    BACKUP_NOTIFY_TELEGRAM_BOT_TOKEN="$(jq -r '.channels.telegram.botToken // .channels.telegram.accounts.default.botToken // empty' "$CONFIG_FILE")"
  fi
  [[ -n "${BACKUP_NOTIFY_TELEGRAM_BOT_TOKEN:-}" ]] || { log 'Telegram bot token not configured; skip'; return 0; }
  [[ -n "${BACKUP_NOTIFY_TELEGRAM_CHAT_ID:-}" ]] || { log 'Telegram chat id not configured; skip'; return 0; }
  need_cmd curl
  curl --silent --show-error --fail \
    -X POST "https://api.telegram.org/bot${BACKUP_NOTIFY_TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${BACKUP_NOTIFY_TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${text}" \
    >/dev/null
}

case "$BACKUP_NOTIFY_CHANNEL" in
  telegram)
    send_telegram
    ;;
  weixin|wechat)
    log 'WeChat notification is not implemented yet; skip'
    ;;
  *)
    log "Unknown notify channel: $BACKUP_NOTIFY_CHANNEL; skip"
    ;;
esac
