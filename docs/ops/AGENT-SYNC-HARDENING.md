# AGENT Sync Hardening Runbook

> Fuente de verdad actual: `.github/AGENT-SYNC-HARDENING.md`.
> Este archivo se mantiene como referencia operativa para documentacion de operaciones.

## Objetivo
Evitar y contener errores de sincronizacion en flujos autonomos supervisados por Sabionda.

## Cobertura
- Orquestador: flujo-trabajo-autonomo
- Especializados: captacion-clientes, atencion-cliente-24h, creacion-apps-dashboards

## Preflight obligatorio
1. Confirmar estado controlado de trabajo (`git status`).
2. Confirmar dependencias y servicios criticos disponibles.
3. Ejecutar baseline rapido de validacion (tests/smoke segun alcance).
4. Definir fuente de verdad para cada sincronizacion (DB, API, workflow).

## Contingencia para `mgt.clearMarks`
Sintoma tipico: `mgt.clearMarks is not a function` o `mgt is undefined`.

Acciones:
1. Pausar ejecuciones concurrentes del flujo afectado.
2. Reintentar una sola vez tras limpiar estado temporal del proceso (sin borrar datos persistentes).
3. Si persiste, activar modo seguro idempotente: continuar sin llamada a `clearMarks` y registrar marca de degradacion.
4. Escalar a Sabionda con evidencia minima: timestamp, modulo, entrada, stack/error, impacto.

## Protocolo de reconciliacion
1. Leer estado local y remoto.
2. Comparar por `id`, `version` y `updated_at`.
3. Resolver conflictos por politica declarada del flujo:
   - Operacional critica: gana remoto validado.
   - Interaccion usuario: gana ultimo cambio confirmado.
4. Registrar diffs aplicados y resultado final.

## Reglas de robustez
- Operaciones idempotentes por defecto.
- Reintentos acotados (maximo 3) con backoff.
- Timeouts explicitos para llamadas externas.
- Locks logicos en tareas de escritura concurrente.
- Auditoria de toda accion de compensacion/rollback.

## Criterios de salida
- Sin errores activos de sincronizacion.
- Estado reconciliado y verificable.
- Evidencia de supervision Sabionda en el reporte final.
