#!/usr/bin/env bash
# report-issue.sh — Report an issue to SysClaw via system_comm.issues
#
# Usage:
#   report-issue.sh <source> <severity> <title> [category] [details] [source_host]
#
# Severity: info | warning | critical
# Category: disk | service | error | resource | network | config | other
#
# Connection (set via environment or .pgpass):
#   ISSUE_DB_HOST     (default: localhost)
#   ISSUE_DB_PORT     (default: 5432)
#   ISSUE_DB_NAME     (default: system_comm)
#   ISSUE_DB_USER     (default: issue_reporter)
#   ISSUE_DB_PASSWORD (optional, or use .pgpass)
#
# Examples:
#   report-issue.sh jobhunter warning "Disk usage above 80%" disk "df shows 82% on /data" srv-prod-01
#   report-issue.sh propertymanager critical "API returning 500" service "" srv-prod-02

set -euo pipefail

DB_HOST="${ISSUE_DB_HOST:-localhost}"
DB_PORT="${ISSUE_DB_PORT:-5432}"
DB_NAME="${ISSUE_DB_NAME:-system_comm}"
DB_USER="${ISSUE_DB_USER:-issue_reporter}"

source="${1:?Usage: report-issue.sh <source> <severity> <title> [category] [details] [source_host]}"
severity="${2:?Severity required: info | warning | critical}"
title="${3:?Title required}"
category="${4:-other}"
details="${5:-}"
source_host="${6:-$(hostname 2>/dev/null || echo unknown)}"

# Validate severity
case "$severity" in
  info|warning|critical) ;;
  *) echo "Error: severity must be info, warning, or critical" >&2; exit 1 ;;
esac

# Escape single quotes for SQL
escape_sql() {
  printf "%s" "$1" | sed "s/'/''/g"
}

title_esc=$(escape_sql "$title")
details_esc=$(escape_sql "$details")
source_esc=$(escape_sql "$source")
category_esc=$(escape_sql "$category")
host_esc=$(escape_sql "$source_host")

# Build psql command
PSQL_CMD=(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -q -t)

# Export password if provided via env
if [[ -n "${ISSUE_DB_PASSWORD:-}" ]]; then
  export PGPASSWORD="$ISSUE_DB_PASSWORD"
fi

"${PSQL_CMD[@]}" -c "
  INSERT INTO issues (source, severity, category, title, details, source_host, status)
  VALUES ('$source_esc', '$severity', '$category_esc', '$title_esc', '$details_esc', '$host_esc', 'open')
  RETURNING 'Issue #' || id || ' reported successfully';
"
