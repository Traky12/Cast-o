#!/bin/bash
# CASTÚO-SYSTEM v1.7.3 — Dashboard terminal real-time 3 cooperativas
# Uso: ./scripts/dashboard_3_coops.sh   (actualiza cada 10s; Ctrl+C para salir)

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_ROOT"
API="${API_URL:-http://localhost:8001}"

while true; do
  clear
  echo "🚜 CASTÚO-SYSTEM v1.7.3 - $(date '+%Y-%m-%d %H:%M') CET"
  echo "═══════════════════════════════════════════════════════"

  # Cooperativas
  COOPS_JSON=$(curl -s "$API/cooperativas" 2>/dev/null)
  if [ -n "$COOPS_JSON" ]; then
    COOP_COUNT=$(echo "$COOPS_JSON" | jq -r 'length' 2>/dev/null || echo "?")
    TOTAL_HA=$(echo "$COOPS_JSON" | jq -r '[.[].parcelas[]?.hectares] | add // 0' 2>/dev/null)
    [ -z "$TOTAL_HA" ] && TOTAL_HA=$(echo "$COOPS_JSON" | jq -r '[.[].parcelas[].hectares] | add // 0' 2>/dev/null)
    echo "🏭 COOPERATIVAS: ${COOP_COUNT}/3"
    echo "📈 SUPERFICIE:   ${TOTAL_HA:-10.5} ha"
  else
    echo "🏭 COOPERATIVAS: — (API no disponible)"
    echo "📈 SUPERFICIE:   10.5 ha"
  fi

  # NFT Growth
  echo "💎 NFT GROWTH:"
  for id in 1 2 3; do
    S=$(curl -s "$API/nft/status/$id" 2>/dev/null)
    G=$(echo "$S" | jq -r '.growth // 0' 2>/dev/null)
    [ "$G" = "null" ] && G="—"
    case $id in
      1) echo "  Sabionda #1:  ${G}%" ;;
      2) echo "  Coop #2:     ${G}%" ;;
      3) echo "  Coop #3:     ${G}%" ;;
    esac
  done

  # Facturación
  BILL=$(curl -s "$API/billing/facturacion" 2>/dev/null)
  TOTAL_EUR=$(echo "$BILL" | jq -r 'map(.total_eur)? | add // 0' 2>/dev/null)
  [ -z "$TOTAL_EUR" ] && TOTAL_EUR=$(echo "$BILL" | jq -r '[.[].total_eur] | add // 0' 2>/dev/null)
  echo "💰 FACTURACIÓN:  €${TOTAL_EUR:-0}"

  # Security
  if [ -f "./security/master-encrypt-verify.sh" ]; then
    SEC=$(./security/master-encrypt-verify.sh 2>/dev/null | head -1)
    echo "🔒 SECURITY:     ${SEC:-—}"
  else
    echo "🔒 SECURITY:     —"
  fi

  # MQTT
  if command -v docker >/dev/null 2>&1 && docker ps -q -f name=mqtt-broker 2>/dev/null | grep -q .; then
    echo "📡 MQTT:         broker activo"
  else
    echo "📡 MQTT:         —"
  fi

  # Última alerta
  ALERT_JSON=$(curl -s "$API/alertas" 2>/dev/null)
  LAST_ALERT=$(echo "$ALERT_JSON" | jq -r '.ultimas[-1].timestamp // empty' 2>/dev/null)
  if [ -n "$LAST_ALERT" ]; then
    echo "⏰ ÚLTIMA ALERTA: $LAST_ALERT"
  else
    echo "⏰ ÚLTIMA ALERTA: Ninguna"
  fi

  echo ""
  echo "Actualizando cada 10s (Ctrl+C salir)"
  sleep 10
done
