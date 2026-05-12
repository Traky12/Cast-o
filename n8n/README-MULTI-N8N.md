# Multi-instancia n8n (AGRI-BRAIN)

## Qué resuelve

Cinco procesos n8n opcionales (`n8n-sensores`, `n8n-satelites`, `n8n-simulacion`, `n8n-drones`, `n8n-trillizo`) con volúmenes separados: la carga o un fallo en satélites no apaga la UI de sensores.

## Inventario verificable (repo) vs. no implementado

Lo que **sí** hace `castuo_main_orchestrator_gateway.json` hoy:

- Comprueba **opcionalmente** `X-API-KEY` frente a `CASTUO_ORCHESTRATOR_API_KEY` (si la variable está vacía, no exige clave).
- Resuelve **`route` / `orchestrator_route` / `request_type`** y **alias** → ruta canónica interna (tabla abajo).
- **Validación ligera** de payload en algunas rutas (sensor, trazabilidad, satélite).
- **Reenvío HTTP** al sub-webhook con `X-API-KEY` de forward y cabecera `X-Forwarded-By`.
- **Bases URL por dominio** (`N8N_WEBHOOK_BASE_SENSORES`, `_SATELITES`, `_SIMULACION`, `_DRONES`, `_TRILLIZO`, fallback `N8N_WEBHOOK_BASE`).

Lo que **no** está en ese workflow (habría que añadir otro componente o capa):

- **HMAC-SHA512** de cuerpo en tránsito.
- **Circuit breaker** con estado compartido (Redis, proxy, mesh).
- **Firma digital** distinta de la API key en header.
- **`ENCRYPTION_KEYHASH_SECRET`** u otro hash de clave en `.env.n8n-castuo.example` (no definido en el repo).
- Un **lienzo de 319 nodos** versionado aquí: los exports grandes viven en tu instancia n8n.

### Alias de `request_type` (entrada → canónico)

| Entrada (`request_type` / `route`) | Ruta canónica | Instancia típica |
|-----------------------------------|----------------|-------------------|
| `sensor-data`, `sensores`, `trazabilidad/*` | (sin cambio) | `N8N_WEBHOOK_BASE_SENSORES` |
| `satelite-ndvi`, `satellite-ndvi`, `satelite/coordinates`, `geoespacial/process` | `satellite-ndvi` o paths satélite | `N8N_WEBHOOK_BASE_SATELITES` |
| `simulacion-root` | `simulacion/computational-simulation` | `N8N_WEBHOOK_BASE_SIMULACION` |
| `drones-command` | `fotogrametria/drone-mission` | `N8N_WEBHOOK_BASE_DRONES` |
| `trillizo/*` | (sin cambio) | `N8N_WEBHOOK_BASE_TRILLIZO` |

La respuesta JSON incluye `orchestrator_meta.incoming_route` y `chosen_route` / `canonical_route` para auditoría.

## Arranque

```bash
cp .env.n8n-multi.example .env.n8n-multi
# Edita N8N_ENCRYPTION_KEY, N8N_PASSWORD, URLs si usas dominios TLS
docker compose -f docker-compose.multi-n8n.yml --env-file .env.n8n-multi up -d
```

Importa en **cada** instancia solo los workflows que correspondan (o el monolito dividido cuando lo tengas). Los webhooks deben existir en la instancia a la que el gateway apunta.

## Gateway y bases URL

El workflow `castuo_main_orchestrator_gateway.json` enruta así:

| Rutas | Variable de entorno |
|--------|---------------------|
| `sensor-data`, `sensores`, `trazabilidad/*` | `N8N_WEBHOOK_BASE_SENSORES` |
| `satelite/coordinates`, `satellite-ndvi`, `geoespacial/process` | `N8N_WEBHOOK_BASE_SATELITES` |
| `simulacion/computational-simulation` | `N8N_WEBHOOK_BASE_SIMULACION` |
| `fotogrametria/drone-mission` | `N8N_WEBHOOK_BASE_DRONES` |
| `trillizo/audit-rotation`, `trillizo/shadow-check` | `N8N_WEBHOOK_BASE_TRILLIZO` |
| `typeform-lead`, `api/query` | `N8N_WEBHOOK_BASE` (fallback) |

Quinta instancia **`n8n-trillizo`**: ver **`n8n/README-TRILLIZO.md`** (límites reales de mTLS, cifrado en reposo, ZKP).

Si el orquestador corre **en el mismo** `docker-compose.multi-n8n.yml`, usa URLs tipo `http://n8n-satelites:5678` (sin barra final). Si corre en el **host** hacia contenedores publicados, usa `http://localhost:5679`, etc.

`CASTUO_FORWARD_API_KEY` (o `CASTUO_API_KEY`) sigue yendo en el `X-API-KEY` del HTTP Request del gateway hacia cada sub-webhook.

## Observabilidad y SLO (evidencia, no narrativa)

### Latencia

- [ ] Instrumentar con OpenTelemetry (o APM) delante de n8n.
- [ ] Medir p50, p95, p99 en producción.
- [ ] Definir SLOs y alertas si p95 supera umbral.

### Throughput

- [ ] Requests/s por endpoint (gateway + cada sub-webhook).
- [ ] Capacidad items/min en ramas pesadas.
- [ ] Saturación CPU/RAM/I/O por contenedor.

### Disponibilidad

- [ ] Uptime / SLA acordado (ej. 99.9%).
- [ ] MTBF / MTTR documentados.

### Escalabilidad

- [ ] Pruebas de carga (k6, JMeter, Locust).
- [ ] Límites de concurrencia y política de escalado horizontal.

### Ya útil sin APM

- Timestamps en `orchestrator_meta` de la respuesta del gateway.
- Logs del proxy o de Docker para cada instancia.

## Parámetros “Actualizar …” en Data Tables / nodos

La lista larga de parámetros (cosechas, `slack_channel`, `lecturas_sensores`, GaiaChain, PIX4D, etc.) se mapea a **`$env.*`** en **`.env.n8n-castuo.example`** y **`.env.n8n-multi.example`**. Crea las tablas en n8n y asigna el mismo identificador en el `.env` o en expresiones de nodo.

## Workflow 02 — Diagnóstico por sector (Trillizo)

- Archivo: **`n8n/workflows/02-agente-diagnostico-ultra.json`** — disparo cada minuto, Postgres (`telemetria`), **sanity** (sin `SECTOR_ID` o desajuste `sector_id` → no POST), inferencia local, **POST** a `audit-trigger` con `kind: ia`, **`tags: [#ia-decision, #sector-…]`**, `actor`/`agente_id` = **`CORE_ID`**, HMAC del **`auditBody`** completo si hay secreto.
- Variables: `SECTOR_ID`, `CORE_ID`, `CASTUO_TRILLIZO_AUDIT_URL`, `CASTUO_AUDIT_WEBHOOK_SECRET` (mismo valor en worker y trillizo si aplica). Referencia Postgres: **`POSTGRES_HOST`** / **`POSTGRES_PORT`** en `.env.n8n-multi.example`; credencial n8n debe apuntar al host/puerto reales (p. ej. `host.docker.internal:5433`). DDL: **`n8n/sql/telemetria_sector_template.sql`**. LQL ejemplo: **`n8n/templates/silverbullet-control-panel-lql.example.md`**.

## Documentación relacionada

- `n8n/README-AGRI-BRAIN.md` — variables y correcciones de nodos.
- `n8n/workflows/castuo_main_orchestrator_gateway.json` — punto de entrada único opcional.
