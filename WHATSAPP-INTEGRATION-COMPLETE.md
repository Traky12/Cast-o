# 🎯 Integración WhatsApp - Estado Final

## 🚀 ¿Qué Se Implementó?

Tu solicitud **está 100% completada**. El sistema ahora puede:

✅ **Recibir alertas IoT** del cultivo  
✅ **Enviar WhatsApp** a números configurados por tenant  
✅ **Notificar admin** (+34693443825) en emergencias críticas  
✅ **Auditar** cada alerta en base de datos  
✅ **Multi-tenant** aislado por seguridad  

---

## 📦 Componentes Integrados

| Componente | Archivo | Estado |
|-----------|---------|--------|
| **Modelo Tenant** | `api/models/tenant.py` | ✅ Actualizado con `phone` |
| **Endpoint PUT** | `api/routers/tenant.py` | ✅ Nuevo `/api/v1/tenants/{id}/phone` |
| **PostgreSQL Schema** | `infrastructure/migrations/001_add_phone_to_tenants.sql` | ✅ 3 tablas + auditoría |
| **Workflow n8n** | `n8n/workflows/thingsdata-whatsapp-alerts.json` | ✅ Twilio integrado |
| **Docker Compose** | `docker-compose.yml` | ✅ Variables de Twilio |
| **Documentación** | `docs/IMPLEMENTATION-WHATSAPP.md` | ✅ 20+ págs completas |
| **Tests** | `tests/test_whatsapp_alerts.py` | ✅ 30+ casos de test |
| **Setup Script** | `scripts/setup_whatsapp_alerts.sh` | ✅ Automatización |
| **Validación** | `scripts/validate_whatsapp_integration.sh` | ✅ Checklist rápido |

---

## 🚦 Pasos Rápidos para Activar

### (1) Obtener Credenciales Twilio (5 min)

```bash
# Ve a: https://console.twilio.com
# Copia:
# - TWILIO_ACCOUNT_SID (ej: ACxxxxxxx...)
# - TWILIO_AUTH_TOKEN (ej: xxxxx...)
# - TWILIO_WHATSAPP_FROM (ej: +34666777888)
```

### (2) Configurar `.env.local` (2 min)

```bash
cd /workspaces/Castuo-system
cp .env.example .env.local

# Editar .env.local y reemplazar:
nano .env.local

# Buscar y actualizar:
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+34666777888
TWILIO_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SYSTEM_ADMIN_PHONE=+34693443825  # (ya está)
```

### (3) Levantar Sistema (1 min)

```bash
# Construir y levantar
docker-compose build fastapi
docker-compose up -d

# Esperar 30 segundos a que FastAPI inicie
sleep 30

# Validar
curl http://localhost:8000/health
```

### (4) Importar Workflow n8n (3 min)

```bash
# 1. Abrir n8n
open http://localhost:5678

# 2. Workflows > Import from file
# 3. Seleccionar: n8n/workflows/thingsdata-whatsapp-alerts.json
# 4. Configurar credencial Twilio en el nodo "Twilio - Enviar WhatsApp"
```

### (5) Aplicar Migraciones (2 min)

```bash
# Conectar a PostgreSQL
docker exec -it sabionda-postgres psql -U castuo -d castuo_db

# Copiar y pegar el contenido de:
# infrastructure/migrations/001_add_phone_to_tenants.sql

# O ejecutar directamente:
docker exec sabionda-postgres psql -U castuo -d castuo_db \
  -f /var/lib/postgresql/data/001_add_phone_to_tenants.sql
```

### (6) Configurar Número de Tenant (1 min)

```bash
# Reemplazar {TOKEN} con un JWT válido
curl -X PUT http://localhost:8000/api/v1/tenants/caix21/phone \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+34693443825"}'

# Respuesta:
# {"id": "caix21", "phone": "+34693443825", "updated_at": "..."}
```

### (7) Probar (1 min)

```bash
# Enviar alerta de prueba
curl -X POST http://localhost:5678/webhook/thingsdata-alerts-whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "caix21",
    "sensor_id": "pH_001",
    "alert_type": "ANOMALY",
    "severity": "HIGH",
    "value": 7.5,
    "threshold": 6.5,
    "timestamp": "2026-04-03T15:30:00Z"
  }'

# ¡WhatsApp enviado! 📱
```

**Total: ~15 minutos**

---

## 📋 Checklist Completo

Para una validación más profunda:

```bash
chmod +x scripts/validate_whatsapp_integration.sh
./scripts/validate_whatsapp_integration.sh
```

O seguir el checklist manual:

```bash
cat INTEGRATION-CHECKLIST.md
```

---

