# Guía MQTT (dispositivos)

**Versión:** 1.0

## Parámetros típicos (laboratorio)

| Parámetro | Valor ejemplo |
|-----------|----------------|
| Host | IP o DNS del servidor (o `localhost` en desarrollo) |
| Puerto | `1883` (plantilla por defecto) o `8883` con TLS |
| Usuario / contraseña | Configurar según `mosquitto.tls.conf.example` y `mosquitto_passwd` |
| TLS | Recomendado en producción; montar `ca.crt` en el dispositivo |

## Cliente Python de ejemplo

```bash
pip install paho-mqtt
```

```bash
set CASTUO_MQTT_HOST=127.0.0.1
set CASTUO_MQTT_PORT=1883
python scripts/iot/mqtt_client.py
```

Con TLS (8883), definir `CASTUO_MQTT_CA` apuntando al fichero CA del broker.

## Temas sugeridos

- `zones/{zone_id}/sensors/{sensor_id}` — telemetría
- `zones/{zone_id}/actuators/{actuator_id}` — comandos (definir ACL en broker para producción)

## Referencia en repo

- `docker/remote-access/mosquitto/`
- `iot/docker-compose.mqtt.yml`
