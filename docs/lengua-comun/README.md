# Lengua Común + Castúo 2040 — Bloque editorial (imprimible / talleres)

Este bloque reúne el material editorial “Lengua Común + Castúo 2040 + Cómic educativo” listo para:

- **Imprimir / maquetar** (A4)
- **Proyectar** en aula
- **Usar en talleres** con scripts educativos

## Uso en aula (45–60 min)

### 1) Relato + cómic (20 min)

- Lee un fragmento del relato 2040 y plantea el dilema.
- Muestra viñetas 1–3 del cómic.
- Pregunta de activación: *“¿Qué harías tú si los tractores se apagaran?”*

### 2) Scripts (15 min)

```bash
python scripts/educacion/recuperar_nucleo_castuo.py
python scripts/educacion/activar_castuo.py
```

### 3) Actividad creativa (10 min)

- Opción A: dibujar la **viñeta 7**.
- Opción B: escribir un mensaje breve de victoria (territorio + datos + comunidad).

## Archivos clave

- `LENGUA-COMUN-PLAN-MAQUETACION.md` — estructura editorial y asignación de páginas (160–170 aprox.).
- `PROLOGO-INTRO.md` — prólogo e introducción limpios para maquetación.
- `PLANTILLA-IMPRIMIR.md` — páginas tipo y fichas A4 listas para PDF.

## Recursos del universo Castúo integrados

- Relato 2040: `docs/cuento-castuo-sabionda/04-castuo-2040-rebelion-datos-verdes.md`
- Cómic 6 viñetas: `docs/cuento-castuo-sabionda/05-comic-castuo-2040.md`
- Scripts educativos: `scripts/educacion/`
- Manual transmedia Castúo Educación 2040: `docs/castuo-educacion-2040/`

## Maquetación e impresión (PDF)

Este repo mantiene el contenido en Markdown para edición y control de cambios. Para generar un PDF local (opcional):

```bash
pandoc docs/lengua-comun/*.md -o lengua-comun-castuo-2040.pdf --pdf-engine=weasyprint
```

## Despliegue digital (repo)

```bash
git add docs/lengua-comun/
git commit -m "feat(educacion): bloque Lengua Común listo para impresión/digital"
git push origin main
```

## Assets

La carpeta `assets/` está preparada para colocar la imagen:

- `assets/Copilot_20250703_222214.png` (pendiente de copiar al repo si está fuera del workspace)

