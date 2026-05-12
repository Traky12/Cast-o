# Guia de Entrega para Auditor

## Objetivo
Generar un dossier de entrega listo para revision externa (CTAEX/CDTI/AENOR) partiendo del ultimo paquete de auditoria exhaustivo.

## Comando

```bash
make auditor-delivery
```

## Salida
Se genera:

- artifacts/auditor-delivery-YYYYMMDD-HHMMSS/
- artifacts/auditor-delivery-YYYYMMDD-HHMMSS.zip

Contenido:
- 01-INDICE-EJECUTIVO.md
- 02-CHECKLIST-FIRMABLE.md
- 03-ANEXOS-EVIDENCIAS.md
- DELIVERY-INTEGRITY.sha256
- Copia del paquete audit-package base

## Recomendacion operativa
1. Ejecutar primero `make audit-package-exhaustive`.
2. Ejecutar despues `make auditor-delivery`.
3. Entregar ZIP + checksum al auditor.
