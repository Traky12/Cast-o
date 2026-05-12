# CASTUO-SYSTEM™ | Integración Odoo (CRM/ERP/LEGAL)

Este directorio agrupa notas de integración entre Odoo (CRM/ERP) y el resto del stack CASTUO:

- **Backend FastAPI** (`backend/`): métricas drones/sensores, Sabionda, etc.
- **Trazabilidad EPCIS**: `docker-compose.jeremie.yml` (API + OpenEPCIS) y/o `docker-compose.odoo-erp-legal.yml` (OpenEPCIS).
- **Documentación legal**: `docs/COMPLIANCE-LEGAL.md`, `docs/LEGAL-SPAIN.md`, `docs/LEGAL-EUROPE.md`.

## Módulo Odoo

El módulo Odoo se encuentra en:

`custom-addons/castu_system/`

Incluye modelos base para:

- Granjas
- Licencias (RD 244/2019)
- Eventos EPCIS
- Campos BioCoin/Git en facturas

## Próximos pasos recomendados

- Reemplazar los stubs de `biocoin_tx` por una integración real (Polygon/Ethereum).
- Implementar `action_send_to_epcis` para enviar eventos al servicio `openepcis`.
- Generar Facturae desde `templates/legal/facturae.xml` y enviar a SII/FACe.

