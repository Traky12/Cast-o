# Configuración ELK Stack — Logs de Auditoría

**Objetivo**: Logs centralizados (Elasticsearch, Logstash, Kibana) con retención de **5 años**.

---

## Componentes

- **Elasticsearch**: Almacenamiento e índice de logs (quién, qué, cuándo).
- **Logstash**: Ingesta desde backend (FastAPI), PostgreSQL, GaiaChain, MQTT.
- **Kibana**: Consultas, dashboards y alertas.

---

## Retención

- **5 años** para logs de auditoría (cumplimiento normativo y ISO 27001).
- Política de rotación/archivo según tamaño y coste.

---

## Integración

- Backend: enviar logs estructurados (JSON) a Logstash (TCP/UDP o Beats).
- Formato: `timestamp`, `user_id`, `action`, `resource`, `result`, `ip`.

---

## Referencias

- PSI: `docs/validation/security/PSI-ISO27001.md`
