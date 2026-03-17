#!/usr/bin/env bash
# request-resource.sh — Submit a request to SysClaw via system_comm.agent_requests
#
# Usage:
#   request-resource.sh <source> <type> <action> <target> <justification> [urgency] [payload] [source_host]
#
# Types:      access | software | resource | config | service | deployment | info
# Actions:    install | remove | create | modify | restart | grant | check | deploy | etc.
# Urgency:    low | normal | urgent (default: normal)
# Payload:    JSON string for request-specific details (optional)
#
# Examples:
#   request-resource.sh jobhunter software install nginx '{"version":"latest"}' normal
#   request-resource.sh pmagent access grant /var/data/pm '{"level":"read"}'
#
# Connection (set via environment or .pgpass):
#   REQUEST_DB_HOST, REQUEST_DB_PORT, REQUEST_DB_NAME, REQUEST_DB_USER, REQUEST_DB_PASSWORD

set -euo pipefail

DB_HOST="${REQUEST_DB_HOST:-localhost}"
DB_PORT="${REQUEST_DB_PORT:-5432}"
DB_NAME="${REQUEST_DB_NAME:-system_comm}"
DB_USER="${REQUEST_DB_USER:-issue_reporter}"

source="${1:?Usage: request-resource.sh <source> <type> <action> <target> <justification> [urgency] [payload] [source_host]}"
request_type="${2:?Type required: access | software | resource | config | service | deployment | info}"
action="${3:?Action required: install | remove | create | modify | restart | grant | check | deploy | etc.}"
target="${4:?Target required — what this request applies to}"
justification="${5:?Justification required — explain why you need this}"
urgency="${6:-normal}"
payload="${7:-}"
source_host="${8:-$(hostname 2>/dev/null || echo unknown)}"

# Validate type
case "$request_type" in
  access|software|resource|config|service|deployment|info) ;;
  *) echo "Error: type must be access, software, resource, config, service, deployment, or info" >&2; exit 1 ;;
esac

# Validate urgency
case "$urgency" in
  low|normal|urgent) ;;
  *) echo "Error: urgency must be low, normal, or urgent" >&2; exit 1 ;;
esac

# Escape single quotes
escape_sql() {
  printf "%s" "$1" | sed "s/'/''/g"
}

source_esc=$(escape_sql "$source")
target_esc=$(escape_sql "$target")
justification_esc=$(escape_sql "$justification")
action_esc=$(escape_sql "$action")
host_esc=$(escape_sql "$source_host")

# Handle JSON payload
if [[ -n "$payload" ]]; then
  payload_esc=$(escape_sql "$payload")
  payload_sql="'$payload_esc'::jsonb"
else
  payload_sql="NULL"
fi

PSQL_CMD=(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -t)

if [[ -n "${REQUEST_DB_PASSWORD:-}" ]]; then
  export PGPASSWORD="$REQUEST_DB_PASSWORD"
fi

# Insert request and capture ID
request_output=$("${PSQL_CMD[@]}" -c "
  INSERT INTO agent_requests (requesting_agent, request_type, action, target, justification, urgency, payload, source_host)
  VALUES ('$source_esc', '$request_type', '$action_esc', '$target_esc', '$justification_esc', '$urgency', $payload_sql, '$host_esc')
  RETURNING id;
")

request_id=$(echo "$request_output" | tr -d ' ')
echo "Request #$request_id submitted successfully"

# Notify SysClaw
"${PSQL_CMD[@]}" -c "
  INSERT INTO notifications (recipient, sender, related_request, message, urgency)
  VALUES ('sysclaw', '$source_esc', $request_id, 'New ${request_type} request: ${action} ${target}', '$urgency');
" >/dev/null 2>&1

echo "SysClaw notified."
