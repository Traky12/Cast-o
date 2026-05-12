# Arquitectura de Seguridad Reforzada (Qubes OS + Whonix + Parrot Security)
**Version:** 1.0  
**Fecha:** 20/03/2026  
**Autor:** Gregorio Jimenez Bodes / Sabionda IA  

> Plantilla de arquitectura y despliegue. Requiere validacion tecnica, auditorias y documentacion contractual (DPA/SLA) segun el proveedor y jurisdiccion.
> Evita claims absolutos: la seguridad real depende de la configuracion, actualizacion y pruebas (pentesting/Wazuh/OpenVAS).

---

## Diagrama logico (compartimentacion)

```mermaid
graph TD
    subgraph QubesOS["Qubes OS (CR)"]
        A[AppVM: CASTUO-Backend] -->|Xen| B[Sys-Whonix]
        B -->|Tor| C[Internet]
        D[AppVM: CASTUO-Gemelo] -->|Xen| B
        E[AppVM: CASTUO-Legal] -->|Xen| B
    end

    subgraph Whonix["Whonix (DE)"]
        F[Whonix-Gateway] -->|Tor| C
        G[Whonix-Workstation] -->|Tor| F
        H[CASTUO-Backend] -->|Docker| G
    end

    subgraph Parrot["Parrot Security (IT)"]
        I[Parrot-Hardening] -->|Wazuh| J[CASTUO-Server]
        J -->|OpenVAS| K[Pentesting]
    end

    subgraph Hetzner["Infraestructura (ej. Hetzner)"]
        L[Hetzner Cloud] -->|Docker| F
        L -->|KVM| A
        L -->|KVM| I
    end

    C -->|Trafico anonimo (objetivo)| M[GaiaChain]
    M -->|Blockchain| N[Auditoria inmutable]
```

---

## 1) Inventario de integraciones (con trazabilidad)

| Integracion | Objetivo verificable | Evidencia / enlace |
|---|---|---|
| Qubes OS (Xen) | Compartimentacion por AppVM (backend/gemelo/legal) | Config/plantillas Qubes en este documento |
| Whonix (Tor) | Minimizar superficie de exposicion (objetivo: trafico anonimizando) | Verificacion: `check.torproject.org` y logs |
| Parrot Security | Deteccion y test continuo (Wazuh + OpenVAS) | Evidencias Wazuh + informes OpenVAS |
| GaiaChain (witness) | Inmutabilidad de eventos de seguridad (hash) | Script: `scripts/Register-SecurityEvent.ps1` |

---

## 2) Integracion con Qubes OS (plantilla)

### 2.1 Configuracion de AppVMs (ejemplo)

```yaml
# qubes-config/castuo-qubes.yml
---
dom0:
  updates:
    - qvm-dom0-update
  services:
    - qubes-mgmt-salt
    - qubes-firewall

appvms:
  - name: castuo-backend
    template: fedora-38
    label: red
    provides_network: false
    netvm: sys-whonix
    include_in_balance: true
    qrexec:
      - allow
    services:
      - qubes-firewall
      - docker
  # ... gemelo/legal analogos ...

sysvms:
  - name: sys-whonix
    template: whonix-gw-16
    label: black
    provides_network: true
    netvm: none
    include_in_balance: false
```

### 2.2 Docker en AppVM (ejemplo)

```bash
# En la AppVM castuo-backend:
sudo qubesctl state.apply docker.host
docker run -d \
  --name castuo-backend \
  --network qubes-tor-only \
  -v /home/user/castuo-data:/data \
  -e GAIA_CHAIN_API_KEY=$(cat /rw/config/gaiachain-key) \
  ghcr.io/castuo-system/backend:v3.0
```

> Nota: No comprometer secretos. Mantener `GAIA_CHAIN_API_KEY` fuera del repo y aplicar minimos privilegios.

---

## 3) Integracion con Whonix (plantilla)

### 3.1 Compose para Hetzner + Tor (ejemplo)

```yaml
# docker/whonix-castuo.yml
version: '3.8'
services:
  whonix-gateway:
    image: qubesos/whonix-gateway:latest
    container_name: whonix-gateway
    cap_add:
      - NET_ADMIN
      - SYS_ADMIN
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      whonix-external:
        ipv4_address: 10.152.152.10

  castuo-backend:
    image: ghcr.io/castuo-system/backend:v3.0
    container_name: castuo-backend
    depends_on:
      - whonix-gateway
    network_mode: "service:whonix-gateway"
    environment:
      - TOR_PROXY=10.152.152.10:9050
    volumes:
      - castuo-data:/data

  # whonix-workstation analogo...

volumes:
  castuo-data:

networks:
  whonix-external:
    driver: bridge
    ipam:
      config:
        - subnet: 10.152.152.0/24
```

### 3.2 Verificacion de Tor (ejemplo)

```bash
docker exec whonix-gateway curl --socks5-hostname 10.152.152.10:9050 https://check.torproject.org
```

---

## 4) Integracion con Parrot Security (plantilla)

### 4.1 Compose con Wazuh + OpenVAS (ejemplo)

```yaml
# parrot-hardening/parrot-castuo.yml
version: '3.8'

services:
  parrot-hardening:
    image: parrotsh/parrot-security:latest
    container_name: parrot-hardening
    cap_add:
      - SYS_ADMIN
      - NET_ADMIN
    security_opt:
      - apparmor:unconfined
      - seccomp:unconfined
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./wazuh-config:/etc/wazuh
      - ./openvas-config:/var/lib/openvas

  castuo-backend:
    image: ghcr.io/castuo-system/backend:v3.0
    depends_on:
      - parrot-hardening
    environment:
      - WAZUH_MANAGER=parrot-hardening
      - OPENVAS_SCAN_TARGET=castuo-backend
```

