# Coherencia del sistema y custodia — Administrador general (2026)

**Rol:** `admin_general` (RBAC en `backend/models/permissions.py`; Bearer en `CASTUO_ADMIN_GENERAL_BEARER` vía `backend/auth_roles.py`).

**Fuente canónica en código (sin secretos):** `backend/models/system_admin_playbook.py` → `get_admin_general_playbook()`.

**Prontuario secrets/Vault (matriz A/B/C):** [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](./PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md)

---

## 1. Qué queda “almacenado” para el administrador general

| Artefacto | Ubicación | Contenido |
|-----------|-----------|-----------|
| Playbook agregado | `system_admin_playbook.py` | Capas de cifrado, rutas doc, nombres de env críticos |
| Permisos RBAC | `permissions.py` → `admin_general` | governance, security, system, compliance, keys (read), + núcleo admin |
| Rutas HTTP CTAEX | `auth_roles.py` | `admin_general` → prefijo `*` (misma amplitud que `admin`) |
| Clave maestra | `security/admin_master_layer.py` | Cifrado bajo custodia del admin (fuera del playbook) |

---

## 2. Refuerzo de seguridad y cifrado (lectura operativa)

1. **Capa 0:** `ADMIN_MASTER_KEY` / secret Docker / `security/.admin_master_key` — ver [ENCRYPTION_9_CAPAS_V1.7.1.md](../security/ENCRYPTION_9_CAPAS_V1.7.1.md).  
2. **PQC:** `backend/security/pq_crypto.py` — instalar `pqcrypto` en prod si se exige Kyber/Dilithium reales.  
3. **Lab robotics:** tokens y claves simétricas solo por env/Vault; nunca en commits.  
4. **GaiaChain:** `GAIA_CHAIN_PRIVATE_KEY` en HSM/Vault; opt-in lab con `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER`.

---

## 3. Coherencia legal ↔ técnica

- [PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md](./PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md)  
- [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) §6  
- [PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md](./PRONTUARIO-MAESTRO-ENCRIPTACION-ROLES-V2.5.md)

El administrador general **no** recibe veredicto legal automático en el repo: valida despliegue con DPO y asesoramiento.

---

## 4. Uso programático

```python
from backend.models.system_admin_playbook import get_admin_general_playbook

payload = get_admin_general_playbook()  # deepcopy; sin secretos
```

## 5. HTTP (robotics lab stub)

Con `CASTUO_ADMIN_GENERAL_BEARER` definido en el **mismo proceso** que `lab_stub_app`:

```bash
curl -sS -H "Authorization: Bearer $CASTUO_ADMIN_GENERAL_BEARER" \
  http://127.0.0.1:8011/admin_general/playbook
```

Vault: [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md) · cliente opcional [vault.py](../../backend/security/vault.py) (`hvac` + `VAULT_ADDR` + token vía `VAULT_TOKEN` o `VAULT_TOKEN_FILE`).

### 5.1 Estado del sistema — trazabilidad secretos (A / B / C)

| Opción | Rol en custodia | Evidencia en repo |
|--------|-----------------|-------------------|
| **A — Docker Secrets** | Recomendado producción: `*_FILE` → `/run/secrets/…` | `robotics-lab-hetzner.env.example`, `auth_roles.read_secret` |
| **B — Vault KV v2** | Alternativo: lectura KV antes de materializar ficheros o sidecar | `VAULT_KV_PATHS.md`, `vault.py`, `VAULT_TOKEN_FILE` |
| **C — env plano** | **No** producción; solo dev local comentado | Prohibido subir `.env` con `CASTUO_ADMIN_GENERAL_BEARER=…` |

**Despliegue resumido**

1. **B:** `vault kv put secret/castuo/admin_general/bearer value="<token>"` (y análogos para lab / Gaia / master); proceso con `hvac` o export a fichero montado.  
2. **A:** `docker secret create castuo_admin_general_bearer …` + `docker secret create robotics_lab_bearer …` + `CASTUO_ADMIN_GENERAL_BEARER_FILE` / `CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE` como en el ejemplo de despliegue.  
3. `cp docs/deploy/robotics-lab-hetzner.env.example .env.hetzner` y ajustar rutas (sin Opción C en servidores compartidos).

`read_secret("CASTUO_ADMIN_GENERAL_BEARER")` usa la variable **`CASTUO_ADMIN_GENERAL_BEARER_FILE`** (ruta al fichero), no un literal `read_secret("…_FILE")`.

---

*El agua del territorio no se cifra en markdown; el playbook ordena quién puede abrir la compuerta.*
