# Changelog

## [3.1.2] - 2026-04-09

### Added
- `docs/MAPA-CONEXION-TOTAL.md`: mapa completo de integraciones con tabla de módulos, contratos, variables de entorno, criterios de aceptación y referencias a tests. Supervisado por Sabionda.
- `tests/test_e2e_smoke_traces.py`: suite de smoke tests E2E para TRACES UE + Hyperledger Fabric (modo simulado, reconciliación, async wrapper, singleton, logging).
- `.github/workflows/integration-gate.yml`: CI/CD gate con 4 jobs (`api-tests`, `traces-smoke`, `security-gate`, `integration-gate`). Publica comentario de estado en PRs. Trigger en push/PR a `main`.
- `TRACESClient.check_status(reference)`: método de reconciliación para consultar estado de sumisión TRACES por referencia.
- `TRACESClient.async_submit_to_traces()`: wrapper asíncrono sobre `submit_to_traces()` para migración incremental a asyncio.

### Changed
- `api/services/traces.py`: migración de `print()` a `logging.getLogger(__name__)` para trazabilidad estructurada. Retries con tenacity (3 intentos, backoff exponencial 2-10s) en `_send_to_traces()` y `_register_in_hyperledger()`. Retrocompatibilidad total con API existente.
- `api/main.py` — `GET /api/v1/iot/telemetry/{sensor_id}/latest`: ahora prioriza lectura desde TimescaleDB cuando disponible (`timescale_db.available`), con fallback a dict en memoria.
- `infrastructure/observability/alertmanager.yml`: añadidos receptores `slack-integration-failures` y `slack-vault-critical`, y rutas para `traces_submit_failed`, `iot_persistence_failed` y `vault_unreachable`.

### Fixed
- IoT GET endpoint devolvía siempre datos en memoria incluso cuando TimescaleDB estaba activo.
- TRACES client usaba `print()` en lugar de logging estructurado, perdiendo contexto de trazabilidad.

## [3.1.1] - 2026-04-02

### Added
- Nuevos tests para orchestrator y autoscaler.
- Configuracion de tests con conftest.py para no depender de PYTHONPATH manual.
- NetworkPolicy base para restringir ingreso a castuo-api en Kubernetes.

### Changed
- Refactorizacion de api/routers/invernadero.py para reducir repeticion en validacion y respuestas.
- Workflow validate-all actualizado para ejecutar suite completa Python con cobertura.
- HPA actualizado con behavior (stabilization windows y politicas de scale up/down).

### Fixed
- Llamada de create_load_balancer en autoscaler ahora usa helper de retry compartido.

