#!/usr/bin/env bash
# config/safe-git-sync.sh
# Safe Git synchronisation — stashes all local changes (including untracked
# files), pulls the latest upstream, then restores the stash.
#
# Usage:
#   bash config/safe-git-sync.sh [remote] [branch]
#
# Examples:
#   bash config/safe-git-sync.sh                  # defaults: origin main
#   bash config/safe-git-sync.sh origin develop

set -euo pipefail

REMOTE="${1:-origin}"
BRANCH="${2:-main}"

echo "===== safe-git-sync.sh ====="
echo "Remote : $REMOTE"
echo "Branch : $BRANCH"

# Require a clean working tree OR stash everything (including untracked files)
STASH_NEEDED=false
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  echo "Stashing local changes (--include-untracked)..."
  git stash push --include-untracked --message "safe-git-sync auto-stash $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  STASH_NEEDED=true
fi

echo "Fetching $REMOTE/$BRANCH..."
git fetch "$REMOTE" "$BRANCH"

echo "Merging $REMOTE/$BRANCH (fast-forward only)..."
git merge --ff-only "$REMOTE/$BRANCH"

if $STASH_NEEDED; then
  echo "Restoring stash..."
  git stash pop
fi

echo "✅ Sync complete"
