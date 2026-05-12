# Changelog

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
