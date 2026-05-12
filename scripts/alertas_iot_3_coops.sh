#!/bin/bash
# CASTÚO-SYSTEM — Alertas automáticas IoT 3 cooperativas (systemd, MQTT, NFT growth, facturación)
# Uso: cron */5 * * * * /root/castuo-system/scripts/alertas_iot_3_coops.sh

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"
ALERTAS_ENVIADAS=0
EMAIL="${ALERT_EMAIL:-gregorio@castuo.es}"
FECHA=$(date +"%Y-%m-%d %H:%M")
API="${API_URL:-http://localhost:8001}"
LOG_FILE="$REPO_ROOT/backend/logs/alertas.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true

echo "🚨 ALERTAS IoT 3 COOPS - $FECHA" >> "$LOG_FILE" 2>/dev/null || true

_send() {
  local subject="$1"
  local body="$2"
  if command -v mail >/dev/null 2>&1; then
    echo "$body" | mail -s "$subject" "$EMAIL" 2>/dev/null || true
  fi
  echo "$(date +"%Y-%m-%d %H:%M") $body" >> "$LOG_FILE" 2>/dev/null || true
}

# 1. Verificar servicios systemd
if command -v systemctl >/dev/null 2>&1; then
  for i in 1 2 3; do
    if ! systemctl is-active --quiet "castuo-iot-coop${i}.service" 2>/dev/null; then
      _send "🚨 CASTÚO-SYSTEM Coop #$i OFFLINE" "CRÍTICO: Coop #$i DOWN — systemctl start castuo-iot-coop${i}.service"
      ALERTAS_ENVIADAS=$((ALERTAS_ENVIADAS + 1))
    fi
  done
fi

# 2. Monitorear sensores MQTT (esperar 1 mensaje con timeout 30s por coop)
for coop in "sabionda_educa_sat" "cooperativa_2" "cooperativa_3"; do
  if command -v mosquitto_sub >/dev/null 2>&1; then
    LAST_SENSOR=$(timeout 30 mosquitto_sub -h localhost -t "hidroponia/$coop/sensors" -C 1 2>/dev/null | tail -1)
    if [ -z "$LAST_SENSOR" ]; then
      _send "⚠️ CASTÚO IoT $coop SILENCIO" "AVISO: $coop sin datos MQTT (30s)"
      ALERTAS_ENVIADAS=$((ALERTAS_ENVIADAS + 1))
    fi
  fi
done

# 3. Verificar NFT growth (mínimo 9%)
for token in 1 2 3; do
  GROWTH=$(curl -s "$API/nft/status/$token" 2>/dev/null | jq -r '.growth // 0' 2>/dev/null)
  if [ -z "$GROWTH" ] || [ "$GROWTH" = "null" ]; then
    GROWTH=0
  fi
  if command -v bc >/dev/null 2>&1; then
    if [ "$(echo "$GROWTH < 9" | bc 2>/dev/null)" = "1" ]; then
      _send "⚠️ CASTÚO NFT #$token Growth Alert" "AVISO: Token #$token growth bajo: ${GROWTH}% (mín 10%)"
      ALERTAS_ENVIADAS=$((ALERTAS_ENVIADAS + 1))
    fi
  else
    G_INT=${GROWTH%%.*}
    if [ -n "$G_INT" ] && [ "$G_INT" -lt 9 ] 2>/dev/null; then
      _send "⚠️ CASTÚO NFT #$token Growth Alert" "AVISO: Token #$token growth bajo: ${GROWTH}% (mín 10%)"
      ALERTAS_ENVIADAS=$((ALERTAS_ENVIADAS + 1))
    fi
  fi
done

# 4. Verificar facturación (mínimo €1.000/mes)
FACT_JSON=$(curl -s "$API/billing/facturacion" 2>/dev/null)
FACT_TOTAL=$(echo "$FACT_JSON" | jq -r '([.[].total_eur] | add) // 0' 2>/dev/null)
if [ -z "$FACT_TOTAL" ]; then
  FACT_TOTAL=0
fi
if command -v bc >/dev/null 2>&1; then
  if [ "$(echo "$FACT_TOTAL < 1000" | bc 2>/dev/null)" = "1" ]; then
    _send "⚠️ CASTÚO Facturación Alert" "AVISO: Facturación baja €${FACT_TOTAL} (mín €1.000/mes)"
    ALERTAS_ENVIADAS=$((ALERTAS_ENVIADAS + 1))
  fi
else
  F_INT=${FACT_TOTAL%%.*}
  if [ -n "$F_INT" ] && [ "$F_INT" -lt 1000 ] 2>/dev/null; then
    _send "⚠️ CASTÚO Facturación Alert" "AVISO: Facturación baja €${FACT_TOTAL} (mín €1.000/mes)"
    ALERTAS_ENVIADAS=$((ALERTAS_ENVIADAS + 1))
  fi
fi

echo "📊 $ALERTAS_ENVIADAS alertas enviadas - $FECHA" >> "$LOG_FILE" 2>/dev/null || true
exit 0
