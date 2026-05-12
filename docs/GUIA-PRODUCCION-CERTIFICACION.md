# Guía producción y certificación — CASTUO-SYSTEM

Pasos para llevar el sistema de desarrollo a un entorno certificado en producción (ISO 9001, ISO 27001, AEMPS/RD 903/2025).

## 1. Configuración del entorno de producción

- **Docker:** Usar `docker/docker-compose.production.yml` (backend, frontend, PostgreSQL, MQTT, GaiaChain/Ganache, Prometheus, Grafana).
- **Variables:** Definir en `.env` o secrets: `DB_PASSWORD`, `MQTT_PASSWORD`, `GAIA_CHAIN_PRIVATE_KEY`, `SECRET_KEY`, `GAIA_CHAIN_CONTRACT_ADDRESS`.
- **Prometheus:** `docker/prometheus.yml` ya incluye scrape de backend, postgres y mqtt.
- **Mosquitto:** `docker/mosquitto.conf` con autenticación; crear `passwords.txt` con credenciales MQTT.

## 2. Pruebas de estrés y validación

- **Backend:** `locust -f tests/load_test_locust.py --host http://localhost:8000` (objetivo: 100–500 usuarios sin errores).
- **MQTT:** Script de publicación masiva (ej. 1000 mensajes) y monitoreo en Grafana (mensajes/s, latencia).
- **GaiaChain:** `python tests/stress_gaiachain.py` (objetivo: 5–10 tx/s en Ganache).

## 3. Documentación para certificación

- **Arquitectura técnica:** Diagrama de red, stack (FastAPI, PostgreSQL, GaiaChain, MQTT, HSM), módulos (ProfileManager, GaiaChainClient, IoTHandler, EuropeanDroneCoordinator, ComplianceManager, AuditSystem, ProductionSystem).
- **Métricas ISO 9001:** % bandejas con QR, % eventos en blockchain, precisión sensores, cumplimiento de rutas.
- **Métricas ISO 27001:** Intentos de login fallidos, tiempo de respuesta a incidentes, transacciones blockchain válidas.
- **AEMPS/RD 903/2025:** Cumplimiento por lote, documentación de auditoría, trazabilidad 100% desde semilla.

## 4. Documentos para auditoría

| Documento | Contenido | Cómo generarlo |
|-----------|-----------|-----------------|
| Arquitectura técnica | Red, stack, módulos | Template en docs/ARQUITECTURA-TECNICA.md |
| Registro de trazabilidad | Historial de lote | track_drone / SabiondaMasterInterface |
| Log de auditoría | Eventos de seguridad | AuditSystem.export_audit_report() |
| Cumplimiento normativo | ISO, RD 903/2025 | generate_certification_reports.py → compliance_certification.json |
| Informe de seguridad | Auth, cifrado, HSM | security_certification.json |
| Informe de producción | Métricas producción | production_certification.json |
| Pruebas de carga | Locust | locust -f tests/load_test_locust.py y guardar reporte |

## 5. Flujo de certificación

- **ISO 9001:** Manual de calidad, procedimientos operativos, trazabilidad 100%, auditoría interna y externa (AENOR/TÜV).
- **ISO 27001:** Controles A.5, A.9, A.12, A.16; pruebas de penetración; presentar security_certification.json y logs.
- **AEMPS:** Protocolo de cultivo, trazabilidad en GaiaChain, plan de seguridad; inspección in situ y licencia.

## 6. Checklist final

- [ ] Servidor (Hetzner/OVH) y DNS configurados
- [ ] PostgreSQL, MQTT, GaiaChain desplegados y accesibles
- [ ] Bandejas/sensores y Raspberry Pi enviando datos a /api/iot/data
- [ ] HSM (opcional) configurado para claves
- [ ] Pruebas de carga (Locust) sin errores
- [ ] Informes de certificación generados en reports/
- [ ] Solicitud a organismo certificador (ISO) y/o AEMPS
- [ ] Primera misión transfronteriza registrada en GaiaChain
