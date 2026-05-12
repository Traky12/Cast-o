#!/bin/bash

# Validación Rápida de Integración WhatsApp
# Uso: ./scripts/validate_whatsapp_integration.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 Validación de Integración WhatsApp - CASTÚO-SYSTEM${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Función para imprimir resultado
check_step() {
    local name=$1
    local exit_code=$2
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅${NC} ${name}"
    else
        echo -e "${RED}❌${NC} ${name}"
    fi
}

# 1. Validar archivo .env.local
echo -e "${YELLOW}1️⃣  Validando configuración${NC}"
if [ -f ".env.local" ]; then
    check_step ".env.local existe" 0
    
    # Validar que tiene credenciales de Twilio
    if grep -q "TWILIO_ACCOUNT_SID" .env.local; then
        check_step "TWILIO_ACCOUNT_SID configurado" 0
    else
        check_step "TWILIO_ACCOUNT_SID configurado" 1
    fi
    
    if grep -q "TWILIO_AUTH_TOKEN" .env.local; then
        check_step "TWILIO_AUTH_TOKEN configurado" 0
    else
        check_step "TWILIO_AUTH_TOKEN configurado" 1
    fi
    
    if grep -q "TWILIO_WHATSAPP_FROM" .env.local; then
        check_step "TWILIO_WHATSAPP_FROM configurado" 0
    else
        check_step "TWILIO_WHATSAPP_FROM configurado" 1
    fi
else
    check_step ".env.local existe" 1
    echo -e "${YELLOW}⚠️  Crear con: cp .env.example .env.local${NC}"
fi

echo ""
echo -e "${YELLOW}2️⃣  Validando contenedores Docker${NC}"

# Validar que docker está corriendo
if command -v docker &> /dev/null; then
    check_step "Docker instalado" 0
    
    # Validar que FastAPI está corriendo
    if docker ps | grep -q "sabionda-api"; then
        check_step "FastAPI corriendo" 0
    else
        check_step "FastAPI corriendo" 1
        echo -e "${YELLOW}   💡 Inicia con: docker-compose up -d${NC}"
    fi
    
    # Validar que n8n está corriendo
    if docker ps | grep -q "sabionda-n8n"; then
        check_step "n8n corriendo" 0
    else
        check_step "n8n corriendo" 1
    fi
    
    # Validar que PostgreSQL está corriendo
    if docker ps | grep -q "sabionda-postgres"; then
        check_step "PostgreSQL corriendo" 0
    else
        check_step "PostgreSQL corriendo" 1
    fi
else
    check_step "Docker instalado" 1
fi

echo ""
echo -e "${YELLOW}3️⃣  Validando conectividad${NC}"

# Validar FastAPI health
if command -v curl &> /dev/null; then
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        check_step "FastAPI responde a /health" 0
    else
        check_step "FastAPI responde a /health" 1
        echo -e "${YELLOW}   💡 FastAPI puede estar iniciando, espera 30 segundos${NC}"
    fi
    
    # Validar endpoint de tenants
    if curl -s -f http://localhost:8000/api/v1/tenants/current > /dev/null 2>&1; then
        check_step "Endpoint GET /api/v1/tenants/current accesible" 0
    else
        check_step "Endpoint GET /api/v1/tenants/current accesible" 1
        echo -e "${YELLOW}   💡 Requiere autenticación, esto es normal${NC}"
    fi
    
    # Validar n8n
    if curl -s -f http://localhost:5678 > /dev/null 2>&1; then
        check_step "n8n accesible en puerto 5678" 0
    else
        check_step "n8n accesible en puerto 5678" 1
    fi
else
    echo -e "${YELLOW}⚠️  curl no instalado, omitiendo tests de conectividad${NC}"
fi

echo ""
echo -e "${YELLOW}4️⃣  Validando archivos de integración${NC}"

# Validar que los archivos están en lugar
files=(
    "api/routers/tenant.py"
    "api/models/tenant.py"
    "n8n/workflows/thingsdata-whatsapp-alerts.json"
    "infrastructure/migrations/001_add_phone_to_tenants.sql"
    "docker-compose.yml"
    "docs/IMPLEMENTATION-WHATSAPP.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        check_step "$file existe" 0
    else
        check_step "$file existe" 1
    fi
done

echo ""
echo -e "${YELLOW}5️⃣  Validando base de datos${NC}"

# Si psql está instalado, validar tablas
if command -v psql &> /dev/null; then
    # Intentar conectar a la BD
    if psql -h localhost -U castuo -d castuo_db -c "SELECT 1" > /dev/null 2>&1; then
        check_step "Conexión a PostgreSQL exitosa" 0
        
        # Validar que las tablas existen
        TABLE_COUNT=$(psql -h localhost -U castuo -d castuo_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('tenant_notification_config', 'whatsapp_alert_log', 'system_emergency_contacts')")
        
        if [ "$TABLE_COUNT" -eq "3" ]; then
            check_step "Tablas WhatsApp creadas (3/3)" 0
        else
            check_step "Tablas WhatsApp creadas ($TABLE_COUNT/3)" 1
            echo -e "${YELLOW}   💡 Ejecutar: psql -h localhost -U castuo -d castuo_db -f infrastructure/migrations/001_add_phone_to_tenants.sql${NC}"
        fi
        
        # Validar que admin contact existe
        ADMIN_COUNT=$(psql -h localhost -U castuo -d castuo_db -t -c "SELECT COUNT(*) FROM system_emergency_contacts WHERE phone_number = '+34693443825'")
        
        if [ "$ADMIN_COUNT" -gt "0" ]; then
            check_step "Contacto admin registrado" 0
        else
            check_step "Contacto admin registrado" 1
        fi
    else
        check_step "Conexión a PostgreSQL exitosa" 1
        echo -e "${YELLOW}   💡 Asegúrate de que PostgreSQL está corriendo${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  psql no instalado, omitiendo validación de BD${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}📋 Resumen de Validación${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Próximos pasos:"
echo ""
echo "1️⃣  Si todo está ✅:"
echo "   - Sistema está listo para recibir alertas"
echo "   - Continúa con: INTEGRATION-CHECKLIST.md (Paso 6)"
echo ""
echo "2️⃣  Si hay ❌:"
echo "   - Revisar el mensaje de error arriba"
echo "   - Seguir troubleshooting en: INTEGRATION-CHECKLIST.md"
echo ""
echo "3️⃣  Para más detalles:"
echo "   - Documentación: docs/IMPLEMENTATION-WHATSAPP.md"
echo "   - Setup: scripts/setup_whatsapp_alerts.sh"
echo ""

# Retornar código de error si hay problemas
if grep -q "❌" <<< "$(echo $OUTPUT)"; then
    exit 1
else
    exit 0
fi
