# Prontuario maestro — seguridad y Multilinker (2026)

*Gestión integrada de **seguridad** y **eficiencia** para CASTÚO-System (red, secretos, observabilidad, gobernanza).*

**Versión:** 2026-03-16 · **Ámbito:** hosts edge (p. ej. Hetzner), LAN mixta con Windows, alineación con Vault A/B y `system_admin_playbook`.

**Límite honesto:** no hay paquete PyPI `multilinker` en este repo. **Multilinker** = capa operativa que **enlaza** checklist TRL6, hardening, métricas y trazabilidad; la implementación canónica de checks en código es `CRITICAL_HARDENING_CHECKS` en `backend/models/system_admin_playbook.py`.

**Relación:** [PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md](./PRONTUARIO-MAESTRO-REFUERZO-SEGURIDAD-AVANZADA-2026.md) · [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) §9 · [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) · [PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) · [ROADMAP-MEJORAS-P1-P5-2026.md](./ROADMAP-MEJORAS-P1-P5-2026.md) · [GNU_RADIO.md](../../backend/integrations/robotics/GNU_RADIO.md) · [pq_crypto.py](../../backend/security/pq_crypto.py)

---

## 1. Diagnóstico de vulnerabilidades

*Análisis técnico de riesgos y papel del Multilinker.*

| Vulnerabilidad / brecha | Impacto | Estado | Mitigación |
|-------------------------|---------|--------|------------|
| **LLMNR poisoning** (y vecinos mDNS/NBT-NS) | Relay / credenciales en LAN; riesgo **compuesto** si el host custodia `CASTUO_*` o Vault | Crítico si LAN hostil o mixta | §2 + §6; evidencia `tcpdump` §2.3 |
| **Integración fragmentada** (sin “Multilinker”) | Runbooks desalineados, métricas y red en silos | Pendiente / en curso | §3: un solo hilo doc ↔ playbook ↔ checklist |
| **Cifrado post-cuántico (Kyber-1024)** | Protección de datos en tránsito/almacén según despliegue | Parcial (depende de `pqcrypto`) | [pq_crypto.py](../../backend/security/pq_crypto.py); auditoría |
| **Monitorización** | Falta de visibilidad de latencia/incidentes | Parcial | Histogramas SNN donde existan; Grafana §4 |

---

## 2. Mitigación de LLMNR poisoning

*Hosts que custodian `CASTUO_ADMIN_GENERAL_BEARER`, Vault (`VAULT_*`) o claves de cadena no deben confiar en resolución por multicast en LAN no controlada.*

### 2.1 Mecanismo (referencia)

| Paso | Evento |
|------|--------|
| 1 | Cliente resuelve nombre corto (“impresora”); DNS no responde. |
| 2 | Cliente emite **LLMNR** (UDP **5355**) en multicast/broadcast. |
| 3 | Atacante en capa 2 responde con IP/MAC falsas. |
| 4 | Tráfico SMB/HTTP/etc. → captura de **NTLMv2** / relay según protocolo. |
| 5 | Escalada (Pass-the-Hash, movimiento lateral, acceso a secretos en el host comprometido). |

**Riesgo CASTÚO:** el bearer **no** “sale” por LLMNR; el vector es **comprometer el sistema** donde vive el token o la sesión de administración.

### 2.2 Linux — mantener `systemd-resolved`, cortar LLMNR y mDNS

**No** deshabilitar `systemd-resolved` entero en Ubuntu típico sin plan DNS alternativo (rompe stub y muchos contenedores).

Bajo `[Resolve]` en `/etc/systemd/resolved.conf`:

```ini
[Resolve]
LLMNR=no
MulticastDNS=no
```

```bash
sudo systemctl restart systemd-resolved
resolvectl status
```

### 2.3 Verificación de tráfico

```bash
sudo tcpdump -ni any udp port 5355 -c 20
```

Criterio: **cero o solo tráfico explícitamente permitido** por política (documentar excepciones, p. ej. impresoras).

### 2.4 Firewall (opcional)

```bash
# Solo tras validar que no rompe servicios acordados
sudo iptables -A INPUT -p udp --dport 5355 -j DROP
```

### 2.5 Windows — NBT-NS y GPO

