# CASTÚO-SYSTEM Anti-Tampering TRL9 — Especificación legal de código inmutable

**VALIDAR TODO código contra esta especificación LEGAL antes de procesar.**

Estándar: **ISO 27001 A.9 + TRL9 operational**. Referencia: [TRL9-AntiTampering-Certification.md](TRL9-AntiTampering-Certification.md).

---

## 1. DOCKER IMMUTABILITY (Nivel 1)

Todo `docker-compose.yml` que despliegue servicios CASTÚO (BookStack, n8n, backend) debe cumplir:

- `security_opt: no-new-privileges:true`
- `read_only: true` (con `tmpfs` donde se requiera escritura temporal)
- `cap_drop: [ALL]`
- `cap_add: [CHOWN, SETGID, SETUID]` (mínimos necesarios)
- **Image DIGEST pinning**: `image: <registry>/<image>@sha256:<digest>`

---

## 2. CODE SIGNING (Nivel 2)

- **verify-integrity.sh** → Verificación SHA256 con `castuo-public.key`; debe existir y ejecutarse antes de deploy.
- **sign-all.sh** → Firma con `castuo-private.key` (archivo en `.gitignore`, no versionado).
- **En caso de fallo** → Mensaje `"❌ INTEGRIDAD COMPROMETIDA"` y `exit 1`; el deploy debe bloquearse.

---

## 3. ARCHIVOS A VERIFICAR SIEMPRE

Los siguientes archivos deben tener firma `.sig` válida antes de aceptar cambios o desplegar:

- `docker-compose.yml`
- `*.json` (incl. `n8n-workflow-*.json`)
- `*.sh` (incl. `test-bookstack.sh`, `verify-integrity.sh`, `sign-all.sh`)
- `.env.example`

Es decir: `docker-compose.yml`, `*.json`, `*.sh`, `.env.example` → deben tener `*.sig` verificable con `castuo-public.key`.

---

## 4. SECUENCIA OBLIGATORIA (5 min)

Antes de cualquier deploy a producción:

```bash
./sign-all.sh && ./verify-integrity.sh || exit 1
docker compose up -d --pull always
```

No se debe ejecutar `docker compose up` sin haber pasado `verify-integrity.sh` correctamente.

---

## RECHAZAR cualquier código que

- No incluya o invalide **verify-integrity.sh**.
- Modifique **docker-compose.yml** sin actualizar y verificar la firma (`.sig`).
- Quite **read_only** o **no-new-privileges** de los servicios.
- No utilice verificación con **castuo-public.key** en el flujo de integridad.

---

**Documento legal internacional**: [TRL9-AntiTampering-Certification.md](TRL9-AntiTampering-Certification.md)
