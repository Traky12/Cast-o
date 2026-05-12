# Guía de despliegue (CASTÚO-SYSTEM + n8n)

## Requisitos

- Docker y Docker Compose (o stack Pro con `docker-compose.n8n-castuo.pro.yml`).
- Dominio y TLS delante de n8n en producción (reverse proxy o cloud).
- PostgreSQL si los workflows persisten fuera de Data Tables embebidas (ver SQL del repo).

## Despliegue rápido n8n standalone

1. Clonar el repositorio y copiar el ejemplo de entorno:

   ```bash
   cp .env.n8n-castuo.example .env.n8n-castuo
   ```

2. Editar `.env.n8n-castuo`: `N8N_PASSWORD`, `N8N_ENCRYPTION_KEY`, `WEBHOOK_URL`, y el bloque `N8N_*` (tablas/canales). **No** commitear claves de API; usar **Credenciales** en la UI de n8n.

3. Levantar el servicio:

   ```bash
   docker compose -f docker-compose.n8n-castuo.yml --env-file .env.n8n-castuo up -d
   ```

4. Importar workflows desde `n8n/workflows/` (por ejemplo `castuo_inicializar_sistema.json`, `castuo_guardar_cosechas.json`, `castuo_reporte_diario.json`, `castuo_sabionda_orchestrator_stub.json`, `castuo_ipfs_investment_memo.json`, `castuo_backup_google_sheets.json`, `castuo_orchestrator_minimal.json`). Credenciales y orquestador: [docs/deploy/N8N-INITIAL-SETUP-CASTUO.md](deploy/N8N-INITIAL-SETUP-CASTUO.md).

5. Crear tablas en Postgres (si aplica):

   ```bash
   psql -h HOST -U USER -d DB -f scripts/sql/n8n_castuo_tables.sql
   ```

## LangGraph (opcional)

Tras `pip install` del backend con `langgraph` y `langchain-core`:

```bash
curl -X POST "http://localhost:8000/langgraph/castuo/run" \
  -H "Content-Type: application/json" \
  -d "{\"payload\":{\"cultivo\":\"tomate\",\"humedad\":75,\"temperatura\":22}}"
```

Salud: `GET /langgraph/castuo/health`. Detalle: [docs/architecture/LANGGRAPH-CASTUO.md](architecture/LANGGRAPH-CASTUO.md).  
QElectroTech / PLC / n8n: [docs/deploy/PRONT-MASTER-QELECTROTECH-CASTUO-INTEGRATION.md](deploy/PRONT-MASTER-QELECTROTECH-CASTUO-INTEGRATION.md).  
Seguridad y trazabilidad (DNS, anti-patrones, IoT): [docs/deploy/PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md](deploy/PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md), [docs/security/SECURITY_AND_TRACING.md](security/SECURITY_AND_TRACING.md).

## API Workspace Sabionda (FastAPI)

Con el backend en marcha (`uvicorn` o stack prod):

- `GET /workspace/agents?page=1&per_page=20` — tarjetas de agentes (`backend/data/sabionda_workspace_agents.json`).
- `GET /workspace/nodes?page=1&per_page=24` — página de entre **367** nodos demo (sustituir por inventario real).
- `GET /workspace/items?kind=agents|nodes&page=1&per_page=20` — unificación.
- `WS /workspace/ws/agents` — eco JSON (sustituir por bus de métricas o usar `GET /agents/dashboard/stream` SSE).

Orquestador n8n de prueba:

```bash
curl -X POST "http://localhost:5678/webhook/sabionda/orchestrator" \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\":\"hydro_analysis\",\"action\":\"run_check\"}"
```

Arquitectura detallada: [docs/architecture/SABIONDA-WORKSPACE-DASHBOARD.md](architecture/SABIONDA-WORKSPACE-DASHBOARD.md). Hook Git opcional: `.githooks/post-commit.example`.

## Validación

- Variables en el contenedor: `docker exec -it n8n-castuo sh -c 'echo "$N8N_DB_COSECHAS"'`.
- Workflow manual **CASTUO_Inicializar_Sistema** (o `CASTUO_SKIP_EXTERNAL_VALIDATION=1` en laboratorio).
- Cosechas de prueba:

  ```bash
  curl -X POST "http://localhost:5678/webhook/guardar-cosechas" \
    -H "Content-Type: application/json" \
    -d "{\"cultivo_id\":\"TEST-001\",\"fecha_cosecha\":\"2026-03-28\",\"peso_total\":1500,\"calidad\":\"A\"}"
  ```

## Stack enterprise (plantilla)

- [docs/deploy/CASTUO-ENTERPRISE-HETZNER-ARSYS.md](deploy/CASTUO-ENTERPRISE-HETZNER-ARSYS.md) — Hetzner + Arsys, n8n, LangGraph, LangSmith, límites reales de MCP.

## Referencias

- Guía despliegue más amplia: [docs/deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)
- Producción / certificación: [docs/DEPLOYMENT_PRODUCTION_GUIDE.md](DEPLOYMENT_PRODUCTION_GUIDE.md)
- Política de credenciales: [docs/SECURITY_POLICY.md](SECURITY_POLICY.md)
- Variables globales JSON opcionales: `config/global_vars.json` y `CASTUO_GLOBAL_VARS_PATH`
