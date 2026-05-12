# Informe de Contingencia - 2026-03-30

## Resumen Ejecutivo
- Incidencia GitHub: Pull Requests en partial_outage y Actions en partial_outage.
- Estado local: Workflows nuevos creados en rama feature.
- Estado remoto: Trigger directo bloqueado por permisos de integración (403) y/o workflow no presente en main (404).

## Hallazgos
- `gh auth status`: autenticado con `GITHUB_TOKEN`.
- `gh secret list`: 403 (token sin permisos de secretos/actions).
- `gh workflow run deploy-hetzner-staging.yml --ref main`: 404 (archivo no existe aún en main).
- `gh workflow run e2e-first-sale.yml --ref main`: 403 (sin permisos de dispatch).
- `https://staging.castuo-system.es/health`: no resoluble desde este entorno (DNS).
- `https://n8n.castuo-system.es/webhook/woocommerce/order-paid`: no resoluble desde este entorno (DNS).

## Acciones Implementadas
- Script de recuperación creado: `scripts/recover.sh`.
- Artefactos de automatización preparados en PR #12.

## Recomendaciones Inmediatas
1. Mergear PR #12 a `main`.
2. Habilitar permisos de Actions en GitHub Settings.
3. Reintentar dispatch de workflows con token que tenga scope `workflow`.
4. Verificar DNS de staging y n8n desde proveedor/servidor.
