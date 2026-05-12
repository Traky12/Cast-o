# Roadmap: squads, Anytype, CASTUO-SYNC

Implementacion **no acoplada** al SSE del dashboard; referencia para siguiente fases.

| Bloque | Estado | Notas |
|--------|--------|--------|
| **Squads / agentes** (JIRA, Slack, Celery) | Futuro | Colas Celery + webhooks; sin credenciales en repo. |
| **Anytype** | Semana proxima | Knowledge base EU; API keys en vault. |
| **CASTUO-SYNC** | Post-CTAEX | GaiaChain completo + witness batch; hoy: `witness_minimal`. |
| **Dashboard SSE** | Activo | `GET /agents/dashboard/stream` + `templates/dashboard.html`. |

## SSE

- Metricas actuales: **simuladas** (CPU/hash); sustituir por lectura de `/health`, Prometheus o psutil en el worker.
- CORS: mismo origen; para otro dominio, ajustar `CORSMiddleware` y cabeceras SSE.
