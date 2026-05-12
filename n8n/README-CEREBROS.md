# Cerebros digitales (Logseq + SilverBullet + Postgres) — CASTÚO

## Estrategia y ética (alineación con AGRI-BRAIN)

- **Soberanía de datos:** Telemetría y decisiones críticas pueden vivir en infraestructura que controlas (UE / on-prem), sin depender de SaaS de notas cerradas para la **memoria auditable**.
- **Interoperabilidad:** Markdown y SQL son formatos **legibles décadas después**; reducen lock-in frente a herramientas propietarias tipo Obsidian Sync / Notion.
- **Transparencia:** Stack **open source** (Logseq, SilverBullet, Postgres) auditable por terceros; la “caja negra” se reduce cuando la **política de decisión** se documenta en notas y en BD con trazas propias.
- **Tres roles (tridente):** *Operativo* (grafo / contexto), *Soberano* (documentación sensible en espacio dedicado), *Auditor* (bitácora de decisiones). **Anytype** puede cubrir el rol “soberano P2P” fuera de Docker cuando lo despliegues tú; aquí el análogo servidor es **SilverBullet soberano** + secretos en **gestor adecuado**, no en el grafo público.

Lo anterior es **diseño y gobernanza**. Valoraciones, ARR o múltiplos **no** se derivan del repo; requieren datos financieros auditados.

## Qué hay en el repo

- **`docker-compose.cerebros.yml`** — Logseq web, dos SilverBullet (soberano / auditor), Postgres 16 en `127.0.0.1:5433`.
- **`.env.cerebros.example`** — variables mínimas.
- Carpetas **`cerebros/soberano`** y **`cerebros/auditoria`** — raíz del “space” de cada SilverBullet (Markdown en disco).
- **`docker-compose.multi-n8n.yml`**: el servicio **`n8n-trillizo`** monta **`./cerebros/auditoria` → `/data/cerebros-auditoria`** para que workflows escriban el diario de operaciones **sin** depender de una API HTTP inventada.

## Aviso sobre plantillas genéricas (LLM / blogs)

Suele colarse contenido **incorrecto** para SilverBullet y Logseq:

