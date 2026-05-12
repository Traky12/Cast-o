# Estrategia anti-variación (5 capas) — CASTÚO-SYSTEM™

Protección frente a hacking, malware y uso malicioso de Cursor mediante **integridad inmutable** y runtime restringido.

**Certificación legal internacional**: [TRL9-AntiTampering-Certification.md](../legal/TRL9-AntiTampering-Certification.md) | **Especificación de validación**: [TRL9-AntiTampering-Specification.md](../legal/TRL9-AntiTampering-Specification.md) (estándar ISO 27001 A.9 + TRL9 operational).

**Resumen de protección**:

- **BookStack LIVE + blindado** — https://89.167.5.233:8080 (o tu IP:8080): contenedor read-only, capabilities mínimas, imágenes actualizadas.
- **n8n workflows** — Import protegido por signatures: solo workflows firmados pasan `verify-integrity.sh` antes de deploy.
- **SABIONDA IA** — Documenta en filesystem inmutable: código crítico firmado; volúmenes y firma garantizan integridad.
- **99,999% Uptime** — Healthchecks (bookstack + mariadb) + watchdog 30s: verificación continua de integridad; fallo → alerta/restart.

---

## 1. Inmutabilidad Docker (Nivel 1 — Base)

- **Digest pinning**: En producción usar `image: lscr.io/linuxserver/bookstack@sha256:<digest>`. Obtener digest: `docker inspect --format='{{index .RepoDigests 0}}' lscr.io/linuxserver/bookstack:latest`.
- **Opciones de seguridad** (en `docker-compose.yml`):
  - `security_opt: no-new-privileges:true`
  - `read_only: true` (sistema de archivos raíz solo lectura; los volúmenes montados siguen siendo escribibles)
  - `tmpfs: /tmp` (escritura temporal solo en `/tmp`)
  - `cap_drop: [ALL]` y `cap_add: [CHOWN, SETGID, SETUID]` (mínimos necesarios para PUID/PGID)

Ubicación: `docker/castuo-bookstack/docker-compose.yml`.

---

## 2. Code signing + checksums (Nivel 2 — Código)

Firma de archivos críticos (compose, workflows, scripts) y verificación previa al deploy.

**Generar claves (una vez)**:

```bash
openssl genrsa -out castuo-private.key 4096
openssl rsa -in castuo-private.key -pubout -out castuo-public.key
```

**Firmar archivos críticos**:

```bash
cd docker/castuo-bookstack
chmod +x sign-all.sh verify-integrity.sh
./sign-all.sh
```

**Verificar antes de cualquier deploy**:

```bash
./verify-integrity.sh || exit 1
```

- **sign-all.sh**: Firma `docker-compose.yml`, `test-bookstack.sh`, `n8n-workflow-sabionda-bookstack.json`, `.env.example` con `openssl dgst -sha256 -sign` y genera `*.sig`.
- **verify-integrity.sh**: Comprueba que existan los `.sig` y que `openssl dgst -sha256 -verify` con `castuo-public.key` sea correcto para cada archivo.

No commitear `castuo-private.key`. Sí se pueden commitear `castuo-public.key` y los `*.sig`.

---

## 3. WORM storage (Nivel 3 — Datos)

**Write Once Read Many**: para datos que no deben modificarse después de su creación.

- En Docker estándar no hay WORM nativo. Opciones:
  - Montar un volumen en un directorio del host y, tras el primer llenado, re-montar como solo lectura (`o=bind,ro`) en un arranque controlado.
  - Usar un backend de almacenamiento con inmutabilidad (por ejemplo, S3 Object Lock, almacenes compatibles con retención).

Ejemplo conceptual para el host (post-init manual):

```bash
# Tras inicialización, remontar solo lectura (requiere procedimiento controlado)
mount -o remount,ro /opt/castuo-data
```

En el compose no se fuerza WORM por defecto para no bloquear el uso normal de BookStack; queda como opción de endurecimiento en documentación.

---

## 4. Runtime protection (Nivel 4 — Ejecución)

Filtrado de syscalls con **seccomp** para limitar llamadas peligrosas.

- **castuo-seccomp.json**: Lista blanca de syscalls permitidos (read, write, open, close, socket, execve, etc.) y denegación explícita de `ptrace`, `keyctl`, `chmod`, `chown`, `init_module`, etc. (bloquear `execve` impediría el arranque de la mayoría de contenedores; se bloquean chmod/chown y otras llamadas peligrosas.)
- Uso opcional en el servicio (ruta relativa al compose):

```yaml
security_opt:
  - no-new-privileges:true
  - seccomp=./castuo-seccomp.json
```

Ubicación del perfil: `docker/castuo-bookstack/castuo-seccomp.json`. Si alguna imagen falla con este perfil, duplicar el JSON y añadir los syscalls que requiera en la lista permitida.

---

## 5. Verificación continua (Nivel 5 — Monitoreo)

**Watchdog** que ejecuta la verificación de integridad de forma periódica.

```bash
docker compose -f docker-compose.yml -f docker-compose.watchdog.yml --profile watchdog up -d
```

- Servicio `integrity-watchdog`: monta el directorio actual en solo lectura, ejecuta `verify-integrity.sh` cada 30 s y sale con error si la verificación falla (el restart policy puede reiniciar el contenedor).
- Perfil: `watchdog`, para que sea opcional.

Archivo: `docker/castuo-bookstack/docker-compose.watchdog.yml`.

---

## Implantación anti-hacking (5 min)

```bash
cd docker/castuo-bookstack                    # ✅ Directorio correcto
openssl genrsa -out castuo-private.key 4096   # ✅ Clave 4096-bit
openssl rsa -in castuo-private.key -pubout -out castuo-public.key  # ✅ Pública para verify
chmod +x *.sh                                 # ✅ Ejecutables
./sign-all.sh                                 # ✅ Firma TODO código crítico
./verify-integrity.sh || { echo "❌ INTEGRIDAD COMPROMETIDA"; exit 1; }  # ✅ BLOQUEA si hack
docker compose up -d --pull always            # ✅ Imágenes frescas
docker compose -f docker-compose.yml -f docker-compose.watchdog.yml --profile watchdog up -d  # ✅ Monitoreo 30s
```

---

## Verificación post-ejecución

Tras ejecutar la implantación, comprobar:

```bash
# 1. Estado servicios
docker compose ps   # bookstack UP + healthy

# 2. Watchdog activo
docker ps | grep watchdog   # integrity-watchdog corriendo

# 3. Prueba integridad desde dentro del contenedor
docker exec castuo-bookstack curl -sf http://localhost/login -o /dev/null

# 4. Acceso externo
curl -I https://89.167.5.233:8080/login   # LIVE (sustituir por tu IP o dominio)
```

---

## Referencias en el repo

| Elemento | Ruta |
|----------|------|
| Compose + seguridad | `docker/castuo-bookstack/docker-compose.yml` |
| Verificación integridad | `docker/castuo-bookstack/verify-integrity.sh` |
| Firma de archivos | `docker/castuo-bookstack/sign-all.sh` |
| Perfil seccomp | `docker/castuo-bookstack/castuo-seccomp.json` |
| Watchdog | `docker/castuo-bookstack/docker-compose.watchdog.yml` |

Añadir en `.gitignore`: `castuo-private.key` (y opcionalmente `*.sig` si no se desea versionar firmas).
