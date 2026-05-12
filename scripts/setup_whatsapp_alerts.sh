#!/bin/bash

# Setup Script para Integración WhatsApp - CASTÚO-SYSTEM
# Este script configura la integración de alertas por WhatsApp con Twilio
# Uso: ./setup_whatsapp_alerts.sh

set -e

echo "🚀 Iniciando setup de alertas WhatsApp para CASTÚO-SYSTEM..."
echo "================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Validar que tenemos las variables de entorno necesarias
echo -e "${YELLOW}📋 Validando variables de entorno...${NC}"

if [ -z "$TWILIO_ACCOUNT_SID" ]; then
    echo -e "${RED}❌ Error: TWILIO_ACCOUNT_SID no está configurado${NC}"
    exit 1
fi

if [ -z "$TWILIO_AUTH_TOKEN" ]; then
    echo -e "${RED}❌ Error: TWILIO_AUTH_TOKEN no está configurado${NC}"
    exit 1
fi

if [ -z "$TWILIO_WHATSAPP_FROM" ]; then
    echo -e "${RED}❌ Error: TWILIO_WHATSAPP_FROM no está configurado${NC}"
    exit 1
fi

if [ -z "$SYSTEM_ADMIN_PHONE" ]; then
    echo -e "${RED}❌ Error: SYSTEM_ADMIN_PHONE no está configurado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Variables de entorno validadas${NC}"

# 2. Ejecutar migración SQL
echo -e "${YELLOW}🗄️  Ejecutando migraciones SQL...${NC}"

if [ -z "$POSTGRES_HOST" ]; then
    POSTGRES_HOST="localhost"
fi

if [ -z "$POSTGRES_PORT" ]; then
    POSTGRES_PORT="5432"
fi

if [ -z "$POSTGRES_DB" ]; then
    POSTGRES_DB="castuo"
fi

if [ -z "$POSTGRES_USER" ]; then
    POSTGRES_USER="postgres"
fi

# Intentar ejecutar la migración
if [ -f "infrastructure/migrations/001_add_phone_to_tenants.sql" ]; then
    echo "Ejecutando: infrastructure/migrations/001_add_phone_to_tenants.sql"
    
    # Usar psql si existe
    if command -v psql &> /dev/null; then
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -f infrastructure/migrations/001_add_phone_to_tenants.sql
        echo -e "${GREEN}✅ Migración SQL completada${NC}"
    else
        echo -e "${YELLOW}⚠️  psql no encontrado, se necesitará ejecutar manualmente${NC}"
        echo "Ejecuta manualmente:"
        echo "psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -f infrastructure/migrations/001_add_phone_to_tenants.sql"
    fi
else
    echo -e "${YELLOW}⚠️  Archivo de migración no encontrado${NC}"
fi

# 3. Validar conexión con Twilio
echo -e "${YELLOW}📱 Validando credenciales de Twilio...${NC}"

# Crear script Python para validar Twilio
cat > /tmp/validate_twilio.py << 'EOF'
#!/usr/bin/env python3
import os
import sys

try:
    from twilio.rest import Client
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        print("❌ Credenciales de Twilio no configuradas")
        sys.exit(1)
    
    client = Client(account_sid, auth_token)
    account = client.api.accounts(account_sid).fetch()
    
    print(f"✅ Conexión a Twilio exitosa")
    print(f"   Cuenta: {account.friendly_name}")
    print(f"   Estado: {account.status}")
    
except ImportError:
    print("⚠️  Librería twilio-python no instalada")
    print("   Instala con: pip install twilio")
except Exception as e:
    print(f"❌ Error validando Twilio: {e}")
    sys.exit(1)
EOF

python3 /tmp/validate_twilio.py || echo -e "${YELLOW}⚠️  No se pudo validar Twilio, continúa configurando manualmente${NC}"

# 4. Crear archivo de configuración local
echo -e "${YELLOW}🔧 Creando archivo de configuración local...${NC}"

# Crear .env.whatsapp.local basado en el ejemplo
if [ ! -f ".env.whatsapp.local" ]; then
    cp config/.env.whatsapp.example .env.whatsapp.local
    
    # Reemplazar valores en el archivo local
    sed -i "s|your_twilio_account_sid_here|$TWILIO_ACCOUNT_SID|g" .env.whatsapp.local
    sed -i "s|your_twilio_auth_token_here|$TWILIO_AUTH_TOKEN|g" .env.whatsapp.local
    sed -i "s|+34XXXXXXXXX|$TWILIO_WHATSAPP_FROM|g" .env.whatsapp.local
    sed -i "s|+34693443825|$SYSTEM_ADMIN_PHONE|g" .env.whatsapp.local
    
    echo -e "${GREEN}✅ Archivo .env.whatsapp.local creado${NC}"
else
    echo -e "${YELLOW}⚠️  .env.whatsapp.local ya existe, no se sobrescribió${NC}"
fi

# 5. Mostrar instrucciones de siguiente paso
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}✅ Setup de WhatsApp completado${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Verifica que .env.whatsapp.local contiene tus credenciales:"
echo "   - TWILIO_ACCOUNT_SID"
echo "   - TWILIO_AUTH_TOKEN"
echo "   - TWILIO_WHATSAPP_FROM"
echo "   - SYSTEM_ADMIN_PHONE=$SYSTEM_ADMIN_PHONE"
echo ""
echo "2. Importa el workflow n8n:"
echo "   n8n/workflows/thingsdata-whatsapp-alerts.json"
echo ""
echo "3. En n8n, configura la credencial de Twilio:"
echo "   Credentials > Create New > Twilio"
echo "   Usa TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN de arriba"
echo ""
echo "4. Actualiza los números de teléfono de tus tenants:"
echo "   PUT /api/v1/tenants/{tenant_id}/phone"
echo "   Body: {\"phone\": \"+34XXXXX\"}"
echo ""
echo "5. Prueba enviando una alerta:"
echo "   POST http://localhost:8000/thingsdata/alerts/whatsapp"
echo "   Body: {\"tenant_id\": \"caix21\", \"sensor_id\": \"pH_001\", ...}"
echo ""
echo -e "${YELLOW}Para más información, revisa:${NC}"
echo "- docs/IMPLEMENTATION-WHATSAPP.md"
echo "- config/.env.whatsapp.example"
echo "- n8n/workflows/thingsdata-whatsapp-alerts.json"
echo ""
