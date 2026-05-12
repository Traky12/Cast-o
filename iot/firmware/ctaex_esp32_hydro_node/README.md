# CTAEX ESP32 — nodo hidropónico (MQTT → CASTÚO)

## Dependencias (Arduino IDE / PlatformIO)

- `PubSubClient`
- `ArduinoJson` (v6+)
- `DHT sensor library` (Adafruit)
- `BH1750` (Christopher Laws)

## Pines (ajustar a tu PCB)

| Señal | GPIO típico ESP32 |
|--------|-------------------|
| DHT22 | 4 |
| I2C SDA/SCL (BH1750) | 21 / 22 |
| pH analog | 34 (ADC1) |
| EC analog | 35 (ADC1) |
| Relé riego | 25 |
| MH-Z19 RX/TX | 16 / 17 (Serial2) |
| ORP (módulo analógico) | 36 (ADC1) |

## Secretos

Definir en `secrets.h` (no versionar) o `-D` en PlatformIO:

```cpp
#define WIFI_SSID "..."
#define WIFI_PASS "..."
#define MQTT_HOST "192.168.x.x"
#define MQTT_PORT 1883
#define MQTT_USER "ctaex"
#define MQTT_PASS "..."
#define BED_ID "B01"
```

## MH-Z19

Precalentamiento ~3 min; lecturas UART 9600 8N1. Consultar datasheet para autocalibración ABC.
