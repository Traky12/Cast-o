# Índice de documentos con afirmaciones históricas no vigentes

> Creado el 2026-09-28 (P0.7). Reconcilia la documentación histórica pública
> con el estado verificado actual del repositorio. Cambio **aditivo**: ningún
> documento se ha borrado, movido ni renombrado, y no se ha reescrito el
> historial. El estado vigente de las capacidades está en la tabla de
> afirmaciones del [`README.md`](../README.md) (benchmarking `TARGET`, suite de
> tests `CURRENT` parcial, licencia pendiente de revisión de PI).

## Documentos marcados como históricos

Cada documento lleva, justo después de su título, el aviso *"Estado documental
histórico — no constituye evidencia vigente de TRL 9, certificación,
validación externa, producción ni conformidad"* y el bloque
`document_status: historical`.

| Documento | Afirmación histórica no vigente |
|---|---|
| [`docs/RESUMEN-SESION-TRL9.md`](RESUMEN-SESION-TRL9.md) | TRL 9 |
| [`docs/IMPLEMENTACION-TRL9-COMPLETADA.md`](IMPLEMENTACION-TRL9-COMPLETADA.md) | "Implementación TRL9 completada" |
| [`docs/ops/PRONTUARIO-MAESTRO-OPERATIVIDAD-CERTIFICADA-TRL9.md`](ops/PRONTUARIO-MAESTRO-OPERATIVIDAD-CERTIFICADA-TRL9.md) | Operatividad "certificada" TRL 9 |
| [`docs/CASTUO-SYSTEM-ANALISIS-COMPLETO.md`](CASTUO-SYSTEM-ANALISIS-COMPLETO.md) | "Estado: Production Ready" |
| [`docs/MATRIZ-COMPONENTES-PRESENTE-VS-REQUERIDO.md`](MATRIZ-COMPONENTES-PRESENTE-VS-REQUERIDO.md) | Componentes "en Producción / Operativo"; "Legal certified" |
| [`docs/EJECUTIVO-EXCELENCIA-OPERATIVA.md`](EJECUTIVO-EXCELENCIA-OPERATIVA.md) | "HA production-ready"; servicios "operativos" |
| [`docs/ops/RUNBOOK-GO-LIVE-PR19.md`](ops/RUNBOOK-GO-LIVE-PR19.md) | Go-live / operación productiva |
| [`docs/ops/GO-LIVE-EJECUTIVO-PR19.md`](ops/GO-LIVE-EJECUTIVO-PR19.md) | Go-live / operación productiva |
| [`docs/ops/CHECKLIST-GO-LIVE-PR19.md`](ops/CHECKLIST-GO-LIVE-PR19.md) | Go-live / operación productiva |
| [`docs/ops/INFORME-TECNICO-OPERATIVIDAD-2026-04-03.md`](ops/INFORME-TECNICO-OPERATIVIDAD-2026-04-03.md) | Operatividad y validación en entorno productivo |
| [`WHATSAPP-INTEGRATION-COMPLETE.md`](../WHATSAPP-INTEGRATION-COMPLETE.md) | "100% completada" |

## Paquetes de auditoría interna

`artifacts/audit-package-20260403-*` (4 directorios y 3 `.zip` con su
`.sha256`) contienen copias de algunos de estos documentos. **No se han
modificado**, porque llevan `manifest.txt` / `integrity.sha256` y editarlos
rompería su integridad. El aviso correspondiente está en
[`artifacts/AUDIT-PACKAGES-NOTICE.md`](../artifacts/AUDIT-PACKAGES-NOTICE.md).

## Criterio de inclusión

Documentos de la rama por defecto con afirmaciones **afirmativas** de TRL 9,
certificación, producción, go-live, validación externa, auditoría
independiente o completitud total. Se excluyeron los falsos positivos:
certificados del dominio agrícola (TRACES, GlobalGAP…), registros de auditoría
como funcionalidad, instrucciones operativas y frases negadas o marcadas como
pendientes. Revisar esta lista si aparecen documentos nuevos.

## Siguientes fases (no incluidas en este cambio)

Matizar el texto de las afirmaciones concretas, o mover los documentos a un
archivo histórico, solo después de revisar los enlaces internos y con
decisión del owner.
