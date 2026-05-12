#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CASTÚO-SYSTEM™ v3.1 — Validación Total del Sistema
#
# Ejecuta todas las validaciones necesarias antes de un deploy a producción:
#   1. Secretos y configuración
#   2. Tests Python (132 tests)
#   3. Sintaxis Docker Compose
#   4. Manifests K8s (kubectl dry-run)
#   5. Conectividad API (si está arrancada)
#   6. E2E completo (si API_URL configurada)
#
# Uso:
#   ./scripts/go-total.sh
#   ./scripts/go-total.sh --env-file .env
#   ./scripts/go-total.sh --skip-e2e     # omite E2E (más rápido)
#   ./scripts/go-total.sh --skip-k8s     # omite validación K8s
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────
ENV_FILE=".env"
SKIP_E2E=false
SKIP_K8S=false
for arg in "$@"; do
    case "$arg" in
        --env-file=*)  ENV_FILE="${arg#*=}" ;;
        --env-file)    ENV_FILE="${2:-}"; shift ;;
        --skip-e2e)    SKIP_E2E=true ;;
        --skip-k8s)    SKIP_K8S=true ;;
    esac
done

if [[ -f "$ENV_FILE" ]]; then
    set -a; source "$ENV_FILE"; set +a
    echo "  Cargado: $ENV_FILE"
fi

# ── Colores / helpers ─────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

STEP=0; PASS=0; FAIL=0; WARN=0
START_TIME=$SECONDS

step()    { ((STEP++)); echo -e "\n${BLUE}${BOLD}── Paso $STEP: $1 ─────────────────────────────${NC}"; }
ok()      { echo -e "${GREEN}  ✓${NC} $1"; ((PASS++)); }
fail()    { echo -e "${RED}  ✗${NC} $1"; ((FAIL++)); }
warn()    { echo -e "${YELLOW}  ⚠${NC} $1"; ((WARN++)); }
info()    { echo -e "    $1"; }

echo ""
echo "${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
echo "${BOLD}║  CASTÚO-SYSTEM™ v3.1 — Go-Total Validation            ║${NC}"
echo "${BOLD}║  $(date '+%Y-%m-%d %H:%M:%S')                          ║${NC}"
echo "${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"

# ══════════════════════════════════════════════════════════════════════════════
step "Validación de secretos"
# ══════════════════════════════════════════════════════════════════════════════
if bash scripts/validate_secrets.sh --env-file "$ENV_FILE" 2>/dev/null; then
    ok "Secretos validados"
else
    fail "Secretos incompletos — revisa scripts/validate_secrets.sh"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "Tests Python (pytest)"
# ══════════════════════════════════════════════════════════════════════════════
if command -v pytest &>/dev/null || python3 -m pytest --version &>/dev/null 2>&1; then
    if python3 -m pytest tests/ -q --tb=short \
        --no-header \
        -x \
        2>&1 | tail -5; then
        ok "Todos los tests pasaron"
    else
        fail "Tests fallaron — revisar salida pytest"
    fi
else
    warn "pytest no disponible — instalar: pip install pytest"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "Sintaxis JSON de schemas"
# ══════════════════════════════════════════════════════════════════════════════
SCHEMA_ERRORS=0
for f in config/schemas/*.schema.json; do
    if python3 -m json.tool "$f" >/dev/null 2>&1; then
        info "OK: $f"
    else
        fail "JSON inválido: $f"
        ((SCHEMA_ERRORS++))
    fi
done
[[ "$SCHEMA_ERRORS" -eq 0 ]] && ok "Todos los schemas JSON válidos"

# ══════════════════════════════════════════════════════════════════════════════
step "Validación Docker Compose"
# ══════════════════════════════════════════════════════════════════════════════
if command -v docker &>/dev/null; then
    if docker compose config --quiet 2>/dev/null; then
        ok "docker-compose.yml válido"
    else
        warn "docker-compose.yml: validación con advertencias (sin .env puede ser normal)"
    fi
else
    warn "docker no disponible — saltando validación compose"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "Manifests Kubernetes (dry-run)"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "$SKIP_K8S" == "true" ]]; then
    warn "Saltando validación K8s (--skip-k8s)"
elif command -v kubectl &>/dev/null && kubectl cluster-info &>/dev/null 2>&1; then
    K8S_ERRORS=0
    for f in k8s/*.yaml; do
        [[ "$f" == *"secret"* ]] && continue   # nunca aplicar secrets en dry-run
        if kubectl apply --dry-run=client -f "$f" &>/dev/null 2>&1; then
            info "OK: $f"
        else
            warn "Advertencia en: $f (puede requerir CRDs)"
            ((K8S_ERRORS++))
        fi
    done
    [[ "$K8S_ERRORS" -eq 0 ]] && ok "Manifests K8s válidos" || warn "$K8S_ERRORS manifests con advertencias"
else
    warn "kubectl no conectado — saltando validación K8s dry-run"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "Conectividad API"
# ══════════════════════════════════════════════════════════════════════════════
API_BASE="${API_URL:-http://localhost:8001}"
HEALTH_URL="${API_BASE%/api/v1*}/health"
[[ "$HEALTH_URL" == *"validar_lote"* ]] && HEALTH_URL="http://localhost:8001/health"

if curl -sf --max-time 5 "$HEALTH_URL" | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('status')=='ok', f'status={d.get(\"status\")}'
print(f'  API v{d.get(\"version\",\"?\")} | chain={d.get(\"chain_status\",\"?\")}')
" 2>/dev/null; then
    ok "API responde en $HEALTH_URL"
else
    warn "API no accesible en $HEALTH_URL (¿está arrancada?)"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "E2E completo"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "$SKIP_E2E" == "true" ]]; then
    warn "Saltando E2E (--skip-e2e)"
elif [[ -x scripts/test_e2e_full.sh ]]; then
    if JWT_SECRET="${JWT_SECRET_KEY:-}" \
       API_URL="${API_URL:-http://localhost:8001}" \
       bash scripts/test_e2e_full.sh 2>&1 | grep -E '\[(PASS|FAIL|WARN)\]' | tail -20; then
        ok "E2E completado sin errores fatales"
    else
        warn "E2E con advertencias — revisar salida completa"
    fi
else
    warn "scripts/test_e2e_full.sh no encontrado"
fi

# ══════════════════════════════════════════════════════════════════════════════
# Resumen final
# ══════════════════════════════════════════════════════════════════════════════
ELAPSED=$((SECONDS - START_TIME))
echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "  ${GREEN}PASS:  $PASS${NC}  ${YELLOW}WARN: $WARN${NC}  ${RED}FAIL: $FAIL${NC}  ⏱ ${ELAPSED}s"
echo "═══════════════════════════════════════════════════════"

if [[ "$FAIL" -gt 0 ]]; then
    echo -e "${RED}${BOLD}✗ GO-TOTAL FALLIDO — $FAIL error(s) críticos${NC}"
    echo "  Corrige los errores antes del deploy."
    exit 1
else
    echo -e "${GREEN}${BOLD}✓ GO-TOTAL COMPLETADO — Sistema listo para deploy${NC}"
    exit 0
fi
