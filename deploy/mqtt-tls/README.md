# Mosquitto MQTT con TLS (Castúo)

**Checklist operativo mínimo:** [../MQTT-TLS-CHECKLIST-MINIMO.md](../MQTT-TLS-CHECKLIST-MINIMO.md)

## Compose

- Desde `deploy/`: `docker compose -f docker-compose.mqtt.yml up -d`
- Desde la raíz del repo: `docker compose -f docker-compose.mqtt.yml up -d` (el fichero raíz incluye el de `deploy/`)

## Orden recomendado

1. **Certificados**

   ```bash
   chmod +x deploy/mqtt-tls/scripts/gen-certs.sh
   MQTT_CN=mqtt.tu-dominio.example ./deploy/mqtt-tls/scripts/gen-certs.sh
   ```

2. **passwd**

   ```bash
   cp deploy/mqtt-tls/scripts/init-passwd.example.sh deploy/mqtt-tls/scripts/init-passwd.sh
   # export CASTUO_MQTT_ADMIN_PASS=… CASTUO_MQTT_ORP_PASS=… (etc., ver cabecera del script)
   ./deploy/mqtt-tls/scripts/init-passwd.sh
   ```

3. **Arranque**

   ```bash
   cd deploy && docker compose -f docker-compose.mqtt.yml up -d && docker logs mosquitto-tls
   ```

4. **Prueba TLS** (8883, sin mTLS por defecto)

   ```bash
   mosquitto_pub -h 127.0.0.1 -p 8883 -t castuo/water/sensor/orp -m "620" \
     --cafile deploy/mqtt-tls/mosquitto/certs/ca.crt \
     -u sensor_orp -P "$CASTUO_MQTT_ORP_PASS" \
     --tls-version tlsv1.2
   ```

## Seguridad

- **1883** en el compose del host queda en `127.0.0.1`; no exponer plano a Internet.
- **UFW:** ver checklist mínimo.
- **mTLS:** `mosquitto/config/mosquitto.conf.mtls.example` y `esp32/mqtt_tls.example.cpp`.

## n8n

Broker `mqtts://host:8883` (o `ssl://`), usuario `n8n_system`, CA del servidor. Workflow: `n8n/workflows/castuo_n8n_water_mqtt_analysis.json`.
