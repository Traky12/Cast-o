# Plan de Certificación GlobalGAP — Checklist Digital

**Objetivo**: Certificación para exportación (mínimo nivel 2). Auditoría de 3 cultivos piloto (microgreens).

---

## Acciones

1. **Contratar auditor GlobalGAP** (empresa acreditada).
2. **Implementar checklists digitales** en la app (por punto de control GlobalGAP).
3. **Pilotos**: 3 cultivos (variedades a definir) con trazabilidad completa (GaiaChain + LIMS).
4. **Validar** con APIs de prueba GlobalGAP cuando estén disponibles.

---

## Puntos de control (resumen)

| Área | Punto de control | Implementación en sistema |
|------|------------------|----------------------------|
| Trazabilidad | 1. Registro de lotes | Sí (cannabis_batches, microgreens_batches) |
| Trazabilidad | 2. Eventos EPCIS | Objetivo EPCIS 2.0 + GS1 Digital Link |
| Calidad | 3. Análisis laboratorio | LIMS sync, lab_results en BD |
| Medio ambiente | 4. Datos ambientales | Sensores IoT (temperatura, humedad, pH, EC) |
| Documentación | 5. Certificados exportables | PDF + QR (certification.py), GlobalGAP endpoint |

---

## Documentos relacionados

- Conector EDI para GlobalGAP: `docs/validation/integration/EDI-Guide.md`
- Servicio GlobalGAP: `backend/services/globalgap.py`
