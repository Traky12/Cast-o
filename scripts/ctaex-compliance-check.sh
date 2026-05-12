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

echo "[INFO] CTAEX compliance check iniciado"

check_file "docs/ops/CTAEX-CUMPLIMIENTO-ANALISIS.md"
check_file "docs/ops/UNE-178101-PAYLOAD-IOT.md"
check_file ".github/workflows/github-operativity-certification.yml"
check_file "scripts/setup-prod-hardening.sh"
check_file "schemas/iot_payload.json"

if grep -q "Certify Operativity TRL9 ON/OFF" scripts/setup-prod-hardening.sh; then
  ok "Check TRL9 incluido en branch protection script"
else
  err "No se detecta check TRL9 en scripts/setup-prod-hardening.sh"
  HAS_ERROR=1
fi

if command -v pytest >/dev/null 2>&1; then
  echo "[INFO] Ejecutando pruebas IoT de calidad de datos (CTAEX)"
  if pytest -q tests/test_api.py -k "iot_telemetry_"; then
    ok "Pruebas IoT de calidad de datos en verde"
  else
    err "Fallaron pruebas IoT de calidad de datos"
    HAS_ERROR=1
  fi
else
  warn "pytest no disponible; se omiten pruebas"
fi

if [[ "$HAS_ERROR" -eq 0 ]]; then
  echo "[OK] CTAEX compliance check: GO"
  exit 0
fi

echo "[ERROR] CTAEX compliance check: NO-GO"
exit 1
