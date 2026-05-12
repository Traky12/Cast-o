#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-main}"
OUTPUT_FILE="${GITHUB_OUTPUT:-}"
COMMIT_COUNT="$(git rev-list --count "origin/${BRANCH}" 2>/dev/null || git rev-list --count HEAD)"
SHOULD_RUN="false"
REASON="regular-push"

if [[ "$COMMIT_COUNT" == "1" ]]; then
  SHOULD_RUN="true"
  REASON="root-commit"
elif [[ ! -f docs/QUICK-REFERENCE.md ]]; then
  SHOULD_RUN="true"
  REASON="bootstrap-missing-quick-reference"
elif git diff --name-only HEAD^ HEAD 2>/dev/null | grep -Eq '^(api/|config/|docker-compose|infrastructure/|scripts/)'; then
  SHOULD_RUN="true"
  REASON="main-change-requires-summary"
fi

if [[ -n "$OUTPUT_FILE" ]]; then
  {
    echo "should_run=$SHOULD_RUN"
    echo "reason=$REASON"
    echo "commit_count=$COMMIT_COUNT"
  } >> "$OUTPUT_FILE"
else
  echo "should_run=$SHOULD_RUN"
  echo "reason=$REASON"
  echo "commit_count=$COMMIT_COUNT"
fi
