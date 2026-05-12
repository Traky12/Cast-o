# Revisión automática — materiales educativos

Scripts de auditoría para detectar:

- enlaces internos rotos en Markdown
- uso de `PLACEHOLDER:` pendiente
- comandos Python mencionados en docs que no existen
- compilación básica de scripts (`py_compile`)

## Uso

```bash
python scripts/revision/revisar_docs.py
python scripts/revision/revisar_scripts.py
python scripts/revision/generar_informe.py --output informe_revision.md
```

## Alcance

El objetivo es **fallar pronto** en lo crítico (enlaces rotos / scripts que no compilan) y dejar trazabilidad clara para correcciones.

