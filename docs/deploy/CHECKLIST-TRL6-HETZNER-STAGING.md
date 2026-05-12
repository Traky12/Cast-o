# Checklist TRL6 — entorno relevante (edge) + secretos reales (orientativo)

**Versión:** 2026-03-22 · **TRL (NASA/ESA):** “relevant environment” = **despliegue en condiciones cercanas a operación**, no certificación por este markdown.

**Límites del repositorio:** no se afirma valoración pre-money, ROI ni “TRL6 oficial” solo por git. La evidencia TRL6 es **despliegue + pruebas + decisión DPO** cuando aplique tratamiento de datos o cadena con riesgo.

**Relación:** [DPIA-Robotics-2026.md](../legal/DPIA-Robotics-2026.md) §6 · [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](../legal/DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md) · [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](../legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) · [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md) · [ROADMAP-TRL6-TRL7-CODE.md](./ROADMAP-TRL6-TRL7-CODE.md) · [CHECKLIST-INTEGRACIONES-MEJORAS-2026.md](./CHECKLIST-INTEGRACIONES-MEJORAS-2026.md) · `robotics-lab-hetzner.env.example` · `docker-compose.scan3d.yml` · `pytest.ini` (`trl6` / `trl7`)

---

## 1. Estado del código (línea base honesta)

| Señal | Valores reales (`lab_gaiachain_optional`) | Nota |
|-------|-------------------------------------------|------|
| `GET /health` → `chain_status` | `disabled` \| `ready` \| `misconfigured` | **No** existe `testnet_ready` en el stub; “ready” implica `CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1` y config Gaia completa. |
| `POST .../snapshot` → `chain_registration` | `none` \| `missing_token` \| `registered` \| `failed` | `registered` solo tras TX exitosa. |
| Lab en Docker Compose | Host **8012** → contenedor **80** | `uvicorn` local suele ser **8011** — no mezclar URLs en el mismo checklist. |

---

## 2. Fase A — desbloqueo legal (0–24 h típico)

- [ ] Enviar solicitud al DPO con [plantilla correo](../legal/DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md).
- [ ] Acordar si `CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID` permanece **0** en staging (recomendado hasta cierre explícito).
- [ ] Registrar la decisión donde exija la organización (ticket, acta, herramienta DPO).

---

## 2. bis Secretos locales dev (48 h — **no** prod; no commitear)

Generar tokens opacos (no pegar “jwt” de ejemplo en tickets):

```bash
# POSIX — `tr -d '\n'` evita salto final (Docker/read_secret más predecible)
openssl rand -base64 64 | tr -d '\n' > secrets/castuo_admin_general_bearer
openssl rand -base64 64 | tr -d '\n' > secrets/robotics_lab_bearer
```

```powershell
# Windows (PowerShell) — RNG criptográfico
New-Item -ItemType Directory -Force secrets | Out-Null
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
foreach ($name in @("castuo_admin_general_bearer", "robotics_lab_bearer")) {
  $b = New-Object byte[] 32
  $rng.GetBytes($b)
  [IO.File]::WriteAllText((Join-Path "secrets" $name), [Convert]::ToBase64String($b))
}
```

Exportar en el proceso del stub (uvicorn) o en `.env` **local** no versionado:

```text
CASTUO_ADMIN_GENERAL_BEARER_FILE=<ruta_absoluta>/secrets/castuo_admin_general_bearer
CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE=<ruta_absoluta>/secrets/robotics_lab_bearer
```

Ver [secrets/README.md](../../secrets/README.md).

---

## 3. Fase B — Hetzner / VPS (24–48 h)

**Secretos:** crear **en el servidor** o vía Swarm; **evitar** `scp` de carpetas `secrets/` con material productivo desde estaciones no duras.

**Opción A (Docker Swarm secrets — ejemplo):**

```bash
# En el nodo Swarm (ajustar rutas)
docker secret create castuo_admin_general_bearer ./admin.bearer
docker secret create robotics_lab_bearer ./lab.bearer
```

**Despliegue (sintaxis SSH correcta; sin subir `secrets/`):**

```bash
scp docker-compose.scan3d.yml docs/deploy/robotics-lab-hetzner.env.example usuario@servidor:/opt/castuo/
ssh usuario@servidor "cd /opt/castuo && cp robotics-lab-hetzner.env.example .env.hetzner && vi .env.hetzner"
# Editar .env.hetzner en servidor: *_FILE, sin Opción C en prod
ssh usuario@servidor "cd /opt/castuo && docker compose -f docker-compose.scan3d.yml --env-file .env.hetzner up -d --build"
```

