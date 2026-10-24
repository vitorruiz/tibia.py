#!/usr/bin/env bash
# Removes the launchd agent that runs the Char Bazaar sync. Pass --purge to also delete its log file.
set -euo pipefail

LABEL="com.vitorruiz.bazaar-sync"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/bazaar-sync.log"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$TARGET"
if [ "${1:-}" = "--purge" ]; then
  rm -f "$LOG"
fi
echo "Removed $LABEL."
