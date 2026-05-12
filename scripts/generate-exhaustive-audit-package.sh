#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

TS="$(date -u +%Y%m%d-%H%M%S)"
OUT_DIR="artifacts/audit-package-${TS}"
LOG_DIR="${OUT_DIR}/logs"
REPORT_MD="${OUT_DIR}/AUDIT-REPORT.md"
REPORT_JSON="${OUT_DIR}/summary.json"
MANIFEST="${OUT_DIR}/manifest.txt"
EXEC_COVER="${OUT_DIR}/PORTADA-EJECUTIVA.md"
CHECKSUM_FILE="${OUT_DIR}.sha256"
ZIP_FILE="${OUT_DIR}.zip"

mkdir -p "$LOG_DIR"

overall_ok=1

TOTAL_CHECKS=7

run_check() {
  local id="$1"
  local cmd="$2"
  local log_file="${LOG_DIR}/${id}.log"

  echo "[INFO] Running ${id}: ${cmd}"
  if bash -lc "$cmd" >"$log_file" 2>&1; then
    echo "PASS" >"${LOG_DIR}/${id}.status"
    echo "[OK] ${id}"
  else
    echo "FAIL" >"${LOG_DIR}/${id}.status"
    overall_ok=0
    echo "[ERROR] ${id}"
  fi
}

write_system_info() {
  {
    echo "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "cwd=$(pwd)"
    echo "kernel=$(uname -srmo 2>/dev/null || true)"
    if command -v lsb_release >/dev/null 2>&1; then
      echo "os=$(lsb_release -ds 2>/dev/null || true)"
    else
      echo "os=$(grep '^PRETTY_NAME=' /etc/os-release 2>/dev/null | cut -d= -f2- | tr -d '"' || echo unknown)"
    fi
    echo "python=$(python --version 2>/dev/null || echo unavailable)"
    echo "pip=$(pip --version 2>/dev/null || echo unavailable)"
    echo "git=$(git --version 2>/dev/null || echo unavailable)"
    echo "docker=$(docker --version 2>/dev/null || echo unavailable)"
    echo "kubectl=$(kubectl version --client --output=yaml 2>/dev/null | head -n 1 || echo unavailable)"
  } > "${OUT_DIR}/system-info.txt"
}

copy_key_evidence() {
  mkdir -p "${OUT_DIR}/evidence"

  for path in \
    docs/ops/PRONTUARIO-MAESTRO-OPERATIVIDAD-CERTIFICADA-TRL9.md \
    docs/ops/CTAEX-CUMPLIMIENTO-ANALISIS.md \
    docs/ops/UNE-178101-PAYLOAD-IOT.md \
    legal/register_activities.json \
    legal/dpias/dpia_sensors.json \
    legal/dpias/dpia_blockchain.json \
    legal/dsar_portal.md \
    legal/retention_policy.md \
    schemas/iot_payload.json \
    .github/workflows/github-operativity-certification.yml; do
    if [[ -f "$path" ]]; then
      mkdir -p "${OUT_DIR}/evidence/$(dirname "$path")"
      cp "$path" "${OUT_DIR}/evidence/$path"
    fi
  done

  if [[ -f artifacts/operativity/github-operativity-latest.txt ]]; then
    cp artifacts/operativity/github-operativity-latest.txt "${OUT_DIR}/evidence/github-operativity-latest.txt"
  fi
}

status_of() {
  local id="$1"
  cat "${LOG_DIR}/${id}.status" 2>/dev/null || echo "NOT-RUN"
}

write_reports() {
  local s1 s2 s3 s4 s5 s6 s7 s8
  s1="$(status_of github_operativity)"
  s2="$(status_of github_certification)"
  s3="$(status_of decoupled_hardening)"
  s4="$(status_of ctaex_gate)"
  s5="$(status_of legal_gate)"
  s6="$(status_of dsar_tests)"
  s7="$(status_of iot_quality_tests)"
  s8="$(status_of evidence_secret_scan)"

  local passed_checks=0
  for status in "$s1" "$s2" "$s3" "$s4" "$s5" "$s6" "$s7" "$s8"; do
    if [[ "$status" == "PASS" ]]; then
      passed_checks=$((passed_checks + 1))
    fi
  done

  local final_status="GO"
  if [[ "$overall_ok" -ne 1 ]]; then
    final_status="NO-GO"
  fi

  local trl_level="TRL 8"
  local trl_note="Sistema casi completo y validado; pendiente certificacion externa formal para TRL 9"
  if [[ "$final_status" == "GO" ]]; then
    trl_level="TRL 8"
  fi

  local badge_state="🟢 GO"
  if [[ "$final_status" != "GO" ]]; then
    badge_state="🔴 NO-GO"
  fi

  cat > "$REPORT_MD" <<EOF
# Exhaustive Audit Package Report

- Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Final status: ${final_status}
- Checks passed: ${passed_checks}/${TOTAL_CHECKS}
- TRL assessment: ${trl_level}
- TRL note: ${trl_note}
- Output directory: ${OUT_DIR}

## Check results

- github_operativity: ${s1}
- github_certification: ${s2}
- decoupled_hardening: ${s3}
- ctaex_gate: ${s4}
- legal_gate: ${s5}
- dsar_tests: ${s6}
- iot_quality_tests: ${s7}
- evidence_secret_scan: ${s8}

## Notes

- GO means all critical checks passed in this environment.
- NO-GO means at least one critical check failed. See logs/ for details.
- Economic valuation figures are internal estimates; not an external valuation report.
EOF

  cat > "$REPORT_JSON" <<EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "${final_status}",
  "checks_passed": ${passed_checks},
  "checks_total": ${TOTAL_CHECKS},
  "trl_assessment": {
    "level": "${trl_level}",
    "note": "${trl_note}"
  },
  "checks": {
    "github_operativity": "${s1}",
    "github_certification": "${s2}",
    "decoupled_hardening": "${s3}",
    "ctaex_gate": "${s4}",
    "legal_gate": "${s5}",
    "dsar_tests": "${s6}",
    "iot_quality_tests": "${s7}",
    "evidence_secret_scan": "${s8}"
  }
}
EOF

  cat > "$EXEC_COVER" <<EOF
