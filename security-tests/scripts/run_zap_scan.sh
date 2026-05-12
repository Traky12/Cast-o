#!/usr/bin/env bash
# security-tests/scripts/run_zap_scan.sh
set -euo pipefail

SCAN_TYPE="${1:-baseline}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="$ROOT_DIR"

case "$SCAN_TYPE" in
  baseline)
    python security-tests/zap/baseline_scan.py
    ;;
  api)
    python security-tests/zap/api_scan.py
    ;;
  *)
    echo "Uso: $0 [baseline|api]" >&2
    exit 1
    ;;
esac

