# Guía EDI — GlobalGAP (EDI X12 / UN/EDIFACT)

**Objetivo**: Conector estándar para intercambio con GlobalGAP y otros sistemas (EDI).

---

## Opciones técnicas

- **python-edi** (Python): Parsing y generación de mensajes EDI.
- **Formato**: EDI X12 o UN/EDIFACT según requisito del certificador.
- **Pruebas**: Con APIs de prueba GlobalGAP cuando estén disponibles.

---

## Flujo propuesto

1. **Exportación**: Desde CASTÚO (lote certificado) → generar mensaje EDI (ej: 856 Advance Ship Notice) → enviar a GlobalGAP / distribuidor.
2. **Importación**: Recibir EDI de distribuidor → parsear → actualizar estado en BD y notificar.

---

## Ubicación del código

- Conector EDI: `backend/services/edi_connector.py` (a implementar).
- Integración GlobalGAP actual: `backend/services/globalgap.py` (REST). El EDI será una capa adicional para clientes que exijan EDI.

---

## Documentación de referencia

- GS1 EDI: estándares GS1 para mensajes de negocio.
- GlobalGAP: requisitos de mensajería para certificación.
