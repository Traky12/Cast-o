# Plan de Contingencia AEMPS/GlobalGAP — Barreras v6.1

**Objetivo**: Si AEMPS o GlobalGAP no están disponibles, modo degradado con últimos datos válidos de LIMS CTAEX; notificación a auditores externos (ej. SGS); registro en GaiaChain.

---

## Triggers

- Indisponibilidad de API AEMPS (timeout o 5xx) durante ventana definida (ej. 5 min).
- Indisponibilidad de API GlobalGAP o de envío de certificaciones durante ventana similar.

---

## Acciones

1. **Modo degradado**: Usar últimos datos válidos de LIMS CTAEX para continuar flujos internos (sin emitir certificado oficial hasta restablecimiento).
2. **Notificación**: Avisar a auditores externos (SGS u otro según contrato) y a CTAEX.
3. **Registro en GaiaChain**: Transacción con `action: "aemps_globalgap_contingency"`, hora del fallo, datos usados como backup (hash o referencia, sin PII), firma del responsable CASTÚO.
4. **Restablecimiento**: Cuando AEMPS/GlobalGAP vuelvan, sincronizar y emitir certificados pendientes; actualizar registro en GaiaChain.

---

## Responsable

Legal Team + Backend Team. Revisión trimestral del plan.
