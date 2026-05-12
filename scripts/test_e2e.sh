#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# CASTÚO-SYSTEM™ v3.1 — E2E test: POST /api/v1/skills/validar_lote
# Uso:
#   ./scripts/test_e2e.sh                         # modo dev (sin JWT)
#   JWT_SECRET=mi-secreto ./scripts/test_e2e.sh   # con autenticación
#   API_URL=http://api:8001 ./scripts/test_e2e.sh  # URL personalizada
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

API_URL="${API_URL:-http://localhost:8001}"
ENDPOINT="${API_URL}/api/v1/skills/validar_lote"
JWT_SECRET="${JWT_SECRET:-}"
LOTE_ID="LOTE-E2E-$(date +%Y%m%dT%H%M%S)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
info() { echo -e "       $1"; }

echo "═══════════════════════════════════════════════════════"
echo "  CASTÚO E2E — validar_lote"
echo "  Endpoint : $ENDPOINT"
echo "  Lote ID  : $LOTE_ID"
echo "═══════════════════════════════════════════════════════"

# ── 0. Generar JWT si JWT_SECRET está configurado ─────────────────────────────
AUTH_HEADER=""
if [[ -n "$JWT_SECRET" ]]; then
    # Requiere python3 + PyJWT
    TOKEN=$(python3 - <<EOF
import jwt, time, sys
secret = "$JWT_SECRET"
tok = jwt.encode({"sub": "e2e-operator", "role": "editor", "exp": int(time.time())+3600}, secret, algorithm="HS256")
print(tok if isinstance(tok, str) else tok.decode())
EOF
)
    AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
    info "Token JWT generado (role=editor)"
else
    warn "JWT_SECRET no configurado → modo dev (sin autenticación)"
fi

# ── 1. Health check ───────────────────────────────────────────────────────────
echo ""
echo "── 1. Health check ──────────────────────────────────────"
HEALTH=$(curl -sf "${API_URL}/health" || true)
if [[ -n "$HEALTH" ]]; then
    STATUS_VAL=$(echo "$HEALTH" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','?'))")
    if [[ "$STATUS_VAL" == "ok" ]]; then
        pass "API responde status=ok"
    else
        fail "API health status=$STATUS_VAL"
    fi
else
    warn "Health endpoint no disponible (¿API arrancada?)"
fi

# ── 2. POST validar_lote ──────────────────────────────────────────────────────
echo ""
echo "── 2. POST /api/v1/skills/validar_lote ─────────────────"

PAYLOAD=$(cat <<JSON
{
  "lote_id": "$LOTE_ID",
  "metadatos": {
    "cultivo": "cannabis_medicinal",
    "variedad": "CBD-Ultra",
    "humedad_pct": 12.3,
    "thc_pct": 0.18,
    "cbd_pct": 8.5,
    "kg_cosechados": 45.2,
    "fecha_cosecha": "$(date +%Y-%m-%d)",
    "ubicacion": "Parcela-A3-Invernadero-2",
    "operador": "Gregorio",
    "eco": true
  },
  "verify_base_url": "https://verify.castuo360.eu/lote"
}
JSON
)

CURL_CMD="curl -sf -X POST \"$ENDPOINT\" \
  -H 'Content-Type: application/json' \
  ${AUTH_HEADER} \
  -d '$PAYLOAD'"

RESPONSE=$(eval "$CURL_CMD" 2>&1) || {
    fail "curl falló — ¿está el servidor arrancado en $API_URL?"
}

info "Respuesta raw: $(echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE")"

# ── 3. Validar campos de la respuesta ────────────────────────────────────────
echo ""
echo "── 3. Validar respuesta ─────────────────────────────────"

python3 - <<PYCHECK
import json, sys

raw = '''$RESPONSE'''
try:
    d = json.loads(raw)
except Exception as e:
    print(f"[FAIL] JSON inválido: {e}")
    sys.exit(1)

errors = []

# Campos requeridos
for field in ("status", "lote_id", "tx_hash", "blockchain", "certificado_path", "qr_path", "generado_en"):
    if field not in d:
        errors.append(f"Campo '{field}' ausente")

