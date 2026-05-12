# Prontuario maestro legal — ejecución 90 días (CASTÚO-SYSTEM)

**Versión documental:** 1.7.1 · **Ámbito:** marco de referencia EU/ES para alinear código, evidencias y expediente.  
**Paradigma operativo:** Sabionda Omega 2040 (territorio, trazabilidad, mínima ficción en compliance).

---

## ⚠️ Límites (obligatorio leer)

| Este documento **sí** hace | Este documento **no** hace |
|----------------------------|----------------------------|
| Enlazar scripts y rutas **reales** del repo | Sustituir **asesoramiento jurídico** (abogado mercantil, contratación pública, MiCA, fiscal) |
| Listar normas como **objetivos de alineación** | Emitir **certificados** ISO, ENISA o “auth” de sistema |
| Recordar DPIA y evidencias ya generadas | Garantizar **cumplimiento LCSP 9/2017** sin expediente y firma |
| Apuntar a planes operativos | Inventar **valoraciones**, run-rate € ni % de certificación “Stage1” |

**No existe** en este repositorio, como prueba legal automática: `SABIONDA-AUTH-V1.cert`, unidad activa `castuo-autonomous-agents.service` instalada en un servidor concreto (solo hay **plantilla** `scripts/systemd/castuo-autonomous-agents.service.example`), `k8s/overlays/production/`, ni ejecución autónoma de contratos públicos. Cualquier cifra de ingresos o valoración es **hipótesis de negocio** a validar fuera del código.

---

## 1. Mandato ejecutivo (traducción a acciones verificables)

**“Ejecutar plan 90 días con cobertura legal”** = mantener trazabilidad, DPIA, contratos firmados por personas jurídicas y evidencias reproducibles. El código **asiste** al expediente; **no** lo sustituye.

---

## 2. Día 1 — evidencias técnicas inmediatas

| Acción | Ruta en repo | Nota |
|--------|--------------|------|
| Informe / generador compliance | `backend/scripts/generate_compliance_report.py` | Salida según implementación; revisar anexos legales aparte |
| Documentación compliance (scripts) | `compliance_docs/scripts/generate_compliance_docs.py` | **No** `compliance/scripts/` (ruta incorrecta en algunos briefings) |
| Demo piloto CTAEX | `./scripts/demo_ctaex.sh` | Requiere API/token/ OpenEPCIS según entorno |
| Tres cooperativas IoT (playbook) | `./scripts/activar_produccion_3_coops.sh` | Mint on-chain opcional (`mint_dynamic_nft.py`) |
| NFT cultivo (si aplica) | `backend/scripts/mint_crop_nft.py` | MiCA / activos digitales: **dictamen externo** |

---

## 3. Contratación pública y fondos (LCSP 9/2017, Next Generation, etc.)

- **LCSP 9/2017** y procedimientos: pliegos, ofertas y firma los elabora **equipo jurídico**; el repo aporta **demo técnica** y documentación de seguridad/privacidad.
- **Ley Startups / régimen emergente:** trámite administrativo, no script.
- **PAC 2023-2027 / rural (Ley 18/2020):** alineación de narrativa de pilotos; sin validez normativa automática desde git.

---

## 4. Mapa técnico ↔ alianzas (referencias reales)

| Tema | Ubicación en repo |
|------|-------------------|
| Aleaciones vegetales / biopolímeros (línea IRTA-type) | `backend/vegetal_alloys/` |
| Cannabis / AEMPS (webhooks) | `backend/routers/aemps_webhooks.py`, `backend/services/cannabis_compliance.py` |
| GaiaChain / witness | `blockchain/gaia_chain.py`, `backend/utils/gaia_chain.py`, `backend/services/gaia_chain.py` |
| Cloud EU / zero-leak | `docker-compose.hetzner.zero-leak.yml` (raíz) |
| Agente cumplimiento (stub/ejecutable) | `backend/agents/compliance_agent.py` |
| Orquestación autónoma (código) | `backend/agents_autonomous/sabionda_omega.py`, `backend/agents/master_agent.py` |

**`legal_agent.py`:** no hay módulo con ese nombre; cumplimiento y gobernanza pasan por **ComplianceAgent**, **master_agent** y proceso legal humano.

---

## 5. Normas y estándares (checklist de alineación — auditar)

- **RGPD / LOPDGDD:** [DPIA-CASTUO-SYSTEM.md](./DPIA-CASTUO-SYSTEM.md)  
- **EU AI Act / Art. 22 (decisiones automatizadas):** revisar DPIA + DPIA-IA donde exista; no afirmar “compliant” sin evaluación.  
- **NIS2:** gobernanza y proveedores; ver docs de seguridad.  
- **ISO 9001 / 14001 / 22000 / 27001, FSSC 22000, GlobalG.A.P.:** certificación por **organismo acreditado**, no por script.  
- **MiCA / REACH** (BioCoin, NFT): obligatorio **asesor especializado**.

---

## 5a. Protocolo de auditoría interna (metodología)

[PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md](./PROTOCOLO-AUDITORIA-INTERNA-LEGAL-COHERENCIA.md) — flujo legal/técnico/ético, matriz de roles y límites (sin cumplimiento automático).  
Comprobación de **presencia** de ficheros: `python scripts/audit/audit_repo_evidence_check.py`

---

## 5b. Spin-offs, systemd y Grafana (qué hay en git)

Inventario sin afirmar “ACTIVE” ni certificados: [../ops/ARTEFACTOS-SYSTEMD-MONITORING-SPINOFFS.md](../ops/ARTEFACTOS-SYSTEMD-MONITORING-SPINOFFS.md) y `spin-offs/README.md` (raíz del repo).

---

## 6. Plan 90 días (operativo + legal)

Detalle día-a-día técnico y disclaimers financieros: [../ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md](../ops/PLAN-90-DIAS-ENTERPRISE-EU-2026.md).

---

## 7. Comandos de verificación (sin systemd ni kubectl ficticios)

Desde la **raíz del repositorio** (Bash / WSL / Git Bash):

```bash
python3 backend/scripts/generate_compliance_report.py
python3 compliance_docs/scripts/generate_compliance_docs.py
./scripts/demo_ctaex.sh
./scripts/activar_produccion_3_coops.sh
# Opcional, si entorno on-chain configurado:
# python3 backend/scripts/mint_crop_nft.py
```

**K8s:** no hay `k8s/overlays/production/` en el árbol actual; despliegues: ver `k8s/sabionda-core/`, `docker-compose.*`.

---

## 8. Trazabilidad de eventos (PowerShell)

```powershell
.\scripts\Register-SecurityEvent.ps1 `
  -EventType "legal_prontuario_90d_reference" `
  -EventData @{ doc = "PRONTUARIO-MAESTRO-LEGAL-EJECUCION-90-DIAS.md"; version = "1.7.1" }
```

---

## 9. Sobre módulos sensibles

El archivo `backend/sabion_omega_2040/god_mode_commands.py` es **código de producto**; su uso requiere política interna de privilegios y **no** constituye autorización legal ni “modo LCSP”. No documentamos aquí flags destructivos.

---

*Documento vivo. Última revisión documental: alinear con cada cambio de ley o contrato firmado.*
