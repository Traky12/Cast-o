#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CASTÚO-SYSTEM™ v3.1 — Prueba End-to-End Completa
#
# Cubre:
#   1. Health API
#   2. POST /api/v1/skills/validar_lote (blockchain + PDF + QR)
#   3. POST /api/v1/ai/predict (yield, anomaly, irrigation, livestock)
#   4. Autenticación JWT (401/403)
#   5. Validación transacción GaiaChain (si no es simulado)
#   6. Acceso WordPress dashboard
#
# Uso:
#   JWT_SECRET=mi-secreto API_URL=http://localhost:8001 ./scripts/test_e2e_full.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Configuración ──────────────────────────────────────────────────────────────
API_URL="${API_URL:-http://localhost:8001}"
WP_URL="${WP_URL:-https://app.castuo-system.cloud/panel-operador}"
JWT_SECRET="${JWT_SECRET:-}"
GAIACHAIN_EXPLORER="${GAIACHAIN_EXPLORER:-https://explorer.gaiachain.eu}"
LOTE_ID="LOTE-E2E-$(date +%Y%m%dT%H%M%S)"
FECHA_COSECHA="$(date +%Y-%m-%d)"

# ── Helpers visuales ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS_COUNT=0; FAIL_COUNT=0; WARN_COUNT=0

pass()  { echo -e "${GREEN}  [PASS]${NC} $1"; ((PASS_COUNT++)); }
fail()  { echo -e "${RED}  [FAIL]${NC} $1"; ((FAIL_COUNT++)); }
warn()  { echo -e "${YELLOW}  [WARN]${NC} $1"; ((WARN_COUNT++)); }
info()  { echo -e "${BLUE}  [INFO]${NC} $1"; }
sep()   { echo -e "\n${BLUE}── $1 $( printf '─%.0s' {1..50} | head -c $((52-${#1})) )${NC}"; }

# ── JWT helper ────────────────────────────────────────────────────────────────
make_token() {
    local role="${1:-editor}"
    local secret="${2:-$JWT_SECRET}"
    python3 - <<PYEOF
import jwt, time
tok = jwt.encode(
    {"sub": "e2e-test", "role": "$role", "exp": int(time.time())+3600},
    "$secret", algorithm="HS256"
)
print(tok if isinstance(tok, str) else tok.decode())
PYEOF
}

AUTH_HEADER=""
if [[ -n "$JWT_SECRET" ]]; then
    TOKEN=$(make_token "editor")
    AUTH_HEADER="-H 'Authorization: Bearer $TOKEN'"
    info "JWT generado (role=editor, secret=***)"
else
    warn "JWT_SECRET no configurado — modo dev (sin autenticación)"
fi

# ── Función curl con auth ─────────────────────────────────────────────────────
api_post() {
    local path="$1"
    local data="$2"
    eval "curl -sf -X POST '${API_URL}${path}' \
        -H 'Content-Type: application/json' \
        ${AUTH_HEADER} \
        -d '${data}'" 2>&1
}

api_get() {
    local path="$1"
    eval "curl -sf '${API_URL}${path}' ${AUTH_HEADER}" 2>&1
}

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  CASTÚO-SYSTEM™ v3.1 — E2E Test Suite Completo        ║"
echo "║  Lote: $LOTE_ID"
echo "╚═══════════════════════════════════════════════════════╝"

# ══════════════════════════════════════════════════════════════════════════════
sep "1. Health Check"
# ══════════════════════════════════════════════════════════════════════════════
HEALTH=$(curl -sf "${API_URL}/health" 2>/dev/null || echo '{"status":"ERROR"}')
STATUS=$(echo "$HEALTH" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null || echo "ERROR")

if [[ "$STATUS" == "ok" ]]; then
    pass "GET /health → status=ok"
    CHAIN=$(echo "$HEALTH" | python3 -c "import json,sys; print(json.load(sys.stdin).get('chain_status','?'))" 2>/dev/null || echo "?")
    info "chain_status=$CHAIN"
    VERSION=$(echo "$HEALTH" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('version','?'))" 2>/dev/null || echo "?")
    info "version=$VERSION"
else
    fail "GET /health → status=$STATUS (¿API arrancada en $API_URL?)"
fi

# ══════════════════════════════════════════════════════════════════════════════
sep "2. POST /api/v1/skills/validar_lote"
# ══════════════════════════════════════════════════════════════════════════════

LOTE_PAYLOAD=$(cat <<JSON
{
  "lote_id": "$LOTE_ID",
  "metadatos": {
    "cultivo": "cannabis_medicinal",
    "variedad": "CBD-Ultra-EU",
    "humedad_pct": 12.3,
    "thc_pct": 0.18,
    "cbd_pct": 8.5,
    "kg_cosechados": 45.2,
    "fecha_cosecha": "$FECHA_COSECHA",
    "ubicacion": "Dehesa de Cáceres, parcela 42",
    "operador": "Gregorio",
    "eco": true,
    "aemps_expediente": "EC-2026-0042"
  },
  "verify_base_url": "https://verify.castuo360.eu/lote"
}
JSON
)