# status
if d.get("status") not in ("OK", "FALLBACK"):
    errors.append(f"status inválido: {d.get('status')}")

# lote_id
if d.get("lote_id") != "$LOTE_ID":
    errors.append(f"lote_id no coincide: {d.get('lote_id')}")

# tx_hash
tx = d.get("tx_hash", "")
if not (tx.startswith("0x") or tx.startswith("sim-")):
    errors.append(f"tx_hash inválido: {tx}")

# blockchain
if d.get("blockchain") not in ("GaiaChain", "simulado"):
    errors.append(f"blockchain inválido: {d.get('blockchain')}")

# archivos
if not d.get("certificado_path", "").endswith(".pdf"):
    errors.append(f"certificado_path no .pdf: {d.get('certificado_path')}")

# generado_en ISO-8601
try:
    from datetime import datetime
    datetime.fromisoformat(d.get("generado_en", ""))
except Exception:
    errors.append(f"generado_en no es ISO-8601: {d.get('generado_en')}")

if errors:
    for e in errors:
        print(f"[FAIL] {e}")
    sys.exit(1)

# Resumen
status_label = "\033[0;32mOK (GaiaChain real)\033[0m" if d["status"]=="OK" else "\033[1;33mFALLBACK (simulado)\033[0m"
print(f"[PASS] status        = {status_label}")
print(f"[PASS] lote_id       = {d['lote_id']}")
print(f"[PASS] tx_hash       = {d['tx_hash'][:30]}...")
print(f"[PASS] blockchain    = {d['blockchain']}")
print(f"[PASS] cert_path     = {d['certificado_path']}")
print(f"[PASS] qr_path       = {d['qr_path']}")
print(f"[PASS] generado_en   = {d['generado_en']}")
PYCHECK

# ── 4. Verificar archivos en disco ───────────────────────────────────────────
echo ""
echo "── 4. Verificar archivos generados en disco ─────────────"

CERT_PATH=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['certificado_path'])" 2>/dev/null || echo "")
QR_PATH=$(echo "$RESPONSE"   | python3 -c "import json,sys; print(json.load(sys.stdin)['qr_path'])"         2>/dev/null || echo "")

if [[ -n "$CERT_PATH" && -f "$CERT_PATH" ]]; then
    SIZE=$(stat -c%s "$CERT_PATH" 2>/dev/null || echo 0)
    pass "Certificado PDF existe ($SIZE bytes): $CERT_PATH"
else
    warn "Certificado no encontrado en disco (puede estar en contenedor): $CERT_PATH"
fi

if [[ -n "$QR_PATH" && -f "$QR_PATH" ]]; then
    SIZE=$(stat -c%s "$QR_PATH" 2>/dev/null || echo 0)
    pass "QR image existe ($SIZE bytes): $QR_PATH"
else
    warn "QR no encontrado en disco (puede estar en contenedor): $QR_PATH"
fi

# ── 5. Test autenticación (solo si JWT_SECRET configurado) ───────────────────
if [[ -n "$JWT_SECRET" ]]; then
    echo ""
    echo "── 5. Test autenticación ─────────────────────────────────"

    # Sin cabecera → 401
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ENDPOINT" \
        -H 'Content-Type: application/json' \
        -d '{"lote_id":"LOTE-NO-AUTH"}')
    if [[ "$HTTP_CODE" == "401" ]]; then
        pass "Sin auth → 401"
    else
        fail "Esperado 401 sin auth, obtenido: $HTTP_CODE"
    fi

    # Token con rol incorrecto → 403
    BAD_TOKEN=$(python3 - <<EOF
import jwt, time
print(jwt.encode({"sub": "x", "role": "viewer", "exp": int(time.time())+60}, "$JWT_SECRET", algorithm="HS256"))
EOF
)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ENDPOINT" \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $BAD_TOKEN" \
        -d '{"lote_id":"LOTE-BAD-ROLE"}')
    if [[ "$HTTP_CODE" == "403" ]]; then
        pass "Rol 'viewer' → 403"
    else
        fail "Esperado 403 con rol viewer, obtenido: $HTTP_CODE"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════"
pass "E2E completado para $LOTE_ID"
echo "═══════════════════════════════════════════════════════"
