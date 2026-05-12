#!/usr/bin/env bash
# trl6-validate.sh — pytest -m trl6; E2E opcional si hay stub en CASTUO_ROBOTICS_LAB_URL
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export PYTHONPATH="$ROOT"
export CASTUO_ROBOTICS_LAB_URL="${CASTUO_ROBOTICS_LAB_URL:-http://127.0.0.1:8011}"

echo "[TRL6] pytest -m trl6 (ROOT=$ROOT)"
cd "$ROOT"
python -m pytest -m trl6 -q

if [[ "${SKIP_TRL6_E2E:-0}" != "1" ]]; then
  echo "[TRL6] PowerShell E2E omitido en POSIX; export SKIP_TRL6_E2E=1 o ejecutar stub y pruebas manuales."
  echo "       curl -sS \"${CASTUO_ROBOTICS_LAB_URL}/health\" | head -c 200"
fi

echo "[TRL6] pytest completado."
