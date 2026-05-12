# Rutas KV v2 (HashiCorp Vault) — Castúo producción

**Montaje por defecto:** `secret` (motor KV v2). Path lógico = filas sin prefijo `secret/data/`.

**Matriz despliegue (estado del sistema — trazabilidad):** misma convención que `docs/deploy/robotics-lab-hetzner.env.example`. Prontuario consolidado: [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../../docs/legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md).

| Opción | Uso | Variables / rutas |
|--------|-----|-------------------|
| **A** | Producción recomendada | `CASTUO_*_FILE` → `/run/secrets/<nombre_secret>`; `read_secret` en `backend/auth_roles.py` |
| **B** | Alternativa enterprise | `VAULT_ADDR` + `VAULT_TOKEN_FILE` (o `VAULT_TOKEN` efímero); KV v2 según tabla inferior; `backend/security/vault.py` |
| **C** | **No** producción | `CASTUO_*` en texto dentro de `.env` versionado — solo dev local comentado; riesgo de fuga en git |

| Path KV (`path` en API) | Campo típico | Variable de entorno equivalente | Variable `*_FILE` (Docker) |
|-------------------------|--------------|----------------------------------|---------------------------|
| `castuo/admin_general/bearer` | `value` | `CASTUO_ADMIN_GENERAL_BEARER` | `CASTUO_ADMIN_GENERAL_BEARER_FILE` |
| `castuo/robotics/lab/bearer` | `value` | `CASTUO_ROBOTICS_LAB_BEARER_TOKEN` | `CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE` |
| `castuo/gaia/chain/private_key` | `value` | `GAIA_CHAIN_PRIVATE_KEY` | `GAIA_CHAIN_PRIVATE_KEY_FILE` |
| `castuo/admin/master_key` | `value` | `ADMIN_MASTER_KEY` | `ADMIN_MASTER_KEY_FILE` |

## CLI (ejemplos — **no** pegues valores reales en tickets)

```bash
# Sustituir <...> por el secreto real (fuera de git)
vault kv put secret/castuo/admin_general/bearer value="<token-largo-unico>"
vault kv put secret/castuo/robotics/lab/bearer value="<token-lab>"
vault kv put secret/castuo/gaia/chain/private_key value="<0x...>"
vault kv put secret/castuo/admin/master_key value="<master-bytes-o-passphrase-según-política>"
```

## Docker / Compose

1. Crear archivos solo en máquina de despliegue: `echo -n '<secret>' > ./secrets/admin_general.bearer`
2. `docker secret create castuo_admin_general_bearer ./secrets/admin_general.bearer`
3. En `.env`: `CASTUO_ADMIN_GENERAL_BEARER_FILE=/run/secrets/castuo_admin_general_bearer` (ruta real del servicio)

`auth_roles.read_secret("CASTUO_ADMIN_GENERAL_BEARER")` ya prioriza `CASTUO_ADMIN_GENERAL_BEARER_FILE` si apunta a un fichero legible.

## Código opcional (`hvac`)

`backend/security/vault.py` expone `read_kv_v2`, `read_admin_general_bearer()`, `vault_token_for_client()`, etc. Requiere `VAULT_ADDR`, token vía `VAULT_TOKEN` **o** `VAULT_TOKEN_FILE`, y `pip install hvac`. Si falta algo, la cadena vacía indica usar env/`read_secret`.
