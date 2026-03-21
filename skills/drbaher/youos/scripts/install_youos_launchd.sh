#!/usr/bin/env bash
# Install or reload the YouOS launchd user agent.
set -euo pipefail

fatal() {
  echo "ERROR: $*" >&2
  exit 1
}

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.youos.server"
GUI_DOMAIN="gui/$(id -u)"
PLIST_SRC="$REPO_DIR/deploy/launchd/${LABEL}.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$REPO_DIR/var"
STDOUT_LOG="$LOG_DIR/launchd.stdout.log"
STDERR_LOG="$LOG_DIR/launchd.stderr.log"

[[ -f "$PLIST_SRC" ]] || fatal "plist not found: $PLIST_SRC"
plutil -lint "$PLIST_SRC" >/dev/null || fatal "plist failed validation: $PLIST_SRC"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
touch "$STDOUT_LOG" "$STDERR_LOG"

if launchctl print "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1; then
  echo "Booting out existing $LABEL"
  launchctl bootout "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
fi

cp -f "$PLIST_SRC" "$PLIST_DST"
echo "Installed $PLIST_DST"

launchctl bootstrap "$GUI_DOMAIN" "$PLIST_DST"
launchctl enable "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
launchctl kickstart -k "$GUI_DOMAIN/$LABEL"

sleep 1

echo ""
echo "=== Service status ==="
launchctl print "$GUI_DOMAIN/$LABEL" 2>&1 | head -20 || true

echo ""
echo "=== Useful commands ==="
echo "Status:  launchctl print $GUI_DOMAIN/$LABEL"
echo "Stop:    launchctl bootout $GUI_DOMAIN/$LABEL"
echo "Start:   launchctl bootstrap $GUI_DOMAIN $PLIST_DST"
echo "Restart: launchctl kickstart -k $GUI_DOMAIN/$LABEL"
echo "Logs:    tail -f $STDERR_LOG"
echo "Health:  curl -s http://127.0.0.1:8765/healthz"
echo "Ready:   curl -s http://127.0.0.1:8765/readyz"
