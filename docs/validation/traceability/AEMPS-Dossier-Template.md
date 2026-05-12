# Dossier Técnico para Auditoría AEMPS

**Empresa**: CASTÚO Agrovoltaic Tech SL  
**Fecha**: [DD/MM/2026]

---

## 1. Descripción del sistema

- **Arquitectura**: API Gateway (FastAPI), microservicios Cannabis, Microgreens, Blockchain, IoT. Bases de datos PostgreSQL (cannabis_db, microgreens_db). GaiaChain para trazabilidad inmutable.
- **Flujos de trazabilidad**: Desde siembra (registro de lote) → cultivo (datos IoT) → análisis LIMS (THC/CBD) → certificación AEMPS → registro en blockchain → venta/expedición.

---

## 2. Datos de 5 lotes piloto

| Lote | THC (%) | CBD (%) | Blockchain TX | Certificación |
|------|---------|---------|---------------|---------------|
| MG-2026-01 | 0.28 | 12.5 | 0x... | Pendiente |
| MG-2026-02 | [ ] | [ ] | 0x... | [ ] |
| MG-2026-03 | [ ] | [ ] | 0x... | [ ] |
| MG-2026-04 | [ ] | [ ] | 0x... | [ ] |
| MG-2026-05 | [ ] | [ ] | 0x... | [ ] |

---

## 3. Cumplimiento normativo

- **RD 903/2025**: THC < 0,3 % en todos los lotes (validado por trigger en BD y endpoint `/cannabis/certify_aemps`).
- **Trazabilidad**: GaiaChain + GS1 Digital Link (objetivo EPCIS 2.0).
- **LIMS**: Integración con CTAEX (`POST /sync/lims`).

---

## 4. Procedimientos técnicos

- **Calibración de sensores**: `backend/services/calibration.py` (rangos UE).
- **Registro en blockchain**: `backend/services/gaia_chain.py` (modo degradado Redis).
- **Certificación AEMPS**: `backend/routers/cannabis.py` (certify_aemps), `backend/services/aemps.py`.

---

## 5. Documentación de apoyo

- Checklist de cumplimiento AEMPS: `docs/validation/traceability/AEMPS-Checklist.md`
- Plan de acción post-auditoría: según informe del auditor.
