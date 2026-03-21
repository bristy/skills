#!/usr/bin/env bash
# Uninstall and disable the YouOS launchd user agent.
set -euo pipefail

LABEL="com.youos.server"
GUI_DOMAIN="gui/$(id -u)"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if launchctl print "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1; then
  echo "Booting out $LABEL"
  launchctl bootout "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true
fi

launchctl disable "$GUI_DOMAIN/$LABEL" >/dev/null 2>&1 || true

if [[ -f "$PLIST_DST" ]]; then
  rm -f "$PLIST_DST"
  echo "Removed $PLIST_DST"
else
  echo "Plist already absent: $PLIST_DST"
fi

echo "YouOS launchd agent disabled."
