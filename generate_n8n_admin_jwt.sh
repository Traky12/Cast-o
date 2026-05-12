#!/usr/bin/env bash
# generate_n8n_admin_jwt.sh
#
# Genera N8N_ADMIN_JWT automáticamente una vez Keycloak está levantado.
#
# Requisitos:
# - Curl disponible en el host
# - jq opcional (se usa si existe; si no, se extrae con fallback)
# - En `.env` deben existir:
#   - KEYCLOAK_CLIENT_SECRET
#   - Opcional: KEYCLOAK_CLIENT_ID (default: n8n-admin)
# - El client `n8n-admin` y su rol `admin` deben existir en Keycloak.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

ENV_FILE="${ENV_FILE:-.env}"
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ No existe $ENV_FILE. Primero ejecuta ./generate_credentials.sh"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl no está instalado en el host."
  exit 1
fi

KEYCLOAK_BASE_URL="${KEYCLOAK_BASE_URL:-http://localhost:8080}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-castuo-system}"
KEYCLOAK_CLIENT_ID="$(grep -E '^KEYCLOAK_CLIENT_ID=' "$ENV_FILE" | cut -d'=' -f2- || true)"
KEYCLOAK_CLIENT_ID="${KEYCLOAK_CLIENT_ID:-n8n-admin}"
KEYCLOAK_CLIENT_SECRET="$(grep -E '^KEYCLOAK_CLIENT_SECRET=' "$ENV_FILE" | cut -d'=' -f2- || true)"

if [ -z "$KEYCLOAK_CLIENT_SECRET" ]; then
  echo "❌ KEYCLOAK_CLIENT_SECRET no encontrado en $ENV_FILE"
  exit 1
fi

echo "🔍 Esperando a que Keycloak esté disponible en: $KEYCLOAK_BASE_URL"
echo "    Realm: $KEYCLOAK_REALM"

# Espera con timeout.
deadline=$(( $(date +%s) + 300 ))
while true; do
  if curl -fsS "$KEYCLOAK_BASE_URL/auth/realms/master" >/dev/null 2>&1; then
    break
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "❌ Timeout esperando Keycloak. Revisa logs: docker logs keycloak"
    exit 1
  fi
  sleep 2
done

echo "✅ Keycloak está disponible."

echo "🔑 Generando N8N_ADMIN_JWT para client_id='$KEYCLOAK_CLIENT_ID'..."

RESP="$(curl -sS -X POST \
  -d "client_id=${KEYCLOAK_CLIENT_ID}" \
  -d "client_secret=${KEYCLOAK_CLIENT_SECRET}" \
  -d "grant_type=client_credentials" \
  "${KEYCLOAK_BASE_URL}/auth/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token" || true)"

# Extraer access_token (jq si existe; fallback por regex).
if command -v jq >/dev/null 2>&1; then
  N8N_ADMIN_JWT="$(printf '%s' "$RESP" | jq -r '.access_token // empty' 2>/dev/null || true)"
else
  N8N_ADMIN_JWT="$(printf '%s' "$RESP" | sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1 || true)"
fi

if [ -z "$N8N_ADMIN_JWT" ] || [ "$N8N_ADMIN_JWT" = "null" ]; then
  echo "❌ No se pudo generar N8N_ADMIN_JWT."
  echo "Respuesta (recorte):"
  printf '%s\n' "$RESP" | head -c 500
  echo
  echo "Causas típicas:"
  echo " - El client '${KEYCLOAK_CLIENT_ID}' no existe."
  echo " - Falta asignar rol 'admin' al client (en realm '${KEYCLOAK_REALM}')."
  exit 1
fi

# Actualiza o añade N8N_ADMIN_JWT en .env sin destruir el resto.
if grep -qE '^N8N_ADMIN_JWT=' "$ENV_FILE"; then
  # shellcheck disable=SC2002
  sed -i.bak -e "s/^N8N_ADMIN_JWT=.*/N8N_ADMIN_JWT=${N8N_ADMIN_JWT}/" "$ENV_FILE"
  rm -f "${ENV_FILE}.bak" || true
else
  printf '\nN8N_ADMIN_JWT=%s\n' "$N8N_ADMIN_JWT" >> "$ENV_FILE"
fi

echo "✅ N8N_ADMIN_JWT generado y escrito en $ENV_FILE"

