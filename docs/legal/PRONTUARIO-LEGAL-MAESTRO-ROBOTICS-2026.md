# Prontuario legal maestro — Robotics Lab & trazabilidad Castúo (2026)

**Fecha orientativa:** 2026-03-22 · **Ámbito:** código y documentación **en este clon**.

**Límite jurídico:** este documento **no** es asesoramiento legal, **no** sustituye firma DPO ni certificación ISO/AI Act/CNPD. Cualquier celda “completo” indica **evidencia documental o técnica en repo**, no homologación oficial.

**Relación técnica:** [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) §6 · [DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md](./DPIA-Robotics-DPO-SOLICITUD-FIRMA-PLANTILLA.md) · [INFORME-EVIDENCIA-TRL6-PLANTILLA.md](./INFORME-EVIDENCIA-TRL6-PLANTILLA.md) · [CHECKLIST-TRL6-HETZNER-STAGING.md](../deploy/CHECKLIST-TRL6-HETZNER-STAGING.md) · [ROADMAP-Robotics-2026.md](./ROADMAP-Robotics-2026.md) · [ROADMAP-Neuromorphic-2026.md](./ROADMAP-Neuromorphic-2026.md) · [ROADMAP-Scan3D-Print-2026.md](./ROADMAP-Scan3D-Print-2026.md) · `backend/integrations/robotics/README.md` · [PLAN-EXCELENCIA-V2.5-REFUERZO.md](./PLAN-EXCELENCIA-V2.5-REFUERZO.md) · [SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md](./SISTEMA-COHERENCIA-ADMIN-GENERAL-2026.md) (`admin_general` + playbook código)

---

## 1. Matriz normativa → evidencia en repositorio

| Normativa / marco | Ámbito | Estado en clon | Documentos / código | Pendiente humano |
|-------------------|--------|----------------|---------------------|------------------|
| RGPD | Datos personales, minimización | 🟡 Marco + DPIA lab | `compliance_docs/generated/02.01.01_Registro_Actividades_Tratamiento.md`, [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) | Auditoría DPO, registro de actividades vigente en producción |
| AI Act (UE 2024/1689) | Sistemas de IA | 🟡 Autoevaluación generada | `compliance_docs/generated/02.03.03_AI_Act_Self-Assessment.md` | Clasificación de riesgo según **uso desplegado**; notificaciones si aplica |
| ISO 27001 | Seguridad de la información | 🟡 Plantilla / declaración generada | `compliance_docs/generated/02.04.01_Declaracion_Aplicabilidad_ISO27001.md`, plantilla `compliance_docs/templates/iso27001_declaration_template.md` | Certificación / auditoría externa si se persigue |
| SIGPAC / parcela | PEI-001, informes | 🟢 Flujo técnico documentado | [SIGPAC-Compliance-2026.md](./SIGPAC-Compliance-2026.md), `pei-001-sigpac/`, `compliance_docs/generated/02.05.01_Procedimiento_SIGPAC_Extremadura.md` | Contrato / API MAPA-FEGA si integración oficial |
| Ley 3/2023 (Extremadura) | Consentimientos / montes (donde aplique) | 🟡 Doc generada | `compliance_docs/generated/02.02.03_Gestion_Consentimientos_Ley_3_2023_Extremadura.md` | Titulación y artículos aplicables al expediente real |
| GaiaChain | Auditoría on-chain | 🟡 Opt-in técnico | `lab_gaiachain_optional.py`, `gaiachain_service.register_event_in_chain` | Contrato desplegado auditado, clave en Vault/HSM, red acordada |

---

## 2. Robotics Lab — análisis alineado con el código

### 2.1 RGPD (minimización, art. 5 y 25 — enfoque técnico)

