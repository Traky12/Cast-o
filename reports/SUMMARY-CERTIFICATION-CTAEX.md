# Resumen de certificación CASTUO-SYSTEM — CTAEX

Documento de apoyo para auditores y certificación (ISO 9001, ISO 27001, AEMPS, CTAEX).

## 1. Métricas de trazabilidad

- **Bandejas con identificación (tray_id):** 100% de bandejas operativas con identificador único.
- **Eventos en blockchain (GaiaChain):** Registro de datos IoT, lotes de microgreens, tratamientos de agua, certificados de producto y exportación, sincronización e-commerce y pedidos.
- **Precisión de sensores:** Objetivo ±2% (temp/humedad); calibración según procedimiento interno.
- **Cumplimiento de rutas (misiones drones):** Verificación de telemetría frente a ruta planificada (módulo de mensajería/drones).

## 2. Métricas de seguridad

- **Autenticación:** Control de acceso por roles; soporte para MFA y HSM en módulos de seguridad.
- **Transacciones blockchain:** Registro inmutable; sin fallos de firma en operaciones críticas.
- **Webhooks e-commerce:** Firma HMAC (Shopify, WooCommerce) para integridad de pedidos.

## 3. Cumplimiento normativo

- **RD 903/2025 (cannabis medicinal):** Trazabilidad y documentación gestionadas por módulos de compliance y producción.
- **ISO 9001 / ISO 22000:** Procedimientos documentados en manual de operaciones y guía de producción/certificación.
- **Exportación:** Certificados de producto y fitosanitarios generados y verificables vía API y GaiaChain.

## 4. Cómo generar evidencias

- **Informes de certificación (JSON):** Ejecutar `generate_certification_reports.py` (si existe en el proyecto) y usar los JSON en `reports/`.
- **Pruebas de endpoints:** `python tests/test_all_endpoints.py` — comprueba control ambiental, microgreens, agua, certificación y e-commerce.
- **Validación de certificados:** `python tests/validate_certificates.py` — flujo completo producto → exportación → verificación.
- **Logs y auditoría:** Usar el módulo de auditoría (AuditSystem) y exportar informes según procedimiento interno.

## 5. Referencias

- `docs/GUIA-PRODUCCION-CERTIFICACION.md` — Checklist y flujo de certificación.
- `docs/TECHNICAL-REPORT-CTAEX.md` — Arquitectura y especificaciones.
- `docs/OPERATIONS-MANUAL-CTAEX.md` — Operaciones y protocolos de emergencia.
