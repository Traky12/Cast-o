# Guía SAP Avanzada — Integración con CTAEX (PyRFC)

**Objetivo**: Conector SAP validado con datos reales. **0 errores** en sincronización de datos.

---

## Tecnología

- **PyRFC**: Conector Python para SAP NetWeaver (RFC/BAPI).
- **Uso**: Sincronización bidireccional de lotes, certificaciones y datos maestros entre CASTÚO y ERP de CTAEX.

---

## Validación

- Contratar consultor SAP para revisar llamadas BAPI y manejo de errores.
- Pruebas con datos reales (entorno de aceptación CTAEX) antes de producción.
- Logs y reintentos para fallos de red o SAP no disponible.

---

## Métrica de éxito

- **0** errores no recuperables en sincronización en ventana de aceptación (ej. 1 semana de pruebas).
