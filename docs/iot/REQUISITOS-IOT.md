# Requisitos para IoT real en explotación (futuro)

**Impacto hídrico y de biocidas:** sin datasheet, calibración y procedimiento de seguridad, el dato no protege el cultivo ni a las personas.

---

## 1. Hardware y campo

- Modelo, fabricante, rango, incertidumbre, mantenimiento y **trazabilidad de calibración** (pH/EC/ozono/riego).
- Protocolo industrial (Modbus, MQTT, SDI-12, etc.) según **documento del fabricante**, no según registros Modbus genéricos de un briefing.

## 2. Software en este repositorio (hoy)

- Broker y handler: `iot/docker-compose.mqtt.yml`, `iot/mqtt_handler.py`.
- API FastAPI: `backend/routers/iot.py`.
- Agentes edge: `iot/docker/edge_agent.py`, `iot/docker/edge_hidro.py`, `iot/raspberry_pi_agent.py`.
- TPM: `iot/tpm_verification/` (no confundir con `config/tpm_config.yaml`, **inexistente** en el árbol).

## 3. Cadena y auditoría

- Eventos on-chain: **`gaiachain_service.register_event_in_chain`** + API audit con JWT; el cliente en `backend/utils/gaia_chain.py` **no** debe usarse como atajo HTTP `register_event_in_chain` desde drivers de sensor.

## 4. Observabilidad

- Reglas Prometheus (`alert-rules-iot.yaml`, métricas `iot_*`) **solo** después de instrumentar exportadores reales.

## 5. Integraciones comerciales (p. ej. riego)

- Ver [REQUISITOS-NETAFIM-FUTURO.md](./REQUISITOS-NETAFIM-FUTURO.md).

---

**Relación:** [IOT-MARCO-REPOSITORIO.md](./IOT-MARCO-REPOSITORIO.md)
