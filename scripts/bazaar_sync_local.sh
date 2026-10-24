#!/usr/bin/env bash
# Runs the Char Bazaar snapshot sync from this machine and publishes it to the "bazaar-latest" release.
#
# Tibia.com blocks the IPs of GitHub Actions runners, so the sync runs from a regular connection instead.
# It is safe to run as often as you like: the script exits early when the snapshot is already up to date.
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

gh release view bazaar-latest --repo "$GITHUB_REPO" >/dev/null 2>&1 \
  || gh release create bazaar-latest --repo "$GITHUB_REPO" --prerelease \
       --title "Bazaar snapshot" --notes "Daily Char Bazaar snapshot. Rebuilt automatically."

status=0
"$PYTHON" scripts/bazaar_sync.py \
  --previous "https://github.com/$GITHUB_REPO/releases/download/bazaar-latest/bazaar.json.gz" \
  --out "$WORK_DIR/bazaar.json.gz" "$@" || status=$?

# Publish even a partial snapshot, so the next run can resume from it.
if [ -f "$WORK_DIR/bazaar.json.gz" ]; then
  gh release upload bazaar-latest "$WORK_DIR/bazaar.json.gz" --repo "$GITHUB_REPO" --clobber
fi
exit "$status"
