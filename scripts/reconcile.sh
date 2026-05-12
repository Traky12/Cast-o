#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source_branch=""
target_branch=""
dry_run=0
output_dir="logs"
summary_json=""

emit_summary_json() {
  local status_code="$1"
  local drift_detected="$2"
  local message="$3"

  if [[ -z "$summary_json" ]]; then
    return 0
  fi

  python3 - "$summary_json" "$source_branch" "$target_branch" "$dry_run" "$drift_detected" "$report" "$patch_file" "$status_code" "$message" <<'PY'
import json
import sys
from datetime import datetime, timezone

(
    summary_path,
    source_branch,
    target_branch,
    dry_run,
    drift_detected,
    report,
    patch_file,
    status_code,
    message,
) = sys.argv[1:]

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "source_branch": source_branch,
    "target_branch": target_branch,
    "dry_run": dry_run == "1",
    "drift_detected": drift_detected == "1",
    "report": report,
    "patch_file": patch_file,
    "status": {
      "code": int(status_code),
      "message": message,
    },
    "status_code": int(status_code),
    "message": message,
}

with open(summary_path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=True, indent=2)
PY
}

finalize() {
  local status_code="$1"
  local drift_detected="$2"
  local message="$3"

  emit_summary_json "$status_code" "$drift_detected" "$message"
  exit "$status_code"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-branch)
      source_branch="$2"
      shift 2
      ;;
    --target-branch)
      target_branch="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --output-dir)
      output_dir="$2"
      shift 2
      ;;
    --summary-json)
      summary_json="$2"
      shift 2
      ;;
    *)
      echo "Parametro no reconocido: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$source_branch" ]]; then
  source_branch="HEAD"
fi

if [[ -z "$target_branch" ]]; then
  target_branch="origin/main"
fi

mkdir -p "$output_dir"
stamp="$(date +%Y%m%d-%H%M%S)"
report="${output_dir}/reconcile-${stamp}.log"
patch_file="${output_dir}/reconcile-${stamp}.patch"

echo "[INFO] Reconciliando ${target_branch} <- ${source_branch}" | tee -a "$report"

git fetch --all --prune > /dev/null 2>&1 || true

if ! git rev-parse --verify "$target_branch" > /dev/null 2>&1; then
  echo "[ERROR] target_branch no existe: ${target_branch}" | tee -a "$report"
  finalize 1 0 "target_branch no existe: ${target_branch}"
fi

if ! git rev-parse --verify "$source_branch" > /dev/null 2>&1; then
  echo "[ERROR] source_branch no existe: ${source_branch}" | tee -a "$report"
  finalize 1 0 "source_branch no existe: ${source_branch}"
fi

git diff --name-status "${target_branch}...${source_branch}" | tee -a "$report"

git diff "${target_branch}...${source_branch}" > "$patch_file"

if [[ ! -s "$patch_file" ]]; then
  echo "[OK] No se detecta drift" | tee -a "$report"
  finalize 0 0 "No se detecta drift"
fi

echo "[WARN] Drift detectado. Parche generado en ${patch_file}" | tee -a "$report"

# Compatibilidad CI/tests: reporte de drift con nombre estable.
drift_report="${output_dir}/drift_report.log"
cp "$report" "$drift_report"

if [[ "$dry_run" -eq 1 ]]; then
  echo "[OK] Modo dry-run: sin aplicar cambios" | tee -a "$report"
  finalize 1 1 "Drift detectado en dry-run"
fi

echo "[WARN] Modo no dry-run: aplicacion automatica deshabilitada por seguridad" | tee -a "$report"
echo "[INFO] Aplicar parche manualmente tras revision Sabionda" | tee -a "$report"
finalize 1 1 "Drift detectado: aplicacion automatica deshabilitada por seguridad"
