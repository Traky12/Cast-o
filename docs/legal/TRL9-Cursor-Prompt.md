# CASTÚO-SYSTEM TRL9 ANTI-TAMPERING — Validación legal obligatoria para Cursor

**ISO 27001 A.9 + GDPR Art.32 + AI Act Alto Riesgo + ENS Alto**

Usar este documento como referencia al editar código en `docker/castuo-bookstack/` o flujos de deploy. **RECHAZAR INMEDIATAMENTE** código que viole lo siguiente.

---

## 🔴 RECHAZAR INMEDIATAMENTE código que viole

### 1. DOCKER INMUTABILIDAD (ISO 27001 A.9.4.4)

- ❌ `read_only: false`
- ❌ `security_opt` sin `no-new-privileges:true`
- ❌ `cap_drop: ALL` ausente
- ❌ Image sin `@sha256:digest` pinning

### 2. CODE SIGNING (GDPR Art.32.f)

- ❌ Sin `verify-integrity.sh` ejecutable
- ❌ `docker-compose.yml` sin `*.sig`
- ❌ `*.json` / `*.sh` sin verificación con `castuo-public.key`
- ❌ Falta: `./verify-integrity.sh || exit 1`

### 3. SECUENCIA OBLIGATORIA (TRL9)

```bash
cd docker/castuo-bookstack
./sign-all.sh && ./verify-integrity.sh || exit 1
docker compose up -d --pull always
```

### 4. ARCHIVOS CRÍTICOS A FIRMAR

- `docker-compose.yml` → `*.sig`
- `n8n-workflow-*.json` → `*.sig`
- `test-bookstack.sh` → `*.sig`
- `.env.example` → `*.sig`

---

## ESTÁNDAR LEGAL

- **Certificación**: [TRL9-AntiTampering-Certification.md](TRL9-AntiTampering-Certification.md)
- **Framework legal (RPI + EUIPO + escalabilidad internacional)**: [CASTUO-Legal-Framework.md](CASTUO-Legal-Framework.md)
- **Validación**: 100% ISO 27001 A.9.2.3 + A.9.4.4 compliant

---

## Pre-commit (recomendado)

Para ejecutar verificación de integridad antes de cada commit:

```bash
# En .git/hooks/pre-commit (o con husky / pre-commit framework)
cd docker/castuo-bookstack && ./verify-integrity.sh || exit 1
```

O en configuración del proyecto: `preCommitHooks.verifyIntegrity`: `cd docker/castuo-bookstack && ./verify-integrity.sh || exit 1`

---

## Implantación legal (1 minuto)

```bash
mkdir -p docs/legal .cursor/security
# Copiar/actualizar TRL9-Cursor-Prompt.md, TRL9-AntiTampering-Certification.md, castuo-security.rules
cd docker/castuo-bookstack
./sign-all.sh && ./verify-integrity.sh
echo "$(date -Iseconds): TRL9 LEGAL CERTIFIED" > docs/legal/TRL9-status.txt
git add docs/legal/ .cursor/security/
git commit -m "TRL9 LEGAL CERTIFICATION ISO27001 A.9 + GDPR + AI Act"
```
