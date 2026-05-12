# Guía de Implementación: Alertas WhatsApp con Twilio

## 📱 Descripción General

Este sistema integra alertas IoT del cultivo con WhatsApp, permitiendo que los administradores y operarios reciban notificaciones críticas directamente en su teléfono móvil.

**Estado**: 🔧 Implementación completa (Twilio listo para configurar)

### Componentes Implementados

- ✅ Modelo de Tenant con campos `phone` y `admin_phone`
- ✅ Endpoint PUT para configurar números de teléfono por tenant
- ✅ Workflow n8n adicional para envio de alertas WhatsApp
- ✅ Tablas PostgreSQL para auditoría de alertas WhatsApp
- ✅ Configuración de contactos de emergencia del sistema
- ✅ Script de setup automático

---

## 🛠️ Instalación y Configuración

### Paso 1: Preparar Credenciales de Twilio

1. Crear cuenta en [Twilio Console](https://console.twilio.com)
2. Habilitar WhatsApp Business API
3. Obtener:
   - **TWILIO_ACCOUNT_SID**: En Dashboard > Account Info
   - **TWILIO_AUTH_TOKEN**: En Dashboard > Auth Token  
   - **TWILIO_WHATSAPP_FROM**: Número WhatsApp Business asignado (ej: +34XXXXXXXXX)

### Paso 2: Configurar Variables de Entorno

```bash
# Copy the example file
cp config/.env.whatsapp.example config/.env.whatsapp.local

# Edit with your values
nano config/.env.whatsapp.local

# Key variables to set:
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_WHATSAPP_FROM="+34XXXXXXXXX"
export SYSTEM_ADMIN_PHONE="+34693443825"
```

### Paso 3: Ejecutar Setup Automático

```bash
chmod +x scripts/setup_whatsapp_alerts.sh
./scripts/setup_whatsapp_alerts.sh
```

Este script:
- ✅ Valida variables de entorno
- ✅ Ejecuta migraciones SQL
- ✅ Valida credenciales de Twilio
- ✅ Crea archivo de configuración local

### Paso 4: Importar Workflow en n8n

1. Abrir n8n en `http://localhost:5678`
2. Click en "+" > "Import from file"
3. Seleccionar: `n8n/workflows/thingsdata-whatsapp-alerts.json`
4. En el workflow importado, configurar la credencial de Twilio:
   - Click en nodo "Twilio - Enviar WhatsApp"
   - Add credential > Twilio
   - Usar `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN`

### Paso 5: Configurar Números de Teléfono del Tenant

Usa el endpoint para actualizar el número de teléfono de tu tenant:

```bash
# Configurar número de teléfono para alertas del cultivo
curl -X PUT http://localhost:8000/api/v1/tenants/caix21/phone \
  -H "Content-Type: application/json" \
  -d '{"phone": "+34693443825"}'

# Respuesta esperada:
{
  "id": "caix21",
  "name": "Caix - Invernadero Principal",
  "phone": "+34693443825",
  "admin_phone": null,
  "updated_at": "2026-04-03T15:30:00Z"
}
```

---

## 📊 Flujo de Alertas

### Arquitectura del Sistema

```
IoT Sensor
    ↓
Mosquitto MQTT → Thingsdata Ingestion
    ↓
TimescaleDB (evento almacenado)
    ↓
n8n Alert Detection
    ↓
┌─────────────────────────────────────┐
│   Clasificar Severidad              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Obtener Números de Contacto        │
│  - Tenant phone (cultivo)           │
│  - Admin phone (emergencias)        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Enviar Alertas (Multi-canal)       │
│  - WhatsApp (Twilio)               │
│  - Email                           │
│  - Slack                           │
│  - PagerDuty                       │
└─────────────────────────────────────┘
    ↓
📱 WhatsApp → +34693443825
📧 Email → admin@castuo.es
💬 Slack → #castuo-alerts
📟 PagerDuty → Incident Created
    ↓
🗄️ Auditoría: whatsapp_alert_log
```

---

## 📝 Ejemplos de Uso

### 1. Enviar Alerta por WhatsApp Manualmente

```bash
# Test de webhook de alertas WhatsApp
curl -X POST http://localhost:5678/webhook/thingsdata-alerts-whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "caix21",
    "sensor_id": "pH_INVERNADERO_001",
    "alert_type": "ANOMALY",
    "severity": "CRITICAL",
    "value": 7.5,
    "threshold": 6.5,
    "timestamp": "2026-04-03T15:30:00Z"
  }'
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "WhatsApp alert processed",
  "phone_notified": "+34693443825",
  "message_id": "SM123456789abc",
  "severity": "CRITICAL",
  "timestamp": "2026-04-03T15:32:00Z"
}
```

**Mensaje recibido en WhatsApp:**
```
🚨 *ALERTA IoT CASTÚO*

🌱*Sensor:* pH_INVERNADERO_001
📊*Tipo:* ANOMALY
🔴*Severidad:* CRITICAL
📈*Valor Actual:* 7.5
🎯*Umbral:* 6.5
⏰*Hora:* 3 de abril de 2026, 15:32:00

*Acción Requerida:* INMEDIATA

Revisa el dashboard: https://niwa.castuo.es/dashboard
```

### 2. Consultar Historial de Alertas WhatsApp

```bash
# Conectar a PostgreSQL y ejecutar:
SELECT 
    id,
    tenant_id,
    sensor_id,
    phone_number,
    severity,
    delivery_status,
    created_at
FROM public.whatsapp_alert_log
ORDER BY created_at DESC
LIMIT 10;
```

### 3. Verificar Contactos de Emergencia Configurados

```bash
# En PostgreSQL:
SELECT * FROM public.system_emergency_contacts WHERE active = true;

# Esperado:
| contact_name                    | phone_number  | role      | active |
|---------------------------------|---------------|-----------|--------|
| Admin del Sistema - CASTÚO      | +34693443825  | admin     | true   |
| Soporte Técnico - CASTÚO        | +34693443825  | technical | true   |
```

---

## 🔔 Niveles de Severidad y Umbrales

| Nivel | Emoji | Acción | Destinatarios | Canales |
|-------|-------|--------|---------------|---------|
| LOW | ℹ️ | Info | Logs | Dashboard |
| MEDIUM | ⚠️ | Revisión | Tenant | Email, Slack |
| HIGH | ⚠️ | Acción | Tenant, Team | WhatsApp, Email, Slack |
| CRITICAL | 🚨 | Inmediata | Admin, Team | WhatsApp, Email, Slack, PagerDuty |

---

## 📋 Mapeo de Parámetros

### Entrada del Webhook

```json
{
  "tenant_id": "caix21",              // ID del tenant
  "sensor_id": "pH_001",              // ID del sensor
  "alert_type": "ANOMALY|THRESHOLD",  // Tipo de alerta
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "value": 7.2,                       // Valor actual de la métrica
  "threshold": 6.5,                   // Umbral configurado
  "timestamp": "2026-04-03T..."       // ISO 8601 timestamp
}
```

### Configuración de Tenant

```python
class Tenant(BaseModel):
    id: str                           # UUID
    name: str                         # Nombre del tenant
    phone: str | None                 # Número para alertas cultivo (+34...)
    admin_phone: str | None           # Número para emergencias (+34...)
    iot_topic_prefix: str            # Tema MQTT: "caix21:invernadero"
    # ...
```

---

## 🔐 Seguridad

### Validaciones Implementadas

- ✅ **Validación multi-tenant**: Solo el tenant propietario puede actualizar su número
- ✅ **Validación de formato de teléfono**: Debe empezar con "+" y 10+ dígitos
- ✅ **Auditoría completa**: Todas las alertas WhatsApp se registran en BD
- ✅ **Rate limiting**: Protección contra spam en endpoints
- ✅ **Credenciales seguras**: Variables de entorno, nunca en código

### Checklist de Seguridad

```bash
# ✅ Validar que el token de Twilio está en .env
grep -q "TWILIO_AUTH_TOKEN" .env && echo "✅ Token secreto protegido"

# ✅ Validar que no hay números de teléfono en código
grep -r "\+34[0-9]" api/ && echo "❌ ALERTA: Número encontrado" || echo "✅ Sin números en código"

# ✅ Validar que .env está en .gitignore
grep -q ".env" .gitignore && echo "✅ .env en .gitignore"
```

---

## 🧪 Testing

### Test de Webhook Manual

```bash
# Test exitoso
$ curl -X POST http://localhost:5678/webhook/thingsdata-alerts-whatsapp \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"test","sensor_id":"TEST_001","alert_type":"ANOMALY","severity":"HIGH","value":7.5,"threshold":6.5}'

# Esperado: HTTP 200
# Status: "success"
```

### Test de Endpoint de Configuración

```bash
# Actualizar número (requiere autenticación)
$ curl -X PUT http://localhost:8000/api/v1/tenants/caix21/phone \
  -H "Authorization: Bearer token..." \
  -H "Content-Type: application/json" \
  -d '{"phone": "+34693443825"}'

# Validación: Número inválido
$ curl -X PUT http://localhost:8000/api/v1/tenants/caix21/phone \
  -d '{"phone": "676123456"}'  # Sin "+"
# Esperado: HTTP 400 - "debe comenzar con +"
```

---

## 📱 Status de Integración

| Componente | Estado | Notas |
|-----------|--------|-------|
| Modelo Tenant | ✅ Done | Campos `phone` agregados |
| Endpoint PUT | ✅ Done | Configuración de números |
| Migración SQL | ✅ Done | Tablas y auditoría creadas |
| Workflow n8n | ✅ Done | Thingsdata-whatsapp-alerts.json |
| Twilio SDK | ⚙️ Config | Requiere credenciales |
| Testing | ⚙️ Pending | Suite de tests unitarios |
| Documentación | ✅ Done | Este archivo |

---

## 🐛 Troubleshooting

### Problema: "TWILIO_ACCOUNT_SID no configurado"
```bash
# Solución:
export TWILIO_ACCOUNT_SID="ACxxxxxxx..."
# O agregar en .env/.env.local
```

### Problema: "No se envía WhatsApp"
```bash
# 1. Verificar que el número existe en tenant_notification_config
SELECT * FROM public.tenant_notification_config WHERE tenant_id = 'caix21';

# 2. Verificar que whatsapp_enabled = true
UPDATE public.tenant_notification_config 
SET whatsapp_enabled = true 
WHERE tenant_id = 'caix21';

# 3. Verificar logs de n8n
docker logs n8n | grep -i whatsapp
```

### Problema: "Credencial de Twilio inválida en n8n"
```bash
# 1. En n8n, ir a:
# Credentials > Twilio > Edit
# 2. Verificar SID y Token desde:
# https://console.twilio.com → Account Info
# 3. Copiar exactamente, sin espacios
```

---

## 📚 Archivos de Referencia

- **Endpoint**: `/api/routers/tenant.py` (línea ~50)
- **Modelo**: `/api/models/tenant.py`
- **Workflow n8n**: `/n8n/workflows/thingsdata-whatsapp-alerts.json`
- **Migraciones SQL**: `/infrastructure/migrations/001_add_phone_to_tenants.sql`
- **Setup Script**: `/scripts/setup_whatsapp_alerts.sh`
- **Config Example**: `/config/.env.whatsapp.example`

---

## 🚀 Próximos Pasos

1. **Integración con Dashboard Frontend**
   - Pantalla de configuración de números
   - Historial de alertas enviadas
   - Estadísticas de entrega WhatsApp

2. **Mejoras de UX**
   - Botones rápidos en WhatsApp para confirmar acción
   - Respuestas por WhatsApp (webhook bidireccional)
   - Notificaciones agrupadas (no ocho alertas por minuto)

3. **Escalabilidad**
   - Rate limiting inteligente por tenant
   - Retry automático con exponential backoff
   - Fallback a SMS si WhatsApp falla

---

## 📞 Soporte

Para problemas o preguntas:
- Issue en GitHub
- Slack: #castuo-support
- Email: admin@castuo.es / +34693443825

**Tu número de teléfono para emergencias**: +34693443825 ✅ Configurado
