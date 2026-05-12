#!/bin/bash
# scripts/ops/security/clamav-scan.sh
#
# Plantilla de escaneo de malware con ClamAV.
# - Usa `freshclam` (si existe) para actualizar firmas.
# - Ejecuta clamscan recursivo excluyendo directorios comunes.
# - Genera `clamav_scan.log` y falla el proceso si hay infectados.
#
# Nota: no usa datos sensibles ni crea persistencia externa. Logs locales.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-.}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-node_modules|venv|.venv|dist|build}"
LOG_PATH="${LOG_PATH:-clamav_scan.log}"

DRY_RUN=false
QUARANTINE_DIR="${QUARANTINE_DIR:-/tmp/quarantine}"
NOTIFY_URL="${NOTIFY_URL:-http://localhost:8080/gemelos/audit/security}"
EVENT_TYPE="${EVENT_TYPE:-malware_detected}"
SEVERITY="${SEVERITY:-high}"

mkdir -p "$QUARANTINE_DIR"

# Parsear argumentos
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    *)
      echo "[ERROR] Argumento desconocido: $1" >&2
      exit 1
      ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Falta comando: $1" >&2; exit 1; }
}

require_cmd clamscan
require_cmd python3
require_cmd awk
require_cmd grep

if command -v freshclam >/dev/null 2>&1; then
  echo "[clamav-scan] Actualizando firmas..."
  # Para runners con privilegios insuficientes, esto puede fallar;
  # como mejora critica para seguridad, abortamos si no actualiza.
  sudo freshclam
else
  echo "[clamav-scan] freshclam no disponible; abortando por seguridad." >&2
  exit 1
fi

echo "[clamav-scan] Escaneando: $PROJECT_ROOT"
echo "[clamav-scan] Excluyendo (regex): $EXCLUDE_DIRS"

# clamscan imprime lineas tipo:
#   /ruta/archivo: Eicar-Test-Signature FOUND
SCAN_LOG="/tmp/clamav_scan_$(date -u +"%Y%m%d_%H%M%SZ").log"
rm -f "$SCAN_LOG" "$LOG_PATH" || true

EXCLUDE_CLAUSES=""
IFS="|" read -r -a parts <<< "$EXCLUDE_DIRS"
for d in "${parts[@]}"; do
  if [[ -n "$d" ]]; then
    EXCLUDE_CLAUSES+=" --exclude-dir=$d"
  fi
done

set +e
clamscan -r --bell -i "$PROJECT_ROOT" $EXCLUDE_CLAUSES | tee "$SCAN_LOG"
CLAMSCAN_RC="${PIPESTATUS[0]:-0}"
set -e

mapfile -t INFECTED_FILES < <(grep -E "FOUND" "$SCAN_LOG" | awk -F: '{print $1}' | sed 's/[[:space:]]*$//' | sort -u || true)

infected_count="${#INFECTED_FILES[@]}"
echo "[clamav-scan] infected_count=$infected_count clamscan_rc=$CLAMSCAN_RC"

if [[ "$infected_count" -gt 0 ]]; then
  echo "[ERROR] Se detectaron archivos infectados. Cuaraentena: $QUARANTINE_DIR" >&2

  quarantine_timestamp="$(date -u +"%Y%m%d_%H%M%SZ")"
  for f in "${INFECTED_FILES[@]}"; do
    if [[ -z "$f" ]]; then
      continue
    fi
    if [[ -f "$f" ]]; then
      dest="$QUARANTINE_DIR/$(basename "$f")_${quarantine_timestamp}"
      if [[ "$DRY_RUN" == false ]]; then
        mv -- "$f" "$dest"
        echo "[clamav-scan] MOVED: $f -> $dest"
      else
        echo "[DRY-RUN] WOULD MOVE: $f -> $dest"
      fi
    else
      echo "[clamav-scan] Saltando (no existe): $f"
    fi
  done

  # Notificar a gemelos digitales (plantilla; endpoint por defecto del repo).
  if command -v curl >/dev/null 2>&1; then
    infected_files_json="$(printf "%s\n" "${INFECTED_FILES[@]}" | python3 -c 'import sys, json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))' 2>/dev/null || echo '[]')"
    now_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    payload="$(python3 - <<PY
import json
from pathlib import Path

infected_files = json.loads('${infected_files_json}')
scan_log_path = '${SCAN_LOG}'
lines = Path(scan_log_path).read_text(errors='ignore').splitlines()
scan_log_excerpt = '\\n'.join(lines[-200:]) if lines else ''

payload = {
  'event_type': '${EVENT_TYPE}',
  'timestamp': '${now_utc}',
  'severity': '${SEVERITY}',
  'data': {
    'infected_files': infected_files,
    'infected_files_count': ${infected_count},
    'scan_log_excerpt': scan_log_excerpt,
    'action': 'quarantined',
    'quarantine_dir': '${QUARANTINE_DIR}'
  }
}

print(json.dumps(payload, ensure_ascii=False))
PY
)"

    curl -sS -X POST "$NOTIFY_URL" \
      -H "Content-Type: application/json" \
      -d "$payload" >/dev/null || true
    echo "[clamav-scan] Notificacion enviada a gemelos (best-effort)."
  else
    echo "[clamav-scan] curl no disponible; omitiendo notificacion." >&2
  fi

  # Mantener logs para auditoria CI.
  cp -f "$SCAN_LOG" "$LOG_PATH" || true
  exit 1
else
  echo "[clamav-scan] Escaneo completado. Sin infectados."
  cp -f "$SCAN_LOG" "$LOG_PATH" || true
  exit 0
fi

