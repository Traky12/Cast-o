# 🔗 Checklist de Integración WhatsApp → CASTÚO-SYSTEM

## ✅ Estado de Implementación Actual

Todos los componentes están desarrollados e integrados. Este checklist te guía para completar la configuración y validación.

---

## 📋 Paso 1: Preparar Credenciales de Twilio

### 1.1 Crear Cuenta Twilio

- [ ] Ir a https://www.twilio.com/console
- [ ] Registrarse o iniciar sesión
- [ ] Verificar email y teléfono
- [ ] Activar prueba gratuita ($15 crédito)

### 1.2 Habilitar WhatsApp Business API

- [ ] En Twilio Console → Messaging → Services
- [ ] Crear nuevo servicio (o usar el existente)
- [ ] Habilitar WhatsApp channel
- [ ] Agregar número WhatsApp Business (ej: Tu carrier o Twilio-provided)
- [ ] Copiar el número en formato `+34XXXXXXXXX`

### 1.3 Obtener Credenciales

- [ ] **TWILIO_ACCOUNT_SID**: Dashboard → Account Info → SID
  ```
  ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

- [ ] **TWILIO_AUTH_TOKEN**: Dashboard → Auth Token
  ```
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

- [ ] **TWILIO_WHATSAPP_FROM**: Messaging → Services → Active Number
  ```
  +34XXXXXXXXX  (ej: +34666777888)
  ```

- [ ] **TWILIO_API_TOKEN**: Same as AUTH_TOKEN
  ```
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ```

---

## 📝 Paso 2: Configurar Variables de Entorno

### 2.1 Crear Archivo `.env.local`

```bash
cd /workspaces/Castuo-system

# Copiar plantilla
cp .env.example .env.local

# Editar con tus valores
nano .env.local
```

### 2.2 Reemplazar Valores de Twilio

En `.env.local`, buscar y reemplazar:

```bash
# ANTES (línea ~190):
TWILIO_ACCOUNT_SID=<CHANGE_ME>
TWILIO_AUTH_TOKEN=<CHANGE_ME>
TWILIO_WHATSAPP_FROM=<CHANGE_ME>
TWILIO_API_TOKEN=<CHANGE_ME>

# DESPUÉS (con tus valores):
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=+34666777888
TWILIO_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2.3 Configurar Contactos de Emergencia

En `.env.local`:

```bash
# Tu número de admin (ya configurado):
SYSTEM_ADMIN_PHONE=+34693443825
SYSTEM_ADMIN_EMAIL=admin@castuo.es

# Habilitar alertas WhatsApp
ENABLE_WHATSAPP_ALERTS=true
DEFAULT_ALERT_CHANNELS=whatsapp,email,slack
WHATSAPP_MIN_SEVERITY=HIGH
```

### 2.4 Validar `.env.local`

```bash
# Verificar que todas las variables están configuradas
grep -E "TWILIO|WHATSAPP|SYSTEM_ADMIN" .env.local | grep -v "<CHANGE_ME>"

# Esperado:
TWILIO_ACCOUNT_SID=ACxxxxxxx...
TWILIO_AUTH_TOKEN=xxxxxxx...
TWILIO_WHATSAPP_FROM=+34666777888
TWILIO_API_TOKEN=xxxxxxx...
SYSTEM_ADMIN_PHONE=+34693443825
```

### ⚠️ SEGURIDAD: NO COMMITEAR `.env.local`

```bash
# Verificar que .env.local está en .gitignore
grep ".env" .gitignore

# Si no está, agregar:
echo ".env.local" >> .gitignore
echo ".env" >> .gitignore
git add .gitignore && git commit -m "fix: asegurar .env en .gitignore"
```

---

## 🚀 Paso 3: Levantar Sistema con Docker Compose

### 3.1 Validar Que Docker Está Corriendo

```bash
docker --version
docker-compose --version
docker ps  # Verificar cualquier contenedor existente
```

### 3.2 Construir e Iniciar

```bash
cd /workspaces/Castuo-system

# Construir imagen de FastAPI con las nuevas variables
docker-compose build fastapi

# Levantar todos los servicios
docker-compose up -d

# Verificar que todo está corriendo
docker-compose ps
```

**Esperado:**
```
STATUS          NAMES
Up (healthy)    sabionda-api
Up (healthy)    sabionda-n8n
Up (healthy)    sabionda-postgres
```

### 3.3 Validar Que FastAPI Está Corriendo

```bash
# Esperar unos segundos a que FastAPI inicie
sleep 10

# Verificar health
curl http://localhost:8000/health

# Esperado:
{
  "status": "ok",
  "uptime": 12.345,
  "version": "3.1.1"
}
```

---

## 📱 Paso 4: Configurar n8n

### 4.1 Acceder a n8n

```bash
# Abrir en navegador
open http://localhost:5678

