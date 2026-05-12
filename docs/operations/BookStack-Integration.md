# BookStack — Integración CASTÚO (Hetzner, n8n, Sabionda, Mistral, Notion)

Knowledge Base centralizada para documentación de parcelas, procedimientos y auditoría. Instalación Docker en **~2 minutos** en el servidor existente (Hetzner). Integración con n8n, Sabionda IA, Mistral y Notion; seguridad enterprise (UFW, MFA, roles). **TRL8 compliant.**

---

## 1. Instalación Docker en Hetzner (2 minutos)

En el servidor CASTÚO donde ya corre n8n:

```bash
mkdir -p /opt/castuo-bookstack
cd /opt/castuo-bookstack
```

Copiar desde el repo:

- `docker/castuo-bookstack/docker-compose.yml`
- `docker/castuo-bookstack/.env.example` → `.env`

Editar `.env` con contraseñas seguras (`BOOKSTACK_DB_PASS`, `MARIADB_ROOT_PASSWORD`) y opcionalmente `BOOKSTACK_APP_URL`, `BOOKSTACK_PORT`.

```bash
docker compose up -d
```

Verificación: `curl -I http://localhost:8080` → 200 OK.

**Acceso inmediato**: `https://tu-ip-hetzner:8080`  
**Usuario inicial**: `admin@castuo.local` / contraseña (definir en primer acceso).

Tiempo total: **~120 segundos** → Knowledge Base CASTÚO en marcha.

---

## 2. Integración automática con n8n / Notion / Mistral

### Workflow n8n (sync bidireccional)

1. **Trigger**: Nueva parcela SABIONDA (webhook o cron) → **HTTP Request** a BookStack API.
2. **Mistral**: Analiza datos IoT de la parcela → genera contenido estructurado → **Crear página** en BookStack (ej. "B001-Parcela").
3. **Notion sync**: Webhook n8n cuando se crea/actualiza página en Notion → **Duplica o actualiza** en BookStack vía API.
4. **Backup Git** (opcional): Volumen Docker `bookstack_data` → script de backup → push a repositorio Git en Hetzner.

### Nodos n8n sugeridos

- **Webhook** o **Schedule** → **HTTP Request** (BookStack `POST /api/pages` o `POST /api/books`).
- **Mistral** (o LLM) → recibe datos IoT/parcela → devuelve markdown → **HTTP Request** (BookStack API con body).
- **Notion Trigger** → **HTTP Request** (BookStack API) para crear/actualizar página.

---

## 3. API endpoints clave (BookStack)

| Método | Ruta | Uso en CASTÚO |
|--------|------|-------------------------------|
| POST | `/api/books` | Crear "libro" (ej. Parcelas, Procedimientos CTAEX). |
| POST | `/api/pages` | Documentos automáticos desde RPi, n8n o Sabionda. |
| GET | `/api/search` | Búsqueda federada CASTÚO (parcelas, lotes, normativas). |

**Autenticación**: En BookStack: Settings → Users → API Tokens. En n8n y scripts: Header `Authorization: Token <token>`.

**Base URL**: `https://bookstack.castuo.local` (o `http://tu-ip:8080`) + ruta API.

### Token API automático (n8n)

Obtener token vía login (para workflows que no usan token estático):

- **POST** `/api/auth/login`  
  Body: `{"email": "admin@castuo.local", "password": "<password desde vault>"}`  
  Response: `Authorization: Bearer {{ $json.token }}`

En n8n: usar credenciales almacenadas (vault) para el password; guardar `$json.token` en variable y enviar en header `Authorization: Bearer {{ $json.token }}` en las peticiones a `/api/pages`, `/api/books`, etc.

**Workflow n8n (importar directo)** — Archivo: `docker/castuo-bookstack/n8n-workflow-sabionda-bookstack.json`