---

## 5) GaiaChain: evidencias inmutables de seguridad

### Script de registro

- Script: `scripts/Register-SecurityEvent.ps1`
- Verifica/crea evidencia local en `security-events/<yyyyMMdd>/<txid>.json`
- Registra hash inmutable en GaiaChain (si `GAIA_CHAIN_API_URL` esta configurado)

Ejemplo:

```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "unauthorized_access_attempt" `
  -EventData @{ source_ip="192.168.1.100"; target_service="castuo-backend"; action="blocked" } `
  -CoopId 1 `
  -Severity "critical" `
  -LogEventInBackend
```

---

## 6) Orden recomendado de despliegue (max seguridad, a validar)

1. Whonix/Tor (perimetro y anonimizacion objetivo)
2. Qubes OS (compartimentacion por AppVM)
3. VeraCrypt EU (cifrado de disco/volumenes en bunker)
4. Parrot Security (Wazuh + OpenVAS)
5. GaiaChain (testigo/inmutabilidad por evento)

---

## 7.1) Evidencia documental: acuerdo de colaboracion Castuo Gate v2.0

Para integracion documental verificable (transcripcion), ver:
- [`ACUERDO-DE-COLABORACION-CASTUO-GATE-V2-0.md`](ACUERDO-DE-COLABORACION-CASTUO-GATE-V2-0.md)

Este acuerdo se incorpora como evidencia de compromisos (acceso e infraestructura, validacion bovina, transferencia de datos y inclusion social).

---

## 7.2) Integracion con VeraCrypt EU (cifrado de extremo a extremo)

Para reforzar la soberania de datos mediante cifrado de disco completo o contenedores cifrados, ver:
- [`VERACRYPT-EU.md`](VERACRYPT-EU.md)

Scripts disponibles en el repo (automatizables en despliegue/runbook):
- `scripts/security/install_veracrypt_eu.sh`
- `scripts/security/create_veracrypt_container_eu.sh`
- `scripts/security/mount_veracrypt_container_eu.sh`
- `scripts/security/umount_veracrypt_container_eu.sh`
- `scripts/security/veracrypt_eu_audit.py`
- `scripts/security/notarize_veracrypt_event.sh`

---

## 7) Observaciones legales prudentes

- Los “resultados” (detecciones, hallazgos, tiempo de recuperacion) deben respaldarse con **informes** y **evidencia**.
- Cualquier dato personal en logs/telemetria requiere minimizacion y cumplimiento (GDPR, Art. 30/32/33 segun aplique).

---

## 8) Relacion con ECSE (Trazabilidad evolutiva)

Este documento se integra con el marco ECSE como parte de la dimension de **Seguridad** y de la **Trazabilidad con evidencia inmutable**.

Enlaces:
- [`PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md`](PRONTUARIO_MAESTRO_EVOLUTIVO_ECSE.md)
- `scripts/Register-SecurityEvent.ps1`

## 9) Documento maestro de seguridad reforzada

Para el marco completo (matriz de severidad, plantilla legal y runbook), ver:
- [`PRONTUARIO_MAESTRO_SEGURIDAD_REFORZADA.md`](PRONTUARIO_MAESTRO_SEGURIDAD_REFORZADA.md)

## 10) Arquitectura legal y tecnica

Para cumplimiento normativo (diagrama, mapa de evidencia y plantillas auditables), ver:
- [`ARQUITECTURA-LEGAL-Y-TECNICA.md`](ARQUITECTURA-LEGAL-Y-TECNICA.md)

## 11) Enlaces de trazabilidad

Para coherencia con documentos existentes (matriz de severidad, witness y checklist), ver:
- [`ENLACES-DE-TRAZABILIDAD.md`](ENLACES-DE-TRAZABILIDAD.md)
- [`EVIDENCIA-LEGAL-VERIFICADA.md`](EVIDENCIA-LEGAL-VERIFICADA.md)

## 12) Integracion con Omega-9 (laboratorio defensivo)

Extiende el perimetro de analisis **autorizado** con:

- **Cadena de custodia** para muestras (hashes y metadatos minimos).
- **Sandbox aislada** (referencia: Firejail / QEMU / contenedores efimeros; por validar en vuestra infra).
- **Trazabilidad** mediante GaiaChain (contrato minimal: `hash`, `coop_id`, `ipfs_cid`).

**Documentacion**

- Arquitectura: [`ops/research/omega9-defensive-lab-architecture-2026.md`](ops/research/omega9-defensive-lab-architecture-2026.md)
- Notarizacion y certificacion (procedimiento): [`ops/research/omega9-notarization-procedure-2026.md`](ops/research/omega9-notarization-procedure-2026.md)
- Cumplimiento DORA (stub): [`compliance/dora.md`](compliance/dora.md)
- Punto de entrada Ops: [`ops/research/README.md`](ops/research/README.md)
- Politicas (indice): [`security/policies.md`](security/policies.md)

**Scripts**

- `scripts/ops/research/ingest-sample.sh`
- `scripts/ops/research/Register-LabEvidence.sh`

## 13) Vision de arquitectura escalable (referencia)

Roadmap global (integraciones, catalogo de servicios, compliance orientativo): [`architecture/ARQUITECTURA-VISION-ESCALABLE-CASTUO-2026.md`](architecture/ARQUITECTURA-VISION-ESCALABLE-CASTUO-2026.md).

