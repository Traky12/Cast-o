# Figuras para la memoria FUNDECYT — Smart Gate v2.0

En `media/` están copiadas las figuras ilustrativas (maqueta / infografías **2025**) con nombres canónicos:

| Archivo | Contenido |
|---------|-----------|
| `fig-01-conectividad-hibrida-dehesa.png` | Topología mesh / enlace / backhaul híbrido (zonas blancas) |
| `fig-02-coste-escalado-v1.png` | Infografía coste y escalado v1 (referencia histórica) |
| `fig-03-resumen-comercial-v1.png` | Resumen comercial v1 (referencia) |
| `fig-04-arquitectura-plataforma-conceptual.png` | Diagrama conceptual plataforma (**anexo delimitador**; no certifica despliegue del repo) |

**Nota legal (también en la memoria principal):** las figuras tienen **carácter ilustrativo**; no constituyen compromiso de producto comercial ni certificación.

Generar PDF (ejemplo, con Pandoc instalado):

```bash
pandoc MEMORIA-TECNICA-CASTUO-SMART-GATE-V2-FUNDECYT.md -o MEMORIA-SMART-GATE-V2-FUNDECYT.pdf --pdf-engine=xelatex -V lang=es
```

Si las imágenes fallan al compilar, comenta las líneas `![]()` o ajusta la ruta.

**Sin Pandoc:** abre `MEMORIA-TECNICA-CASTUO-SMART-GATE-V2-FUNDECYT.md` en un visor Markdown (p. ej. VS Code) y usa **Imprimir → Guardar como PDF**, o instala [Pandoc](https://pandoc.org/) y un motor LaTeX (MiKTeX / TeX Live).
