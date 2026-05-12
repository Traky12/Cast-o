# Auditoria Operativa: GitHub Opcional

Fecha: 2026-04-03
Estado: CERTIFICADO (operativa core sin dependencia obligatoria de GitHub)

## Objetivo
Certificar que la ejecucion completa de la operativa principal de CASTUO-SYSTEM no depende de GitHub Goldfish y que la integracion GitHub queda en modo opcional/contingencia.

## Alcance auditado
- API principal FastAPI (carga de routers y health)
- Router de webhook GitHub (habilitacion condicional)
- Script de hardening operativo
- Tests de integracion y smoke
- Separacion entre runtime core y CI/CD auxiliar

## Evidencias tecnicas

### 1) Feature flags por defecto en modo desacoplado
Archivo: api/main.py
- ENABLE_GITHUB_INTEGRATION con default false
- REQUIRE_GITHUB_HARDENING con default false
- Carga condicional del router github_webhook solo cuando ENABLE_GITHUB_INTEGRATION=true

Resultado:
- En modo por defecto, el router de GitHub no se monta.
- El runtime principal mantiene endpoints core activos, incluido /health.

### 2) Hardening no bloqueante sin GitHub
Archivo: scripts/setup-prod-hardening.sh
- Si REQUIRE_GITHUB_HARDENING no es true, el script entra en modo desacoplado y finaliza en GO sin exigir GH_TOKEN ni conectividad GitHub.

Ejecucion verificada:
- Comando: REQUIRE_GITHUB_HARDENING=0 bash scripts/setup-prod-hardening.sh
- Salida clave:
  - [INFO] Modo desacoplado activo: se omite dependencia operativa de GitHub
  - [OK] GO: sistema procesable sin conexion obligatoria a GitHub

### 3) Test funcional y smoke ON/OFF
Archivo: tests/test_github_integration_toggle.py
Cobertura:
- GitHub desactivado explicitamente
- Variables ausentes (defaults)
- GitHub activado explicitamente
- Smoke de arranque y /health en ambos modos

Ejecucion verificada:
- Comando: pytest -q tests/test_github_integration_toggle.py tests/test_github_webhook_router.py
- Resultado: 11 passed

## Distincion core vs componentes auxiliares
Se detectan referencias GitHub en scripts de transferencia, automatizacion y workflows CI/CD (por ejemplo, scripts/github-transfer.sh y .github/workflows). Estas rutas no forman parte del runtime core de ejecucion local/produccion del servicio API.

## Conclusiones
1. La operativa principal del sistema queda certificada como local-first y ejecutable sin GitHub.
2. GitHub pasa a rol opcional de contingencia (opt-in) mediante feature flag.
3. El hardening GitHub se separa como politica bajo demanda y no como requisito de arranque operativo.
4. El sistema mantiene trazabilidad/observabilidad en el flujo principal sin bloqueo por conectividad GitHub.

## Criterio final de certificacion
APROBADO: no existe dependencia estructural obligatoria de GitHub Goldfish para la ejecucion completa de la operativa core.
