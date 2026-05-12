# Prontuario — refuerzo secrets / Vault (coherencia Castúo-System)

**Versión:** 2026-03-22 · **Ámbito:** trazabilidad A/B/C entre docs, `vault.py`, `auth_roles.read_secret`, despliegue lab/edge.

**Límite:** “listo para producción” aquí = **matriz y código alineados en el repositorio**. El cierre operativo (DPO, staging, TLS, backups) es **externo** al markdown. No confundir bearer opaco con JWT salvo que el despliegue use JWT real.

**Relación:** [SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md](./SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md) · [PLAN-EXCELENCIA-V2.5-REFUERZO.md](./PLAN-EXCELENCIA-V2.5-REFUERZO.md) §2.1 bis · [PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md](./PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](../deploy/PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [ROADMAP-TRL6-TRL7-CODE.md](../deploy/ROADMAP-TRL6-TRL7-CODE.md) · [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](./INFORME-EVIDENCIA-TRL6-PLANTILLA.md) · [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](./DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md) · `docs/deploy/robotics-lab-hetzner.env.example` · [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md) · [vault.py](../../backend/security/vault.py) · [auth_roles.py](../../backend/auth_roles.py)

---

## 1. Matriz secrets A / B / C (cruzada)

| Opción | Prod | Variables / rutas | Docker secret (ejemplo nombre) | Path KV v2 lógico (`read_kv_v2`) | Uso en código |
|--------|------|-------------------|-------------------------------|----------------------------------|---------------|
| **A** — recomendado | Sí | `CASTUO_*_FILE=/run/secrets/…` | `castuo_admin_general_bearer`, `robotics_lab_bearer` | N/A | `read_secret("CASTUO_ADMIN_GENERAL_BEARER")` lee env **`CASTUO_ADMIN_GENERAL_BEARER_FILE`** (ruta). **No** llamar `read_secret("…_FILE")`. Igual patrón para `CASTUO_ROBOTICS_LAB_BEARER_TOKEN`. |
| **B** — alternativo | Sí | `VAULT_ADDR` + `VAULT_TOKEN` o `VAULT_TOKEN_FILE` | Opcional (`vault_token`) | `castuo/admin_general/bearer`, `castuo/robotics/lab/bearer`, … | `vault_token_for_client()` → `_client()` → `read_kv_v2(path)` |
| **C** — prohibido prod | No | `CASTUO_ADMIN_GENERAL_BEARER=…` en `.env` versionado | N/A | N/A | Solo dev local **comentado** en ejemplo; riesgo de fuga en git |

**Aclaración crítica:** el primer argumento de `read_secret` es el **nombre lógico** del secreto (`CASTUO_ADMIN_GENERAL_BEARER`), no el sufijo `_FILE`. El código resuelve `CASTUO_ADMIN_GENERAL_BEARER_FILE` automáticamente.

---

## 2. Tabla secret → Docker (A) vs Vault (B)

| Custodia | Opción A (fichero montado) | Opción B (`vault kv put` — mount `secret`) |
|----------|----------------------------|---------------------------------------------|
| Admin general | Secret Swarm/file → `/run/secrets/castuo_admin_general_bearer` | `vault kv put secret/castuo/admin_general/bearer value="<token-opaco>"` |
| Robotics lab | `/run/secrets/robotics_lab_bearer` | `vault kv put secret/castuo/robotics/lab/bearer value="<token-opaco>"` |
| Gaia clave (si aplica) | `…/castuo_gaia_private_key` | `vault kv put secret/castuo/gaia/chain/private_key value="<clave-según-política>"` |
| Master admin | `…/castuo_admin_master_key` | `vault kv put secret/castuo/admin/master_key value="<según-política>"` |

Los paths lógicos sin prefijo `secret/data/` coinciden con [VAULT_KV_PATHS.md](../../backend/security/VAULT_KV_PATHS.md).

---

## 3. Implementación `vault_token_for_client()` (referencia)

Prioridad: **`VAULT_TOKEN`** (env) → **`VAULT_TOKEN_FILE`** (lectura directa del fichero con `open`, no `read_secret(path)`). Si falta token o `VAULT_ADDR`, `read_kv_v2` devuelve `""` y el flujo productivo debe seguir en `*_FILE` / env según política.

---

## 4. `docker-compose.scan3d.yml`

La cabecera del fichero documenta A / B / no C. El servicio actual expone **8012→80** y usa por defecto variable de entorno para el bearer del lab; para **Opción A** en Compose con ficheros locales, definir en `.env` las rutas `*_FILE` **y** montar `/run/secrets` (Swarm) o usar `secrets:` con `file:` (Compose) en el host de despliegue — **no** se incluyen rutas `file:` en el repo para no romper clones sin `./secrets/`.

Ejemplo **orientativo** (solo en servidor, rutas ajustadas):

```yaml
# secrets:
#   castuo_admin_general_bearer:
#     file: ./secrets/admin_general.bearer
#   robotics_lab_bearer:
#     file: ./secrets/robotics_lab.bearer
# services:
#   robotics-lab-scan3d:
#     secrets:
#       - castuo_admin_general_bearer
#       - robotics_lab_bearer
#     environment:
#       CASTUO_ADMIN_GENERAL_BEARER_FILE: /run/secrets/castuo_admin_general_bearer
#       CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE: /run/secrets/robotics_lab_bearer
```

En **Docker Swarm**, `docker secret create <nombre>` debe coincidir con el basename bajo `/run/secrets/<nombre>`.

---

## 5. Tests (nombres reales en el clon)

| Módulo | Función | Qué valida |
|--------|---------|------------|
| `tests/security/test_vault_optional.py` | `test_read_kv_without_vault_returns_empty` | Sin Vault → `read_kv_v2` → `""` |
| mismo | `test_vault_token_for_client_prefers_env_over_file` | `VAULT_TOKEN` gana sobre fichero |
| mismo | `test_vault_token_for_client_reads_file_when_env_empty` | Token desde `VAULT_TOKEN_FILE` |
| mismo | `test_vault_constants_paths` | Paths KV alineados con doc |
| `tests/models/test_system_admin_playbook.py` | `test_playbook_has_no_secrets` | Playbook sin material sensible |
| mismo | `test_check_permission_admin_general_governance` | RBAC `admin_general` |

Integración HTTP playbook: `tests/integrations/test_lab_admin_playbook_http.py` (ruta `/admin_general/playbook` en app lab).

Ejecutar: `pytest tests/security/test_vault_optional.py tests/models/test_system_admin_playbook.py tests/integrations/test_lab_admin_playbook_http.py -q`

---

## 6. Despliegue — comandos alineados (bash)

**Opción A (Swarm / secret create):**

```bash
docker secret create castuo_admin_general_bearer ./secrets/admin_general.bearer
docker secret create robotics_lab_bearer ./secrets/robotics_lab.bearer
# Servicio debe montar secrets y fijar *_FILE como en robotics-lab-hetzner.env.example
```

**Opción B (Vault CLI — mount por defecto `secret`):**

```bash
vault kv put secret/castuo/admin_general/bearer value="$(openssl rand -base64 48)"
# Token del agente en VAULT_TOKEN_FILE, no en git
```

**Puertos:** lab en compose scan3d suele ser **8012** (mapeo a 80 del contenedor); uvicorn local del stub **8011**. Ajustar `curl` al puerto que esté levantado.

---

## 7. TRL6 — edge + pruebas (enlace)

Despliegue relevante (VPS/Hetzner), criterios `chain_status` / `chain_registration` alineados al código y paquete pytest + PowerShell: [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md). Solicitud DPO §6: [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](./DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md).

---

## 8. Checklist inmediato (PowerShell — no subir `secrets/` al git)

1. Crear directorio `secrets/` en `.gitignore` si aplica; nunca commitear contenido.  
2. Copiar `docs/deploy/robotics-lab-hetzner.env.example` → `.env` local **fuera** del control de versiones.  
3. Elegir A o B; si migraste de `castuo_robotics_lab_bearer`, renombrar secret o actualizar `*_FILE` para que el basename coincida.  
4. DPIA robotics §6 antes de tratar parcela identificable en cadena o logs persistentes (plantilla DPO enlazada en §7).

---

## 9. Opción D — endurecimiento LLMNR / NBT-NS (red local, edge staging)

Complementa A/B: reduce la superficie donde un atacante en la misma capa 2 empuja resoluciones falsas y encadena hacia **credenciales de sesión** en estaciones Windows o servicios SMB expuestos.

| Control | Objetivo |
|---------|----------|
| `LLMNR=no` / `MulticastDNS=no` en `systemd-resolved` | Cerrar descubrimiento multicast innecesario en el host Linux del edge |
| GPO / registro Windows (*multicast name resolution*, NetBIOS) | Misma política en puestos que administran secretos o acceden a Vault |
| Evidencia | Captura o bitácora de `tcpdump` UDP 5355 en ventana de prueba; sin sustituir auditoría formal |

**Fuente unificada (Multilinker doc + playbook):** [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](../deploy/PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · `get_admin_general_playbook()["critical_hardening_checks"]` en `backend/models/system_admin_playbook.py`.

---

*El agua que no se custodia en capas A o B se evapora en la Opción C.*
