# Seguridad y trazabilidad (CASTÚO-SYSTEM)

Documento de referencia alineado al **código del repositorio**. No sustituye DPIA, registro de tratamientos ni evaluación de riesgos del responsable.

## 1. Arquitectura lógica

```text
[Cliente / IoT / Webhook] → [TLS en borde: Traefik / nginx / Arsys]
    → [FastAPI castuo-api + LangGraph + hooks GaiaChain/Slack]
    → [n8n orquestación]
[MQTT] → [broker Mosquitto] (HTTP no sustituye MQTT; ver `docker/api-gateway/api_gateway.py`)
```

## 2. Mecanismos de seguridad

| Componente | Mecanismo típico | Notas |
|------------|------------------|--------|
| Borde | TLS (Let's Encrypt o certificado gestionado) | `deploy/traefik.yml` es plantilla estática; ACME y dominios reales se configuran en despliegue. |
| API | `X-API-KEY` u OAuth/JWT según rutas | **No** reutilizar `JWT_SECRET` como token Bearer en webhooks n8n; usar claves de firma solo en el emisor JWT. |
| n8n | Basic auth, cifrado `N8N_ENCRYPTION_KEY`, credenciales en UI | Variables sensibles en entorno del host, no en workflows exportados. |
| MQTT | `allow_anonymous false`, TLS 8883, usuarios `mosquitto_passwd` | Ver `docker/remote-access/mosquitto/` y documentación de despliegue remoto. |
| PostgreSQL | Red interna Docker, contraseña fuerte | Separar BD de n8n y BD de aplicación si escalas. |
| Mistral | `MISTRAL_API_KEY` en **castuo-api** | Evita duplicar la clave en n8n salvo nodos que llamen directo a Mistral. |

## 3. Trazabilidad

| Capa | Qué registra | Dónde |
|------|----------------|-------|
| LangGraph | `trace_hash` (SHA-256 sobre payload + análisis) | Respuesta `POST /langgraph/castuo/execute-graph` |
| GaiaChain | Registro HTTP opcional con `trace_hash` y vista previa | Solo si `GAIACHAIN_REGISTER_URL` está definida en castuo-api |
| LangSmith | Trazas de ejecución LLM | Variables `LANGCHAIN_TRACING_V2`, `LANGSMITH_API_KEY` en **castuo-api** |
| n8n | Historial de ejecuciones | Activar retención acorde a RGPD |
| Auditoría SQL | Tablas opcionales `castuo_prod_*` | Migraciones en `backend/models/migrations/` |

## 4. Anti-patrones (borradores genéricos)

| Incorrecto | Motivo |
|------------|--------|
| `http://langgraph:8123/...` | LangGraph corre **dentro** de FastAPI en este repo. |
| `Authorization: Bearer {{ $env.JWT_SECRET }}` | El secreto firma tokens; no es el token del cliente. |
| URL fija `https://api.gaiachain.eu/v3/register` | Usar endpoint configurable (`GAIACHAIN_REGISTER_URL`). |
| `CURSOR_MCP_URL` hacia n8n | Cursor no expone MCP HTTP estándar hacia tu n8n; usar webhooks y scripts. |
| Logging de cuerpos completos en middleware | Riesgo RGPD; minimizar, enmascarar y basar retención en finalidad. |

## 5. Tablas de auditoría opcionales

Definiciones SQL en el repo:

- `optional_castuo_prod_sensor_readings_audit.sql` — lecturas IoT tras workflows.
- `optional_castuo_prod_qelectrotech.sql` — proyectos QElectroTech.

Ajusta nombres y columnas a tu DBA antes de producción.

## 6. Verificación rápida

```bash
dig +short castuo-system.es
openssl s_client -connect api.ejemplo:443 -servername api.ejemplo </dev/null 2>/dev/null | openssl x509 -noout -dates
curl -sS "https://api.ejemplo/langgraph/castuo/health"
```

## 7. Referencias cruzadas

- [ARCHITECTURE-VISION-AND-BOUNDARIES.md](../architecture/ARCHITECTURE-VISION-AND-BOUNDARIES.md) (visión “hiper-dimensional” vs. lo implementado)
- [PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md](../deploy/PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md)
- [PRONT-MASTER-QELECTROTECH-CASTUO-INTEGRATION.md](../deploy/PRONT-MASTER-QELECTROTECH-CASTUO-INTEGRATION.md)
- [N8N-LANGGRAPH-INTEGRATED.md](../architecture/N8N-LANGGRAPH-INTEGRATED.md)
- [LANGGRAPH-CASTUO.md](../architecture/LANGGRAPH-CASTUO.md)
- [CASTUO-ENTERPRISE-HETZNER-ARSYS.md](../deploy/CASTUO-ENTERPRISE-HETZNER-ARSYS.md)
