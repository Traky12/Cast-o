# Roadmap de agentes y automatización — Castúo-System (2026)

**Ámbito:** prioridades **realistas** alineadas al código y documentación **existentes** en el clon. **No** se listan como hechos: LexBot con Mistral embebido, GaiaChain 2.0, QKD, SwissVault, NVIDIA Omniverse, u Odoo+chain sin contrato.

**Relación:** [ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md](./ROADMAP-INTEGRACIONES-SIGPAC-GAIACHAIN-AEMET.md) · [TraceChain-Compliance-2026.md](./TraceChain-Compliance-2026.md) · [DPIA-TraceChain-2026.md](./DPIA-TraceChain-2026.md) · [ROADMAP-Robotics-2026.md](./ROADMAP-Robotics-2026.md) · [ROADMAP-Neuromorphic-2026.md](./ROADMAP-Neuromorphic-2026.md) · [ROADMAP-Scan3D-Print-2026.md](./ROADMAP-Scan3D-Print-2026.md) · [PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md](./PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md) · [PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md](./PRONTUARIO-MATRIZ-TRL-ACELERADORA-2026-2027.md) · [PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md](./PRONTUARIO-REFUERZO-SECRETS-VAULT-2026.md) · [PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md](../PRONTUARIO-MAESTRO-EXCELENCIA-SISTEMA-ANALISIS.md)

---

## 1. Capas ya trazables en el repo

| Capa | Evidencia en código / docs |
|------|----------------------------|
| Validación SIGPAC estructural | `backend/integrations/sigpac_validator.py` |
| Cruce parcela / capa local + mapping | `pei-001-sigpac/scripts/validate_sigpac.py` |
| Cifrado PQC | `backend/security/pq_crypto.py` |
| Registro cadena (auditoría) | `gaiachain_service.register_event_in_chain` + `POST /api/audit/register-event` |
| Digest informe PEI-001 | `pei-002-tracechain/register_sigpac_digest.py` |
| CI SIGPAC | `.github/workflows/sigpac-validation-pei001.yml` |
| CI PEI-002 / envelope | `.github/workflows/tracechain-pei002.yml` (`workflow_dispatch` + `workflow_run` PEI-001) |

### PEI-002 TraceChain (laboratorio vs producción)

- **Stub:** `pei-002-tracechain/api/` en puerto **8010**, `POST /api/pei-002/envelope` y `/api/pei-002/parcel`.
- **Producción:** `POST /api/audit/register-event` + `register_event_in_chain` (payload generado por `register_sigpac_digest.py`, `tokenId` entero).
- **Legal:** [DPIA-TraceChain-2026.md](./DPIA-TraceChain-2026.md) antes de registro por parcela con datos identificativos.

---

## 2. Iniciativas tipo “agente” (sin APIs inventadas)

| Concepto | Función | Próximo paso honesto |
|----------|---------|----------------------|
| **Auditoría legal asistida** | Chequeos documentales RD 903 / RGPD / PAC | Reglas y checklists en `docs/legal/` + revisión humana; **no** `legal_engine.py` en el clon hoy |
| **Trazabilidad cadena** | Ancla de informes | PEI-002 + JWT DPO; ampliar `details` según DPIA |
| **Seguridad reforzada** | PQC + políticas de secretos | Extender uso de `pq_crypto.py` y rotación documentada |
| **Automatización** | GDAL / PEI-001 / tests | Workflows existentes + ampliación de pruebas |
| **Gemelo / teledetección** | Simulación y riesgos | Roadmap hasta contrato PIX4D u otra fuente; **no** módulo `pix4d.py` en el árbol actual |
| **Robótica / señales** | PCM lab, GA, sellado PQC vía `pq_crypto` | `backend/integrations/robotics/` + [DPIA-Robotics-2026.md](./DPIA-Robotics-2026.md); ROS2/GNU Radio fuera del wheelhouse |

---

## 3. Lo que este roadmap **rechaza** como “ya implementado”

- Clientes HTTP a nodos etiquetados “GaiaChain 2.0” sin URL y ABI en despliegue.
- Registro on-chain desde CI sin Bearer y sin política de secretos.
- Contratos Solidity nuevos en el repo sin compilación, red y auditoría acordadas.

---

## 4. Hitos sugeridos (trimestre)

1. PEI-001 en piloto con `data/mapping.json` ajustado al shapefile real.  
2. PEI-002 en entorno staging con `CASTUO_AUDIT_*` y un `tokenId` de prueba.  
3. Revisión legal de campos enviados en `details` (minimización).  

---

*Documento orientativo; no certificación automática.*
