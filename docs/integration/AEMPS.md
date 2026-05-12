# Integración AEMPS

**Objetivo**: Certificación de lotes de cannabis medicinal según RD 903/2025 (THC < 0,3 %). Trazabilidad y registro en GaiaChain.

---

## Endpoints

- **Certificación**: `POST /cannabis/certify_aemps` — valida THC/CBD y envía solicitud (simulación o API real cuando exista).
- **Servicio**: `backend/services/aemps.py` — `request_certification`, `check_status`.

---

## Validación

- THC ≤ 0,3 % en todos los lotes (trigger en BD y validación en API).
- Datos de laboratorio (LIMS) asociados al lote.
- Registro en GaiaChain antes o después de certificación según flujo acordado.

---

## Documentación

- [AEMPS-Dossier-Template.md](../validation/traceability/AEMPS-Dossier-Template.md)
- [AEMPS-Checklist.md](../validation/traceability/AEMPS-Checklist.md)
