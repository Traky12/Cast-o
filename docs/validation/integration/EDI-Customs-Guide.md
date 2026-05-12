# Guía EDI Aduanas UE — DUNS y Documentación Exportación

**Objetivo**: **100%** de lotes exportables con documentación aduanera automática. Conector EDI para DUNS (Data Universal Numbering System) y validación con Aduanas UE.

---

## Alcance

- Identificación de empresas: **DUNS** (Dun & Bradstreet) para partners y destinatarios.
- Documentación: facturas, albaranes, certificados fitosanitarios/AEMPS/GlobalGAP en formato electrónico (EDI o estructurado).
- Integración con ventanillas aduaneras UE cuando esté disponible (ej. AES, ATLAS según país).

---

## Implementación

- Backend: módulo de generación de documentos de exportación (plantillas + datos de lote).
- Conector EDI para intercambio con agentes o sistemas aduaneros (mensajes según estándar del país/UE).
- Validar con un agente de aduanas o autoridad de prueba en un piloto.

---

## Métrica de éxito

- **100%** de lotes marcados como exportables con documentación aduanera generada/entregada de forma automática (o semiautomática con un solo clic).
