# Plan de mejora inmediata — CASTÚO-System (2026)

*Acciones priorizadas alineadas al **código y prontuarios** del repo. Los fragmentos shell son **plantillas** — adaptar rutas, redes y SO; probar en **staging**. **No** uses remedición LLMNR con `sed -a` ciego sobre `resolved.conf` (duplica bloques y rompe resolución).*

**Relación:** [PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-BACKUP-PEN-DRIVE-2026.md) (pendrive cifrado) · [PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md](./PRONTUARIO-PLAN-FASES-ESTABILIZACION-20S-2026.md) · [PRONTUARIO-MAESTRO-EVALUACION-TECNICA-CASTUO-2026.md](./PRONTUARIO-MAESTRO-EVALUACION-TECNICA-CASTUO-2026.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [backend/integrations/robotics/README.md](../../backend/integrations/robotics/README.md)

---

## 1. Acciones críticas *(prioridad alta)*

### 1.1. Seguridad y estabilidad

#### Mitigar LLMNR poisoning (~1 semana)

**No ejecutar** `sed -i '/\[Resolve\]/a LLMNR=no…'` en producción sin revisión: puede **duplicar** líneas en cada pasada.

**Canónico:** editar `/etc/systemd/resolved.conf` una vez bajo `[Resolve]`:

```ini
[Resolve]
LLMNR=no
MulticastDNS=no
```

```bash
sudo systemctl restart systemd-resolved
resolvectl status
```

**Verificación** (coherente con playbook):

```bash
grep -E '^LLMNR=|^MulticastDNS=' /etc/systemd/resolved.conf || true
```

*Detalle:* [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) §2.2 · Windows: GPO / registro por interfaz.

#### Configurar backups automáticos (~2 semanas)

SQLite de resiliencia por defecto: `resilience.db` en raíz del repo *(configurable en `LocalResilienceDB`)* — **no** versionar el fichero; sí versionar el **job** de backup.

```bash
#!/usr/bin/env bash
set -euo pipefail
# Ajustar DB_PATH y destino (S3/OVH via rclone, restic, etc.)
DB_PATH="${CASTUO_SQLITE_PATH:-/var/lib/castuo/resilience.db}"
BACKUP_DIR="${CASTUO_BACKUP_DIR:-/var/backups/castuo}"
mkdir -p "$BACKUP_DIR"
DST="${BACKUP_DIR}/resilience_$(date -u +%Y%m%dT%H%M%SZ).db"
sqlite3 "$DB_PATH" ".backup ${DST}"
# Ejemplo: rclone copy "$BACKUP_DIR/" remote:castuo-backups/
```

**Criterio de aceptación:** restauración documentada en ticket (fecha + hash o tamaño).

#### Hardening básico — firewall (~1 semana)

*Ejemplo Ubuntu `ufw` — ajustar puertos a la topología real (solo bastión SSH si aplica):*

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

*Reglas cloud (SG/OVH firewall) deben coincidir; no dejar paneles expuestos.*

---

## 2. Mejoras de infraestructura *(prioridad media)*

### 2.1. Redundancia básica

**Nodo secundario + HAProxy** (~2 semanas) — *plantilla; IPs y puertos ficticios:*

```
frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    server node1 192.168.1.10:8000 check
    server node2 192.168.1.11:8000 check
```

*TLS terminación en HAProxy o en backend según diseño; versionar `haproxy.cfg` fuera del repo si contiene secretos.*

### 2.2. Monitorización básica (~2 semanas)

- Grafana: instalación depende de distro/compose; importar dashboards JSON acordados.  
- Nombres útiles para el lab: `castuo_neuro_hydro_infer_seconds` — ver [robotics README](../../backend/integrations/robotics/README.md).

```bash
# Ejemplo Debian/Ubuntu — verificar versión y repo oficial Grafana
# sudo apt install -y grafana
# sudo systemctl enable --now grafana-server
# Importar JSON desde UI o grafana-cli según documentación vigente
```

---

## 3. Mejoras de seguridad *(prioridad media)*

### 3.1. Cifrado

**Redis TLS** *(resumen — certificados en secretos):*

```bash
redis-server --tls-port 6379 --port 0 \
  --tls-cert-file /etc/redis/redis.crt \
  --tls-key-file /etc/redis/redis.key \
  --tls-ca-cert-file /etc/redis/ca.crt
```

*Guía completa:* [PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md](./PRONTUARIO-MAESTRO-INTEGRACION-CIFRADA-SOBERANA-2026.md)

### 3.2. Autenticación robusta

**YubiKey + PAM** puede **bloquear** el acceso si se malconfigura. Preferir **IdP** (Keycloak, etc.) con WebAuthn/OATH en aplicaciones; PAM solo con consola de rescate probada.

```bash
# Solo laboratorio / con acceso físico alternativo
# sudo apt install libpam-yubico
# Revisar /etc/pam.d/* con documentación del paquete — no copiar una línea suelta a common-auth sin prueba
```

---

## 4. Mejoras de integración *(prioridad baja)*

### 4.1. GaiaChain *(prueba / lab)*

**No** clonar repositorios genéricos no verificados como “oficial”. En este proyecto la vía soportada es **opt-in** vía configuración y servicios existentes:

- `backend/integrations/robotics/lab_gaiachain_optional.py`  
- `GAIA_CHAIN_*` / `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER` — ver [robotics README](../../backend/integrations/robotics/README.md) y `backend/api/services/gaiachain_service.py`.

**Criterio de aceptación:** `tx` o hash registrado en explorer/testnet documentado internamente.

### 4.2. SIGPAC

Lógica real de entrada: `backend/integrations/sigpac_validator.py` (GeoJSON). Ampliar con API regional **oficial**, no un `return True` ficticio.

```python
# Anti-patrón: no usar en producción
def validate_sigpac_stub(data) -> bool:
    return True  # ❌ sustituir por validador real o flujo manual auditado
```

---

## 5. Documentación y gobernanza

| Acción | Enlace |
|--------|--------|
| Actualizar evolución | [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) |
| Auditoría técnica y ética | [PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md](./PRONTUARIO-AUDITORIA-TECNICA-ETICA-CASTUO-2026.md) |
| Checklist ejecutable | [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) |

*Playbook admin:* `GET /admin_general/playbook` — lista `governance_doc_paths`.*

---

## 🎯 Resumen de acciones

| Prioridad | Acción | Plazo | Recursos |
|-----------|--------|-------|----------|
| Alta | Mitigar LLMNR / mDNS | ~1 semana | DevOps ~10 h |
| Alta | Backups automáticos SQLite + prueba restauración | ~2 semanas | Storage *(cotizar — ej. €50/mes)* |
| Alta | Hardening firewall / SG | ~1 semana | DevOps ~10 h |
| Media | Nodo secundario + HAProxy | ~2 semanas | Infra *(cotizar — ej. €150/mes)* |
| Media | Grafana / alertas básicas | ~2 semanas | Monitoring ~15 h |
| Media | TLS componentes críticos | ~3 semanas | Security ~30 h |
| Media | MFA / IdP *(preferido)* o PAM YubiKey *(riesgo)* | ~2 semanas | Security ~20 h |
| Baja | GaiaChain lab opt-in coherente | ~2 semanas | Blockchain ~25 h |
| Baja | SIGPAC API real o manual auditado | ~3 semanas | GIS ~30 h |

---

*Mejora inmediata sin evidencia es riego a ciegas: cada ítem cierra con ticket y captura o informe.*

🚜 *Pa'lante, campeón.* 🌱
