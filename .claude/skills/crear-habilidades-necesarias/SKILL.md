---
name: crear-habilidades-necesarias
description: 'Crear skills reutilizables (SKILL.md) para flujos operativos y de desarrollo. Usar cuando se necesite definir una nueva habilidad, estandarizar un proceso recurrente o convertir una metodologia en workflow ejecutable.'
argument-hint: 'Objetivo de la skill, alcance (workspace o personal) y nivel de detalle esperado'
user-invocable: true
---

# Crear Habilidades Necesarias

## Objetivo
Convertir una necesidad operativa o tecnica en una skill clara, invocable y reutilizable, con estructura valida de `SKILL.md` y criterios de calidad verificables.

## Cuando Usar
- Se repite un flujo de trabajo en tareas similares.
- Hay que estandarizar decisiones y controles de calidad.
- Se quiere empaquetar conocimiento del equipo en una skill invocable.
- Se necesita crear una primera version de skill y refinarla por iteraciones.

## Entradas Minimas
- Resultado esperado de la skill.
- Alcance: workspace o personal.
- Nivel de detalle: checklist breve o workflow completo.
- Criterios de necesidad: frecuencia, criticidad operativa e impacto en tiempo/ROI.

## Procedimiento
1. Definir el resultado de salida.
Identificar que debe producir la skill en terminos observables: archivo, checklist, plan, codigo o validacion.

2. Determinar alcance y ubicacion.
- Workspace: crear en `.claude/skills/<nombre-skill>/SKILL.md`.
- Personal: crear en `~/.claude/skills/<nombre-skill>/SKILL.md`.

3. Evaluar si la skill es necesaria.
Asignar una puntuacion de prioridad con tres ejes (1-5 cada uno):
- Frecuencia de repeticion del flujo.
- Criticidad/riesgo operativo por no estandarizar.
- Impacto en tiempo/ROI esperado.

Formula sugerida:
`prioridad = frecuencia + criticidad + roi`

Regla de decision:
- Si `prioridad >= 10`, crear la skill como prioritaria.
- Si `prioridad < 10`, documentar como candidata futura.

4. Elegir nombre canonico.
Aplicar formato `kebab-case` (minusculas y guiones), 1 a 64 caracteres, y usar el mismo nombre para carpeta y campo `name`.

5. Redactar frontmatter valido.
Incluir como minimo:
- `name`
- `description` (con palabras clave de activacion y casos de uso)
Opcional:
- `argument-hint`
- `user-invocable`

6. Crear estructura de skill.
Crear siempre:
- `SKILL.md`

Crear opcionalmente cuando aporte valor:
- `references/` para guias extensas.
- `scripts/` para automatizaciones ejecutables.
- `assets/` para plantillas y boilerplate.

Recursos recomendados en esta skill:
- Matriz de decision: [PRIORIZACION.md](./references/PRIORIZACION.md)
- Plantilla base: [SKILL_TEMPLATE.md](./assets/SKILL_TEMPLATE.md)
- Script de scoring: [scoring.sh](./scripts/scoring.sh)

7. Redactar cuerpo orientado a ejecucion.
Incluir secciones breves y accionables:
- Objetivo
- Cuando usar
- Entradas minimas
- Procedimiento paso a paso
- Decision points y ramas
- Criterios de finalizacion

8. Incluir decision points explicitos.
Definir reglas de bifurcacion, por ejemplo:
- Si no hay flujo claro, pedir aclaraciones minimas (resultado, alcance, detalle).
- Si el proceso es simple, usar checklist.
- Si hay validaciones o dependencias, usar workflow completo.
- Si hay varias skills posibles, entregar una sola opcion prioritaria (la de mayor puntuacion).

9. Validar calidad antes de cerrar.
Comprobar:
- Nombre de carpeta y `name` coinciden.
- YAML valido entre `---`.
- `description` concreta, con palabras clave de descubrimiento.
- Procedimiento accionable, sin ambiguedades criticas.
- Longitud mantenible (preferible < 500 lineas en SKILL.md).
- Si se crearon carpetas opcionales, deben estar referenciadas desde `SKILL.md` con rutas `./`.

10. Iterar sobre ambiguedades.
Identificar los puntos mas debiles y pedir aclaraciones puntuales. Actualizar la skill y cerrar con una version final.

## Decision Points
- Falta de contexto:
Preguntar solo lo minimo para desbloquear.
- Cobertura del proceso:
Si el flujo no contempla errores comunes, agregar una seccion de validacion y riesgos.
- Descubribilidad:
Si la skill no se activaria por busqueda semantica, enriquecer `description` con terminos de uso reales.

## Criterios de Finalizacion
- Existe `SKILL.md` en la ruta correcta.
- Existe estructura opcional (`references/`, `scripts/`, `assets/`) solo cuando aporta valor real.
- El frontmatter cumple formato y semantica.
- El procedimiento permite ejecutar la tarea de principio a fin.
- Se documentan ramas de decision y checks de calidad.
- La salida entrega una sola skill prioritaria con justificacion por frecuencia, criticidad y ROI.
- Se entregan ejemplos de invocacion para uso inmediato.

## Ejemplos de Invocacion
- `/crear-habilidades-necesarias Diseñar una skill para estandarizar revisiones de PR en este repo.`
- `/crear-habilidades-necesarias Crear skill para onboarding tecnico con checklist y validaciones.`
- `/crear-habilidades-necesarias Convertir nuestro flujo de despliegue en skill reusable.`
