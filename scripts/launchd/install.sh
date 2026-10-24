#!/usr/bin/env bash
# Installs (or reinstalls) the launchd agent that runs the Char Bazaar sync every hour.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LABEL="com.vitorruiz.bazaar-sync"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

sed -e "s#__REPO_ROOT__#$REPO_ROOT#g" -e "s#__HOME__#$HOME#g" \
  "$REPO_ROOT/scripts/launchd/$LABEL.plist.template" > "$TARGET"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$TARGET"
echo "Installed $TARGET. Logs: ~/Library/Logs/bazaar-sync.log"
