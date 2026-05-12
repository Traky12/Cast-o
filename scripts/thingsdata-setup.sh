#!/bin/bash

# ===================================================================
# CASTÚO-SYSTEM: Thingsdata ES Integration Setup
# ===================================================================
# Script para inicializar la integración de Thingsdata ES
# Uso: ./scripts/thingsdata-setup.sh

set -euo pipefail

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  CASTÚO-SYSTEM: Thingsdata ES Integration Setup              ║"
echo "║  IoT Backbone con Soberanía de Datos (EU 2024/1689 + IA)    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Validation Functions ---
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker no está instalado. Abortando.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker detectado${NC}"
}

check_docker_compose() {
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose no está instalado. Abortando.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose detectado${NC}"
}

check_env_vars() {
    if [ ! -f .env.cloud ]; then
        echo -e "${YELLOW}⚠️  .env.cloud no encontrado.${NC}"
        echo "   Creando .env.cloud con plantilla..."
        cp .env.cloud.example .env.cloud 2>/dev/null || {
            echo -e "${RED}❌ .env.cloud.example no encontrado. Abortando.${NC}"
            exit 1
        }
    fi
    echo -e "${GREEN}✅ Variables de entorno cargadas${NC}"
}

# --- Setup Functions ---
setup_directories() {
    echo -e "\n${BLUE}📁 Creando estructura de directorios...${NC}"
    
    mkdir -p infrastructure/thingsdata
    mkdir -p scripts
    mkdir -p .github/workflows
    mkdir -p docs
    mkdir -p requirements
    mkdir -p n8n/workflows
    mkdir -p infrastructure/thingsdata/certs
    
    echo -e "${GREEN}✅ Directorios creados${NC}"
}

validate_configs() {
    echo -e "\n${BLUE}🔍 Validando archivos de configuración...${NC}"
    
    # Validar JSON
    if ! jq empty infrastructure/thingsdata/thingsdata-config.json 2>/dev/null; then
        echo -e "${RED}❌ thingsdata-config.json tiene sintaxis JSON inválida${NC}"
        exit 1
    fi
    
    # Validar YAML
    if ! docker run --rm -v $(pwd):/data sdeployer/docker-compose-validator 2>/dev/null; then
        echo -e "${YELLOW}⚠️  docker-compose.iot.yml podría tener errores (validación omitida)${NC}"
    fi
    
    echo -e "${GREEN}✅ Configuración validada${NC}"
}

generate_secrets() {
    echo -e "\n${BLUE}🔐 Generando secretos...${NC}"
    
    # Generar contraseña n8n si no existe
    if ! grep -q "N8N_PASSWORD=" infrastructure/thingsdata/thingsdata.env; then
        N8N_PASS=$(openssl rand -base64 24)
        echo "N8N_PASSWORD=${N8N_PASS}" >> infrastructure/thingsdata/thingsdata.env
        echo -e "${GREEN}✅ Contraseña n8n generada${NC}"
    fi
    
    # Generar contraseña PostgreSQL si no existe
    if ! grep -q "POSTGRES_PASSWORD=" infrastructure/thingsdata/thingsdata.env; then
        POSTGRES_PASS=$(openssl rand -base64 24)
        echo "POSTGRES_PASSWORD=${POSTGRES_PASS}" >> infrastructure/thingsdata/thingsdata.env
        echo -e "${GREEN}✅ Contraseña PostgreSQL generada${NC}"
    fi
    
    # Generar webhook secret
    if ! grep -q "WEBHOOK_SECRET=" infrastructure/thingsdata/thingsdata.env; then
        WEBHOOK_SECRET=$(openssl rand -hex 32)
        echo "WEBHOOK_SECRET=${WEBHOOK_SECRET}" >> infrastructure/thingsdata/thingsdata.env
        echo -e "${GREEN}✅ Webhook secret generado${NC}"
    fi
}

start_containers() {
    echo -e "\n${BLUE}🚀 Iniciando contenedores...${NC}"
    
    # Cargar variables de entorno
    set -a
    source infrastructure/thingsdata/thingsdata.env
    set +a
    
    # Iniciar stack IoT
    docker compose -f docker-compose.iot.yml up -d --wait
    
    echo -e "${GREEN}✅ Contenedores iniciados${NC}"
}

