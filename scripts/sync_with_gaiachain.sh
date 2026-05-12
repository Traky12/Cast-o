#!/bin/bash
set -euo pipefail

# Sincroniza evidencia local (SQLite) con GaiaChain cuando la red vuelve.
# Mantiene la jurisdicción operativa: si no hay red, no se rompe nada.

LOG_FILE="/var/log/castuo/gaiachain_sync.log"
MAX_RETRIES=5
INITIAL_INTERVAL=10
BACKOFF_FACTOR=2
ADMIN_EMAIL="${ADMIN_EMAIL:-}"

log() {
  local msg="$1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $msg" | tee -a "$LOG_FILE"
}

ensure_log_dir() {
  local d
  d="$(dirname "$LOG_FILE")"
  if [ ! -d "$d" ]; then
    mkdir -p "$d" || true
  fi
}

check_gaiachain() {
  if gaiachain version >/dev/null 2>&1; then
    log "✅ GaiaChain disponible"
    return 0
  fi
  log "❌ GaiaChain NO disponible"
  return 1
}

attempt_sync() {
  local attempt=1
  local success=0
  local current_interval=$INITIAL_INTERVAL

  while [ $attempt -le $MAX_RETRIES ]; do
    log "INFO: Intento de sincronización $attempt/$MAX_RETRIES (intervalo: ${current_interval}s)"

    local resp
    resp="$(curl -s -X POST "http://localhost:8001/agents/system/sync-gaiachain" 2>&1 || true)"

    if command -v jq >/dev/null 2>&1; then
      local synced
      local failed
      local total
      synced="$(echo "$resp" | jq -r '.synced // 0')"
      failed="$(echo "$resp" | jq -r '.failed // 0')"
      total="$(echo "$resp" | jq -r '.total // 0')"

      if [ "$synced" -gt 0 ]; then
        log "INFO: Sincronización exitosa: $synced/$total"
        success=1
        break
      fi
      if [ "$failed" -eq 0 ] && [ "$total" -eq 0 ]; then
        log "INFO: No hay operaciones pendientes"
        success=1
        break
      fi

      log "WARN: Sincronización parcial: $synced/$total (fallidos: $failed). Se considera ok parcial."
      success=1
      break
    else
      log "WARN: jq no disponible. Resultado sync: $resp"
      success=1
      break
    fi

    if [ $attempt -lt $MAX_RETRIES ]; then
      sleep "$current_interval"
      current_interval=$((current_interval * BACKOFF_FACTOR))
    fi

    attempt=$((attempt + 1))
  done

  if [ $success -ne 1 ]; then
    log "CRITICAL: Fallo en todos los intentos de sincronización (max: $MAX_RETRIES)."
  fi

  return $success
}

ensure_log_dir
log "=== INICIO DE SINCRONIZACIÓN CON GAIACHAIN ==="

if check_gaiachain; then
  attempt_sync || true
else
  log "WARN: GaiaChain no disponible. Reintentando en 30 segundos..."
  sleep 30
  if check_gaiachain; then
    attempt_sync || true
  else
    log "GaiaChain sigue sin estar disponible. Abortando."
    exit 1
  fi
fi

log "=== FIN DE SINCRONIZACIÓN ==="
exit 0

