#!/bin/bash
set -euo pipefail

# Protocolo de Continuidad Crítica (>24h offline) para resiliencia extrema.
# Entorno esperado: Linux con `curl`, `jq` (opcional) y `mail` (opcional).

ADMIN_EMAIL="${ADMIN_EMAIL:-emergency@castuo-system.com}"
EMERGENCY_CONTACTS=(
  "gregorio@castuo-system.com"
  "soporte@castuo-system.com"
  "legal@castuo-system.com"
)

BACKUP_NODES=(
  "backup1.castuo-system.com"
  "backup2.castuo-system.com"
)

CRITICAL_THRESHOLD="${CRITICAL_THRESHOLD:-50}"
OFFLINE_HOURS_THRESHOLD="${OFFLINE_HOURS_THRESHOLD:-24}"

LOG_FILE="${LOG_FILE:-/var/log/castuo/emergency.log}"

ensure_log_dir() {
  local d
  d="$(dirname "$LOG_FILE")"
  if [ ! -d "$d" ]; then
    mkdir -p "$d" >/dev/null 2>&1 || true
  fi
}

log_emergency() {
  local message="$1"
  ensure_log_dir
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [EMERGENCY] $message" | tee -a "$LOG_FILE"

  if command -v mail >/dev/null 2>&1; then
    for contact in "${EMERGENCY_CONTACTS[@]}"; do
      echo "$message" | mail -s "🚨 EMERGENCIA CASTÚO-SYSTEM" "$contact" >/dev/null 2>&1 || true
    done
  fi
}

SERVER_URL="${SERVER_URL:-http://localhost:8001/agents/system/health}"

check_critical() {
  local health_status
  health_status="$(curl -s "$SERVER_URL" 2>/dev/null || echo '{}')"

  if ! command -v jq >/dev/null 2>&1; then
    # Sin jq, no podemos evaluar con precisión: mantenemos modo seguro (no activa automáticamente).
    return 1
  fi

  local gaiachain_status
  local pending_ops
  local last_sync

  gaiachain_status="$(echo "$health_status" | jq -r '.components.gaiachain.status // "unknown"')"
  pending_ops="$(echo "$health_status" | jq -r '.components.gaiachain.pending_operations // 0')"
  last_sync="$(echo "$health_status" | jq -r '.components.gaiachain.last_sync_attempt // ""')"

  # Si no hay last_sync, asumimos crítico tras umbral.
  local last_sync_ts
  last_sync_ts="$(date -d "$last_sync" +%s 2>/dev/null || echo 0)"
  local now_ts
  now_ts="$(date +%s)"

  local hours_offline=0
  if [ "$last_sync_ts" -gt 0 ]; then
    hours_offline=$(( (now_ts - last_sync_ts) / 3600 ))
  else
    hours_offline="$OFFLINE_HOURS_THRESHOLD"
  fi

  if [ "$gaiachain_status" == "offline" ] && [ "$pending_ops" -gt "$CRITICAL_THRESHOLD" ] && [ "$hours_offline" -gt "$OFFLINE_HOURS_THRESHOLD" ]; then
    return 0
  fi

  return 1
}

activate_protocol() {
  log_emergency "🚨 INICIANDO PROTOCOLO DE CONTINUIDAD CRÍTICA"

  local health_json
  health_json="$(curl -s "$SERVER_URL" 2>/dev/null || echo '{}')"

  local report_file
  report_file="/var/log/castuo/emergency_report_$(date +%Y%m%d%H%M%S).json"
  ensure_log_dir
  echo "$health_json" > "$report_file"

  # Intento de sincronización con nodos de respaldo (simulado: solo evidencia).
  for node in "${BACKUP_NODES[@]}"; do
    log_emergency "Intentando sincronización con nodo de respaldo: $node"
    sleep 2
  done

  if command -v mail >/dev/null 2>&1; then
    for contact in "${EMERGENCY_CONTACTS[@]}"; do
      echo "Se ha activado el Protocolo de Continuidad Crítica en CASTÚO-SYSTEM. Adjunto: $report_file" \
        | mail -s "🚨 PROTOCOLO DE EMERGENCIA ACTIVADO" -a "$report_file" "$contact" >/dev/null 2>&1 || true
    done
  fi

  # Registrar evento en el sistema (endpoint en runtime).
  curl -s -X POST "http://localhost:8001/agents/system/log-event" \
    -H "Content-Type: application/json" \
    -d "{\"event_type\":\"emergency_protocol_activated\",\"details\":\"$report_file\",\"severity\":\"critical\"}" \
    >/dev/null 2>&1 || true

  log_emergency "Protocolo de emergencia completado."
}

if check_critical; then
  echo "✅ Sistema operativo (no se requiere acción)."
  exit 0
else
  activate_protocol
  exit 1
fi

