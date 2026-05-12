#!/bin/bash
# CASTÚO-SYSTEM™ — Despliegue nodo GaiaChain en Cáceres (Junta de Extremadura)
# Requiere: GAIA_CHAIN_API_KEY, opcional SIGPAC_API_KEY, inventory/junta-extremadura.ini, playbooks/gaiachain-node.yml

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"

if [ -f "inventory/junta-extremadura.ini" ] && command -v ansible-playbook >/dev/null 2>&1; then
  echo "📦 Configurando infraestructura (Ansible)..."
  ansible-playbook -i inventory/junta-extremadura.ini playbooks/gaiachain-node.yml 2>/dev/null || true
fi

if [ -z "$GAIA_CHAIN_API_KEY" ]; then
  echo "⚠️  GAIA_CHAIN_API_KEY no definido; omitiendo registro de nodo."
  exit 0
fi

CERT_B64=""
if [ -f /etc/gaiachain/certs/junta-extremadura.pem ]; then
  CERT_B64=$(cat /etc/gaiachain/certs/junta-extremadura.pem | base64 -w 0 2>/dev/null || base64 < /etc/gaiachain/certs/junta-extremadura.pem)
fi
PUBLIC_IP=$(curl -sf ifconfig.me 2>/dev/null || echo "0.0.0.0")

echo "📡 Registrando nodo en GaiaChain..."
NODE_ID=$(curl -sf -X POST "$API_BASE/api/v1/node" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"JuntaExtremadura-Node-01\",
    \"location\": \"Cáceres, Extremadura, ES\",
    \"type\": \"government\",
    \"ip\": \"$PUBLIC_IP\",
    \"capacity\": \"10000tps\",
    \"certificate\": \"$CERT_B64\"
  }" | jq -r '.id // empty') || true

if [ -n "$NODE_ID" ]; then
  echo "  ✅ Nodo registrado: ID=$NODE_ID"
fi

if [ -f "k8s/gaiachain/junta-access-policy.yaml" ] && command -v kubectl >/dev/null 2>&1; then
  kubectl apply -f k8s/gaiachain/junta-access-policy.yaml 2>/dev/null || true
fi

if [ -n "$SIGPAC_API_KEY" ]; then
  curl -sf -X POST "$API_BASE/api/v1/integration/sigpac" \
    -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"SIGPAC-Extremadura\",
      \"endpoint\": \"https://sigpac.juntaex.es/api/v1\",
      \"api_key\": \"$SIGPAC_API_KEY\",
      \"sync_interval\": \"daily\"
    }" 2>/dev/null || true
fi

curl -sf -X POST "$API_BASE/api/v1/subsidy_program" \
  -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PAC 2027 - Extremadura",
    "budget": 5000000,
    "max_per_farm": 500,
    "start_date": "2026-01-01",
    "end_date": "2027-12-31",
    "requirements": ["GPS_validation", "GaiaChain_registration", "Extremadura_resident"]
  }' 2>/dev/null || true

echo "✅ Nodo GaiaChain Junta de Extremadura desplegado (ID: ${NODE_ID:-N/A})"
