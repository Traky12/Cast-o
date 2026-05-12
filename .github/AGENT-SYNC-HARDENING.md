---
title: "Runbook de Sincronizacion - CASTUO-SYSTEM AGENTS"
version: "4.3.1"
last_updated: "2026-04-01"
---

# Protocolos Anti-Sincronizacion y Mitigacion mgt.clearMarks

## Contingencia para mgt.clearMarks
Causa tipica: corrupcion de contexto de sincronizacion en herramientas de edicion colaborativa.

### Mitigacion operativa
1. Reintento controlado con backoff exponencial y maximo 3 intentos.
2. Si falla el tercer intento, activar modo seguro idempotente.
3. Notificar a Sabionda y registrar incidencia en logs/sync-failure-YYYYMMDD.log.
4. Ejecutar reconciliacion local/remoto antes de continuar.

### Snippet de referencia
```python
import time

retry_count = 0
max_retries = 3

while retry_count < max_retries:
    try:
        result = execute_critical_operation()
        break
    except Exception as e:
        if "mgt.clearMarks" in str(e):
            retry_count += 1
            time.sleep(2 ** retry_count)
            continue
        raise
```

## Preflight de robustez (obligatorio)
Ejecutar antes de cualquier accion de agentes:

0. Validar soberania OpenClaw y residencia EU (`scripts/validate_openclaw_sovereignty.sh`).
1. Comprobar conectividad a proveedor AI configurado (Mistral u otro endpoint soberano).
2. Validar perfil cloud del repositorio.
3. Revisar sincronizacion Git y registrar advertencias.
4. Validar autenticacion Sabionda cuando haya clave y endpoint configurados.

Script oficial: scripts/preflight.sh

### Reglas de soberania OpenClaw# 1. WordPress plugin
wp plugin install utell-iai --activate
wp option set utell_iai_key "sk-mistral-castuo"

# 2. n8n workflow
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: n8n_secret" \
  -d @n8n/workflows/utell-iai-castuo.json

# 3. Test
curl -X POST http://localhost:8000/api/ai/utell \
  -d '{"query": "invernadero 123 estado", "shard_id": "CAX21"}'

- `OPENCLAW_SOVEREIGN_MODE` debe mantenerse en `strict`.
- `OPENCLAW_DATA_RESIDENCY` debe mantenerse en `eu-only`.
- `OPENCLAW_ALLOWED_REGION` debe limitarse a `eu-*`.
- `OPENCLAW_ENDPOINT` (si se define) debe ser HTTPS y dominio EU/soberano.

## Reconciliacion
1. Comparar estado local vs remoto con git diff.
2. Detectar drift y generar parche de reconciliacion.
3. Aplicar solo cambios auditables y trazables.
4. Confirmar estado final con validacion de pruebas/smoke.

Script oficial: scripts/reconcile.sh

## Criterios de bloqueo
- Preflight fallido.
- Drift no resuelto.
- Errores de sincronizacion repetidos (>3 en 24h).
- Incumplimiento de supervision soberana de Sabionda.

## Aprobacion Sabionda
- Reconcile no dry-run requiere aprobacion manual de Sabionda y 2 revisores DPO.
- Modo seguro se mantiene activo por defecto en PRs.
- Objetivo de MTTR para incidentes criticos: <30 minutos.

## Evidencia minima en cada incidente
- git status --porcelain
- git log --oneline -5
- logs/sync-failure-YYYYMMDD.log
- salida de scripts/preflight.sh
- metricas de scripts/metrics-sync.sh