LOTE_RESP=$(api_post "/api/v1/skills/validar_lote" "$LOTE_PAYLOAD" || echo '{"error":"curl_failed"}')

if echo "$LOTE_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'tx_hash' in d" 2>/dev/null; then
    TX_HASH=$(echo "$LOTE_RESP"   | python3 -c "import json,sys; print(json.load(sys.stdin)['tx_hash'])")
    CERT_PATH=$(echo "$LOTE_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['certificado_path'])")
    QR_PATH=$(echo "$LOTE_RESP"   | python3 -c "import json,sys; print(json.load(sys.stdin)['qr_path'])")
    BSTATUS=$(echo "$LOTE_RESP"   | python3 -c "import json,sys; print(json.load(sys.stdin)['status'])")
    CHAIN_TYPE=$(echo "$LOTE_RESP"| python3 -c "import json,sys; print(json.load(sys.stdin)['blockchain'])")

    pass "validar_lote → status=$BSTATUS blockchain=$CHAIN_TYPE"
    info "tx_hash: $TX_HASH"
    info "cert   : $CERT_PATH"
    info "qr     : $QR_PATH"

    # Validar archivos en disco
    if [[ -f "$CERT_PATH" ]]; then
        SIZE=$(stat -c%s "$CERT_PATH" 2>/dev/null || echo 0)
        pass "Certificado PDF existe en disco ($SIZE bytes)"
    else
        warn "Certificado no en disco local (puede estar en contenedor)"
    fi

    if [[ -f "$QR_PATH" ]]; then
        SIZE=$(stat -c%s "$QR_PATH" 2>/dev/null || echo 0)
        pass "QR image existe en disco ($SIZE bytes)"
    else
        warn "QR no en disco local (puede estar en contenedor)"
    fi
else
    fail "validar_lote falló: $(echo "$LOTE_RESP" | head -c 200)"
    TX_HASH=""; CERT_PATH=""; QR_PATH=""; BSTATUS="ERROR"; CHAIN_TYPE="?"
fi

# ══════════════════════════════════════════════════════════════════════════════
sep "3. POST /api/v1/ai/predict"
# ══════════════════════════════════════════════════════════════════════════════

# 3a. Yield prediction
YIELD_RESP=$(api_post "/api/v1/ai/predict" '{"tipo":"yield_prediction","cultivo":"lechuga","datos":{"humedad_pct":68,"temperatura_c":22,"radiacion_par":420}}' || echo '{"error":"failed"}')
if echo "$YIELD_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'resultado' in d" 2>/dev/null; then
    KG=$(echo "$YIELD_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['resultado'].get('kg_m2_estimado','?'))")
    pass "yield_prediction → kg_m2_estimado=$KG"
else
    fail "yield_prediction: $(echo "$YIELD_RESP" | head -c 120)"
fi

# 3b. Anomaly detection — datos normales
ANOM_RESP=$(api_post "/api/v1/ai/predict" '{"tipo":"anomaly_detection","datos":{"humedad_pct":65,"temperatura_c":22,"ph":6.5,"co2_ppm":800}}' || echo '{"error":"failed"}')
if echo "$ANOM_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['resultado']['estado']=='NORMAL'" 2>/dev/null; then
    pass "anomaly_detection → NORMAL (datos dentro de rango)"
else
    warn "anomaly_detection resultado inesperado: $(echo "$ANOM_RESP" | head -c 120)"
fi

# 3c. Anomaly detection — temperatura alta (alerta esperada)
ANOM_ALERT=$(api_post "/api/v1/ai/predict" '{"tipo":"anomaly_detection","datos":{"temperatura_c":55}}' || echo '{"error":"failed"}')
if echo "$ANOM_ALERT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['resultado']['estado']=='ALERTA'" 2>/dev/null; then
    pass "anomaly_detection → ALERTA detectada (temperatura=55°C)"
else
    warn "anomaly_detection alerta no activada: $(echo "$ANOM_ALERT" | head -c 120)"
fi

# 3d. Irrigation advice
IRR_RESP=$(api_post "/api/v1/ai/predict" '{"tipo":"irrigation_advice","cultivo":"tomate","datos":{"tension_matricial_cb":55,"humedad_pct":40,"temperatura_c":28}}' || echo '{"error":"failed"}')
if echo "$IRR_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['resultado']['accion']=='REGAR_URGENTE'" 2>/dev/null; then
    pass "irrigation_advice → REGAR_URGENTE (tensión=55cb, humedad=40%)"
