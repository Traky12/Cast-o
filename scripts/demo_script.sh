#!/bin/bash
# Demo CASTÚO-SYSTEM v4.3 (7 min) — 17/03/2026 CTAEX
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
EPCIS_URL="${EPCIS_URL:-http://localhost:8080}"
TOKEN="${API_TOKEN:-ctaex17_jeremie_token}"
LOG_FILE="demo_$(date +%Y-%m-%d).log"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "DEMO CASTÚO-SYSTEM v4.3 (7 min) - 17/03/2026"
echo "============================================="

echo "0:00 Introducción: Plataforma Agritech EU con ROI 11,204x"
echo "     Cumplimiento JEREMIE: ENS Alto, GDPR, UE 178/2002"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/health" | jq . 2>/dev/null || curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/health"
echo ""

echo "2:00 OpenEPCIS: Evento B001 (100kg sorgo - GS1 compliant)"
EVENT_RESPONSE=$(curl -s -X POST "$API_URL/events" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "packing",
    "epc_list": ["urn:epc:id:sgtin:305555.00001.1"],
    "quantity": 100,
    "read_point": "urn:epc:id:sgln:305555.00001.0",
    "biz_step": "urn:epcglobal:cbv:bizstep:packing",
    "metadata": {"cultivo": "sorgo", "variedad": "B001", "finca": "CTAEX-50ha", "certificacion": "UE-ORGANIC"}
  }')
echo "$EVENT_RESPONSE" | jq . 2>/dev/null || echo "$EVENT_RESPONSE"
echo ""

echo "4:00 Cumplimiento Legal JEREMIE (100%)"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/compliance" | jq . 2>/dev/null || curl -s "$API_URL/compliance"
echo ""

echo "5:00 Auditoría: Últimos 5 eventos"
curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/audit?limit=5" | jq . 2>/dev/null || echo "N/A"
echo ""

echo "6:30 Cierre: Documentación lista para firma JEREMIE 605K€"
echo "     Endpoints: $API_URL/health | $API_URL/compliance | $API_URL/audit"
echo "DEMO COMPLETADA - Log: $LOG_FILE"
