# Smoke tests (operación)

Scripts opcionales; no sustituyen a `pytest`. Requieren herramientas del host (bash, docker, curl, jq).

| Script | Objetivo |
|--------|----------|
| [`smoke_test_persistence.sh`](./smoke_test_persistence.sh) | PEI-002: envelope persiste tras `docker restart` con volumen en `/app/data`. |

Variables útiles: `PEI002_STUB_BEARER_TOKEN`, `PEI002_STUB_IMAGE`, `PEI002_SMOKE_DATA` (directorio host montado en `/app/data`).
