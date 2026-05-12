#!/bin/bash
# Watchdog PostgreSQL CTAEX: comprueba pg_isready en el contenedor; reinicia el servicio si no responde.

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-$REPO_ROOT/docker/docker-compose.ctaex.yml}"
LOG_FILE="${LOG_FILE:-/var/log/castuo/postgres_watchdog.log}"

mkdir -p "$(dirname "$LOG_FILE")"

notify() {
  local msg="$1"
  echo "$(date -Iseconds) - $msg" | tee -a "$LOG_FILE"
  [ -n "${NOTIFY_SCRIPT:-}" ] && [ -x "$NOTIFY_SCRIPT" ] && "$NOTIFY_SCRIPT" "[CTAEX PostgreSQL] $msg" || true
}

while true; do
  if ! docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U castuo_admin 2>/dev/null; then
    notify "ERROR: PostgreSQL no responde. Reiniciando contenedor postgres..."
    docker compose -f "$COMPOSE_FILE" restart postgres 2>&1 | tee -a "$LOG_FILE" || true
    sleep 15
  fi
  sleep 60
done
