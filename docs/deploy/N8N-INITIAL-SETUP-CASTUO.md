# Configuración inicial n8n (CASTÚO-SYSTEM)

Guía **corregida** para el stack del repositorio. Sustituye instrucciones genéricas con `http://mistral:11434`, `http://langgraph:8123`, base de datos `sabionda` para n8n, GaiaChain fija o “MCP Cursor → n8n” como si fuera soporte oficial.

---

## 1. Credenciales en n8n (Settings → Credentials)

### 1.1 PostgreSQL (metadatos de n8n)

En `deploy/docker-compose.castuo.enterprise.example.yml` el servicio Postgres usa por defecto:

| Campo | Valor típico (Docker Compose interno) |
|--------|----------------------------------------|
| Host | `postgres` |
| Database | **`n8n`** (no `sabionda` salvo que cambies tú el compose) |
| User | `postgres` (o `POSTGRES_USER`) |
| Password | El de `POSTGRES_PASSWORD` en tu `.env` |

**Importante:** las tablas `castuo_prod_*` de aplicación pueden vivir en **otra** base y otro host; el nodo Postgres de workflows debe apuntar a esa BD si insertáis auditoría allí.

### 1.2 Mistral AI

**Recomendación del repo:** no configurar Mistral en n8n para el flujo LangGraph principal. El análisis corre en **castuo-api** con `MISTRAL_API_KEY` y `https://api.mistral.ai`.

- Si aun así usas un nodo “OpenAI-compatible” u Ollama en LAN: Base URL será **tu** endpoint (p. ej. `http://host:11434`), no una imagen inventaria.
- No uses `http://mistral:11434` a menos que hayas definido tú un servicio con ese nombre en **tu** compose.

### 1.3 GaiaChain

No existe credencial oficial “GaiaChain” universal. Opciones alineadas al código:

- **Preferido:** dejar el registro al hook del API (`GAIACHAIN_REGISTER_URL` + token en **castuo-api**).
- **Alternativa n8n:** credencial **HTTP Header Auth** o **Generic** con URL tomada de variable de entorno (p. ej. `GAIACHAIN_REGISTER_URL`), **sin** hardcodear `https://api.gaiachain.eu/v3` salvo que sea vuestro endpoint real.

### 1.4 MQTT (Mosquitto)

| Campo | Notas |
|--------|--------|
| Host | Nombre del servicio Docker (p. ej. `mosquitto`) o FQDN público si expones broker |
| Port | `1883` TLS off; **8883** si usáis TLS (recomendado en producción) |
| User / Password | Los creados con `mosquitto_passwd` |

Los topics tipo `castuo/iot/...` son **convención**; deben coincidir con lo que publican los dispositivos y con workflows que usen **MQTT Trigger**.

### 1.5 Slack

- **Webhook:** URL entrante (`https://hooks.slack.com/...`) en credencial **HTTP Request** o variable `SLACK_WEBHOOK` / `SLACK_WEBHOOK_URL` según el workflow.
- OAuth Slack es opcional si usáis el nodo Slack nativo.

### 1.6 Autenticación del orquestador (webhook)

Para `POST /webhook/castuo-orchestrate`:

- Definid `CASTUO_ORCHESTRATOR_KEY` en el entorno de n8n y enviad cabecera `X-API-Key: <valor>`.
- O configurad **Header Auth** en el nodo Webhook en la UI (no exportamos IDs de credencial ficticios).

---

## 2. Workflow “CASTÚO Orchestrator” (versión mínima real)

No existe en el repo un JSON de **384 nodos** válido único. Usad:

**`n8n/workflows/castuo_orchestrator_minimal.json`**

- Webhook: `castuo-orchestrate`
- Clasifica `request_type`: `sensores` | `qelectrotech` | `plc` | `simulacion`
- Una sola llamada a `POST /langgraph/castuo/execute-graph` en castuo-api
- Sin `langgraph:8123`, sin nodos `function` deprecados, sin GaiaChain duplicado (opcional Slack desactivado)

Workflows específicos ya disponibles:

- IoT: `castuo_n8n_iot_sensor_langgraph.json`
- QET: `castuo_n8n_qelectrotech_langgraph.json`
- PLC: `castuo_n8n_plc_generate_langgraph.json`

MQTT masivo: añadid un workflow aparte con **MQTT Trigger** y el mismo patrón HTTP hacia castuo-api.

---

## 3. Cursor y “MCP”

Cursor **no** consume un archivo `.cursor/mcp_config.json` apuntando a `https://n8n.../webhook/cursor-mcp` como si fuera un servidor MCP estándar.

Patrones válidos:

- Disparar webhooks con **curl**, script o CI desde tu máquina.
- Mantener la lógica en el repo y desplegar con git.

---

## 4. Tablas PostgreSQL (opcional)

```bash
psql -h HOST -U USER -d NOMBRE_BD_APLICACION -f backend/models/migrations/optional_castuo_prod_executions.sql
```

Ajustad `NOMBRE_BD_APLICACION` (no confundir con la BD interna `n8n`).

---

## 5. Pruebas

```bash
export KEY=tu_clave_orquestador
curl -sS -X POST "http://127.0.0.1:5678/webhook/castuo-orchestrate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{"request_type":"sensores","data":{"sensor_id":"HUM-001","value":65.3,"type":"humedad_suelo","location":"invernadero_A"}}'
```

QElectroTech (requiere `svg_base64`):

```bash
curl -sS -X POST "http://127.0.0.1:5678/webhook/castuo-orchestrate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d "{\"request_type\":\"qelectrotech\",\"data\":{\"project_id\":\"P1\",\"author\":\"eq\",\"svg_base64\":\"$(base64 -w0 esquema.svg 2>/dev/null || base64 esquema.svg | tr -d '\n')\"}}"
```

PLC:

```bash
curl -sS -X POST "http://127.0.0.1:5678/webhook/castuo-orchestrate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{"request_type":"plc","data":{"project_id":"P1","requirements":"Bomba y humedad","hardware":"S7-1200"}}'
```

Verificación GaiaChain: depende de vuestro backend (`GAIACHAIN_REGISTER_URL`), no de `GET https://api.gaiachain.eu/v3/transactions` genérico.

---

## 6. Referencias

- [SECURITY_AND_TRACING.md](../security/SECURITY_AND_TRACING.md)
- [N8N-LANGGRAPH-INTEGRATED.md](../architecture/N8N-LANGGRAPH-INTEGRATED.md)
- [PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md](PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md)
