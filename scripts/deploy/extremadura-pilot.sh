#!/bin/bash
# CASTÚO-SYSTEM™ — Despliegue piloto en cooperativas extremeñas (Fase 1, 2026)
# Requiere: GAIA_CHAIN_API_KEY, SABIONDA_API_KEY (opc.), inventory/extremadura.ini, playbooks/iot-deploy.yml
# Uso: desde repo root, ./scripts/deploy/extremadura-pilot.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

COOPERATIVES=("Agraria Badajoz" "Copagro Mérida" "Cooperativa Trujillo")
API_BASE="${GAIA_CHAIN_API_URL:-https://gaiachain.castuo-system.com}"
SABIONDA_BASE="${SABIONDA_API_URL:-https://sabionda.agro}"

for coop in "${COOPERATIVES[@]}"; do
  echo "🌱 Configurando IoT en $coop..."

  if [ -f "inventory/extremadura.ini" ] && command -v ansible-playbook >/dev/null 2>&1; then
    ansible-playbook -i inventory/extremadura.ini playbooks/iot-deploy.yml --limit "$coop" 2>/dev/null || true
  fi

  if [ -n "$GAIA_CHAIN_API_KEY" ]; then
    COOP_ID=$(curl -sf -X POST "$API_BASE/api/v1/cooperative" \
      -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"name\":\"$coop\",\"region\":\"Extremadura\",\"gln\":\"0614141$(printf "%05d" $RANDOM)\"}" | jq -r '.id // empty') || true
    if [ -n "$COOP_ID" ]; then
      for sensor in $(seq 1 6); do
        curl -sf -X POST "$API_BASE/api/v1/sensor" \
          -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
          -H "Content-Type: application/json" \
          -d "{\"cooperative_id\":\"$COOP_ID\",\"sensor_id\":\"$coop-$sensor\",\"type\":\"libelium\",\"location\":\"Extremadura\"}" 2>/dev/null || true
      done
      WALLET=$(curl -sf -X POST "$API_BASE/api/v1/wallet" \
        -H "Authorization: Bearer $GAIA_CHAIN_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"cooperative_id\":\"$COOP_ID\",\"type\":\"cooperative\"}" | jq -r '.address // empty') || true
      echo "  ✅ $coop: COOP_ID=$COOP_ID, Wallet=$WALLET"
    fi
  fi
done

if [ -f "k8s/gaiachain/extremadura-node.yaml" ] && command -v kubectl >/dev/null 2>&1; then
  echo "📦 Desplegando nodo GaiaChain (Extremadura)..."
  kubectl apply -f k8s/gaiachain/extremadura-node.yaml 2>/dev/null || true
fi

if [ -n "$SABIONDA_API_KEY" ]; then
  echo "🎓 Inscripción formación agricultores..."
  for coop in "${COOPERATIVES[@]}"; do
    curl -sf -X POST "$SABIONDA_BASE/api/v1/course/enroll" \
      -H "Authorization: Bearer $SABIONDA_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"cooperative\":\"$coop\",\"course\":\"agrovoltaica-extremadura\",\"language\":\"es\",\"certificate_type\":\"nft\"}" 2>/dev/null || true
  done
fi

echo "🚀 Piloto en Extremadura desplegado (completar con APIs reales y Ansible según entorno)."
