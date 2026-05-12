# Integración CTAEX LIMS

**Objetivo**: Sincronización bidireccional con el sistema de laboratorio de CTAEX (datos THC/CBD, resultados de análisis).

---

## Protocolos

- **API REST**: `POST /sync/lims` para recepción de resultados de laboratorio (batch_id, thc, cbd, terpenes, heavy_metals, pesticides, lab_technician).
- **EDI X12**: Opcional para intercambio estructurado con sistemas legacy.
- **Webhooks**: Notificación a CTAEX tras registro en GaiaChain (confirmación y tx_hash).

---

## Validación

- THC ≤ 0,3 % (RD 903/2025). Rechazar lote si se supera.
- Calibración de datos si aplica: `backend/services/calibration.py`.
- Registro en GaiaChain tras validación: `backend/services/gaia_chain.py`.

---

## Referencias

- [LIMS-Automation.md](LIMS-Automation.md)
- Backend: `backend/routers/lims_sync.py`
