# AGRI-BRAIN — configuración centralizada (CASTÚO + n8n)

Directorio de plantillas y workflows para integrar n8n con Castúo-System (gateway, sensores, seguridad).

## Recursos de seguridad y validación

| Recurso | Ubicación |
|---------|-----------|
| Guía Cursor + trust + n8n | [`.cursor/CURSOR-IMMEDIATE-SECURE.md`](../.cursor/CURSOR-IMMEDIATE-SECURE.md) |
| Plantilla de política (referencia) | [`docs/deploy/n8n-security-policy.example.json`](../docs/deploy/n8n-security-policy.example.json) |
| Script de validación | `bash scripts/n8n/validate_n8n_security.sh` |
| Workflow placeholder (importar inactivo) | [`workflows/castuo-secure-http-placeholder.json`](workflows/castuo-secure-http-placeholder.json) |

### Requisitos rápidos

1. **n8n en PATH** (o Docker): si no hay CLI en Windows, en Git Bash/WSL ejecuta el script con `N8N_ALLOW_MISSING_CLI=1` tras comprobar `docker exec … n8n --version`.
2. Copia o adapta la plantilla JSON a tu **ENV / UI**; sustituye dominios `*.invalid`.
3. Valida: `bash scripts/n8n/validate_n8n_security.sh` (estricto) o `N8N_ALLOW_MISSING_CLI=1 bash scripts/n8n/validate_n8n_security.sh` si solo usas contenedor.

## Dónde vive la configuración

1. **Docker (recomendado self-hosted):** copia `.env.n8n-castuo.example` → `.env.n8n-castuo`. Los ficheros `docker-compose.n8n-castuo.yml` y `docker-compose.n8n-castuo.pro.yml` usan `env_file: .env.n8n-castuo`, de modo que las claves llegan al proceso n8n y los nodos pueden usar `{{ $env.DATA_TABLE_SENSORES }}`, etc.
2. **Variables de UI en n8n Cloud / planes con “Variables”:** si tu instancia usa `{{ $vars.NOMBRE }}` en lugar de `$env`, define los mismos nombres en **Settings → Variables**. No mezcles convenciones en el mismo nodo.

## Correcciones respecto a plantillas genéricas

- **Inserción en Data Table:** el nodo correcto es el de **Data Table** (operación insert/upsert según versión), no `n8n-nodes-base.set`. En el campo de tabla usa expresión, p. ej. `={{ $env.DATA_TABLE_SENSORES }}`, si la UI lo permite.
- **`GET /api/variables`:** la API REST de n8n depende de la versión y suele exigir autenticación; no uses ese `curl` como verificación ciega.
- **Webhooks de prueba** (`/webhook/test-slack`, `/webhook/test-db`): no existen hasta que crees workflows que los expongan.
- **Gateway CASTÚO:** `n8n/workflows/castuo_main_orchestrator_gateway.json` acepta `route`, `orchestrator_route` o `request_type`, y si envías `data: { ... }`, solo ese objeto se reenvía al sub-webhook.

## Prueba del gateway (tras importar y activar el workflow)

```bash
curl -X POST "${N8N_WEBHOOK_BASE}/webhook/castuo-orchestrate" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: ${CASTUO_ORCHESTRATOR_API_KEY}" \
  -d "{\"request_type\":\"sensor-data\",\"data\":{\"sensor_id\":\"sensor-001\",\"sensor_type\":\"ph\",\"value\":6.5,\"cultivo_id\":\"cultivo-001\"}}"
```

Sustituye `N8N_WEBHOOK_BASE` (sin barra final en la variable de entorno del contenedor; la URL del `curl` lleva path). Si `CASTUO_ORCHESTRATOR_API_KEY` está vacío en dev, omite el header `X-API-KEY`.

## Stress / inyección masiva (laboratorio)

- Script async (httpx): `scripts/tests/stress_gateway_injection.py` — usa la **misma** forma de cuerpo que el `curl` anterior (`request_type` + `data`). No confundir con plantillas genéricas que postean a `/webhook/sensor-data` sin workflow activo.
- Carga muy alta (miles de RPS): sube `--max-connections` y `--chunk` con cuidado; el cuello de botella suele ser cliente, Docker o n8n downstream — las cifras de “25k RPS validados” solo valen si las **has medido** en tu entorno.
- En otra terminal, nombres reales de contenedores: `docker ps --format '{{.Names}}'`; ejemplo de bucle: `scripts/tests/docker_stats_watch.example.sh` (variable `CASTUO_DOCKER_STATS_NAMES`).

## Valores reales

Sustituye dominios `*.example.com`, claves vacías y nombres `agri_brain.*` por los que muestre tu instancia al crear **Data Tables** y credenciales (Slack, Gmail, Google Sheets, etc.).

## Excelencia operativa (export grande)

Si importas un workflow monolítico desde plantillas AGRI-BRAIN, ancla la parte **audit-grade** a los JSON pequeños del repo y sigue la checklist en [docs/ops/opex-trillizo-integration.md](../docs/ops/opex-trillizo-integration.md) (sección *Blueprint export masivo*). Variables extra: `.env.n8n-multi.example` (bloque *Blueprint extendido*).

## Sabionda · dashboard HTML (GET, demo)

- Guía (HTML dinámico vs frontend, CORS, iframe n8n, CI/CD, Directus, WebSocket): [docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md](../docs/architecture/SABIONDA-N8N-WEB-FRONTEND.md).
- Workflow importable: `n8n/workflows/castuo-sabionda-dashboard-html-stub.json` → `GET .../webhook/sabionda-dashboard` (añade nodo Agente IA entre Code y Respond si generas UI con LLM).
- Directus (preparar POST a `/items/:collection`): `n8n/workflows/castuo-directus-upsert-stub.json`; compose de ejemplo en `docker-compose.directus.example.yml`.
- WebSocket de laboratorio: `scripts/ws-metrics-stub/`.
- Cliente Python orquestador + Holobrain opcional: `scripts/sabionda/sabionda_core.py`.

## Holobrain (demo holográfica, webhook stub)

- Workflow importable: `n8n/workflows/castuo-holobrain-webhook-stub.json` → `POST .../webhook/holobrain-display` con cuerpo `{"metrics":{...}}`.
- Guion técnico + matices DD: `docs/architecture/HOLOGRAPHIC-CASTUO-ARCHITECTURE.md`.
- Cliente de prueba: `python scripts/holo/cursor_holobrain_example.py --demo-critical` (`N8N_WEBHOOK_BASE`, basic auth opcional, `HOLOBRAIN_HMAC_SECRET` / `--hmac-secret` para `X-Holobrain-HMAC` alineado al nodo Code). Módulo reutilizable: `scripts/holo/holobrain_client.py`.

## Multi-instancia n8n

Cinco contenedores opcionales (incl. Trillizo) y gateway con rutas a bases distintas: **`n8n/README-MULTI-N8N.md`**, **`n8n/README-TRILLIZO.md`**, **`docker-compose.multi-n8n.yml`**, **`.env.n8n-multi.example`**.

## Cerebros (Logseq + SilverBullet + Postgres)

Stack opcional **`docker-compose.cerebros.yml`**, **`.env.cerebros.example`**, guía **`n8n/README-CEREBROS.md`**.
