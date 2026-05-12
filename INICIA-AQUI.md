# ⚡ INICIA AQUÍ - Integración WhatsApp Lista

TU SISTEMA YA ESTÁ IMPLEMENTADO. Solo necesitas **3 cosas para activarlo**:

---

## 📱 ¿Qué Hace?

Cuando hay una alerta en el cultivo (pH, EC, temperatura fuera de rango), la app envía **WhatsApp**:

```
🚨 ALERTA IoT CASTÚO
🌱 Sensor: pH_001
📊 Tipo: ANOMALY
🔴 Severidad: CRITICAL
📈 Valor: 7.5 (umbral: 6.5)
⏰ Hora: 3 de abril, 15:30
👉 Acción: INMEDIATA
```

Directo a: **+34693443825** (tu admin phone)

---

## 🚀 Activar en 3 Pasos

### Paso 1: Obtener Credenciales Twilio (🆓 Gratis)

1. Ir a https://www.twilio.com/console
2. Registrarse (tienes $15 crédito gratis)
3. Habilitar WhatsApp Business
4. Copiar 3 valores:
   - **TWILIO_ACCOUNT_SID** → `AC...`
   - **TWILIO_AUTH_TOKEN** → `...`
   - **TWILIO_WHATSAPP_FROM** → `+34XXXXXXXXX`

**Tempo**: 5 min

### Paso 2: Actualizar `.env.local`

```bash
# Copiar template
cp .env.example .env.local

# Editar
nano .env.local

# Buscar y reemplazar (línea ~190):
TWILIO_ACCOUNT_SID=TU_SID_DE_TWILIO
TWILIO_AUTH_TOKEN=TU_TOKEN
TWILIO_WHATSAPP_FROM=+34XXXXXXXXX
SYSTEM_ADMIN_PHONE=+34693443825  # Ya está
```

**Tempo**: 2 min

### Paso 3: Levantar Sistema

```bash
# Docker
docker-compose build fastapi
docker-compose up -d

# Esperar 30 segundos
sleep 30

# Validar
curl http://localhost:8000/health
```

**Tempo**: 3 min

---

## ✅ ¿Está Listo?

```bash
# Ejecutar validación
./scripts/validate_whatsapp_integration.sh
```

Si todo está ✅, el sistema:
- Recibe alertas IoT
- Envía WhatsApp por Twilio
- Audita todo en BD

---

## 📋 ¿Qué se Implementó?

✅ **Modelo Tenant** actualizado → campos `phone`  
✅ **Endpoint PUT** para configurar números → `/api/v1/tenants/{id}/phone`  
✅ **Workflow n8n** para envío WhatsApp → `thingsdata-whatsapp-alerts.json`  
✅ **PostgreSQL Schema** con auditoría → 3 tablas nuevas  
✅ **Docker Compose** actualizado → variables de Twilio  
✅ **Documentación completa** → 5 guías  
✅ **Tests** incluidos → 30+ casos  
✅ **Scripts de setup** → automáticos  

---

## 📚 Siguiente

1. **Si quieres más detalles**: Lee `INTEGRATION-CHECKLIST.md` (pasos 1-8)
2. **Si quieres documentación técnica**: Lee `docs/IMPLEMENTATION-WHATSAPP.md`
3. **Si quieres validar rápido**: Ejecuta `./scripts/validate_whatsapp_integration.sh`

---

## 🎯 Puntos Clave

| Aspecto | Valor |
|--------|-------|
| Tu número admin | **+34693443825** ✅ |
| Alertas críticas | Van al admin + tenant |
| Auditoría | Completa en BD (tabla `whatsapp_alert_log`) |
| Seguridad | Multi-tenant isolado |
| Coste Twilio | ~$0.0075/mensaje ($0.20/día máx) |

---

## 🐛 Si Hay Problema

1. **"TWILIO_ACCOUNT_SID no válido"**  
   → Copiar exacto de Twilio Console (sin espacios)

2. **"No se envía WhatsApp"**  
   → Verificar que .env.local está actualizado

3. **"FastAPI no levanta"**  
   → Ver logs: `docker logs sabionda-api`

**Para más**: INTEGRATION-CHECKLIST.md → "Troubleshooting"

---

**¿Listo? Comienza por el Paso 1 arriba. 🚀**
