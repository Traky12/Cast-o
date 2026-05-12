# PRONT MAESTRO FINAL — SISTEMA COMPLETO DE ACCIÓN EDUCATIVA SABIONDA-OMEGA 2040

Documento integral y accionable para operar el ecosistema educativo (aula, comunidad y territorio) con auditoría continua, tecnología ética y métricas de impacto **sin dependencia obligatoria de Internet**.

---

## 0) Alcance del ecosistema (qué se gobierna)

**Bloque educativo (fuentes canónicas):**

- `docs/cuento-castuo-sabionda/` (relato 2040 + cómic + guía rápida)
- `docs/lengua-comun/` (bloque editorial A4 + plantillas)
- `docs/castuo-educacion-2040/` (manual transmedia)
- `scripts/educacion/` (scripts de aula)
- `docs/ops/kids/` (matriz validacion por edad; documento canonico: [`validacion-por-edad-y-nivel-educativo-2026.md`](../ops/kids/validacion-por-edad-y-nivel-educativo-2026.md))

## Bloque Educativo: Validacion por Edad y Nivel

*(Referencia canonica: [`docs/ops/kids/validacion-por-edad-y-nivel-educativo-2026.md`](../ops/kids/validacion-por-edad-y-nivel-educativo-2026.md))*

| Grupo de Edad | Nivel Educativo | Contenidos adaptados (resumen) | Protocolos de seguridad (resumen) |
|---|---|---|---|
| 3-5 anos | Educacion Infantil (1er ciclo) | Memoria; plantas; cuentos sostenibles | 15 min; filtro estricto; avatares no realistas; sin datos personales |
| 6-8 anos | Educacion Primaria (1er ciclo) | Ciclo del agua; cultivos; energia solar basica | 20 min; validacion pedagogica; notarizacion GaiaChain (anonima) |
| 9-12 anos | Educacion Primaria (2do ciclo) | Agrovoltaica basica; matematicas; intro blockchain | 30 min; supervision; registro GaiaChain anonimo |
| 13-16 anos | ESO | Sistemas agrovoltaicos; eficiencia; proyectos STEM | Auth parental; datos anonimizados; GDPR |
| 16-18 anos | Bachillerato / FP Medio | Instalacion; ROI; gemelos digitales | YubiKey en modulos sensibles; certificacion verificable |
| 18+ anos | Universidad / FP Superior | Cursos especializados; datos reales (si aplica) | Certificado digital; NDA |
| Profesionales | Formacion continua / Master | Especializacion; I+D | Firma digital; licencias anuales |

> **Nota**: Protocolos completos, LOMLOE, DigCompEdu e ISTE estan en el [documento canonico](../ops/kids/validacion-por-edad-y-nivel-educativo-2026.md).

**Auditoría y métricas:**

- `scripts/revision/` (auditoría automática)
- `scripts/dashboard/` (métricas y dataset de impacto)
- `docs/lengua-comun/DASHBOARD/` (salidas JSON/plantillas)

---

## 1) Componentes críticos (faltantes → integrados aquí)

| Componente | Propósito | Ubicación en repo |
|-----------|-----------|-------------------|
| **Guía de Facilitadores** | manual de implementación y evaluación | `docs/lengua-comun/GUIA-FACILITADORES.md` |
| **Sistema de Badges** | reconocimiento (logros diversos, no solo técnicos) | `docs/lengua-comun/BADGES/` |
| **Dashboard de Impacto** | métricas offline-first + exportable | `docs/lengua-comun/DASHBOARD/` + `scripts/dashboard/` |
| **Red de Aliados** | colaboración institucional y comunitaria | `docs/lengua-comun/ALIADOS.md` |
| **Sostenibilidad** | financiación y escalado sin dependencia única | `docs/lengua-comun/SOSTENIBILIDAD.md` |
| **Certificaciones** | microcredenciales verificables (plan) | `docs/lengua-comun/CERTIFICACIONES/` |
| **Traducciones** | flujo colaborativo y validación con comunidades | `docs/lengua-comun/TRANSLATIONS/` |
| **Kit de Prensa** | difusión y materiales reutilizables | `docs/lengua-comun/PRENSA/` |
| **Kit de Emergencia** | modo low-tech (sin internet / pocos recursos) | `docs/lengua-comun/KIT-EMERGENCIA.md` |
| **App móvil offline (futuro)** | acceso sin internet a PDFs + guías | `mobile/README.md` |