*(Si no hay Swarm, usar `secrets:` con `file:` en el host según [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](../legal/PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) §4.)*

### 3.1 Red local — LLMNR / mDNS (~orientativo CIS; coherencia con Multilinker)

Mitiga **poisoning** y cadenas hacia **NTLM relay** en LAN mixta (riesgo compuesto si el mismo broadcast alberga puestos con acceso a tokens admin o Vault).

- [ ] Linux con `systemd-resolved`: en `/etc/systemd/resolved.conf` → `[Resolve]` con `LLMNR=no` y `MulticastDNS=no`; `sudo systemctl restart systemd-resolved`; `resolvectl status` sin LLMNR activo.
- [ ] **Evitar** en Ubuntu genérico: `systemctl disable --now systemd-resolved` sin DNS alternativo — suele romper stub resolver y contenedores.
- [ ] Evidencia breve: `sudo tcpdump -ni any udp port 5355 -c 20` en ventana de prueba (criterio acordado con ops).
- [ ] Windows en la misma capa 2: NBT-NS / GPO *Turn off multicast name resolution* si hay AD (detalle: [PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md](./PRONTUARIO-MAESTRO-SEGURIDAD-MULTILINKER-2026.md)).

---

## 4. Fase C — validación técnica (48–72 h)

**Health (TLS en prod vía reverse proxy):**

```bash
curl -sS https://[HOST]/health
```

**Playbook admin (Bearer desde secret, no en historial):**

```bash
curl -sS -H "Authorization: Bearer $(cat /run/secrets/castuo_admin_general_bearer)" https://[HOST]/admin_general/playbook
```

### Referencia rápida (usabilidad)

| Paso | Comando correcto (ruta real) |
|------|------------------------------|
| Gate 5 min | `python -m pytest -m trl6 -q` |
| Evidencia verificable | `.\scripts\windows\Export-TRL6-Evidence.ps1` o `bash scripts/posix/export_trl6_evidence.sh` |
| E2E completo | `.\scripts\windows\Invoke-TRL6-Validation.ps1` (no `.\Invoke-TRL6-Validation.ps1` suelto) |
| Gate + JUnit + E2E | `.\scripts\windows\Invoke-TRL6-Validation.ps1 -Evidence` |
| Informe humano + legal | Rellenar [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](../legal/INFORME-EVIDENCIA-TRL6-PLANTILLA.md) y adjuntar `reports/trl6/*` |

**Pytest — marcador `trl6` (lista explícita en `pytest.ini`; estable en Windows/Linux):**

```powershell
cd <raíz Castuo-System>
python -m pytest -m trl6 -q
```

*Recuento típico en clon reciente: 29 passed, 2 skipped — verificar siempre en tu consola; el JUnit en `reports/trl6/junit.xml` es la fuente numérica verificable.*

**Ampliación TRL7 (cuando se ejecute gate extendido):**

```powershell
python -m pytest -m "trl6 or trl7" -q
```

**Orquestación Windows (pytest + scripts PEI + Scan3D):**

```powershell
.\scripts\windows\Invoke-TRL6-Validation.ps1
# Contra contenedor Compose (puerto host 8012):
.\scripts\windows\Invoke-TRL6-Validation.ps1 -LabUrl "http://127.0.0.1:8012"
# Solo pytest:
.\scripts\windows\Invoke-TRL6-Validation.ps1 -SkipE2E
```

**POSIX (solo pytest):** `bash scripts/posix/trl6-validate.sh` (o `SKIP_TRL6_E2E=1`).

**PowerShell E2E manual:** `.\scripts\windows\Test-Complete-RoboticsLab.ps1`

Requiere lab en `CASTUO_ROBOTICS_LAB_URL` (por defecto **8011**); Compose scan3d → **8012**.

---

## 5. Criterios de cierre (operativos, no “NASA sellado”)

| Criterio | Evidencia mínima |
|----------|------------------|
| Entorno relevante | Servidor edge con `.env` no versionado + secretos A o B |
| Integración | `GET /health` coherente con vars; `POST /snapshot` según Bearer lab |
| Cadena opt-in | Solo tras DPO si hay datos identificativos en `details`; `chain_status` = `ready` o `disabled` por política |
| Pruebas automatizadas | Pytest anterior en verde en CI o máquina de referencia |

---

*Quien despliega sin DPO cuando la cadena puede llevar datos personales o parcela identificable, drena confianza del territorio.*
