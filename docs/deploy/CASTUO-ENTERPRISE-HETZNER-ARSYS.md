# CASTÚO-SYSTEM — plantilla enterprise (Hetzner + Arsys + n8n + LangGraph + LangSmith)

Este documento **sustituye** el guion ejecutivo genérico con una implementación **coherente con el monorepo**: un solo API FastAPI (LangGraph en `/langgraph/castuo/run`), n8n con Postgres, Redis opcional, staging MySQL en Arsys.

## 1. Arquitectura real (correcciones al plan “400 nodos”)

| Idea del plan | Realidad técnica |
|---------------|------------------|
| **MCP en `http://n8n:5678/mcp`** | Cursor usa **servidores MCP** (stdio/SSE) definidos en la config del IDE. n8n **no** expone MCP estándar en esa URL. Patrones válidos: webhook n8n → API; **servidor MCP propio** que llame a n8n; o integraciones GitHub → Actions → n8n. |
| **Imagen `mistral-proxy` :11434** | 11434 es patrón típico de **Ollama**, no de Mistral Cloud. Mistral EU suele ser **HTTPS API** (`api.mistral.ai` o endpoint alojado en UE). El backend ya llama a Mistral por HTTP con `MISTRAL_API_KEY`. |
| **LangSmith con `require('langsmith')` en n8n** | El runtime de nodos Code **no** trae LangSmith como en Node de proyecto. Las trazas LangSmith aplican sobre todo a **Python LangChain/LangGraph** con `LANGCHAIN_TRACING_V2` y `LANGSMITH_API_KEY` en el contenedor **`castuo-api`**. |
| **Grafo `langgraph.graph.Graph`** | API antigua/incorrecta. En el repo se usa **`StateGraph`** (`backend/integrations/langgraph_castuo/graph.py`). |
| **“400 nodos n8n”** | n8n no licencia por “nodos” así; es metáfora operativa. Escala = **réplicas**, **queue mode** + workers, y límites de DB. |

## 2. Hetzner — stack Docker (producción / laboratorio VPS)

Archivos:

- `deploy/docker-compose.castuo.enterprise.example.yml`
- `deploy/.env.castuo-enterprise.example` → copiar a `deploy/.env.castuo-enterprise` (no versionar).

Servicios:

- **castuo-api**: imagen construida desde el `Dockerfile` raíz (puerto 8000).
- **n8n**: `docker.n8n.io/n8nio/n8n:latest`, Postgres interno, volumen de datos.
- **postgres**: BD `n8n` para persistencia n8n.
- **redis**: disponible para caché o futuro **queue mode** (no activado en la plantilla para evitar workers extra).

Variables útiles en `castuo-api`:

- `LANGCHAIN_TRACING_V2=true`, `LANGSMITH_API_KEY`, `LANGCHAIN_PROJECT`
- `MISTRAL_API_KEY`, `GAIACHAIN_REGISTER_URL`, `SLACK_WEBHOOK`

Comprobaciones:

```bash
curl -s http://IP:8000/health/enterprise | jq .
curl -s http://IP:8000/langgraph/castuo/health | jq .
```

Ingress TLS y subdominios (`n8n.`, `api.`, `grafo.`) van en **nginx / Traefik / Caddy** delante del host; ejemplos en `deploy/k8s/castuo-langgraph-ingress.example.yaml`.

## 3. Arsys — staging

- `deploy/docker-compose.arsys-staging.example.yml`
- `deploy/.env.arsys-staging.example`

n8n en **5679** (host) con **MySQL 8**. Tras el primer arranque, si n8n falla por timing, reiniciar el contenedor `n8n-staging` cuando MySQL esté listo.

WordPress en Arsys puede convivir en el mismo servidor **fuera** de Docker o en otro vhost; no forma parte del compose.

## 4. Cursor ↔ n8n ↔ API

1. **Webhook** `POST …/webhook/enterprise/cursor-bridge` — workflow `n8n/workflows/castuo_enterprise_cursor_bridge.json` (reenvío a `/langgraph/castuo/run`).
2. **Cursor**: desde un script o extensión, `curl`/HTTP al webhook o directamente al API con el JSON `{"payload":{...}}`.
3. **MCP**: si necesitas MCP, añade un **servidor MCP** (plantilla oficial Cursor) que encapsule esas llamadas; no uses `N8N_ENCRYPTION_KEY` como “API Key MCP” (son conceptos distintos).

## 5. LangSmith

1. Crea proyecto en [LangSmith](https://smith.langchain.com).
2. En **`castuo-api`**, define `LANGSMITH_API_KEY` y `LANGCHAIN_TRACING_V2=true`.
3. El grafo actual usa **httpx** directo a Mistral; para spans ricos en LangSmith, evoluciona el nodo a **ChatMistralAI** (`langchain-mistralai`) manteniendo el mismo grafo.

## 6. DNS (ejemplo)

| Host | Destino |
|------|---------|
| `api.castuo-system.es` | VPS Hetzner (reverse proxy → 8000) |
| `n8n.castuo-system.es` | Mismo VPS → 5678 |
| `staging.castuo-system.es` | IP Arsys → 5679 + TLS |

## 7. GitHub → n8n

Webhook de repositorio apuntando a un workflow n8n (URL del webhook + secreto HMAC). No duplicar secretos en JSON exportado.

## 8. Referencias cruzadas

- n8n ↔ LangGraph (diagrama integrado): [docs/architecture/N8N-LANGGRAPH-INTEGRATED.md](../architecture/N8N-LANGGRAPH-INTEGRATED.md)
- QElectroTech / PLC / Mistral / GaiaChain: [PRONT-MASTER-QELECTROTECH-CASTUO-INTEGRATION.md](PRONT-MASTER-QELECTROTECH-CASTUO-INTEGRATION.md)
- Seguridad, DNS, IoT, trazabilidad: [PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md](PRONT-INTEGRACION-SEGURA-TRAZABILIDAD-2026.md) y [SECURITY_AND_TRACING.md](../security/SECURITY_AND_TRACING.md)
- LangGraph: [docs/architecture/LANGGRAPH-CASTUO.md](../architecture/LANGGRAPH-CASTUO.md)
- Despliegue general: [docs/DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
- n8n Pro mismo red: `docker-compose.n8n-castuo.pro.yml`
