# Claude Design — evidence boundary / límite de evidencia

**Fecha de corte:** 2026-11-13  
**Estado:** `DESIGN_REVIEW_CANDIDATE / GO_BLOCKED`  
**Rama de trabajo:** `docs/claude-design-evidence-boundary-20261113`

## Propósito

Este documento extiende el control de trazabilidad del PR #679 y esta superficie a esta superficie frontend/diseño. No aplica cambios de runtime, CSS, tokens, componentes ni configuración de despliegue. Define qué puede considerarse evidencia retenida antes de aceptar una exportación de Claude Design.

## Boundary

- Un relato o resultado visto dentro de Claude Design es `REPORTED_NOT_RETAINED` hasta que exista una exportación exacta, un commit/blob identificable y un manifiesto reproducible.
- Un archivo presente en este repositorio no demuestra que proceda de Claude Design ni que haya sido revisado por una persona independiente.
- No se declara sincronización, accesibilidad real, prueba visual, CI verde, staging, merge readiness ni producción por ausencia de fallos observados.
- Los repositorios archivados y las ramas principales no se modifican como parte de este incremento.

## Evidencia mínima para una futura importación

1. Fuente exacta/exportación autorizada y lista de archivos.
2. SHA o comparación de blobs contra la rama destino.
3. Manifiesto regenerado y explicación de cualquier archivo no previsto.
4. Pruebas de interacción y accesibilidad, incluyendo teclado, foco y lector de pantalla cuando aplique.
5. Revisión humana independiente y PR separado; sin merge automático.

## Estado de esta entrega

| Control | Estado |
|---|---|
| Claude Design source export retained | `NOT_AVAILABLE` |
| Component/style changes applied | `NO` |
| Visual evidence | `NOT_TESTED` |
| Independent review | `NOT_TESTED` |
| CI/staging/production promotion | `BLOCKED` |
| Next action | `REVIEW_SOURCE_EXPORT` |

## No-claims

Este documento es una mejora de gobernanza y no una certificación del sistema de diseño. La ausencia de cambios de código mantiene el riesgo acotado, pero no sustituye la evidencia externa pendiente.
