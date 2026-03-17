#!/usr/bin/env bash
# check-notifications.sh — Check and display notifications for an agent
#
# Usage:
#   check-notifications.sh <agent_name> [mark_read]
#
# Arguments:
#   agent_name   — Your agent name (e.g., jobhunter, pmagent)
#   mark_read    — Set to 'yes' to mark displayed notifications as read (default: no)
#
# Examples:
#   check-notifications.sh jobhunter          # View unread notifications
#   check-notifications.sh jobhunter yes      # View and mark as read
#
# Connection (set via environment or .pgpass):
#   SYSCLAW_DB_HOST, SYSCLAW_DB_PORT, SYSCLAW_DB_NAME, SYSCLAW_DB_USER, SYSCLAW_DB_PASSWORD

set -euo pipefail

DB_HOST="${SYSCLAW_DB_HOST:-localhost}"
DB_PORT="${SYSCLAW_DB_PORT:-5432}"
DB_NAME="${SYSCLAW_DB_NAME:-system_comm}"
DB_USER="${SYSCLAW_DB_USER:-issue_reporter}"

agent_name="${1:?Usage: check-notifications.sh <agent_name> [mark_read]}"
mark_read="${2:-no}"

escape_sql() {
  printf "%s" "$1" | sed "s/'/''/g"
}

agent_esc=$(escape_sql "$agent_name")

PSQL_CMD=(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -t -A -F'|')

if [[ -n "${SYSCLAW_DB_PASSWORD:-}" ]]; then
  export PGPASSWORD="$SYSCLAW_DB_PASSWORD"
fi

# Fetch unread notifications
results=$("${PSQL_CMD[@]}" -c "
  SELECT id, sender, related_request, message, urgency, created_at
  FROM notifications
  WHERE recipient = '$agent_esc' AND read = FALSE
  ORDER BY created_at ASC;
" 2>/dev/null || echo "")

if [[ -z "$results" ]]; then
  echo "No unread notifications."
  exit 0
fi

echo "# Unread Notifications"
echo ""
count=0
while IFS='|' read -r id sender related_req message urgency created; do
  count=$((count + 1))
  echo "- [ ] #$id [$urgency] from $sender ($created)"
  echo "  $message"
  if [[ -n "$related_req" && "$related_req" != "" ]]; then
    echo "  Related request: #$related_req"
  fi
  echo ""
done <<< "$results"
echo "Total: $count notification(s)"

# Mark as read if requested
if [[ "$mark_read" == "yes" ]]; then
  "${PSQL_CMD[@]}" -c "
    UPDATE notifications SET read = TRUE
    WHERE recipient = '$agent_esc' AND read = FALSE;
  " >/dev/null 2>&1
  echo "All marked as read."
fi
