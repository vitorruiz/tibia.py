#!/usr/bin/env bash
# Builds the event calendar snapshot from this machine and publishes it to the "events-latest" release.
# It only makes three requests to Tibia.com, so it can safely run once a day.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITHUB_REPO="${BAZAAR_GITHUB_REPO:-vitorruiz/tibia.py}"
PYTHON="${PYTHON:-$REPO_ROOT/venv/bin/python}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

cd "$REPO_ROOT"
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# python.org builds on macOS don't use the system certificates.
if [ -z "${SSL_CERT_FILE:-}" ]; then
  SSL_CERT_FILE="$("$PYTHON" -c 'import certifi; print(certifi.where())' 2>/dev/null || true)"
  [ -n "$SSL_CERT_FILE" ] && export SSL_CERT_FILE
fi

gh release view events-latest --repo "$GITHUB_REPO" >/dev/null 2>&1 \
  || gh release create events-latest --repo "$GITHUB_REPO" --prerelease \
       --title "Event calendar snapshot" --notes "Event calendar consumed by the Tibia Companion app. Rebuilt automatically."

"$PYTHON" scripts/events_sync.py --out "$WORK_DIR/events.json"
gh release upload events-latest "$WORK_DIR/events.json" --repo "$GITHUB_REPO" --clobber