# CASTUO-SYSTEM PAQUETE AUDITORIA TRL9

## CASTUO-SYSTEM v2.1 (Badged: $(date -u "+%Y-%m-%d %H:%M:%S") UTC)

**Estado**: ${badge_state} | **${passed_checks}/${TOTAL_CHECKS} Checks** | **TRL Evaluado: ${trl_level}**

## Verificadores Externos READY

| Auditor | Bundle Entregado | Estado Esperado | Contacto |
|---|---|---|---|
| CDTI | $(basename "$ZIP_FILE") | Validacion TRL | cdti.es |
| CTAEX | CAX21 + $(basename "$ZIP_FILE") | Fase tecnica | ctaex.com |
| AENOR | Evidencias ISO/RGPD incluidas | Pre-auditoria | aenor.com |

## Bundle

- Ruta local: ${OUT_DIR}
- ZIP: ${ZIP_FILE}
- Checksum: ${CHECKSUM_FILE}
- Reporte: ${REPORT_MD}
- Resumen JSON: ${REPORT_JSON}

## Enlace recomendado

Si se publica en repositorio remoto, usar:
- https://github.com/Traky12/Castuo-system/tree/main/$(basename "$OUT_DIR")

## Valoracion economica (estimativa interna, no tasacion externa)

| Escenario | Valor estimado |
|---|---|
| Base tecnica (post-auditoria interna) | EUR 350000 |
| Con auditorias externas completadas | EUR 500000 |

Nota: estas cifras son una referencia interna de negocio y deben validarse por terceros para uso financiero formal.
EOF

if command -v zip >/dev/null 2>&1; then
  (cd artifacts && zip -rq "$(basename "$ZIP_FILE")" "$(basename "$OUT_DIR")")
fi

if command -v sha256sum >/dev/null 2>&1; then
  find "$OUT_DIR" -type f | sort | while read -r f; do
    sha256sum "$f"
  done > "${OUT_DIR}/integrity.sha256"
elif command -v shasum >/dev/null 2>&1; then
  find "$OUT_DIR" -type f | sort | while read -r f; do
    shasum -a 256 "$f"
  done > "${OUT_DIR}/integrity.sha256"
fi

if command -v sha256sum >/dev/null 2>&1; then
  if [[ -f "$ZIP_FILE" ]]; then
    sha256sum "$ZIP_FILE" > "$CHECKSUM_FILE"
  else
    sha256sum "$REPORT_MD" > "$CHECKSUM_FILE"
  fi
fi

  {
    echo "audit_package=${OUT_DIR}"
    echo "report_md=${REPORT_MD}"
    echo "report_json=${REPORT_JSON}"
    echo "executive_cover=${EXEC_COVER}"
    echo "zip_file=${ZIP_FILE}"
    echo "checksum_file=${CHECKSUM_FILE}"
    echo "status=${final_status}"
    echo "checks_passed=${passed_checks}/${TOTAL_CHECKS}"
    find "$OUT_DIR" -type f | sort
  } > "$MANIFEST"

  echo "[INFO] Final status: ${final_status}"
  echo "[INFO] Report: ${REPORT_MD}"
  echo "[INFO] JSON: ${REPORT_JSON}"
}

echo "[INFO] Building exhaustive audit package in ${OUT_DIR}"
write_system_info

TOTAL_CHECKS=8

run_check "github_operativity" "make test-github-operativity"
run_check "github_certification" "make test-github-certification"
run_check "decoupled_hardening" "REQUIRE_GITHUB_HARDENING=0 bash scripts/setup-prod-hardening.sh"
run_check "ctaex_gate" "make ctaex-compliance-check"
run_check "legal_gate" "make legal-compliance-check"
run_check "dsar_tests" "pytest -q tests/test_dsar_router.py"
run_check "iot_quality_tests" "pytest -q tests/test_api.py -k iot_telemetry_"

copy_key_evidence
run_check "evidence_secret_scan" "bash scripts/audit-evidence-security-scan.sh \"${OUT_DIR}/evidence\""
write_reports

if [[ "$overall_ok" -eq 1 ]]; then
  exit 0
fi

exit 1
