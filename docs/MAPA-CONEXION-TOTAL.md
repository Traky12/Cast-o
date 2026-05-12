# MAPA DE CONEXIÓN TOTAL — CASTUO-SYSTEM v3.1.1

> **Supervisión:** Sabionda | **Soberanía:** EU (GDPR + AI Act + Gaia-X)  
> **Actualizado:** 2026-04-09 | **Estado:** Operativo / Integración continua

---

## 1. Índice de Módulos

| ID | Módulo | Rol | Tecnología |
|----|--------|-----|------------|
| M1 | API FastAPI | Backend principal | Python 3.11, FastAPI 3.1.1 |
| M2 | IoT / MQTT Bridge | Ingesta de telemetría | ESP32, MQTT, HTTP |
| M3 | TimescaleDB | Persistencia series temporales | PostgreSQL + TimescaleDB ext |
| M4 | TRACES (UE) | Trazabilidad oficial agropecuaria | REST HTTPS, eIDAS |
| M5 | Hyperledger Fabric | Registro inmutable de trazas | Fabric SDK, chaincode |
| M6 | Vault | Gestión de secretos | HashiCorp Vault, REST |
| M7 | n8n | Automatización de workflows | REST, Webhooks |
| M8 | Observabilidad | Métricas, alertas, dashboards | Prometheus, Grafana, Alertmanager |
| M9 | Frontend / Dashboard | Interfaz operativa | React / Next.js |

---

## 2. Tabla de Integraciones

### M1 ↔ M2: API FastAPI ↔ IoT/MQTT

| Campo | Detalle |
|-------|---------|
| **Owner** | Backend Team + IoT Team |
| **Dependencia** | `api/routers/esp32_iot.py`, `api/main.py` (endpoint `/api/v1/iot/telemetry`) |
| **Contrato** | POST `/api/v1/iot/telemetry` → `IotTelemetryRequest` (JSON); respuesta: `{estado, sensor_id, traces_status, persisted, received_at}` |
| **Autenticación** | JWT `Authorization: Bearer <token>` (obligatorio en producción); `device_auth.validate_device_token()` |
| **Rate limiting** | 100 req/min por sensor (`IOT_RATE_LIMIT` env var) |
| **Variables de entorno** | `IOT_RATE_LIMIT`, `JWT_SECRET` |
| **Criterios de aceptación** | ✅ POST retorna 200 con `persisted: true/false`; ✅ 401 sin token en prod; ✅ 429 al superar límite |
| **Tests** | `tests/test_esp32_iot.py`, `tests/test_api.py` |

---

### M1 ↔ M3: API FastAPI ↔ TimescaleDB

| Campo | Detalle |
|-------|---------|
| **Owner** | Backend Team + Infra Team |
| **Dependencia** | `api/database/timescale.py` → singleton `timescale_db` |
| **Contrato** | `timescale_db.insert_sensor_event(event: dict) → bool`; `timescale_db.get_device_latest(device_id, metric) → dict \| None` |
| **Conexión** | `psycopg2` a `TIMESCALE_DB_HOST:TIMESCALE_DB_PORT`; hipertabla `telemetry` |
| **Fallback** | Si `TIMESCALE_DB_HOST` no configurado → modo degradado en memoria (`IOT_LAST_BY_SENSOR`) |
| **Variables de entorno** | `TIMESCALE_DB_HOST`, `TIMESCALE_DB_PORT`, `TIMESCALE_DB_USER`, `TIMESCALE_DB_PASSWORD`, `TIMESCALE_DB_NAME` |
| **Health check** | `GET /health` devuelve `"timescale": "ok"` si `timescale_db.available` es True |
| **Criterios de aceptación** | ✅ Sin host → `available=False`, fallback activo; ✅ Con host → `available=True`, datos persistidos; ✅ Health refleja estado |
| **Tests** | `tests/test_api.py`, `tests/test_main_hardening.py` |

---

### M1 ↔ M4: API FastAPI ↔ TRACES (UE)

