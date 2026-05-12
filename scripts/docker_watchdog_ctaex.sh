#!/bin/bash
# Watchdog Docker CTAEX: comprueba que backend, frontend, postgres y mqtt estén running; reinicia si no.
# Ejecutar desde la raíz del repo o definir REPO_ROOT y COMPOSE_FILE.
# Uso como servicio systemd: ver docs/CTAEX-WATCHDOGS-MONITORING.md

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-$REPO_ROOT/docker/docker-compose.ctaex.yml}"
LOG_FILE="${LOG_FILE:-/var/log/castuo/docker_watchdog.log}"
SERVICES="backend frontend postgres mqtt"

mkdir -p "$(dirname "$LOG_FILE")"

notify() {
  local msg="$1"
  echo "$(date -Iseconds) - $msg" | tee -a "$LOG_FILE"
  [ -n "${NOTIFY_SCRIPT:-}" ] && [ -x "$NOTIFY_SCRIPT" ] && "$NOTIFY_SCRIPT" "[CTAEX Docker] $msg" || true
}

while true; do
  for service in $SERVICES; do
    status=$(docker compose -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null | xargs -r docker inspect -f '{{.State.Status}}' 2>/dev/null || echo "missing")
    if [ "$status" != "running" ]; then
      notify "ERROR: $service está $status. Reiniciando..."
      docker compose -f "$COMPOSE_FILE" up -d "$service" 2>&1 | tee -a "$LOG_FILE" || true
      sleep 15
    fi
  done
  sleep 60
done