| Afirmación frecuente | Realidad en este repo |
|----------------------|------------------------|
| Variable `SB_AUTH=admin:…` | La imagen oficial usa **`SB_USER=usuario:contraseña`**. Opcional: **`SB_AUTH_TOKEN`**. |
| `PUT http://…/api/v1/space/log-….md` | **No** usar como contrato estable sin leer la [documentación actual](https://silverbullet.md/) de tu versión. La vía soportada aquí es **escritura en disco** vía volumen compartido. |
| Logseq + volumen `./cerebros/operativo:/data` | La imagen **logseq-webapp** usa **File System Access API** en el navegador; no persiste el grafo en un volumen del contenedor como un servidor de archivos clásico. |
| Red `castuo-network` | Los compose CASTÚO usan **`castuo_multi_n8n`** o **`castuo_cerebros`** según fichero. |
| “Markdown cifrado con llave rotativa” en el disco | Sin **cifrado de volumen / LUKS / disco del proveedor**, los `.md` en disco son legibles quien tenga acceso al host. |

## Lo que no resuelve este compose

- **Anytype** — sin servicio Docker oficial en este repositorio; añádelo cuando tengas despliegue soportado.
- **Logseq remoto** — requiere **HTTPS** según la [guía oficial](https://github.com/logseq/logseq/blob/master/docs/docker-web-app-guide.md).
- **mTLS** entre servicios — no incluido; usar proxy / mesh si lo exige tu política.

## Arquitectura híbrida (realista)

| Capa | Uso |
|------|-----|
| **Postgres** (`postgres-cerebros`) | Lecturas/escrituras de alta frecuencia, SQL, informes (nodo Postgres en n8n). |
| **SilverBullet auditor** | Bitácoras y decisiones en **Markdown** legible (`./cerebros/auditoria`). |
| **SilverBullet soberano** | Documentación / PI operativa separada del auditor (`./cerebros/soberano`). |
| **Logseq web** | UI de grafo local; encaja con cultura “EU OSS” si aceptas el modelo browser-first. |

## Integración n8n → diario en Markdown (Trillizo)

1. Levanta **`docker-compose.cerebros.yml`** (SilverBullet auditor usa `./cerebros/auditoria`).
2. Levanta **`docker-compose.multi-n8n.yml`**; **`n8n-trillizo`** ya tiene el bind **`/data/cerebros-auditoria`**.
3. Importa y activa **`n8n/workflows/01-trillizo-auditoria-basica.json`** en esa instancia.

**OpEx / excelencia operativa:** importa **`n8n/workflows/03-castuo-opex-auditoria-trillizo.json`** en la instancia que emita auditorías (o la misma que el grafo grande) y enlaza un **HTTP Request** desde la salida del agente OpEx hacia `POST …/webhook/castuo/opex-audit`. Contrato y riesgos: **`docs/ops/opex-trillizo-integration.md`**.

**Webhook:** `POST /webhook/audit-trigger` — **append** a **`/data/cerebros-auditoria/journal/diario-YYYY-MM-DD.md`**. Si el fichero del día no existe, se crea con **frontmatter** y secciones “Decisiones de IA” / “Eventos del sistema” (alineado con **`n8n/templates/journal/plantilla.md`**).

**Body (resumen):**

- **`kind`:** `sistema` (por defecto) | `ia` | `analitico` — rama **sistema:** `event`, `actor`, `status`, `details`. Rama **IA:** `agente_id` o `agente`, `decision` o `output.decision`, `confianza` o `output.confianza`, `contexto` opcional, **`tags` (array de strings)** → línea **Etiquetas:** en el Markdown. Los bloques llevan **`#evento-sistema`** o **`#ia-decision`** para búsqueda en el space.

**HMAC opcional:** define `CASTUO_AUDIT_WEBHOOK_SECRET` en el contenedor n8n-trillizo. Cabecera **`X-Castuo-Signature`** = hex HMAC-SHA256 del **body JSON completo** (misma canonicalización `stableStringify` que en el nodo Code). Generador: **`scripts/n8n/sign_audit_webhook_body.py`** (pasa el JSON exacto del POST). Sin variable de entorno, el webhook sigue abierto (solo dev).

**Códigos HTTP:** 200 éxito, **401** firma inválida, **500** fallo de escritura en disco.

**Stress test (laboratorio / staging):** con Trillizo publicado (p. ej. host `127.0.0.1:5682` según `.env.n8n-multi.example`):

- Solo CPU (firma idéntica a n8n): `python scripts/tests/stress_test_313_cores.py`
- Ráfaga HTTP contra el webhook: `python scripts/tests/castuo_trillizo_audit_http_stress.py --url http://127.0.0.1:5682/webhook/audit-trigger`

Usa la **misma** `CASTUO_AUDIT_WEBHOOK_SECRET` en tu shell y en el contenedor **n8n-trillizo** si el webhook exige HMAC; si Trillizo va sin secreto, añade `--no-hmac` al script HTTP. No sustituye HA ni pruebas de failover.

**Plantilla SilverBullet:** copia **`n8n/templates/silverbullet-journal-index.md`** a `cerebros/auditoria/journal/` si quieres una página índice versionada (el `.gitignore` ignora el contenido de `auditoria/` salvo `.gitkeep`; conserva la plantilla en `n8n/templates/`).

**Backup:** **`scripts/backup_castuo_cerebros.sh`** y **`deploy/RUNBOOK-BACKUP-CEREBROS-POSTGRES.md`**.

**Libro de actas en SQL (opcional):** **`n8n/sql/schema_auditoria_trillizo.sql`** define `trillizo_audit_log` y la vista `vista_eficiencia_operativa` como registro estructurado **paralelo** al Markdown; hoy el workflow `01` no inserta filas automáticamente (hay que añadir nodo Postgres o servicio si quieres doble pista).

**Consultas en SilverBullet:** la sintaxis de “Live Query” / índices depende de la **versión** instalada; contrasta con [silverbullet.md](https://silverbullet.md/) antes de automatizar filtros por `#ia-decision`.

**Plantilla manual (si duplicas el flujo):**

```markdown
# Diario AGRI-BRAIN — …
```

Logseq **no** se alimenta solo desde esta carpeta para un grafo automático; el camino **auditable** inmediato es **SilverBullet + Markdown en `auditoria`**.

## Conexión n8n → Postgres (este stack)

- Host (desde el host): `127.0.0.1`
- Puerto: **`CEREBROS_POSTGRES_PORT`** (por defecto **5433**)
- DB / user / password: variables `CEREBROS_POSTGRES_*` en `.env.cerebros`

Desde **otro contenedor Docker**, usa `host.docker.internal:5433` o une el contenedor n8n a la red **`castuo_cerebros`** y el hostname **`postgres-cerebros`**.

## SilverBullet y API

- Autenticación de UI: **`SB_USER=user:password`**
- Token opcional: **`SB_AUTH_TOKEN`** → `Authorization: Bearer …` según documentación vigente.

## Parámetros n8n (“Actualizar cosechas…”, etc.)

Siguen mapeados en **`.env.n8n-castuo.example`** / **`.env.n8n-multi.example`**; el Trillizo **no** sustituye completar Data Tables en la UI.

## Arranque

```bash
cp .env.cerebros.example .env.cerebros
docker compose -f docker-compose.cerebros.yml --env-file .env.cerebros up -d
```

URLs locales por defecto (solo loopback):

- Logseq: `http://127.0.0.1:3001`
- SilverBullet soberano: `http://127.0.0.1:3002`
- SilverBullet auditor: `http://127.0.0.1:3003`