---

## 2) Roles y responsabilidades (Sabionda-Omega)

| Rol | Responsable | Enfoque | KPI operativo |
|-----|------------|---------|--------------|
| **Sabionda-Omega (Coordinadora)** | IA central | coherencia global y priorización | 0 CRITICAL por release |
| **Agente-Técnico** | revisión de scripts | ejecución, seguridad, resiliencia | 0 CRITICAL en `scripts/educacion/` |
| **Agente-Narrativa** | coherencia textual | puente relato↔cómic↔scripts | 0 comandos mencionados que no existan |
| **Agente-Cultural** | inclusión/diversidad | representación ética | reducción continua de sesgos repetitivos |
| **Agente-Accesibilidad** | diseño universal | legibilidad / imprimible / offline | kit emergencia usable (sin internet) |
| **Agente-Comunidad** | validación real | feedback y adopción | issues cerradas por impacto |
| **Agente-Automatización** | auditoría + métricas | ejecutar y consolidar | 100% scripts ejecutables en Windows/Linux |

---

## 3) Checklists (operación)

### A) Documentos (relato/cómic/editorial)

- **Enlaces internos**: 0 rotos.
- **Placeholders**: rastreables con `PLACEHOLDER:` y documentados.
- **Legibilidad**: secciones cortas, pasos accionables, versiones por edad.
- **Coherencia**: lo que se promete en narrativa existe en scripts (o se marca como ficción).

### B) Scripts educativos

- **Offline-first**: no red por defecto; si hay red, debe ser opt-in.
- **Resiliencia**: entradas vacías/errores no rompen; devuelven guía.
- **Seguridad pedagógica**: no induce prácticas dañinas; prioriza ahorro hídrico.

### C) Implementación comunitaria

- **Facilitación**: preparación clara y rúbricas simples.
- **Reconocimiento**: badges accesibles para perfiles diversos.
- **Kit emergencia**: funciona solo con papel, lápiz y dinamización.

---

## 4) Protocolo de mejora continua (ciclo)

### Fase 1 — Auditoría automática (semanal o por release)

```bash
python scripts/revision/revisar_docs.py > revision_docs.log
python scripts/revision/revisar_scripts.py > revision_scripts.log
python scripts/revision/generar_informe.py --output informe_revision.md
```

### Fase 2 — Métricas (mensual o por evento)

```bash
python scripts/dashboard/generar_metricas.py
```

Salida esperada:

- `docs/lengua-comun/DASHBOARD/metricas.json`

### Fase 3 — Validación en territorio (pilotos)

- **Cáceres**: aula + comunidad rural.
- **Oaxaca**: enfoque kit emergencia y traducciones.

### Fase 4 — Corrección y liberación

- Rama: `fix/educacion-...`
- Validación mínima: auditoría + ejecución básica de scripts de aula.

---

## 5) KPIs (mínimos y ampliados)

**Mínimos (medibles sin servicios externos):**

- CRITICAL en auditoría: 0
- Enlaces internos rotos: 0
- Scripts de aula compilables: 100%
- Placeholders: decreciente

**Ampliados (cuando haya infraestructura):**

- Nº talleres / trimestre
- Participación activa (encuestas post-taller)
- Lenguas representadas en traducciones
- Proyectos comunitarios derivados

---

## 6) Principios Sabionda-Omega 2040

- **Validar la vida antes que el dato**: si una práctica educativa daña el territorio, se bloquea.
- **Ahorro hídrico**: el agua es condición de continuidad; el material enseña a decidir con cuidado.
- **Interoperabilidad**: lo que se imprime debe poder ejecutarse en aula; lo que se ejecuta debe poder explicarse en papel.
- **Resiliencia**: el fallo debe dejar aprendizaje, no frustración.

