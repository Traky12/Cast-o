#!/bin/bash
# scripts/Setup-AEMPS-Webhook-Staging.sh
#
# Staging: crea/usa AEMPS_WEBHOOK_SECRET y prueba POST /api/aemps/webhook
# con validacion de firma local (sin dependencia real de AEMPS externa).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.staging.yml}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env.staging}"

BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_URL="${BACKEND_URL:-http://localhost:$BACKEND_PORT}"
WEBHOOK_URL="$BACKEND_URL/api/aemps/webhook"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "No existe $COMPOSE_FILE" >&2
  exit 1
fi

# 1) Crear/asegurar env-file staging
if [[ ! -f "$ENV_FILE" ]]; then
  touch "$ENV_FILE"
fi

if ! grep -q "^AEMPS_WEBHOOK_SECRET=" "$ENV_FILE"; then
  AEMPS_WEBHOOK_SECRET="$(openssl rand -hex 32)"
  echo "AEMPS_WEBHOOK_SECRET=$AEMPS_WEBHOOK_SECRET" >> "$ENV_FILE"
else
  AEMPS_WEBHOOK_SECRET="$(sed -n 's/^AEMPS_WEBHOOK_SECRET=//p' "$ENV_FILE" | tail -n 1)"
fi

echo "AEMPS_WEBHOOK_SECRET (staging) configurado."

# 2) Reiniciar backend en staging
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d backend

sleep 2

# 3) Probar webhook con evento simulado
payload='{"event_type":"test","trial_id":"CT-2026-001","status":"test_successful","timestamp":"'"$(date -u +"%Y-%m-%dT%H:%M:%SZ")"'","environment":"staging"}'

expected_sig="$(printf "%s%s" "$payload" "$AEMPS_WEBHOOK_SECRET" | sha256sum | awk '{print $1}')"

echo "Probando webhook en $WEBHOOK_URL ..."
resp="$(curl -sS -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-AEMPS-Event: test" \
  -H "X-AEMPS-Signature: $expected_sig" \
  -d "$payload")"

if command -v jq >/dev/null 2>&1; then
  echo "$resp" | jq .
else
  echo "$resp"
fi

echo "Webhook staging verificado (firma OK)."

