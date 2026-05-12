#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
VERSION="${VERSION:-Unreleased}"
DATE_UTC="$(date -u +"%Y-%m-%d")"

{
  echo "# CHANGELOG"
  echo
  echo "## [$VERSION] - $DATE_UTC"
  echo
  git log --pretty=format:'- %s (%h)' -n 30
  echo
} > "$OUTPUT"

echo "Generated $OUTPUT"
