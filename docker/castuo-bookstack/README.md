# BookStack CASTÚO — Knowledge Base (Hetzner + n8n + Sabionda + Mistral + Notion)

Instalación en **~2 minutos** en el servidor CASTÚO existente (donde ya corre n8n). Máxima seguridad (UFW, MFA, roles). TRL8 compliant.

**Estado con anti-tampering**:

| Objetivo | Estado |
|----------|--------|
| **https://89.167.5.233:8080** | BookStack LIVE + blindado (read-only, caps, signatures) |
| **n8n workflows** | Import protegido por signatures (verify-integrity.sh) |
| **SABIONDA IA** | Documenta en filesystem inmutable (volúmenes + firma código) |
| **99,999% Uptime** | Healthchecks + watchdog 30s (verificación continua) |

---

## Instalación rápida (Hetzner)

```bash
# En el servidor CASTÚO (donde ya tienes n8n)
mkdir -p /opt/castuo-bookstack
cd /opt/castuo-bookstack

# Copiar docker-compose.yml y .env.example desde el repo
# cp docker/castuo-bookstack/docker-compose.yml .
# cp docker/castuo-bookstack/.env.example .env
# Editar .env con contraseñas seguras

docker compose up -d
```

**Comprobar**: `curl -I http://localhost:8080` → Knowledge Base CASTÚO en marcha.

**Acceso inicial**: https://tu-ip-hetzner:8080 — Usuario: `admin@castuo.local` / Contraseña: la que definas en el primer acceso (cambiar desde el panel).

---

## Variables de entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `BOOKSTACK_APP_URL` | URL pública de BookStack | `https://bookstack.castuo.local` |
| `BOOKSTACK_PORT` | Puerto en el host | `8080` |
| `BOOKSTACK_DB_PASS` | Contraseña usuario BD BookStack | (generar fuerte) |
| `MARIADB_ROOT_PASSWORD` | Contraseña root MariaDB | (generar fuerte) |

Usar `.env` (no versionado) con valores reales. Ver `.env.example`.

### Generar contraseñas automáticas (seguridad enterprise)

```bash
# Añadir a .env (no commitear)
openssl rand -base64 32   # → BOOKSTACK_DB_PASS=xxx
openssl rand -base64 48   # → MARIADB_ROOT_PASSWORD=xxx
```

### Verificación post-deploy

```bash
chmod +x test-bookstack.sh
./test-bookstack.sh
# ✅ BookStack LIVE + TRL8 compliant!
```

---

## Integración con n8n / Notion / Mistral

- **Trigger**: Nueva parcela SABIONDA → HTTP Request a BookStack API.
- **Mistral**: Analiza datos IoT → genera página tipo "B001-Parcela" en BookStack.
- **Notion**: Sincronización bidireccional vía webhook (n8n): duplica contenido en BookStack.
- **Backup**: Volumen Docker → script de backup a repositorio Git en Hetzner (opcional).

Documentación detallada: [docs/operations/BookStack-Integration.md](../../docs/operations/BookStack-Integration.md).

---

## API endpoints clave (BookStack)

| Método | Ruta | Uso |
|--------|------|-----|
| POST | `/api/books` | Crear "libro" (ej. parcelas) |
| POST | `/api/pages` | Documentos automáticos desde RPi / n8n |
| GET | `/api/search` | Búsqueda federada CASTÚO |

Autenticación: Token API en BookStack (Settings → Users → API Tokens). En n8n usar Header `Authorization: Token <token>`.

---

## Seguridad (JEREMIE / enterprise)

- **Firewall**: `ufw allow 8080/tcp && ufw reload` (o el puerto configurado).
- **MFA**: Activar 2FA en BookStack para usuarios con acceso sensible.
- **Roles**:
  - **Admin**: SABIONDA IA + Config + Money.
- **Técnico**: Parcelas RO + RPi logs.
- **Auditor**: Export PDF + logs completos.
- **IA**: API token only (no UI access).
- Exponer solo por HTTPS (nginx reverse proxy) y no dejar 8080 abierto a internet sin restricciones.

---

## Roadmap 2026

| Fase | Trimestre | Hito |
|------|-----------|------|
| Fase 1 | Q1 | BookStack LIVE + n8n sync |
| Fase 2 | Q2 | Mobile PWA para fincas |
| Fase 3 | Q3 | Graph views (plugins JS) |
| Fase 4 | Q4 | €6.5M → evaluación OpenKM migración |

---

## Anti-tampering (5 capas)

Protección frente a hacking/malware/Cursor malicioso: integridad inmutable y runtime restringido.

1. **Docker**: read-only rootfs, tmpfs /tmp, no-new-privileges, cap_drop ALL, digest pinning (prod).
2. **Code signing**: `./sign-all.sh` firma archivos críticos; `./verify-integrity.sh` verifica antes de deploy.
3. **WORM**: ver documentación para volúmenes inmutables (opcional).
4. **Runtime**: perfil seccomp `castuo-seccomp.json` (bloqueo de syscalls peligrosos).
5. **Watchdog**: `docker compose -f docker-compose.yml -f docker-compose.watchdog.yml --profile watchdog up -d` ejecuta verificación cada 30 s.

Implantación rápida:

```bash
cd docker/castuo-bookstack
openssl genrsa -out castuo-private.key 4096
openssl rsa -in castuo-private.key -pubout -out castuo-public.key
chmod +x *.sh
./sign-all.sh
./verify-integrity.sh || { echo "❌ INTEGRIDAD COMPROMETIDA"; exit 1; }
docker compose up -d --pull always
docker compose -f docker-compose.yml -f docker-compose.watchdog.yml --profile watchdog up -d
```

**Verificación post-ejecución**:

```bash
docker compose ps                              # bookstack UP + healthy
docker ps | grep watchdog                      # integrity-watchdog corriendo
docker exec castuo-bookstack curl -sf localhost/login -o /dev/null
curl -I https://89.167.5.233:8080/login         # LIVE (tu IP/dominio)
```

Ver [Anti-Tampering-Strategy.md](../../docs/security/Anti-Tampering-Strategy.md).

---

## Referencias

- [BookStack API](https://www.bookstackapp.com/docs/api/)
- [BookStack-Integration.md](../../docs/operations/BookStack-Integration.md) — Integración n8n, Notion, Mistral, seguridad y roles.
- [Anti-Tampering-Strategy.md](../../docs/security/Anti-Tampering-Strategy.md) — Estrategia anti-variación 5 capas.
