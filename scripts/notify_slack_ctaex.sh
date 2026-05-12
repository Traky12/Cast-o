#!/bin/bash
# Envía notificación a Slack (webhook). Uso: ./notify_slack_ctaex.sh "Mensaje de alerta"
# Definir SLACK_WEBHOOK_URL en el entorno o en .env del servidor.

WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
MESSAGE="${1:-Test CASTUO-CTAEX}"

if [ -z "$WEBHOOK_URL" ]; then
  echo "SLACK_WEBHOOK_URL no definido. Mensaje: $MESSAGE" >&2
  exit 0
fi

if command -v jq >/dev/null 2>&1; then
  payload=$(jq -n --arg msg "$MESSAGE" '{text: $msg, username: "CASTUO-CTAEX Alert", icon_emoji: ":rotating_light:"}')
  curl -sS -X POST -H 'Content-type: application/json' --data "$payload" "$WEBHOOK_URL" >/dev/null || true
else
  curl -sS -X POST -H 'Content-type: application/json' --data "{\"text\":\"$MESSAGE\"}" "$WEBHOOK_URL" >/dev/null || true
fi