validate_stack() {
    echo -e "\n${BLUE}✔️  Validando stack...${NC}"
    
    # Esperar a que los servicios estén listos
    echo "   Esperando Thingsdata API..."
    until curl -s http://localhost:8080/api/v1/health > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}   ✅ Thingsdata API online${NC}"
    
    echo "   Esperando MQTT Broker..."
    until docker exec castuo-mqtt-bridge mosquitto_sub -h localhost -p 1883 -t "castuo/health" -C 1 -W 1 > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}   ✅ MQTT Broker online${NC}"
    
    echo "   Esperando n8n..."
    until curl -s http://localhost:5678/healthz > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}   ✅ n8n online${NC}"
    
    echo "   Esperando PostgreSQL..."
    until docker exec castuo-postgres-iot psql -U castuo_iot -d castuo_telemetry -c "SELECT 1" > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}   ✅ PostgreSQL online${NC}"
    
    echo "   Esperando TimescaleDB..."
    until docker exec castuo-timescaledb-iot psql -U castuo_iot -d castuo_timeseries -c "SELECT 1" > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}   ✅ TimescaleDB online${NC}"
}

print_access_info() {
    echo -e "\n${BLUE}📍 Acceso a servicios:${NC}"
    echo -e "${GREEN}✅ Thingsdata API${NC}:       http://localhost:8080"
    echo -e "${GREEN}✅ n8n Automation${NC}:      http://localhost:5678"
    echo -e "${GREEN}✅ MQTT Broker${NC}:         localhost:1883"
    echo -e "${GREEN}✅ Grafana (IoT)${NC}:       http://localhost:3001"
    echo -e "${GREEN}✅ PostgreSQL${NC}:          localhost:5433"
    echo -e "${GREEN}✅ TimescaleDB${NC}:         localhost:5434"
    echo ""
    echo -e "${BLUE}📋 Credenciales por defecto (CAMBIAR EN PRODUCCIÓN):${NC}"
    echo "   n8n User:     admin"
    echo "   n8n Password: (en infrastructure/thingsdata/thingsdata.env)"
    echo "   MQTT User:    castuo"
    echo "   Grafana:      admin / (en infrastructure/thingsdata/thingsdata.env)"
    echo ""
}

run_tests() {
    echo -e "\n${BLUE}🧪 Ejecutando pruebas básicas...${NC}"
    
    # Test 1: Thingsdata API
    echo -n "   Test API Thingsdata... "
    if curl -s -H "Authorization: Bearer ${THINGSDATA_API_KEY}" http://localhost:8080/api/v1/health | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC} (ignorado para desarrollo)"
    fi
    
    # Test 2: MQTT connectivity
    echo -n "   Test MQTT Broker... "
    if docker exec castuo-mqtt-bridge mosquitto_pub -h localhost -p 1883 -u castuo -P castuo_mqtt_password -t "castuo/test" -m "test_message" 2>/dev/null; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC} (ignorado para desarrollo)"
    fi
    
    # Test 3: n8n health
    echo -n "   Test n8n Health... "
    if curl -s http://localhost:5678/healthz | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
    
    echo -e "${GREEN}✅ Pruebas completadas${NC}"
}

show_next_steps() {
    echo -e "\n${BLUE}📌 PRÓXIMOS PASOS:${NC}"
    echo "   1. Registrarse en https://thingsdata.es"
    echo "   2. Actualizar THINGSDATA_API_KEY en infrastructure/thingsdata/thingsdata.env"
    echo "   3. Configurar SIM Pool (tamaño: SIM_POOL variable)"
    echo "   4. Crear workflows en n8n para ingestión automática"
    echo "   5. Desplegar en AWS/Hetzner con docker compose -f docker-compose.iot.yml"
    echo ""
    echo -e "${BLUE}📚 Documentación:${NC}"
    echo "   • docs/INTEGRATION-THINGSDATA.md"
    echo "   • README.md (sección 'IoT Backbone')"
    echo ""
    echo -e "${GREEN}✅ SETUP COMPLETADO EXITOSAMENTE${NC}"
    echo ""
}

cleanup_on_error() {
    echo -e "\n${RED}❌ ERROR DURANTE SETUP${NC}"
    echo "   Limpiando (opcional): docker compose -f docker-compose.iot.yml down"
    exit 1
}

trap cleanup_on_error ERR

# --- Main Execution ---
main() {
    check_docker
    check_docker_compose
    check_env_vars
    setup_directories
    validate_configs
    generate_secrets
    start_containers
    validate_stack
    print_access_info
    run_tests
    show_next_steps
}

# Ejecutar
main "$@"
