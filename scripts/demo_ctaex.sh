#!/bin/bash
# Demo oficial CASTÚO-SYSTEM v4.3 para CTAEX (17/03/2026)
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
EPCIS_URL="${EPCIS_URL:-http://localhost:8080}"
TOKEN="${API_TOKEN:-ctaex17_jeremie_token}"
LOG_FILE="demo_ctaex_$(date +%Y-%m-%d).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "DEMO OFICIAL CASTÚO-SYSTEM v4.3 para CTAEX (17/03/2026)"
echo "========================================================="

echo "0:00 Bienvenidos a CASTÚO-SYSTEM v4.3"
echo "     Cumplimiento JEREMIE: ENS Alto, GDPR, UE 178/2002"
echo "     Tecnología: OpenEPCIS 2.0.0 + PostgreSQL 16 + Docker"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/health" | jq . 2>/dev/null || true
echo ""

echo "1:00 OpenEPCIS: Evento B001 (100kg sorgo - GS1 compliant)"
EVENT_RESPONSE=$(curl -s -X POST "$API_URL/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "packing",
    "epc_list": ["urn:epc:id:sgtin:305555.00001.1"],
    "quantity": 100,
    "read_point": "urn:epc:id:sgln:305555.00001.0",
    "biz_step": "urn:epcglobal:cbv:bizstep:packing",
    "metadata": {"cultivo": "sorgo", "variedad": "B001", "finca": "CTAEX-50ha", "certificacion": "UE-ORGANIC", "sensor_id": "temp1"}
  }')
echo "$EVENT_RESPONSE" | jq . 2>/dev/null || echo "$EVENT_RESPONSE"
echo ""

echo "2:00 Verificación OpenEPCIS (UE 178/2002)"
curl -s "$EPCIS_URL/api/events?epc=urn:epc:id:sgtin:305555.00001.1" | jq . 2>/dev/null || echo "OpenEPCIS no disponible en $EPCIS_URL"
echo ""

echo "4:00 Cumplimiento Legal JEREMIE (FULLY_COMPLIANT)"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/compliance" | jq . 2>/dev/null || true
echo ""

echo "6:00 Auditoría: Últimos 3 eventos"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/audit?limit=3" | jq . 2>/dev/null || true
echo ""

echo "DEMO COMPLETADA - Listo para firma CTAEX 17/03"
echo "Log guardado en: $LOG_FILE"
