#!/usr/bin/env bash
# deploy_zero_leak_hetzner_1click.sh
# 1-click: genera credenciales -> levanta stack endurecido -> valida TRL9.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

chmod +x ./generate_credentials.sh || true
./generate_credentials.sh

if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  echo "❌ Ni `docker-compose` ni `docker compose` disponibles."
  exit 1
fi

echo "🚀 Paso 1/3: levantando Keycloak + Postgres + backend..."
$DC -f docker-compose.hetzner.zero-leak.yml up -d --build postgres keycloak backend mosquitto mosquitto-setup prometheus grafana || true

echo "🔑 Paso 2/3: generando N8N_ADMIN_JWT desde Keycloak..."
chmod +x ./generate_n8n_admin_jwt.sh || true
./generate_n8n_admin_jwt.sh

echo "🌐 Paso 3/3: levantando n8n..."
$DC -f docker-compose.hetzner.zero-leak.yml up -d --build n8n

echo "🔒 Validando workflow TRL9 con hardener..."
python scripts/harden_n8n_flow.py \
  --input n8n/workflows/zero_leak_encrypt_forward_v2.json \
  --fail-on-violation

echo "✅ 1-click completado (TRL9 validado)."
echo "📌 Ahora ya tienes `N8N_ADMIN_JWT` en .env. Siguiente: importar/activar el workflow en n8n y probar feedback loop."