Ver §6 y [documentación Microsoft](https://learn.microsoft.com/) para **Turn off multicast name resolution** y NetBIOS por interfaz.

---

## 3. Integración con Multilinker

*Gestión unificada: misma verdad en código, checklist y ops.*

### 3.1 Checks en código (canónico)

Fragmento real (`backend/models/system_admin_playbook.py` — clave `llmnr_multicast_off`; incluye `cmd` / `expected` para operadores):

```python
CRITICAL_HARDENING_CHECKS = {
    "llmnr_multicast_off": {
        "scope": "Linux con systemd-resolved (p. ej. VPS Ubuntu / Hetzner)",
        "cmd": "grep -E '^LLMNR=|^MulticastDNS=' /etc/systemd/resolved.conf || true",
        "expected": ["LLMNR=no", "MulticastDNS=no"],
        "verify": "Ambas directivas bajo [Resolve]; resolvectl status",
        "remediation": "Editar /etc/systemd/resolved.conf (ver PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md §2.2)",
        "territorio": "Cierra descubrimiento por multicast que alimenta poisoning en capa 2.",
    },
    # … nbt_ns_windows, udp_5355_evidence, avoid_nuke_systemd_resolved
}
```

`GET /admin_general/playbook` expone `critical_hardening_checks` vía `get_admin_general_playbook()`.

### 3.2 Funcionalidades objetivo del Multilinker

| Funcionalidad | Estado | Nota |
|---------------|--------|------|
| Coherencia hardening + Vault A/B | En curso | [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) |
| Autenticación reforzada (p. ej. YubiKey) en entorno prod | Según despliegue | No fijado en este repo |
| PQC Kyber-1024 donde aplique | Parcial | `pq_crypto.py` + dependencia opcional |
| Monitorización Prometheus / Grafana | Parcial / diseño | §4 |
| Trazabilidad GaiaChain | Opt-in | DPIA §6 robotics |

---

## 4. Monitorización y eficiencia

| Métrica | Descripción | Estado |
|---------|-------------|--------|
| `castuo_neuro_hydro_infer_seconds` | Latencia inferencia SNN (histograma) | Implementada donde el servicio exporte `/metrics` |
| `llmnr_poisoning_attempts` | Conteo de intentos / tráfico sospechoso 5355 | Diseño futuro (agente o eBPF según política) |
| `token_usage` | Uso agregado Bearer/Vault (sin valores secretos) | Diseño futuro |
| `system_uptime` / disponibilidad | Actividad del servicio edge | Según stack (node exporter, probe HTTP, etc.) |

---

## 5. Sistema de mejora continua

| Proceso | Descripción | Frecuencia | Herramientas |
|---------|-------------|------------|--------------|
| Auditoría de seguridad | Vulnerabilidades, PQC, red | Trimestral (orientativo) | OpenSCAP, Nessus u homólogo; checklist Multilinker |
| Pruebas de campo | SNN / RF / robotics | Mensual según programa | GNU Radio, lab TRL6 |
| Revisión DPIA | RGPD / AI Act según alcance | Anual o ante cambio de tratamiento | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |
| Optimización de rendimiento | TTL, caché, SLO | Mensual | Prometheus, roadmap P1–P5 |

---

## 6. Hardening y seguridad (referencia rápida)

| Medida | Comando / acción | Prioridad |
|--------|-------------------|-----------|
| LLMNR off | Editar `[Resolve]` → `LLMNR=no` (no `tee -a` ciego: evita duplicar claves o saltarse `[Resolve]`) | Alta |
| mDNS off | `MulticastDNS=no` en el mismo bloque | Alta |
| Hetzner / `sed` | `sed '/\\[Resolve\\]/a …'` **una sola vez** si no existían líneas; reejecutar duplica — ver [PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-SISTEMA-2026.md) §2.2 | Media |
| Reiniciar resolver | `sudo systemctl restart systemd-resolved` | Alta |
| Verificar | `resolvectl status` | Alta |
| Evidencia red | `tcpdump` UDP 5355 | Media |
| Windows | GPO / NetBIOS §2.5 | Alta en LAN mixta |

---

## 7. Documentación y enlaces

| Documento | Propósito | Enlace |
|-----------|-----------|--------|
| Evolución TRL superior | Hoja de ruta TRL | [PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md](./PRONTUARIO-MAESTRO-EVOLUCION-TRL-SUPERIOR-2026.md) |
| Integraciones P1–P3 | Tareas y estado | [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) |
| TRL6 Hetzner | Staging + red §3.1 | [CHECKLIST-TRL6-HETZNER-STAGING.md](./CHECKLIST-TRL6-HETZNER-STAGING.md) |
| DPIA Robotics | Impacto legal | [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) |

---

## 8. Hoja de ruta de seguridad (≈3 meses)

| Acción | Plazo orientativo | Criterio de éxito |
|--------|-------------------|-------------------|
| Formalizar Multilinker (agente o solo playbook+CI checks) | 2 semanas | Checks ejecutados en staging con bitácora |
| Mitigar LLMNR/mDNS en edge + puestos admin | 1 semana | `resolvectl` + política Windows; `tcpdump` acordado |
| Grafana / dashboards | 2 semanas | Paneles con SLO definidos |
| Auditoría externa | 1 mes | Informe archivado según política de confidencialidad |

---

## Anexo — antes / después (territorio)

| Estado | Descripción |
|--------|-------------|
| **Antes** | Multicast de nombres activo en LAN mixta → superficie de poisoning y relay. |
| **Después** | LLMNR/mDNS desactivados en política; DNS estable; custodia A/B intacta; evidencia registrada. |

*Ningún hardening sustituye segmentación perimetral ni auditoría independiente.*

---

*Quien apaga el resolver sin mapa de DNS, deja el invernadero sin lectura de presión atmosférica.*