| Campo | Detalle |
|-------|---------|
| **Owner** | Backend Team + Compliance Team |
| **Dependencia** | `api/services/traces.py` → `TRACESClient`; `api/routers/traces.py` |
| **Contrato** | `traces_client.submit_to_traces(lote_id, metadata) → {traces, hyperledger, signed_payload}`; `traces_client.check_status(reference) → dict` |
| **Firma** | eIDAS: `eidas_signer.sign_payload(payload)` antes del envío |
| **Retry** | Tenacity: 3 intentos, backoff exponencial 2-10s |
| **Modo simulado** | Si `TRACES_API_KEY` vacía → retorna `status: SIMULATED` |
| **Reconciliación** | `check_status(reference)` consulta estado de la sumisión TRACES |
| **Variables de entorno** | `TRACES_API_URL`, `TRACES_API_KEY`, `TRACES_OPERATOR_ID` |
| **Criterios de aceptación** | ✅ Sin API key → modo simulado; ✅ Con key → retry automático ante error; ✅ `check_status` retorna estado válido |
| **Tests** | `tests/test_e2e_smoke_traces.py` |

---

### M1 ↔ M5: API FastAPI ↔ Hyperledger Fabric

| Campo | Detalle |
|-------|---------|
| **Owner** | Backend Team + Blockchain Team |
| **Dependencia** | `api/services/traces.py` → `TRACESClient._register_in_hyperledger()` |
| **Contrato** | POST a `HYPERLEDGER_URL/channels/{channel}/chaincodes/{cc}` con `{fcn: "registerTrace", args: [lote_id, hash, traces_response]}` |
| **Retry** | Tenacity: 3 intentos, backoff exponencial 2-10s |
| **Variables de entorno** | `HYPERLEDGER_URL`, `HYPERLEDGER_CHANNEL`, `HYPERLEDGER_CHAINCODE` |
| **Criterios de aceptación** | ✅ Hash registrado en cadena; ✅ Retry ante timeout; ✅ `status: ERROR` en fallo persistente |
| **Tests** | `tests/test_e2e_smoke_traces.py` |

---

### M1 ↔ M6: API FastAPI ↔ Vault

| Campo | Detalle |
|-------|---------|
| **Owner** | Infra Team + Security Team |
| **Dependencia** | Variables de entorno inyectadas desde Vault en runtime |
| **Contrato** | Vault KV v2: secretos en `secret/castuo-system/`; inyectados como env vars en contenedor |
| **Política** | Solo lectura para el rol `castuo-api`; auditoría habilitada |
| **Variables de entorno** | `VAULT_ADDR`, `VAULT_TOKEN` (o AppRole: `VAULT_ROLE_ID`, `VAULT_SECRET_ID`) |
| **Criterios de aceptación** | ✅ Secretos no hardcodeados; ✅ Rotación de tokens sin downtime; ✅ Alerta `vault_unreachable` en Alertmanager |
| **Tests** | `tests/test_security_hardening.py` |

---

### M1 ↔ M7: API FastAPI ↔ n8n

| Campo | Detalle |
|-------|---------|
| **Owner** | Automation Team |
| **Dependencia** | Webhooks n8n → endpoints API; n8n workflows en `n8n/` |
| **Contrato** | POST webhooks en `/api/v1/webhooks/*`; respuesta JSON; autenticación por header `X-N8N-SECRET` |
| **Variables de entorno** | `N8N_WEBHOOK_SECRET`, `N8N_BASE_URL` |
| **Criterios de aceptación** | ✅ Webhook autenticado procesa payload; ✅ Rechazo con 401 sin secreto válido |
| **Tests** | `tests/test_api.py` |

---

### M1 ↔ M8: API FastAPI ↔ Observabilidad

