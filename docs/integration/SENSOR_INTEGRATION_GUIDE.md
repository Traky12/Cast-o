# Integración de sensores reales (MQTT / REST)

**Versión:** 1.0

## 1. Protocolos

| Protocolo | Puerto típico | Uso |
|-----------|-----------------|-----|
| MQTT | 1883 (lab) / 8883 (TLS) | ESP32, Raspberry Pi |
| REST | HTTPS / API gateway | Sistemas legados |
| Modbus TCP | 502 | PLC (vía VPN) |

## 2. Ingesta REST (backend)

```bash
curl -s -X POST "http://127.0.0.1:8000/api/sensors/zone_cannabis_1/readings" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sensor_id\":\"temp_1\",\"value\":23.1,\"unit\":\"°C\"}"
```

Con `AUTH_DISABLED=true` en laboratorio, el Bearer puede omitirse según política (no recomendado en exposición pública).

## 3. MQTT

Publicar en tópicos coherentes con actuadores edge, por ejemplo:

- `zones/{zone_id}/sensors/{sensor_id}` con JSON `{"value", "unit", "timestamp"}`.

Cliente de ejemplo: `scripts/iot/mqtt_client.py`.

## 4. DHT22 + ESP32

Ejemplo de bucle (sustituir credenciales y broker):

```cpp
// Pseudocódigo: WiFi + PubSubClient + DHT
float t = dht.readTemperature();
float h = dht.readHumidity();
client.publish("zones/zone_demo/sensors/dht22_1/temperatura", String(t).c_str());
```

## 5. Espectrómetro / I2C

En Raspberry Pi, aislar lectura I2C y publicación MQTT en un servicio systemd; no bloquear el hilo MQTT con sleeps largos.

## 6. Seguridad

- TLS en broker en producción.
- Usuarios/contraseñas MQTT por dispositivo; rotación periódica.
- No embebáis secretos en firmware sin hueco de rotación (OTA o provisionamiento seguro).

## 7. Referencias en repo

- `docker/remote-access/mosquitto/`
- `docs/deploy/ARQUITECTURA-ACCESO-REMOTO-CTAEX.md`
- `backend/routers/hydro_remote.py`
