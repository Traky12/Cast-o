# Plan 90 días — refuerzo enterprise EU (CASTÚO-SYSTEM)

**Horizonte:** 2026 · **Ámbito:** documentación operativa y rutas reales del repositorio.

> **Aviso legal y financiero:** Las cifras de ingresos, valoraciones, run-rate o “benchmark catalán” citadas en briefings internos son **hipótesis o objetivos a validar** con asesoría fiscal, legal y contratos firmados. Este documento **no** es oferta de inversión ni compromiso de resultados.

---

## 1. Aceleradoras y fondos (días 1–15)

| Canal (referencia) | Enfoque |
|--------------------|---------|
| Programas agrotech / Generalitat / valencianos / Ebro | Postulación con **demo reproducible** + paquete cumplimiento |
| Paquete mínimo repo | `scripts/demo_ctaex.sh`, [DEMO-TRL10.1](./icex-hlth-europe/DEMO-TRL10.1.md), [PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md](../PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md) |
| Seguridad / ISO 27001 (evidencia) | [ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md](../ARQUITECTURA-SEGURIDAD-REFORZADA-QUBES-WHONIX-PARROT.md) |
| Privacidad | [legal/DPIA-CASTUO-SYSTEM.md](../legal/DPIA-CASTUO-SYSTEM.md) |

**Acción humana:** enviar formularios, deadlines y anexos según cada convocatoria (no automatizable desde el código).

---

## 2. Refuerzo técnico inmediato (días 1–30)

| Objetivo | Artefacto en repo |
|----------|-------------------|
| Compliance JP (checklist/script) | `scripts/validate_JP.py` |
| Informe cumplimiento | `backend/scripts/generate_compliance_report.py` |
| Laboratorio seguridad / QKD (script) | `scripts/security/quantum_destruction_qkd.py` |
| PQC Kyber (motor) | `backend/sabion_omega_2040/kyber2048_pqc.py` (también `backend/crypto_master/kyber2048_engine.py`) |
| Despliegue soberanía EU | `docker-compose.hetzner.zero-leak.yml` (raíz del repo) |
| K8s multi-región EU | **`k8s/overlays/eu/deployment-patch.yaml` — no existe aún.** Base actual: `k8s/sabionda-core/deployment.yaml`, `k8s/cursor/*.yaml` |

**Backlog técnico:** crear `k8s/overlays/eu/` con Kustomize o Helm alineado a política de residencia de datos.

---

## 3. Ingresos / pilotos (objetivos internos — validar)

| Línea (ejemplo de playbook) | Script / notas |
|-----------------------------|----------------|
| Demo CTAEX / feria | `./scripts/demo_ctaex.sh` — requiere API/OpenEPCIS según entorno (`API_URL`, `EPCIS_URL`, token) |
| Activación 3 coops IoT | `./scripts/activar_produccion_3_coops.sh` — MQTT opcional; mint vía `backend/scripts/mint_dynamic_nft.py` si env on-chain |
| NFT / cultivo | `backend/scripts/mint_crop_nft.py` (y variantes en `backend/scripts/`) |

Ningún script **garantiza** importes en €; dependen de contratos, despliegue y mercado.

---

## 4. Alianzas estratégicas (días 30–60)

Trabajo de **partnership** (IRTA, GaiaChain, AEMPS, Hetzner, etc.): MOU, pilotos, DPA y anexos técnicos. Cruzar con DPIA y [MOTIONEYE-CASTUO-INTEGRATION.md](./MOTIONEYE-CASTUO-INTEGRATION.md) si hay vídeo/IoT.

---

## 5. Estructura corporativa (días 60–90)

Spin-offs, participadas y valoraciones: **solo con asesoría mercantil y fiscal** (España / UE). Este repo documenta **tecnología y cumplimiento**, no constitución de sociedades.

---

## 6. Comandos inmediatos (desde raíz del repo)

**Linux / macOS / Git Bash / WSL:**

```bash
./scripts/demo_ctaex.sh && ./scripts/activar_produccion_3_coops.sh
```

**PowerShell (si `bash` está en PATH):**

```powershell
bash ./scripts/demo_ctaex.sh; if ($LASTEXITCODE -eq 0) { bash ./scripts/activar_produccion_3_coops.sh }
```

**Requisitos habituales:** `curl`, `jq` (demo CTAEX), API en marcha si se esperan respuestas 200, variables para cadena/NFT si aplica.

---

## 7. Trazabilidad de eventos (post-despliegue)

```powershell
.\scripts\Register-SecurityEvent.ps1 -EventType "enterprise_90d_plan" -EventData @{ phase = "kickoff"; doc = "PLAN-90-DIAS-ENTERPRISE-EU-2026.md" }
```

---

## 8. KPIs (revisión quincenal)

| Métrica | Cómo medirla |
|---------|----------------|
| Demo reproducible | Ejecución exitosa de `demo_ctaex.sh` en staging |
| Postulaciones enviadas | Registro interno (no en git) |
| Evidencias seguridad | Informes + logs en `security-events/` si aplica |
| Ingresos | Solo tras facturación auditada |

---

**Relación:** [MANIFESTO-CASTUO-SYSTEM-1-0.md](../MANIFESTO-CASTUO-SYSTEM-1-0.md) · [PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md](../PRONTUARIO-MAESTRO-CASTUO-SYSTEM-2040.md) · [legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md](../legal/PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md)
