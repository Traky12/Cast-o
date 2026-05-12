#!/usr/bin/env bash
# CASTÚO-SYSTEM™ v3.1 — Full System Validation Script
# Usage: ./scripts/validate.sh [--prod] [--api-only]
set -euo pipefail

API_BASE="${CASTUO_API:-http://localhost:8000}"
PROD_BASE="https://api.castuo-system.cloud"
MODE="dev"
API_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --prod)     MODE="prod"; API_BASE="$PROD_BASE" ;;
    --api-only) API_ONLY=true ;;
  esac
done

# ── Colors ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'
BOLD='\033[1m'; RESET='\033[0m'

PASS=0; FAIL=0; WARN=0

pass() { echo -e "${GREEN}✓${RESET} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}✗${RESET} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}⚠${RESET} $1"; WARN=$((WARN+1)); }
header() { echo -e "\n${BOLD}── $1 ──${RESET}"; }

http_check() {
  local desc="$1" url="$2" expected="${3:-200}"
  local code
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
  if [ "$code" = "$expected" ]; then
    pass "$desc → $code"
  else
    fail "$desc → $code (esperado $expected)"
  fi
}

http_post_check() {
  local desc="$1" url="$2" body="$3" expected="${4:-200}"
  local code
  code=$(curl -sk -o /dev/null -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" -d "$body" "$url" 2>/dev/null || echo "000")
  if [ "$code" = "$expected" ]; then
    pass "$desc → $code"
  else
    fail "$desc → $code (esperado $expected)"
  fi
}

json_field() {
  local desc="$1" url="$2" field="$3" expected="$4"
  local val
  val=$(curl -sk "$url" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$field','MISSING'))" 2>/dev/null || echo "ERROR")
  if [ "$val" = "$expected" ]; then
    pass "$desc: $field=$val"
  else
    warn "$desc: $field=$val (esperado $expected)"
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}CASTÚO-SYSTEM™ v3.1 — Validación ($MODE)${RESET}"
echo "API: $API_BASE"
echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# ── 1. API Health ─────────────────────────────────────────────────────────────
header "1. API Health"
http_check "GET /health"            "$API_BASE/health"
http_check "GET /docs"              "$API_BASE/docs"
http_check "GET /openapi.json"      "$API_BASE/openapi.json"
http_check "GET /metrics"           "$API_BASE/metrics"
http_check "GET / (root redirect)"  "$API_BASE/" "200"

# ── 2. Core Endpoints ─────────────────────────────────────────────────────────
header "2. Core Endpoints"
http_check "GET /api/v1/audit/actions"    "$API_BASE/api/v1/audit/actions"
http_check "GET /api/v1/tenants/current"  "$API_BASE/api/v1/tenants/current"
http_check "GET /api/v1/actuadores/estado" "$API_BASE/api/v1/actuadores/estado"

# ── 3. Claude / SABIONDA IA ────────────────────────────────────────────────────
header "3. Claude / SABIONDA IA"
http_check "GET /api/v1/claude/status"    "$API_BASE/api/v1/claude/status"
json_field "SDK instalado" "$API_BASE/api/v1/claude/status" "sdk_disponible" "True"
http_post_check "POST /api/v1/claude/generate (fallback)" \
  "$API_BASE/api/v1/claude/generate" \
  '{"prompt":"pH óptimo lechuga hidropónica","contexto":"agricultura"}' "200"

# ── 4. GitHub Integration ─────────────────────────────────────────────────────
header "4. GitHub Integration"
http_check "GET /api/v1/github/status"   "$API_BASE/api/v1/github/status"

# ── 5. Response Schema ────────────────────────────────────────────────────────
header "5. Response Schema"
HEALTH=$(curl -sk "$API_BASE/health" 2>/dev/null || echo "{}")
for field in status version environment; do
  echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); assert '$field' in d, '$field missing'" 2>/dev/null \
    && pass "health.$field presente" || fail "health.$field AUSENTE"
done

# ── 6. Python / SDK checks ────────────────────────────────────────────────────
header "6. Dependencias Python"
python3 -c "import anthropic; print(anthropic.__version__)" 2>/dev/null \
  && pass "anthropic SDK instalado ($(python3 -c 'import anthropic; print(anthropic.__version__)'))" \
  || fail "anthropic SDK NO instalado — pip install anthropic>=0.40.0"

python3 -c "import fastapi" 2>/dev/null \
  && pass "fastapi instalado" || fail "fastapi NO instalado"

python3 -c "import pydantic" 2>/dev/null \
  && pass "pydantic instalado" || fail "pydantic NO instalado"

python3 -c "import jwt" 2>/dev/null \
  && pass "PyJWT instalado" || warn "PyJWT no instalado (optional)"

# ── 7. Archivos críticos ──────────────────────────────────────────────────────
header "7. Archivos críticos"
CRITICAL_FILES=(
  "api/main.py"
  "api/requirements.txt"
  "api/routers/claude_proxy.py"
  "services/claude_client.py"
  "services/firmware/esp32_castuo.ino"
  "n8n/workflows/agriculture/ctaex-cultivo.json"
  "postgres/init.sql"
  "frontend/index.html"
  "docker-compose.dev.yml"
  "Makefile"
)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for f in "${CRITICAL_FILES[@]}"; do
  [ -f "$REPO_ROOT/$f" ] && pass "$f" || fail "$f FALTA"
done

# ── 8. Variables de entorno ───────────────────────────────────────────────────
header "8. Variables de entorno"
[ -f "$REPO_ROOT/.env" ] && pass ".env existe" || warn ".env no existe (usar .env.example)"
[ -n "${CLAUDE_API_KEY:-}" ] && pass "CLAUDE_API_KEY configurada" || warn "CLAUDE_API_KEY no configurada (modo fallback)"
[ -n "${JWT_SECRET_KEY:-}" ] && pass "JWT_SECRET_KEY configurada" || warn "JWT_SECRET_KEY no configurada (modo dev)"

# ── 9. Tests ─────────────────────────────────────────────────────────────────
if ! $API_ONLY; then
  header "9. pytest (claude + servicios)"
  if command -v pytest &>/dev/null; then
    cd "$REPO_ROOT/api" && python -m pytest ../tests/test_claude.py -q --tb=line 2>&1 | tail -5
    PYTEST_EXIT=${PIPESTATUS[0]}
    [ $PYTEST_EXIT -eq 0 ] && pass "pytest test_claude.py OK" || fail "pytest falló (exit $PYTEST_EXIT)"
    cd "$REPO_ROOT"
  else
    warn "pytest no disponible"
  fi
fi

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}── Resumen ──${RESET}"
echo -e "  ${GREEN}✓ Pasaron:${RESET}  $PASS"
echo -e "  ${YELLOW}⚠ Advertencias:${RESET} $WARN"
echo -e "  ${RED}✗ Fallaron:${RESET} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}${BOLD}Sistema CASTÚO-SYSTEM™ operativo ✓${RESET}"
  exit 0
else
  echo -e "${RED}${BOLD}$FAIL verificaciones fallaron — revisar arriba${RESET}"
  exit 1
fi