| Campo | Detalle |
|-------|---------|
| **Owner** | SRE Team |
| **Dependencia** | `api/metrics/prometheus.py`; `infrastructure/observability/` |
| **Contrato** | `GET /metrics` → Prometheus scrape; métricas: `IOT_REQUESTS`, `api_uptime`, `api_request_total` |
| **Alertas** | Alertmanager: `traces_submit_failed`, `iot_persistence_failed`, `vault_unreachable` → Slack |
| **Dashboards** | Grafana con datasource Prometheus |
| **Variables de entorno** | `SLACK_WEBHOOK_URL`, `PAGERDUTY_SERVICE_KEY` |
| **Criterios de aceptación** | ✅ Métricas expuestas en `/metrics`; ✅ Alertas enrutadas a Slack; ✅ Dashboard operativo en Grafana |
| **Tests** | `tests/test_main_hardening.py` |

---

### M1 ↔ M9: API FastAPI ↔ Frontend/Dashboard

| Campo | Detalle |
|-------|---------|
| **Owner** | Frontend Team |
| **Dependencia** | `GET /api/v1/user/{tenant_id}/status`; `GET /health`; CORS configurado en `SecurityHeadersMiddleware` |
| **Contrato** | Respuesta JSON con métricas NIWA (pH, EC, temperatura, humedad), alertas y estado TRACES |
| **Autenticación** | JWT `Authorization: Bearer <token>`; roles via RBAC |
| **Variables de entorno** | `CORS_ORIGINS`, `JWT_SECRET` |
| **Criterios de aceptación** | ✅ Dashboard recibe métricas en <500ms; ✅ CORS válido para orígenes EU; ✅ 404 si no hay telemetría |
| **Tests** | `tests/test_api.py`, `tests/test_rbac_security.py` |

---

## 3. Diagrama de Flujo de Datos

```
ESP32/IoT Device
      │ POST /api/v1/iot/telemetry (JWT)
      ▼
┌─────────────────────────────────────────────┐
│           API FastAPI (M1)                   │
│  ┌───────────────┐   ┌─────────────────────┐│
│  │ IoT Ingest    │   │ TRACES Submit        ││
│  │ (main.py)     │   │ (services/traces.py) ││
│  └───────┬───────┘   └──────────┬──────────┘│
│          │                      │            │
└──────────┼──────────────────────┼────────────┘
           │                      │
    ┌──────▼──────┐        ┌──────▼──────────────┐
    │ TimescaleDB │        │   TRACES UE (REST)   │
    │    (M3)     │        │   + Hyperledger (M5) │
    └─────────────┘        └──────────────────────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │         Prometheus (M8)                      │
    │  ┌────────────┐  ┌────────────────────────┐ │
    │  │  Grafana   │  │     Alertmanager        │ │
    │  │ Dashboards │  │ (Slack / PagerDuty)     │ │
    │  └────────────┘  └────────────────────────┘ │
    └─────────────────────────────────────────────┘
           │
    ┌──────▼──────┐
    │  Frontend   │
    │    (M9)     │
    └─────────────┘
```

---

## 4. Matriz de Secretos por Módulo

| Secreto | Módulo | Método de inyección | Rotación |
|---------|--------|---------------------|----------|
| `JWT_SECRET` | M1, M9 | Env var / Vault KV | Semestral |
| `TIMESCALE_DB_PASSWORD` | M3 | Env var / Vault KV | Trimestral |
| `TRACES_API_KEY` | M4 | Env var / Vault KV | Anual |
| `VAULT_TOKEN` | M6 | AppRole / K8s SA | 24h TTL |
| `SLACK_WEBHOOK_URL` | M8 | Env var / Vault KV | Bajo demanda |
| `PAGERDUTY_SERVICE_KEY` | M8 | Env var / Vault KV | Anual |

> ⚠️ **Ningún secreto debe aparecer en código, logs ni respuestas de API.**

---

## 5. Criterios de Aceptación Globales (Sabionda)

| Criterio | Estado |
|----------|--------|
| Cobertura de tests ≥ 95% | 🟡 En progreso |
| Sin secretos hardcodeados | ✅ Cumple |
| Soberanía EU (datos en EU) | ✅ Hetzner EU / AWS eu-west |
| Retries en integraciones críticas | ✅ TRACES + Hyperledger |
| Observabilidad end-to-end | ✅ Prometheus + Alertmanager |
| GDPR / AI Act compliance | ✅ Auditado |
| Documentación actualizada | ✅ Este documento |
