# PRONT MAESTRO INTEGRADO — SABIONDA-OMEGA + REVISIÓN EDUCATIVA 2040

Sistema de auditoría colaborativa para revisar **Lengua Común**, **Castúo 2040**, **cómic**, y **scripts educativos** con enfoque en:

- **Inclusión** (lenguaje y representación)
- **Precisión técnica** (código, comandos, compatibilidad)
- **Coherencia narrativa** (relato↔cómic↔scripts)
- **Accesibilidad** (estructura, legibilidad, material imprimible)

Este documento es el **prompt maestro** (ejecutivo-técnico) para coordinar auditorías y correcciones del bloque educativo:

- `docs/cuento-castuo-sabionda/` (relato + cómic + guía)
- `docs/lengua-comun/` (bloque editorial A4)
- `docs/castuo-educacion-2040/` (manual transmedia)
- `scripts/educacion/` (scripts de aula)
- `scripts/revision/` (auditoría automática)

---

## 1) Roles (equipo de revisión)

| Rol | Responsable | Herramientas | Enfoque | KPI principal |
|-----|------------|--------------|--------|--------------|
| **Sabionda-Omega (Coordinadora)** | IA central | Python + scripts de auditoría | coherencia global | 0 CRITICAL por release |
| **Agente-Técnico** | revisión de código | `py_compile` (y extensible a linters) | precisión técnica | 0 errores críticos en `scripts/educacion/` |
| **Agente-Narrativa** | coherencia textual | checklist | fluidez y puente relato↔scripts | 0 referencias a comandos inexistentes |
| **Agente-Cultural** | inclusión y diversidad | checklist | representación ética | reducción continua de sesgos repetitivos |
| **Agente-Accesibilidad** | diseño universal | checklist | legibilidad / imprimible | 0 “bloques ilegibles” en plantillas |
| **Agente-Comunidad** | feedback real | issues + talleres | mejora continua | issues priorizados por impacto |
| **Agente-Automatización** | pipeline | `scripts/revision/` | eficiencia | 100% auditorías ejecutables en Windows/Linux |

---

## 2) Checklist (automatizable + manual)

### A. Relato y cómic (texto)

- **Coherencia**: personajes, lugares, tiempo; no hay “saltos” sin puente.
- **Conexión con scripts**: todo comando mencionado existe (o está marcado como ejemplo).
- **Lenguaje**: frases aptas para 12–16 (o claramente etiquetadas por nivel).
- **Inclusión**: evitar sesgos repetitivos; presencia de voces diversas sin folclorizar.
- **Territorio**: la tecnología se explica con impacto (agua, suelo, soberanía, energía).

### B. Scripts educativos (Python)

- **Ejecutan** en Windows (PowerShell) y Linux.
- **Manejo de error**: no “rompen” por entrada vacía o inesperada.
- **Seguridad**: no piden/guardan credenciales reales; no hacen red por defecto.
- **Claridad**: salida comprensible; mensajes alineados con la narrativa.
- **Resiliencia**: si falla una parte, el resto sigue y deja rastro útil.

### C. Documentación y enlaces

- **Enlaces internos**: rutas correctas, sin dependencias externas prematuras.
- **Placeholders**: explícitos y rastreables (misma marca: `PLACEHOLDER:`).
- **Imprimible**: secciones cortas, listas, títulos claros.

---

## 3) Protocolo de revisión (ciclo)

### Fase 1 — Auditoría automática (repo)

Comandos:

```bash
python scripts/revision/revisar_docs.py > revision_docs.log
python scripts/revision/revisar_scripts.py > revision_scripts.log
python scripts/revision/generar_informe.py --output informe_revision.md
```

Salida:

- `informe_revision.md` con hallazgos, severidad y recomendaciones.

### Fase 2 — Revisión humana (con apoyo IA)

- Convertir hallazgos en **issues** con etiquetas:
  - `bug` (rompe ejecución / enlace roto)
  - `enhancement` (mejora narrativa/pedagógica)
  - `cultural` (representación / precisión)
  - `accessibility` (legibilidad / impresión)

### Fase 3 — Corrección + validación

- Rama por temática: `fix/educacion-...`
- Validación mínima:
  - scripts compilan (`py_compile`)
  - docs pasan auditoría de enlaces internos

---

## 4) KPIs (métricas mínimas dentro del repo)

Estas métricas deben ser **medibles sin servicios externos**:

| Métrica | Cómo se mide (repo) | Objetivo |
|--------|----------------------|----------|
| **Errores críticos** | `CRITICAL` en `informe_revision.md` | 0 |
| **Enlaces internos rotos** | contador en auditoría docs | 0 |
| **Placeholders pendientes** | `PLACEHOLDER:` count | decreciente |
| **Scripts compilables** | % que pasan `py_compile` | 100% |
| **Mensajes alineados** | heurística “narrativa” (keywords) | estable |

---

## 5) Plantilla de informe (formato)

El informe automático usa esta estructura:

- **Resumen ejecutivo**
- **Hallazgos críticos**
- **Hallazgos altos/medios/bajos**
- **Acciones inmediatas (máx. 5)**
- **KPIs**

---

## 6) Principios (Sabionda_Omega_2040)

- Validar la vida antes que el dato: si el material induce prácticas dañinas, **se bloquea**.
- Ahorro hídrico y soberanía: ejemplos y prácticas deben priorizar **uso responsable del agua**.
- Interoperabilidad: enlaces internos claros; scripts sin dependencias innecesarias.
- Resiliencia: si algo falla, el sistema debe explicar cómo recuperarse.