# O desde terminal remota:
# https://n8n.castuo-system.cloud (en producción)
```

### 4.2 Importar Workflow de WhatsApp

- [ ] N8n → Workflows
- [ ] Click en "+" → "Import from file"
- [ ] Seleccionar: `n8n/workflows/thingsdata-whatsapp-alerts.json`
- [ ] Hacer clic en "Import"

### 4.3 Configurar Credencial de Twilio

En el workflow importado:

- [ ] Abrir nodo "Twilio - Enviar WhatsApp"
- [ ] Click en "Select Credential" → "Create New"
- [ ] Tipo: **Twilio**
- [ ] Rellenar:
  - **Account SID**: Tu `TWILIO_ACCOUNT_SID`
  - **Auth Token**: Tu `TWILIO_AUTH_TOKEN`
- [ ] Click "Save"

### 4.4 Validar el Workflow

- [ ] Click en "Save workflow"
- [ ] Click en "Test workflow"
- [ ] Ejecutar con datos de prueba (ver sección "Testing" abajo)

---

## 🗄️ Paso 5: Aplicar Migraciones SQL

### 5.1 Conectar a PostgreSQL

```bash
# Desde el contenedor
docker exec -it sabionda-postgres psql -U castuo -d castuo_db

# O desde tu máquina (si psql está instalado):
psql -h localhost -p 5432 -U castuo -d castuo_db
```

### 5.2 Ejecutar Migración

```sql
-- Desde psql, ejecutar:
\i /workspaces/Castuo-system/infrastructure/migrations/001_add_phone_to_tenants.sql

-- O copiar el contenido del archivo y pegar
```

**Confirmación:**
```sql
-- Verificar que las tablas fueron creadas
\dt public.tenant_notification_config
\dt public.whatsapp_alert_log
\dt public.system_emergency_contacts

-- Esperado:
Did not find any relation named "..." 
-- Si dice esto, la tabla YA EXISTE (bueno)
```

### 5.3 Verificar Datos

```sql
-- Verificar que el contacto admin está registrado
SELECT * FROM public.system_emergency_contacts WHERE role = 'admin';

-- Esperado:
 id | contact_name                 | phone_number  | role   |
----+------------------------------+---------------+--------|
  1 | Admin del Sistema - CASTÚO   | +34693443825  | admin  |
```

---

## 📱 Paso 6: Configurar Número de Teléfono por Tenant

### 6.1 Obtener Token de Autenticación

Para usar el endpoint, necesitas un token JWT. En producción usa tu auth system, para testing:

```bash
# Generar token de prueba (válido por 1 hora)
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Copiar el "access_token" retornado
```

### 6.2 Configurar Número para Tenant

```bash
# Reemplazar:
# - {TENANT_ID}: El ID del tenant (ej: "caix21")
# - {TOKEN}: El access_token del paso anterior

curl -X PUT http://localhost:8000/api/v1/tenants/caix21/phone \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+34693443825"}'

# Respuesta esperada:
{
  "id": "caix21",
  "name": "Caix - Invernadero",
  "phone": "+34693443825",
  "admin_phone": null,
  "updated_at": "2026-04-03T15:30:00Z"
}
```

### 6.3 Verificar en BD

```sql
-- Desde psql:
SELECT * FROM public.tenant_notification_config WHERE tenant_id = 'caix21';

-- O:
SELECT * FROM public.tenants WHERE id = 'caix21';
```

---

## 🧪 Paso 7: Testing

### 7.1 Test Básico: Webhook de Alerta

```bash
# Enviar una alerta de prueba
curl -X POST http://localhost:5678/webhook/thingsdata-alerts-whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "caix21",
    "sensor_id": "pH_INVERNADERO_001",
    "alert_type": "ANOMALY",
    "severity": "HIGH",
    "value": 7.5,
    "threshold": 6.5,
    "timestamp": "2026-04-03T15:30:00Z"
  }'

# Respuesta esperada:
{
  "status": "success",
  "message": "WhatsApp alert processed",
  "phone_notified": "+34693443825",
  "message_id": "SMxxxxxxxxxxxxxxx",
  "severity": "HIGH",
  "timestamp": "2026-04-03T15:32:00Z"
}
```

### 7.2 Test Crítico: Alerta al Admin

```bash
# Cambiar severity a CRITICAL
curl -X POST http://localhost:5678/webhook/thingsdata-alerts-whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "caix21",
    "sensor_id": "pH_INVERNADERO_001",
    "alert_type": "ANOMALY",
    "severity": "CRITICAL",
    "value": 8.5,
    "threshold": 6.5,
    "timestamp": "2026-04-03T15:30:00Z"
  }'

# Resultado: WhatsApp al número del tenant + al admin (+34693443825)
```

### 7.3 Verificar Auditoría

```sql
-- Ver todas las alertas WhatsApp enviadas
SELECT id, tenant_id, sensor_id, phone_number, severity, delivery_status, created_at
FROM public.whatsapp_alert_log
ORDER BY created_at DESC
LIMIT 5;

