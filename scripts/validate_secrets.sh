#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# CASTÚO-SYSTEM™ v3.1 — Validación de Secretos y Configuración
#
# Verifica que todas las variables de entorno necesarias estén configuradas.
# Categoriza en: REQUERIDAS (bloquea deploy), OPCIONALES (aviso), SEGURIDAD.
#
# Uso:
#   source .env && ./scripts/validate_secrets.sh
#   ./scripts/validate_secrets.sh --env-file .env
#   ./scripts/validate_secrets.sh --strict   # falla en cualquier WARNING
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────────────
ENV_FILE=""
STRICT=false
for arg in "$@"; do
    case "$arg" in
        --env-file) ENV_FILE="${2:-}"; shift ;;
        --strict)   STRICT=true ;;
        --env-file=*) ENV_FILE="${arg#*=}" ;;
    esac
done

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a; source "$ENV_FILE"; set +a
    echo "  Cargado: $ENV_FILE"
fi

# ── Colores ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

ERRORS=0; WARNINGS=0; OK=0

check_required() {
    local var="$1"; local desc="$2"
    if [[ -z "${!var:-}" ]]; then
        echo -e "${RED}  [ERROR]${NC} ${BOLD}${var}${NC} — ${desc}"
        ((ERRORS++))
    else
        local preview="${!var:0:8}***"
        echo -e "${GREEN}  [OK]   ${NC} ${var} = ${preview}"
        ((OK++))
    fi
}

check_optional() {
    local var="$1"; local desc="$2"
    if [[ -z "${!var:-}" ]]; then
        echo -e "${YELLOW}  [WARN] ${NC} ${var} — ${desc}"
        ((WARNINGS++))
    else
        local preview="${!var:0:6}***"
        echo -e "${GREEN}  [OK]   ${NC} ${var} = ${preview}"
        ((OK++))
    fi
}

check_file() {
    local var="$1"; local desc="$2"
    local path="${!var:-}"
    if [[ -z "$path" ]]; then
        echo -e "${YELLOW}  [WARN] ${NC} ${var} — ${desc}"
        ((WARNINGS++))
    elif [[ ! -f "$path" ]]; then
        echo -e "${RED}  [ERROR]${NC} ${var}=${path} — fichero no encontrado"
        ((ERRORS++))
    else
        echo -e "${GREEN}  [OK]   ${NC} ${var} → ${path}"
        ((OK++))
    fi
}

check_url() {
    local var="$1"; local desc="$2"
    local url="${!var:-}"
    if [[ -z "$url" ]]; then
        echo -e "${YELLOW}  [WARN] ${NC} ${var} — ${desc}"
        ((WARNINGS++))
    elif ! curl -sf --max-time 5 "$url" >/dev/null 2>&1; then
        echo -e "${YELLOW}  [WARN] ${NC} ${var}=${url} — no accesible (puede ser correcto en dev)"
        ((WARNINGS++))
    else
        echo -e "${GREEN}  [OK]   ${NC} ${var} → ${url} (accesible)"
        ((OK++))
    fi
}

echo ""
echo "${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
echo "${BOLD}║  CASTÚO-SYSTEM™ — Validación de Secretos               ║${NC}"
echo "${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── Autenticación API ─────────────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_required "JWT_SECRET_KEY"    "Secreto JWT para firmar tokens"
check_optional "JWT_SECRET"        "Alias de JWT_SECRET_KEY (acepta ambos)"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── GaiaChain / Blockchain ────────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "GAIACHAIN_RPC_URL"         "URL nodo RPC GaiaChain"
check_optional "GAIACHAIN_PRIVATE_KEY"     "Clave privada 0x... para firmar TX"
check_file     "GAIACHAIN_PRIVATE_KEY_FILE" "Fichero con clave privada GaiaChain"
check_optional "GAIA_CHAIN_PRIVATE_KEY"    "Alias legacy de GAIACHAIN_PRIVATE_KEY"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── Base de Datos ─────────────────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "POSTGRES_PASSWORD"  "Contraseña PostgreSQL"
check_optional "DATABASE_URL"       "URL completa de PostgreSQL"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── Inteligencia Artificial ───────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "MISTRAL_API_KEY"    "Clave API Mistral AI"
check_optional "SABIONDA_API_KEY"   "Clave API SABIONDA"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── Infraestructura (Hetzner) ─────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "HETZNER_API_KEY"    "Hetzner Cloud API Key"
check_optional "HETZNER_IP"         "IP del servidor Hetzner (para SSH deploy)"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── Satélite EU / Copernicus ──────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "COPERNICUS_CLIENT_ID"     "Client ID de CDSE (registro gratuito)"
check_optional "COPERNICUS_CLIENT_SECRET" "Client Secret CDSE"
check_optional "OBJECT_STORAGE_KEY"       "S3 access key (Hetzner Object Storage)"
check_optional "OBJECT_STORAGE_SECRET"    "S3 secret key"
check_optional "OBJECT_STORAGE_ENDPOINT"  "Endpoint S3-compatible"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── IoT ───────────────────────────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "CASTUO_IOT_TELEMETRY_URL"  "Endpoint telemetría IoT"
check_optional "CASTUO_IOT_DEVICE_CMD_URL" "Endpoint comandos dispositivos"
check_optional "CASTUO_IOT_BEARER"         "Bearer token IoT"
check_optional "MQTT_BROKER_HOST"          "Broker MQTT"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── Monitoreo / Grafana ───────────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "GRAFANA_PASSWORD"   "Contraseña Grafana admin"
check_optional "ELASTIC_PASSWORD"   "Contraseña Elasticsearch"
check_optional "ALERT_WEBHOOK_URL"  "Webhook para alertas"

# ══════════════════════════════════════════════════════════════════════════════
echo -e "\n${BLUE}── n8n / Workflows ───────────────────────────────────────${NC}"
# ══════════════════════════════════════════════════════════════════════════════
check_optional "N8N_PASSWORD"         "Contraseña n8n basic auth"
check_optional "N8N_ENCRYPTION_KEY"   "Clave de cifrado n8n"
check_optional "WEBHOOK_URL"          "URL webhook n8n"

# ══════════════════════════════════════════════════════════════════════════════
# Resumen
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════"
echo -e "  ${GREEN}OK:      $OK${NC}"
echo -e "  ${YELLOW}WARN:    $WARNINGS${NC}"
echo -e "  ${RED}ERRORS:  $ERRORS${NC}"
echo "═══════════════════════════════════════════════════════"

if [[ "$ERRORS" -gt 0 ]]; then
    echo -e "${RED}✗ Validación FALLIDA — $ERRORS variable(s) requerida(s) no configurada(s)${NC}"
    exit 1
fi

if [[ "$STRICT" == "true" && "$WARNINGS" -gt 0 ]]; then
    echo -e "${YELLOW}✗ Modo --strict: $WARNINGS advertencia(s) tratadas como errores${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Validación OK${NC}"
exit 0
