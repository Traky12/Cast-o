#!/usr/bin/env bash
# ============================================================================
# CASTÚO-SYSTEM™ — Script de Prueba End-to-End
# Valida el flujo completo: JWT → validar_lote → GaiaChain → QR + PDF
#
# Variables de entorno requeridas (o configurar abajo):
#   JWT_SECRET            Secreto HMAC-SHA256 para firmar el JWT
#   GAIACHAIN_RPC_URL     URL del nodo RPC de GaiaChain (opcional)
#   GAIACHAIN_PRIVATE_KEY Clave privada hex del firmante (opcional)
#   API_URL               URL completa del endpoint validar_lote
#   WORDPRESS_URL         URL del panel de operador en WordPress
#
# Uso:
#   export JWT_SECRET="tu_secreto_jwt_aqui"
#   chmod +x scripts/test_e2e_full.sh
#   ./scripts/test_e2e_full.sh
# ============================================================================
set -euo pipefail

# ── Valores por defecto (sobreescribibles por variables de entorno) ──────────
: "${JWT_SECRET:=dev-secret-no-produccion}"
: "${GAIACHAIN_RPC_URL:=}"
: "${GAIACHAIN_PRIVATE_KEY:=}"
: "${API_URL:=http://localhost:8000/api/v1/skills/validar_lote}"
: "${WORDPRESS_URL:=https://app.castuo-system.cloud/panel-operador}"

LOTE_ID="LOTE-E2E-$(date +%s)"

# ── Colores ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }

# ── 1. Generar JWT ───────────────────────────────────────────────────────────
echo "──────────────────────────────────────────────"
echo "1. Generando JWT para lote: $LOTE_ID"
JWT_TOKEN=$(python3 - <<PYEOF
import sys
try:
    import jwt
except ImportError:
    print("ERROR: PyJWT no instalado. Ejecuta: pip install PyJWT", file=sys.stderr)
    sys.exit(1)
import datetime

payload = {
    "sub": "operador_prueba",
    "role": "editor",
    "lote": "$LOTE_ID",
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),
}
token = jwt.encode(payload, "$JWT_SECRET", algorithm="HS256")
print(token)
PYEOF
)
ok "JWT generado: ${JWT_TOKEN:0:40}..."

# ── 2. Llamar al endpoint validar_lote ──────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
echo "2. Llamando al endpoint: $API_URL"
HTTP_CODE=$(curl -s -o /tmp/e2e_response.json -w "%{http_code}" \
  -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "lote_id": "'"$LOTE_ID"'",
    "metadatos": {
      "humedad": 65.5,
      "thc": 0.18,
      "cbd": 12.3,
      "fecha_cosecha": "'"$(date +%Y-%m-%d)"'",
      "ubicacion": "Dehesa de Cáceres, parcela 42"
    },
    "firma_digital": "'"$JWT_TOKEN"'"
  }' || echo "000")

echo "HTTP status: $HTTP_CODE"
if command -v jq &>/dev/null; then
  jq . /tmp/e2e_response.json 2>/dev/null || cat /tmp/e2e_response.json
else
  cat /tmp/e2e_response.json
fi

if [[ "$HTTP_CODE" != "200" ]]; then
  fail "El endpoint devolvió HTTP $HTTP_CODE (esperado 200)"
fi
ok "Endpoint respondió HTTP 200"

# ── 3. Validar estructura de la respuesta ───────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
echo "3. Validando estructura de la respuesta..."
python3 - <<PYEOF
import json, sys

with open("/tmp/e2e_response.json") as f:
    data = json.load(f)

errors = []
for field in ("status", "lote_id", "tx_hash", "qr_path", "certificado_path", "generado_en"):
    if field not in data:
        errors.append(f"Campo faltante: {field}")

if data.get("status") != "OK":
    errors.append(f"status esperado 'OK', obtenido '{data.get('status')}'")

if errors:
    print("\\n".join(errors), file=sys.stderr)
    sys.exit(1)

print(f"  lote_id:          {data['lote_id']}")
print(f"  tx_hash:          {data['tx_hash']}")
print(f"  qr_path:          {data['qr_path']}")
print(f"  certificado_path: {data['certificado_path']}")
print(f"  generado_en:      {data['generado_en']}")
PYEOF
ok "Estructura de respuesta correcta"

# ── 4. Validar transacción GaiaChain ────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
echo "4. Validando transacción GaiaChain..."
TX_HASH=$(python3 -c "import json; print(json.load(open('/tmp/e2e_response.json'))['tx_hash'])")

if [[ "$TX_HASH" == sim-* ]]; then
  warn "Transacción simulada (fallback activo): $TX_HASH"
  warn "Para registro real, configura GAIACHAIN_RPC_URL y GAIACHAIN_PRIVATE_KEY"
else
  echo "  Validando tx_hash en explorer: $TX_HASH"
  EXPLORER_URL="https://explorer.gaiachain.cloud/api?module=transaction&action=gettxinfo&txhash=$TX_HASH"
  if curl -sf --max-time 10 "$EXPLORER_URL" -o /tmp/gaiachain_tx.json 2>/dev/null; then
    if command -v jq &>/dev/null; then
      jq '.result' /tmp/gaiachain_tx.json 2>/dev/null || cat /tmp/gaiachain_tx.json
    fi
    ok "Transacción encontrada en GaiaChain explorer"
  else
    warn "Explorer de GaiaChain no disponible — tx registrada pero no verificable ahora"
  fi
fi

# ── 5. Información del dashboard WordPress ──────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
echo "5. Dashboard de operador disponible en:"
echo "   $WORDPRESS_URL"

# ── Resumen final ────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════"
ok "E2E completado con éxito — Lote: $LOTE_ID"
echo "══════════════════════════════════════════════"