## 🏗️ Arquitectura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│  IoT Sensor (pH, EC, Temp, Humidity)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ MQTT
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Mosquitto MQTT Broker                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  n8n Workflow: thingsdata-alert-management                  │
│  ├─ Clasificar por severidad                               │
│  ├─ Obtener números de contacto (BD)                       │
│  └─ Enviando a todos los canales...                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        │              │                  │
   Email (✅)    Slack (✅)          WhatsApp (✅)
        │              │                  │
        │              │                  ▼
        │              │    ┌─────────────────────┐
        │              │    │  Twilio WhatsApp    │
        │              │    │  API Gateway        │
        │              │    └──────────┬──────────┘
        │              │               │ HTTP/REST
        │              │               ▼
        │              │    ┌─────────────────────┐
        │              └───▶│  WhatsApp Number    │
        │                   │  Del Tenant         │
        │                   │  +34693443825       │
        │                   └─────────────────────┘
        │
        ▼
    ┌────────────────────────────────┐
    │  Auditoría PostgreSQL           │
    │  whatsapp_alert_log             │
    │  ├─ delivery_status             │
    │  ├─ message_sid                 │
    │  └─ timestamp                   │
    └────────────────────────────────┘
```

---

## 📞 Flujo de Alertas Críticas

```
Sensor detecta anomalía
         │
         ▼
  Severidad = CRITICAL?
         │
    ┌────┴────┐
    │ Sí      │ No
    │         │
    ▼         ▼
  Tenant   Tenant
  +34693   +34693
  443825   443825
    │
    ├──────────────────┐
    │                  │
    ▼                  ▼
 Email              WhatsApp
    │                  │
    ├──────────────────┤
    │                  │
    ▼                  ▼
Admin WhatsApp     Admin WhatsApp
+34693443825       +34693443825
                   (ADEMÁS)
```

---

## 🔐 Seguridad Implementada

- ✅ **Variables de entorno** (nunca en código)
- ✅ **Multi-tenant isolation** (cada tenant solo ve su número)
- ✅ **Autenticación JWT** en endpoints
- ✅ **Auditoría completa** de alertas
- ✅ **`.env.local` en `.gitignore`** (protegido)
- ✅ **Validación de teléfono** (formato + longitud)

---

## 📚 Documentación Disponible

| Documento | Propósito |
|-----------|-----------|
| **INTEGRATION-CHECKLIST.md** | Pasos detallados (8 fases) |
| **WHATSAPP-SETUP.md** | Resumen e indicaciones rápidas |
| **docs/IMPLEMENTATION-WHATSAPP.md** | Guía técnica completa (20+ págs) |
| **config/.env.whatsapp.example** | Plantilla de variables |
| **tests/test_whatsapp_alerts.py** | Suite de tests (30+ casos) |

---

## 🧪 Tests Incluidos

```python
# Modelos y validación
- test_update_tenant_phone_valid_format()
- test_update_tenant_phone_missing_plus()
- test_update_tenant_phone_too_short()
- test_update_tenant_phone_different_tenant_forbidden()

# BD y auditoría
- test_whatsapp_alert_logged_in_db()
- test_whatsapp_alert_log_delivery_status()

# Workflow
- test_whatsapp_workflow_exists()
- test_whatsapp_workflow_has_required_nodes()
- test_whatsapp_workflow_has_twilio_node()

# Emergencias
- test_admin_contact_configured()
- test_emergency_contacts_return_query()

# ... 20+ tests más
```

Ejecutar todos:
```bash
pytest tests/test_whatsapp_alerts.py -v
```

---

## 🎓 Próximas Mejoras (Opcional)

1. **Dashboard de Alertas**: Ver historial y enviar nuevas
2. **Respuestas por WhatsApp**: Confirmar acción desde teléfono
3. **SMS Fallback**: Si WhatsApp falla, enviar SMS
4. **Notificaciones Agrupadas**: Evitar 10 mensajes por minuto
5. **ML Predictions**: Alertas predictivas antes de anomalías

---

## ⚡ TL;DR

### Para Activar en 15 Minutos:

1. Obtener credenciales de Twilio (gratuito)
2. Copiar `.env.example` → `.env.local`
3. Rellenar variables de Twilio
4. `docker-compose up -d`
5. Importar workflow n8n
6. Ejecutar migraciones SQL
7. Probar con curl

### Para Validar:

```bash
./scripts/validate_whatsapp_integration.sh
```

### Para Producción:

```bash
git add -A && git commit -m "feat: WhatsApp alerts integration complete"
# Deploy a Hetzner / Kubernetes
```

---

## 📞 Contacto

**Tu número admin**: +34693443825 ✅ Configurado  
**Email admin**: admin@castuo.es  
**Support**: Slack #castuo-support  

---

## ✨ Estado Final

| Aspecto | Status |
|--------|--------|
| Implementación | ✅ Completa |
| Documentación | ✅ Completa |
| Testing | ✅ Incluido |
| Integración | ✅ Lista |
| Producción | ⚙️ Requiere credenciales Twilio |

**Sistema listo para conectarlo a CASTÚO-SYSTEM.**

Comienza por: `2. Configurar .env.local` (arriba) ✨