-- Filtrar por tenant
SELECT * FROM public.whatsapp_alert_log 
WHERE tenant_id = 'caix21' 
ORDER BY created_at DESC;
```

### 7.4 Verificar Logs

```bash
# Ver logs de FastAPI
docker logs sabionda-api | tail -20

# Ver logs de n8n
docker logs sabionda-n8n | tail -20

# Ver logs de PostgreSQL
docker logs sabionda-postgres | tail -20
```

---

## ✅ Paso 8: Validación Final

### 8.1 Checklist de Integración

- [ ] ✅ Credenciales de Twilio obtenidas
- [ ] ✅ Variables de entorno configuradas en `.env.local`
- [ ] ✅ Docker Compose levantado (`docker-compose up -d`)
- [ ] ✅ FastAPI está sano (`curl http://localhost:8000/health`)
- [ ] ✅ n8n accesible (`http://localhost:5678`)
- [ ] ✅ Workflow de WhatsApp importado y configurado
- [ ] ✅ Migraciones SQL ejecutadas
- [ ] ✅ Tabla `system_emergency_contacts` contiene admin (_+3469344382_5)
- [ ] ✅ Número de tenant configurado via endpoint PUT
- [ ] ✅ Test de alerta completado sin errores
- [ ] ✅ Auditoría registrada en `whatsapp_alert_log`

### 8.2 Endpoints Disponibles

```
GET  /api/v1/tenants/current                    → Info del tenant
PUT  /api/v1/tenants/{tenant_id}/phone          → Configurar número
POST /api/v1/iot/telemetry                      → Ingerir datos IoT
GET  /api/v1/user/{tenant_id}/status            → Dashboard status
POST /webhook/thingsdata-alerts-whatsapp        → Trigger alertas
```

### 8.3 Archivos Clave

| Ruta | Descripción |
|------|-------------|
| `.env.local` | Credenciales (NO COMMITEAR) |
| `api/routers/tenant.py` | Endpoint de configuración |
| `api/models/tenant.py` | Modelo de Tenant |
| `n8n/workflows/thingsdata-whatsapp-alerts.json` | Workflow ejecutable |
| `infrastructure/migrations/001_add_phone_to_tenants.sql` | Schema de BD |
| `docker-compose.yml` | Orquestación (actualizado) |

---

## 🐛 Troubleshooting

### Problema: "TWILIO_ACCOUNT_SID no válido"

**Causa**: Variable mal copiada o espacios en blanco
**Solución**:
```bash
# Verificar sin espacios
cat .env.local | grep TWILIO_ACCOUNT_SID

# Copiar nuevamente de Twilio Console, eliminar espacios
```

### Problema: "No se envía WhatsApp"

**Causa**: Número de teléfono no configurado para tenant
**Solución**:
```sql
-- 1. Verificar que el tenant tiene número
SELECT tenant_id, phone FROM public.tenant_notification_config WHERE tenant_id = 'caix21';

-- 2. Si no existe, insertar
INSERT INTO public.tenant_notification_config (tenant_id, phone, whatsapp_enabled)
VALUES ('caix21', '+34693443825', TRUE);

-- 3. O actualizar vía endpoint PUT (recomendado)
```

### Problema: "Credencial de Twilio inválida en n8n"

**Causa**: Token expirado o copiado mal
**Solución**:
```bash
# 1. Eliminar credencial en n8n: Credentials > Twilio > Delete
# 2. Crear nueva: Credentials > Add > Twilio
# 3. Copiar exactamente desde Twilio Console (SIN espacios)
```

### Problema: "Contenedor FastAPI no levanta"

**Causa**: Error en variables de entorno
**Solución**:
```bash
# 1. Ver logs
docker logs sabionda-api

# 2. Validar .env.local
source .env.local
echo $TWILIO_ACCOUNT_SID  # Debe imprimir el valor

# 3. Reconstruir
docker-compose build --no-cache fastapi
docker-compose up -d fastapi
```

---

## 📞 Contacto y Soporte

Si encuentras problemas:

1. Revisar los logs: `docker logs <container_name>`
2. Validar variables: `grep TWILIO .env.local`
3. Abrir issue en GitHub
4. Chat en Slack: #castuo-support

---

## 🎉 ¿Listo para Producción?

Una vez completado este checklist:

```bash
# 1. Commitear cambios (SIN .env.local)
git add -A && git commit -m "feat: integrate WhatsApp alerts with Twilio"

# 2. Deploy a Hetzner (si es aplicable)
# kubectl apply -f k8s/deployment.yaml

# 3. Monitorear
# Dashboard: https://grafana.castuo-system.cloud
# Alertas: https://n8n.castuo-system.cloud
```

---

**Estado**: 🟢 Sistema listo para conectar  
**Última actualización**: 2026-04-03  
**Versión**: CASTÚO-SYSTEM v3.1.1
