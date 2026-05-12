#!/bin/bash
# Watchdog Nginx CTAEX: reinicia Nginx si no está activo.
# Requiere permisos para systemctl (ejecutar como root o con sudo en el servicio).

LOG_FILE="${LOG_FILE:-/var/log/castuo/nginx_watchdog.log}"

mkdir -p "$(dirname "$LOG_FILE")"

notify() {
  local msg="$1"
  echo "$(date -Iseconds) - $msg" | tee -a "$LOG_FILE"
  [ -n "${NOTIFY_SCRIPT:-}" ] && [ -x "$NOTIFY_SCRIPT" ] && "$NOTIFY_SCRIPT" "[CTAEX Nginx] $msg" || true
}

while true; do
  if ! systemctl is-active --quiet nginx 2>/dev/null; then
    notify "ERROR: Nginx está down. Reiniciando..."
    systemctl restart nginx 2>&1 | tee -a "$LOG_FILE" || true
    sleep 10
  fi
  sleep 60
done
