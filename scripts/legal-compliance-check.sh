#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ok() { echo "[OK] $*"; }
warn() { echo "[WARN] $*"; }
err() { echo "[ERROR] $*"; }

HAS_ERROR=0

check_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    ok "Existe: $path"
  else
    err "Falta: $path"
    HAS_ERROR=1
  fi
}

echo "[INFO] Legal compliance check iniciado"

check_file "legal/register_activities.json"
check_file "legal/dpias/dpia_sensors.json"
check_file "legal/dpias/dpia_blockchain.json"
check_file "legal/dsar_portal.md"
check_file "legal/retention_policy.md"
check_file "api/routers/dsar.py"

# Validacion JSON mínima (estructura parseable)
if command -v python >/dev/null 2>&1; then
  python - <<'PY'
import json
from pathlib import Path

for path in [
    "legal/register_activities.json",
    "legal/dpias/dpia_sensors.json",
    "legal/dpias/dpia_blockchain.json",
]:
    json.loads(Path(path).read_text(encoding="utf-8"))
print("JSON legal artifacts parseable")
PY
  ok "Artefactos legales JSON validos"
else
  warn "python no disponible; se omite validacion JSON"
fi

if command -v pytest >/dev/null 2>&1; then
  echo "[INFO] Ejecutando pruebas DSAR (RGPD)"
  if pytest -q tests/test_dsar_router.py; then
    ok "Pruebas DSAR en verde"
  else
    err "Fallaron pruebas DSAR"
    HAS_ERROR=1
  fi
else
  warn "pytest no disponible; se omiten pruebas DSAR"
fi

if [[ "$HAS_ERROR" -eq 0 ]]; then
  echo "[OK] Legal compliance check: GO"
  exit 0
fi

echo "[ERROR] Legal compliance check: NO-GO"
exit 1
