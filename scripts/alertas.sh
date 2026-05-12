#!/bin/bash
# CASTÚO-SYSTEM — Alertas críticas: IoT monitors caídos → email
# Uso: cron cada 5 min → */5 * * * * /root/castuo-system/scripts/alertas.sh

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ALERT_EMAIL="${ALERT_EMAIL:-gregorio@castuo.es}"

send_alert() {
  local subject="$1"
  local body="$2"
  if command -v mail >/dev/null 2>&1; then
    echo "$body" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
  fi
  echo "$(date -Iseconds) ALERT: $subject — $body" >> "$REPO_ROOT/backend/logs/alertas.log" 2>/dev/null || true
}

# Solo en Linux con systemctl
if ! command -v systemctl >/dev/null 2>&1; then
  exit 0
fi

DOWN=""
for i in 1 2 3; do
  if ! systemctl is-active --quiet "castuo-iot-coop${i}.service" 2>/dev/null; then
    DOWN="${DOWN} Coop #$i"
  fi
done

if [ -n "$DOWN" ]; then
  send_alert "ALERTA CASTÚO — IoT monitor(s) DOWN" "Servicios caídos:${DOWN}. Revisar: systemctl status castuo-iot-coop*"
fi

exit 0
