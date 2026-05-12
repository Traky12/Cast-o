#!/bin/bash
# Watchdog MQTT (Mosquitto) CTAEX: comprueba que el proceso mosquitto esté vivo en el contenedor; reinicia si no.

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-$REPO_ROOT/docker/docker-compose.ctaex.yml}"
LOG_FILE="${LOG_FILE:-/var/log/castuo/mqtt_watchdog.log}"

mkdir -p "$(dirname "$LOG_FILE")"

notify() {
  local msg="$1"
  echo "$(date -Iseconds) - $msg" | tee -a "$LOG_FILE"
  [ -n "${NOTIFY_SCRIPT:-}" ] && [ -x "$NOTIFY_SCRIPT" ] && "$NOTIFY_SCRIPT" "[CTAEX MQTT] $msg" || true
}

while true; do
  if ! docker compose -f "$COMPOSE_FILE" exec -T mqtt sh -c "pidof mosquitto >/dev/null 2>&1" 2>/dev/null; then
    notify "ERROR: MQTT (mosquitto) no responde. Reiniciando contenedor mqtt..."
    docker compose -f "$COMPOSE_FILE" restart mqtt 2>&1 | tee -a "$LOG_FILE" || true
    sleep 15
  fi
  sleep 60
done
