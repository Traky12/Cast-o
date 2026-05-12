# Patrón PRONT — evolución de sistemas integrados CASTÚO

Los **PRONT** (`docs/deploy/PRONT-*.md`, prefijo exacto **`PRONT-`**) son guías **cortas, imprimibles en A4**, para una **cinta de integración** concreta (RGI, SIGPAC, n8n, robotics edge, pendrive, etc.).

Los **PRONTUARIO-*** son documentos maestros largos: **no** los sustituyen; el PRONT puede enlazarlos.

---

## Cuándo crear un PRONT nuevo

- Nace un **módulo** con scripts, `docker-compose.*.example.yml`, variables y flujo de campo/laboratorio.
- Hay **riesgo operativo** (secretos, LUKS, datos personales, TRL mal explicado).
- Hace falta **trazabilidad documental** para auditorías **internas** (sin confundir con certificación regulatoria: eso es proceso + evidencia fuera del markdown).
- Necesitas **una sola hoja** que enganche diagrama, comandos reales y troubleshooting.

---

## Estructura base (checklist)

| Sección | Contenido |
|---------|-----------|
| **Metadatos** | Versión, fecha, alcance, responsable (en copia interna). |
| **Patrón** | Enlace a este archivo. |
| **Aviso legal / TRL** | Qué **no** garantiza el repo (regulador, TRL industrial). |
| **Diagrama Mermaid** | Solo nodos existentes o roadmap explícito en el repo. |
| **Componentes** | Tabla con **rutas reales** (`scripts/…`, `backend/…`, `deploy/…`). |
| **Flujo operativo** | Pasos numerados; comandos verificados. |
| **TRL y normativa** | **Objetivo + evidencia**; sin ISO/RD como hecho sin informe. |
| **Seguridad** | `auth_roles`, `*_FILE`, LUKS, DPIA/ethics si aplica. |
| **Cronograma** | Plantilla editable. |
| **Troubleshooting** | NTFS vs LUKS, BOM, permisos, red, dependencias opcionales. |
| **Anexos** | Comandos, árbol de directorios, contactos en blanco (repo público). |

Referencia completa: `PRONT-CASTUO-RGI-v2-2026.md`. Plantilla vacía: `docs/deploy/_templates/PRONT-SKELETON.md`.

---

## Cableado fijo en el repositorio

### 1. README del módulo

```markdown
## Documentación imprimible (A4)
- [PRONT-CASTUO-…](docs/deploy/PRONT-CASTUO-….md)
- Patrón: [PRONT-PATRON-SISTEMAS-INTEGRADOS.md](docs/deploy/PRONT-PATRON-SISTEMAS-INTEGRADOS.md)
```

### 2. Copia al pendrive (Windows)

`Prepare-CastuoPendrive.ps1` copia **todos** los `docs/deploy/PRONT-*.md` (no afecta a `PRONTUARIO-*`) y, si existe, `docs/deploy/TRL-MASTER.md`.

### 3. Árbol USB

Actualizar `deploy/PENDRIVE-CONTENIDO.md` cuando un PRONT sea crítico en campo (el script ya copia el glob completo).

### 4. Producción

**No** fusionar `docker-compose.*.example.yml` en `docker-compose.prod.yml` sin revisión explícita.

---

## TRL y normativa: cómo tratarlos

- **TRL:** siempre como *estado + evidencia* (lab / integración / industrial). Tabla de seguimiento: `docs/deploy/TRL-MASTER.md`.
- **Normativa (GDPR, AEMPS, AI Act, etc.):** puedes listar **requisitos a revisar con asesoría**; no afirmar “cumple” o “TRL-9 garantizado” desde el código o un markdown sin dictamen.

Ejemplo de fila (plantilla):

| Área | Estado en repo | Objetivo | Evidencia |
|------|----------------|----------|-----------|
| Compresión NF | Plantilla + datos sintéticos | Validar con N muestras reales | Informe error reconstrucción + versión modelo |

---

## Qué **no** incluye un PRONT

- Certificaciones o TRL **inventados** o ligados solo a versión de librería.
- Código o APIs **no probadas** en el repo (si el script no existe, no enlazarlo).
- **PII** en copia pública (emails/teléfonos reales): usar `PRONT-INTERNO-PLANTILLA.md.example`.

---

## Evolución por fases (cualquier integración)

1. Contrato de datos (dimensión, esquema, fuente de verdad).
2. Código mínimo verificable (sin APIs inventadas).
3. Dependencias opcionales (no hinchar `backend/requirements.txt`).
4. Observabilidad (medir antes de prometer latencias en RPi).
5. Seguridad (secretos, LUKS, IAM).
6. PRONT + fila en `TRL-MASTER.md`.
7. Evidencia TRL (checklist industrial si aplica).

---

## Generar un PRONT nuevo (esqueleto)

```bash
python scripts/docs/pront_new_skeleton.py SIGPAC --version 1 --scope "Parcelas SIGPAC (completar)"
# o alias:
python scripts/generate_pront.py N8N --version 1 --subtitle "Workflows y webhooks"
```

Editar el `.md` generado: Mermaid, tablas, comandos reales. No sustituir mecánicamente el patrón por el nombre del módulo en un único archivo maestro.

---

## Ejemplo de estructura de módulo (SIGPAC, n8n, robotics)

```text
scripts/ai/<modulo>/
├── README.md
├── <contrato>.py          # loader, cliente API, etc.
└── requirements_<modulo>.txt   # opcional

docs/deploy/PRONT-CASTUO-<MODULO>-v1-<AAAA>.md
```

- **SIGPAC:** en el repo ya existen `pei-001-sigpac/` y `backend/integrations/sigpac_validator.py`; un PRONT SIGPAC debe **apuntar** a esas rutas antes de duplicar lógica.
- **n8n:** enlazar `docs/deploy/PRONTUARIO-AUTOMATIZACION-N8N-2026.md` y workflows bajo `n8n/workflows/`.
- **Robotics:** `backend/integrations/robotics/README.md` y laboratorio HTTP documentados.

---

## PRONT interno (contactos reales)

Plantilla: `docs/deploy/PRONT-INTERNO-PLANTILLA.md.example` — copiar fuera del remoto público o usar rama/copia interna si incluye PII. Incluye ejemplo de impresión con `pandoc`.

---

## Beneficios del patrón

- **Consistencia** entre módulos.
- **Escalabilidad** sin reescribir criterios TRL/legal cada vez.
- **Seguridad narrativa:** límites claros en cada guía.
- **Mantenimiento:** actualizar este patrón orienta PRONTs futuros; cada PRONT versiona por sí mismo.

---

## Índice (`PRONT-*.md` y relacionados)

| Documento | Uso |
|-----------|-----|
| `TRL-MASTER.md` | Tabla orientativa TRL / evidencia |
| `PRONT-PATRON-SISTEMAS-INTEGRADOS.md` | Este patrón |
| `PRONT-CASTUO-RGI-v2-2026.md` | RGI / NF, pendrive, edge |
| *Futuro* `PRONT-CASTUO-SIGPAC-v1-*.md` | SIGPAC / parcelas (alinear con PEI-001) |
| *Futuro* `PRONT-CASTUO-N8N-v1-*.md` | n8n campo |
| *Futuro* `PRONT-CASTUO-ROBOTICS-v1-*.md` | robotics edge |

Guía larga relacionada (no es PRONT): `PRONTUARIO-AGROTECH-TLS.md`.

*Añade filas al crear nuevos `PRONT-CASTUO-*`.*
