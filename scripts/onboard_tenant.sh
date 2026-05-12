#!/usr/bin/env bash
# ============================================================
# scripts/onboard_tenant.sh — Onboarding de nuevo tenant
# Uso: ./scripts/onboard_tenant.sh <tenant_id> <tenant_name>
# ============================================================
set -euo pipefail

TENANT_ID="${1:-}"
TENANT_NAME="${2:-}"

if [[ -z "$TENANT_ID" || -z "$TENANT_NAME" ]]; then
  echo "Uso: $0 <tenant_id> <tenant_name>"
  exit 1
fi

# Validar tenant_id (solo alfanumérico y guion)
if [[ ! "$TENANT_ID" =~ ^[a-z0-9-]+$ ]]; then
  echo "❌ tenant_id debe ser alfanumérico en minúsculas (puede contener guiones)"
  exit 1
fi

echo "🚀 Iniciando onboarding para tenant: $TENANT_ID ($TENANT_NAME)"

# ─────────────────────────────────────────────────────────────
# 1. Desplegar ConfigMap + Deployment + Ingress en Kubernetes
# ─────────────────────────────────────────────────────────────
export TENANT_ID="$TENANT_ID"
export TENANT_NAME="$TENANT_NAME"

if command -v kubectl &>/dev/null; then
  echo "📦 Aplicando manifiestos Kubernetes..."
  envsubst < k8s/tenant-template.yaml | kubectl apply -f - -n castuo-system
  echo "✅ Manifiestos desplegados"
else
  echo "⚠️  kubectl no disponible. Omitiendo despliegue Kubernetes."
fi

# ─────────────────────────────────────────────────────────────
# 2. Crear esquema en TimescaleDB
# ─────────────────────────────────────────────────────────────
if [[ -n "${TIMESCALE_DB_HOST:-}" && -n "${TIMESCALE_DB_PASSWORD:-}" ]]; then
  echo "🗄️  Creando esquema tenant_${TENANT_ID} en TimescaleDB..."
  PGPASSWORD="$TIMESCALE_DB_PASSWORD" psql \
    -h "${TIMESCALE_DB_HOST}" \
    -U "${TIMESCALE_DB_USER:-castuo_iot}" \
    -d "${TIMESCALE_DB_NAME:-castuo_telemetry}" \
    -c "CREATE SCHEMA IF NOT EXISTS tenant_${TENANT_ID};" \
    -c "GRANT USAGE ON SCHEMA tenant_${TENANT_ID} TO ${TIMESCALE_DB_USER:-castuo_iot};"
  echo "✅ Esquema creado"
else
  echo "⚠️  TIMESCALE_DB_HOST/PASSWORD no configurados. Omitiendo creación de esquema."
fi

# ─────────────────────────────────────────────────────────────
# 3. Crear usuario MQTT en Mosquitto (si está disponible)
# ─────────────────────────────────────────────────────────────
if command -v docker &>/dev/null && docker ps --filter name=mosquitto -q | grep -q .; then
  MQTT_PASS="$(openssl rand -hex 16)"
  echo "📡 Creando usuario MQTT para tenant ${TENANT_ID}..."
  docker exec mosquitto mosquitto_ctrl add-user "${TENANT_ID}" "${MQTT_PASS}" 2>/dev/null || true
  docker exec mosquitto mosquitto_ctrl set-acl "${TENANT_ID}" "castuo/${TENANT_ID}/#" "readwrite" 2>/dev/null || true
  echo "✅ Usuario MQTT: ${TENANT_ID}"
else
  echo "⚠️  Mosquitto no disponible. Omitiendo creación de usuario MQTT."
fi

# ─────────────────────────────────────────────────────────────
# 4. Generar JWT de acceso para el tenant
# ─────────────────────────────────────────────────────────────
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"

TENANT_JWT=$(python3 - <<PYEOF
import jwt, datetime, sys
payload = {
    "sub": "${TENANT_ID}",
    "role": "tenant_admin",
    "tenant": "${TENANT_ID}",
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365),
}
try:
    token = jwt.encode(payload, "${JWT_SECRET}", algorithm="HS256")
    print(token)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
)

# ─────────────────────────────────────────────────────────────
# 5. Resumen
# ─────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════"
echo "✅ Tenant '$TENANT_ID' ($TENANT_NAME) creado"
echo "════════════════════════════════════════════════"
echo "🔑 JWT API: $TENANT_JWT"
echo "📡 MQTT Topic: castuo/$TENANT_ID/#"
echo "🌐 URL API: https://$TENANT_ID.api.castuo-system.cloud"
echo "════════════════════════════════════════════════"
