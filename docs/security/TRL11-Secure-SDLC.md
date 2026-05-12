# Pipeline CI/CD inmutable TRL11 — SDLC seguro y verificación criptográfica

**CASTÚO-SYSTEM™** — Pipeline con pre-commit de integridad, GitHub Actions TRL11, cifrado E2E v1.1 (AES-256-GCM + Shamir 3/5), volúmenes cifrados, STRIDE continuo y despliegue zero-downtime.

---

## 1. Evolución versionada (TRL9 → TRL11)

| Versión   | TRL  | Contenido |
|-----------|------|-----------|
| v1.0.0    | TRL9 | BookStack baseline + firmas |
| v1.1.0    | TRL10| Swiss Vault, Quantum, Federated Learning |
| v1.2.0    | TRL11| Secure SDLC, CI/CD, AES-256-GCM, STRIDE |

---

## 2. Pre-commit (100% inmutable)

Instalación del hook:

```bash
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

En cada commit:

1. Se ejecuta `docker/castuo-bookstack/verify-integrity.sh`.
2. Si falla → **TRL10 violado**, commit rechazado.
3. Se ejecuta `sign-all.sh` y se añaden `*.sig` al commit.

---

## 3. CI/CD (GitHub Actions)

- **Workflow:** `.github/workflows/castuo-trl11.yml`
- **Eventos:** `push` y `pull_request` en `main` y `develop`.

Pasos:

1. **Verify TRL10** en `docker/castuo-bookstack` (verify-integrity.sh).
2. **Sign (CI):** opcional con secreto `CASTUO_PRIVATE_KEY`.
3. **Build:** imagen `castuo/bookstack:trl11.${GITHUB_SHA::8}` (buildx, sin provenance/sbom si se desea imagen mínima).
4. **Cosign:** opcional si `COSIGN_PRIVATE_KEY` está configurado y `COSIGN_SIGN=true`.

Secrets útiles: `CASTUO_PRIVATE_KEY`, `COSIGN_PRIVATE_KEY`, `COSIGN_PASSWORD`, y los de registro si se hace push a un registry.

---

## 4. Cifrado E2E v1.1 (AES-256-GCM + Shamir 3/5)

- **Script:** `scripts/crypto/castuo_crypto_v1.1.py`
- **Shards:** hsm, swiss, gaia, rpi, quantum (5 total, 3 requeridos para recuperar clave).
- **Uso:** recuperar clave desde 3 shards o con password; `encrypt_data` / `decrypt_data` con AES-256-GCM.

Ejemplo con password (sin shards):

```bash
python3 scripts/crypto/castuo_crypto_v1.1.py
```

Crear shards desde password (para distribuir a cada ubicación), ejecutando el módulo desde la raíz del repo:

```python
import sys, importlib.util
spec = importlib.util.spec_from_file_location("castuo_crypto_v11", "scripts/crypto/castuo_crypto_v1.1.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
salt, shards = mod.create_shards_from_password("secret")
# shards['hsm'], shards['swiss'], ...
```

---

## 5. Data at rest — volúmenes inmutables

- **Compose:** `docker/castuo-bookstack/docker-compose-trl11.yml`
- Volumen `castuo_data` sobre dispositivo cifrado (ej. `/dev/mapper/castuo-crypt` con LUKS).
- En producción, crear el mapper LUKS y luego usar este compose como extensión.

---

## 6. STRIDE — threat modeling continuo

- **Script:** `scripts/security/stride_pipeline.py`
- **Uso:** `python3 scripts/security/stride_pipeline.py v1.2.0`

Comprueba:

| Categoría        | Check |
|------------------|--------|
| Spoofing         | Auth con sharding (YubiKey/HSM/Shamir) |
| Tampering        | verify-integrity.sh en BookStack |
| Repudiation      | GaiaChain configurado para auditoría |
| Info Disclosure  | Cifrado E2E (castuo_crypto_v1.1) |
| DoS              | Healthchecks en docker-compose |
| Elevation        | cap_drop / no-new-privileges |

El resultado se envía a GaiaChain como testigo (`/api/v1/stride_witness`) si `GAIA_CHAIN_ADMIN_KEY` está definido.

---

## 7. Despliegue zero-downtime (TRL11 prod)

- **Compose:** `docker/castuo-bookstack/docker-compose-trl11.prod.yml`
- Servicio `castuo-v1.2`, imagen con digest: `castuo/bookstack:trl11.${GIT_SHA}@${IMAGE_DIGEST}`.
- `deploy.replicas: 3`, `update_config.order: start-first`, `rollback_config` definido.

Variables: `GIT_SHA`, `IMAGE_DIGEST`.

---

## 8. Verificación ejecutiva TRL11

| Elemento        | Estado |
|----------------|--------|
| v1.2.0 LIVE    | https://89.167.5.233:8080 (o `CASTUO_VERIFY_URL`) |
| CI/CD          | GitHub Actions pipeline TRL11 |
| Crypto         | AES-256-GCM + Shamir 3/5 (castuo_crypto_v1.1) |
| Threat Model   | STRIDE v1.2.0 audited (stride_pipeline.py) |
| Uptime         | Rolling upgrades (start-first, replicas) |
| GaiaChain      | Transacciones firmadas (fragmentos, STRIDE, alertas) |

---

## 9. Ejecutar evolución (~15 min)

```bash
# 1. Baseline seguro
git checkout v1.1.0
cd docker/castuo-bookstack && ./verify-integrity.sh && cd ../..

# 2. Merge TRL11
git merge v1.2.0 --no-ff
cd docker/castuo-bookstack && ./sign-all.sh && ./verify-integrity.sh && cd ../..

# 3. CI/CD (push dispara el pipeline)
git push origin main

# 4. Verificación LIVE
curl -f https://89.167.5.233:8080
python3 scripts/security/stride_pipeline.py v1.2.0
```

O usando el script de upgrade:

```bash
./scripts/deploy/trl11-upgrade.sh
```

---

**Referencias:** [Sistema-Seguridad-Extrema.md](Sistema-Seguridad-Extrema.md) | [Full-Implementation-Guide.md](Full-Implementation-Guide.md) | [Anti-Tampering-Strategy.md](Anti-Tampering-Strategy.md)
