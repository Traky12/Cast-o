#!/bin/bash
# Watchdog disco CTAEX: alerta si el uso de disco supera el umbral (no reinicia servicios).

THRESHOLD="${DISK_THRESHOLD:-90}"
LOG_FILE="${LOG_FILE:-/var/log/castuo/disk_watchdog.log}"
CHECK_INTERVAL="${DISK_CHECK_INTERVAL:-300}"

mkdir -p "$(dirname "$LOG_FILE")"

notify() {
  local msg="$1"
  echo "$(date -Iseconds) - $msg" | tee -a "$LOG_FILE"
  [ -n "${NOTIFY_SCRIPT:-}" ] && [ -x "$NOTIFY_SCRIPT" ] && "$NOTIFY_SCRIPT" "[CTAEX Disco] $msg" || true
}

while true; do
  usage=$(df -P / 2>/dev/null | awk 'NR==2 {print $5}' | tr -d '%')
  if [ -n "$usage" ] && [ "$usage" -ge "$THRESHOLD" ] 2>/dev/null; then
    notify "ALERTA: Uso de disco ${usage}% (umbral ${THRESHOLD}%). Liberar espacio."
  fi
  sleep "$CHECK_INTERVAL"
done
