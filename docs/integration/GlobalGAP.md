# Integración GlobalGAP

**Objetivo**: Certificaciones para exportación (nivel 2 como mínimo). Generación de certificados y documentación EDI cuando aplique.

---

## APIs y flujos

- **REST**: `POST /microgreens/certify_globalgap` — genera certificado (PDF + QR) usando `backend/services/certification.py`.
- **Servicio**: `backend/services/globalgap.py` — envío a API GlobalGAP cuando `GLOBALGAP_API_KEY` esté configurado.
- **EDI**: Ver [EDI-Guide.md](../validation/integration/EDI-Guide.md) para documentación de exportación.

---

## Checklist digital

- Ver [GlobalGAP-Checklist.md](../validation/traceability/GlobalGAP-Checklist.md) para puntos de control y trazabilidad.
