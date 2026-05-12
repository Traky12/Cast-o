#!/bin/bash
set -euo pipefail

# Monitor crítico de resiliencia (GaiaChain + recursos).
# Diseñado para entornos Linux; en Windows usa Task Scheduler equivalente.

ADMIN_EMAIL="${ADMIN_EMAIL:-tu@email.com}"
LOG_FILE="${LOG_FILE:-/var/log/castuo/monitor_critical.log}"
CRITICAL_THRESHOLD="${CRITICAL_THRESHOLD:-5}"
ERROR_THRESHOLD="${ERROR_THRESHOLD:-3}"

ensure_log_dir() {
  local d
  d="$(dirname "$LOG_FILE")"
  if [ ! -d "$d" ]; then
    mkdir -p "$d" >/dev/null 2>&1 || true
  fi
}

send_alert() {
  local subject="$1"
  local message="$2"
  ensure_log_dir
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $subject - $message" | tee -a "$LOG_FILE"

  # Notificación opcional: si no existe `mail`, no falla.
  if command -v mail >/dev/null 2>&1; then
    echo "$message" | mail -s "$subject" "$ADMIN_EMAIL" >/dev/null 2>&1 || true
  fi
}

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=1
fi

SERVER_URL="${SERVER_URL:-http://localhost:8001/agents/system/health}"

# 1) Verifica que el servidor responda
http_code="$(curl -s -o /dev/null -w \"%{http_code}\" -I "$SERVER_URL" || echo 0)"
if [ "$http_code" != "200" ]; then
  send_alert "❌ ALERTA CRÍTICA" "El endpoint $SERVER_URL no responde (HTTP $http_code)."
  exit 1
fi

health_json="$(curl -s "$SERVER_URL" || echo '{}')"

if [ "$HAS_JQ" -ne 1 ]; then
  send_alert "⚠️ Monitor (sin jq)" "jq no está disponible; imprimimos payload: $health_json"
  exit 0
fi

gaia_status="$(echo "$health_json" | jq -r '.components.gaiachain.status // empty')"
pending_ops="$(echo "$health_json" | jq -r '.components.gaiachain.pending_operations // 0')"
disk_usage="$(echo "$health_json" | jq -r '.components.storage.disk_usage // "0%"' | tr -d '%')"
memory_usage="$(echo "$health_json" | jq -r '.components.storage.memory_usage // "0%"' | tr -d '%')"
critical_events_count="$(echo "$health_json" | jq '.critical_events | length // 0')"

if [ "$gaia_status" == "offline" ] && [ "${pending_ops}" -gt "$CRITICAL_THRESHOLD" ]; then
  send_alert "❌ GaiaChain offline con cola" "GaiaChain offline y $pending_ops operaciones pendientes."
elif [ "$gaia_status" == "offline" ]; then
  send_alert "⚠️ GaiaChain offline" "GaiaChain offline. Operaciones pendientes: $pending_ops."
fi

if [ "${disk_usage}" -gt 90 ]; then
  send_alert "❌ Disco casi lleno" "Disco al ${disk_usage}%."
elif [ "${disk_usage}" -gt 80 ]; then
  send_alert "⚠️ Disco al alza" "Disco al ${disk_usage}%. Monitorea espacio."
fi

if [ "${memory_usage}" -gt 90 ]; then
  send_alert "❌ Memoria alta" "Uso memoria ${memory_usage}%."
elif [ "${memory_usage}" -gt 80 ]; then
  send_alert "⚠️ Memoria alta" "Uso memoria ${memory_usage}%. Monitorea rendimiento."
fi

if [ "${critical_events_count}" -gt "$ERROR_THRESHOLD" ]; then
  send_alert "⚠️ Eventos críticos recientes" "Eventos críticos: ${critical_events_count}."
fi

exit 0

