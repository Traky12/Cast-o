# Refuerzo de Riesgos/Debilidades — Seguridad (ISO 27001 + ENS Alto)

| Riesgo/Debilidad | Acción de Refuerzo | Responsable | Plazo | Métrica de Éxito | Documentación |
|------------------|--------------------|-------------|--------|------------------|---------------|
| Falta de HSM para gestión de claves | Contratar HSM (Thales o AWS CloudHSM). Migración gradual de claves. | Seguridad | 3 meses | 100% claves críticas en HSM | [Guía HSM](../../security/HSM-Guide.md) |
| Pentesting semestral no implementado | Contratar pentesting S21sec (junio y diciembre 2026). Corregir en <7 días. | Seguridad | 1 mes | 0 vulnerabilidades críticas en informe final | Informe Pentesting |
| Falta de DPO interno | Contratar DPO certificado. Registrar actividades en AEPD. | Legal Team | 1 mes | DPO nombrado y registrado en AEPD | Contrato DPO |
| Logs de auditoría no centralizados | ELK Stack (Elasticsearch, Logstash, Kibana). Retención 5 años. | DevOps | 2 meses | 100% logs centralizados y buscables | [Guía ELK](../../security/ELK-Setup.md) |