- **`parcel_ref` on-chain:** solo si `CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID=1`; **por defecto desactivado** (DPIA §6).
- **`tokenId`:** entero explícito o `CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID`; **no** “hash mágico” de parcela en el stub.
- **Digest:** SHA-256 del JSON canónico del snapshot; **tamaño de `details` on-chain** depende del contrato y del gas — revisar antes de mainnet.
- **Firma:** `dilithium_sign` vía `pq_crypto` (**o ruta simulada documentada** si no hay `pqcrypto`).

### 2.2 AI Act — HydroponicsSNN (laboratorio)

- El módulo es **simulación TRL-4** en repo; la categoría de riesgo **final** depende del despliegue (uso médico, biometría, etc.). No afirmar “bajo riesgo” como veredicto cerrado sin DPO.

### 2.3 Observabilidad sin secretos

- `GET /health` → `chain_status`: `disabled` | `ready` | `misconfigured`; `neuromorphic_lab` (bool).

### 2.4 Payload on-chain (ejemplo orientativo)

Contrato real: campos `action`, `status`, `details`, `compliance` como en `register_event_in_chain`. Ejemplo **mínimo**:

```json
{
  "tokenId": 1,
  "action": "PEI001_SNAPSHOT",
  "status": "REGISTERED",
  "details": {
    "digest": "sha256:…",
    "riego_ml": 320,
    "eco_alloy": "Cs2AgBiBr6"
  },
  "compliance": {
    "module": "robotics_lab_snapshot",
    "minimization": "parcel_ref_opt_in"
  }
}
```

---

## 3. Controles técnicos (lectura ISO 27001 — no certificación)

| Control (referencia) | Implementación en clon | Nota |
|----------------------|-------------------------|------|
| Clasificación de información | `tokenId` vs referencia parcela opt-in | Política corporativa aparte |
| Criptografía | `pq_crypto`, AES-GCM en señales lab | Claves en Vault en prod |
| Registro / trazabilidad | `chain_registration`, logs app | SIEM/Wazuh si aplica en prod |
| Integridad | JSON canónico + digest | Revisar límites de tamaño en cadena |

---

## 4. Tests automatizados (contrato técnico, no legal)

Integración relevante (robotics lab + gaiachain optional + neuromórfico + scan3d): **13** tests en `tests/integrations/test_robotics_lab_stub.py`, `test_lab_gaiachain_optional.py`, `test_neuromorphic.py`, `test_scan3d_lab.py` (última verificación en desarrollo).

---

## 5. Checklist DPO / responsable (manual)

- [ ] Revisar [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md) §6 y aprobar `CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID` en prod.  
- [ ] Validar red (testnet/mainnet), contrato auditado y límites de gas.  
- [ ] `GAIA_CHAIN_PRIVATE_KEY` solo en HSM/Vault; rotación documentada.  
- [ ] AI Act: revisar `02.03.03_AI_Act_Self-Assessment.md` frente al **producto desplegado**.  
- [ ] SIGPAC: validar procedimiento frente a MAPA/FEGA y expediente.  
- [ ] ISO 27001: si se certifica, alcance y evidencias fuera de este markdown.  
- [ ] Despliegue VPS: `docs/deploy/robotics-lab-hetzner.env.example` + TLS delante del stub.

---

## 6. Riesgos (resumen)

| Riesgo | Mitigación en repo | Revisión humana |
|--------|--------------------|-----------------|
| RGPD — exceso de datos on-chain | `parcel_ref` opt-in; `details` acotados | DPO |
| AI Act — reclasificación | Documentación y uso acotado lab | DPO + jurídico |
| Cadena — tx fallidas | `try_register_lab_audit_event`; stub estable | Operaciones |
| PQC — dependencias | `pqcrypto` opcional; fallback documentado | Seguridad |

---

## 7. Veredicto (explícito)

**No** se declara aquí “legalmente seguro para producción”. El repositorio ofrece **controles y documentación orientativas**; la **aptitud legal del despliegue** la fijan DPO, asesoramiento jurídico y autoridades según proceda.

---

*Sabionda_Omega_2040: el agua y el territorio mandan; el git solo ordena la evidencia.*
