#!/usr/bin/env bash
# Notifica al Trillizo (webhook) un evento de auditoría sin modificar claves ni reiniciar n8n.
# Uso en servidor Linux/WSL:
#   TRILLIZO_WEBHOOK_BASE=http://n8n-trillizo:5678 bash scripts/n8n/trillizo_audit_notify.sh rotation_scheduled
#   TRILLIZO_WEBHOOK_BASE=http://localhost:5682 CASTUO_FORWARD_API_KEY=... bash scripts/n8n/trillizo_audit_notify.sh manual_review

set -euo pipefail
EVENT_TYPE="${1:-audit_event}"
BASE="${TRILLIZO_WEBHOOK_BASE:-http://localhost:5682}"
BASE="${BASE%/}"
URL="${BASE}/webhook/audit-rotation"
PAYLOAD=$(printf '{"event":"%s","source":"trillizo_audit_notify","ts":"%s"}' "$EVENT_TYPE" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")")

args=( -sS -X POST "$URL" -H "Content-Type: application/json" -d "$PAYLOAD" )
if [[ -n "${CASTUO_FORWARD_API_KEY:-}" ]]; then
  args+=( -H "X-API-KEY: ${CASTUO_FORWARD_API_KEY}" )
fi

curl "${args[@]}"
echo
