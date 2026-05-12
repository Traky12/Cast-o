# Checklist de Cumplimiento AEMPS (RD 903/2025)

**Uso**: Verificación previa a auditoría o certificación de lotes de cannabis medicinal.

---

## Requisitos obligatorios

- [ ] **THC < 0,3 %** en todos los lotes (validado en BD y en endpoint de certificación).
- [ ] **Trazabilidad completa** desde semilla hasta venta (registros en GaiaChain o equivalente).
- [ ] **Integración con LIMS** de CTAEX operativa (`/sync/lims`).
- [ ] **Registros en blockchain** inmutables (GaiaChain); modo degradado con cola Redis documentado.
- [ ] **Datos de laboratorio** (THC, CBD, metales pesados, pesticidas) asociados a cada lote.
- [ ] **Código de centro autorizado** (cuando aplique) registrado y verificado.

---

## Documentación asociada

- Dossier técnico: `AEMPS-Dossier-Template.md`
- Procedimientos: `backend/services/calibration.py`, `backend/services/gaia_chain.py`, `backend/routers/cannabis.py`