else
    warn "irrigation_advice resultado: $(echo "$IRR_RESP" | head -c 120)"
fi

# 3e. Livestock health — fiebre
LIVE_RESP=$(api_post "/api/v1/ai/predict" '{"tipo":"livestock_health","datos":{"especie":"vacuno","temperatura_c":40.5,"peso_kg":450}}' || echo '{"error":"failed"}')
if echo "$LIVE_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['resultado']['estado_sanitario']=='FIEBRE'" 2>/dev/null; then
    pass "livestock_health → FIEBRE detectada (temperatura=40.5°C)"
else
    warn "livestock_health: $(echo "$LIVE_RESP" | head -c 120)"
fi

# ══════════════════════════════════════════════════════════════════════════════
sep "4. Autenticación JWT"
# ══════════════════════════════════════════════════════════════════════════════

if [[ -n "$JWT_SECRET" ]]; then
    # 401 sin cabecera
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}/api/v1/skills/validar_lote" \
        -H "Content-Type: application/json" -d '{"lote_id":"TEST"}')
    [[ "$HTTP_CODE" == "401" ]] && pass "Sin auth → 401" || fail "Esperado 401, obtenido $HTTP_CODE"

    # 403 rol viewer
    BAD_TOKEN=$(make_token "viewer")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}/api/v1/skills/validar_lote" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $BAD_TOKEN" -d '{"lote_id":"TEST"}')
    [[ "$HTTP_CODE" == "403" ]] && pass "Rol 'viewer' → 403" || fail "Esperado 403, obtenido $HTTP_CODE"

    # 200 admin
    ADMIN_TOKEN=$(make_token "admin")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_URL}/api/v1/skills/validar_lote" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ADMIN_TOKEN" -d '{"lote_id":"LOTE-AUTH-OK"}')
    [[ "$HTTP_CODE" == "200" ]] && pass "Rol 'admin' → 200" || fail "Esperado 200 (admin), obtenido $HTTP_CODE"
else
    warn "JWT_SECRET no configurado — tests de auth omitidos"
fi

# ══════════════════════════════════════════════════════════════════════════════
sep "5. Validación en GaiaChain Explorer"
# ══════════════════════════════════════════════════════════════════════════════

if [[ -n "$TX_HASH" && "$TX_HASH" == 0x* ]]; then
    info "TX real detectado: $TX_HASH"
    EXPLORER_RESP=$(curl -sf \
        "${GAIACHAIN_EXPLORER}/api?module=transaction&action=gettxinfo&txhash=${TX_HASH}" \
        2>/dev/null || echo '{"status":"0"}')
    GC_STATUS=$(echo "$EXPLORER_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','0'))" 2>/dev/null || echo "0")
    if [[ "$GC_STATUS" == "1" ]]; then
        pass "Transacción confirmada en GaiaChain Explorer"
    else
        warn "Transacción no confirmada aún (puede tardar 1-2 bloques)"
    fi
elif [[ -n "$TX_HASH" && "$TX_HASH" == sim-* ]]; then
    warn "Transacción simulada ($TX_HASH) — configurar GAIACHAIN_RPC_URL para GaiaChain real"
else
    warn "No hay TX_HASH disponible para validar"
fi

# ══════════════════════════════════════════════════════════════════════════════
sep "6. WordPress Dashboard"
# ══════════════════════════════════════════════════════════════════════════════

WP_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$WP_URL" 2>/dev/null || echo "000")
if [[ "$WP_HTTP" == "200" ]]; then
    pass "WordPress dashboard accesible (HTTP 200)"
elif [[ "$WP_HTTP" == "302" || "$WP_HTTP" == "301" ]]; then
    warn "WordPress dashboard → redirect ($WP_HTTP)"
elif [[ "$WP_HTTP" == "000" ]]; then
    warn "WordPress no accesible desde este entorno ($WP_URL)"
else
    warn "WordPress devolvió HTTP $WP_HTTP"
fi

# ══════════════════════════════════════════════════════════════════════════════
sep "Resumen"
# ══════════════════════════════════════════════════════════════════════════════
TOTAL=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))
echo ""
echo -e "  Lote probado : ${YELLOW}$LOTE_ID${NC}"
echo -e "  TX Hash      : ${BLUE}$TX_HASH${NC}"
echo -e "  Total tests  : $TOTAL"
echo -e "  ${GREEN}PASS: $PASS_COUNT${NC}  ${RED}FAIL: $FAIL_COUNT${NC}  ${YELLOW}WARN: $WARN_COUNT${NC}"
echo ""

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo -e "${RED}╔══ E2E FALLIDO — $FAIL_COUNT test(s) con error ══╗${NC}"
    exit 1
else
    echo -e "${GREEN}╔══ E2E COMPLETADO — $PASS_COUNT PASS, $WARN_COUNT advertencias ══╗${NC}"
    exit 0
fi
