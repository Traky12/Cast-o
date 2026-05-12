# Politicas CI/CD de Reconcile y Secretos

## Objetivo
Establecer un criterio operativo claro para evitar falsos bloqueos en PR y mantener integridad en ramas de release.

## Politica de Reconcile
- En `pull_request`: se permite `drift_detected=true` y el job no bloquea por ese motivo.
- En `workflow_dispatch` (o ramas de release): `drift_detected=true` bloquea el job.
- En cualquier evento: errores criticos de ejecucion de reconcile (status distinto de 0 sin drift permitido) bloquean.

## Artefactos Requeridos
El workflow debe generar y subir:
- `artifacts/summary.json`
- `artifacts/drift_report.log` (cuando haya drift)
- `artifacts/reconcile-*.log`
- `artifacts/reconcile-*.patch`

## Politica de Secretos
- No hardcodear claves en codigo ni workflows.
- Usar `GitHub Actions Secrets` para credenciales de CI.
- Secret esperado: `SABIONDA_API_KEY`.
- En runtime CI, el workflow puede materializar `secrets/sabionda_key` localmente con permisos restringidos para compatibilidad con scripts existentes.

## Alta de SABIONDA_API_KEY
### Opcion CLI (si el token tiene permisos)
```bash
gh auth login --scopes "repo,actions:write"
printf '%s' '<TU_API_KEY>' | gh secret set SABIONDA_API_KEY -R Traky12/Castuo-system
```

### Opcion Web UI
1. Ir a `Settings` del repositorio.
2. Abrir `Secrets and variables` > `Actions`.
3. Crear secret `SABIONDA_API_KEY`.

## Criterio GO/NO-GO
- GO:
  - Tests Python y Node en verde.
  - Reconcile en PR con drift permitido o sin drift.
  - Reconcile fuera de PR sin drift.
- NO-GO:
  - Fallos de tests.
  - Reconcile fuera de PR con drift.
  - Secretos faltantes en jobs que dependan de credenciales.