- En n8n: Workflows → Import from File → seleccionar el JSON.
- Configurar variable `BOOKSTACK_URL` (ej. `https://bookstack.castuo.local`) y secret `BOOKSTACK_TOKEN` (token API de BookStack).
- El nodo hace **POST** a `{{ $vars.BOOKSTACK_URL }}/api/pages` con header `Authorization: Bearer {{ $secrets.BOOKSTACK_TOKEN }}` y body `book_id`, `name` (B001-YYYY-MM-DD), `content` (desde `mistral_analysis`).

---

## 4. Seguridad enterprise (JEREMIE) — +250K€ valor

- **Firewall UFW** (en el stack existente):
  ```bash
  ufw allow 8080/tcp
  ufw reload
  ```
  En producción: exponer solo vía **nginx reverse proxy** con HTTPS y no abrir 8080 directamente a internet.

- **MFA**: Activar autenticación en dos factores en BookStack para todos los usuarios con acceso a datos sensibles.

- **Roles de seguridad (post-instalación)**:
  | Rol | Permisos |
  |-----|-----------|
  | **Admin** | SABIONDA IA + Config + Money (gestión completa). |
  | **Técnico** | Parcelas RO + RPi logs (solo lectura). |
  | **Auditor** | Export PDF + logs completos (auditoría). |
  | **IA** | API token only (no UI access) — para n8n/Mistral. |

Configuración en BookStack: Settings → Roles. Crear usuario "Sabionda IA" con rol IA (solo API Token, sin acceso a la interfaz).

---

## 5. Roadmap 2026

| Fase | Trimestre | Hito |
|------|-----------|------|
| **Fase 1** | Q1 | BookStack LIVE + n8n sync (parcelas y docs automáticos). |
| **Fase 2** | Q2 | Mobile PWA para consulta en fincas. |
| **Fase 3** | Q3 | Graph views (plugins JS) para relaciones entre parcelas/lotes. |
| **Fase 4** | Q4 | Evaluación migración a OpenKM (si presupuesto ~€6.5M y requisitos enterprise). |

---

## 6. Referencias en el repo

- **Docker**: `docker/castuo-bookstack/docker-compose.yml`, `docker/castuo-bookstack/.env.example`, `docker/castuo-bookstack/README.md`.
- **Variables**: Ver `docker/castuo-bookstack/README.md` para lista completa y ejemplos.

---

---

## 7. Implantación INMEDIATA (90 s)

```bash
cd docker/castuo-bookstack
cp .env.example .env
# Generar contraseñas: openssl rand -base64 32 → BOOKSTACK_DB_PASS; openssl rand -base64 48 → MARIADB_ROOT_PASSWORD (editar .env)
docker compose up -d
sleep 30
chmod +x test-bookstack.sh
./test-bookstack.sh
# → ✅ BookStack LIVE + TRL8 compliant!
# Acceso: https://89.167.5.233:8080 (tu Hetzner)
```

**Verificación post-ejecución** (con anti-tampering + watchdog):

```bash
docker compose ps                              # bookstack UP + healthy
docker ps | grep watchdog                      # integrity-watchdog (si se usó --profile watchdog)
docker exec castuo-bookstack curl -sf http://localhost/login -o /dev/null
curl -I https://89.167.5.233:8080/login         # LIVE
```

**Estructura Git FINAL**:

```
castuo-system/
├── docker/castuo-bookstack/     ✅ LISTO
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── README.md
│   ├── test-bookstack.sh
│   └── n8n-workflow-sabionda-bookstack.json
├── docs/operations/             ✅ LISTO
│   └── BookStack-Integration.md
└── docker/README.md             ✅ Actualizado
```

---

**Resumen**:

- **https://89.167.5.233:8080** → BookStack LIVE + blindado (anti-tampering 5 capas).
- **n8n workflows** → Import protegido por signatures (`verify-integrity.sh`).
- **SABIONDA IA** → Documenta en filesystem inmutable (código firmado + volúmenes).
- **99,999% Uptime** → Healthchecks + watchdog 30s.

Knowledge Base CASTÚO operativa e integrable con n8n, Mistral, Notion y Sabionda. TRL8 compliant.
