# Extrusora para bio-compuestos (CASTUO-SYSTEM™)

Prototipo Arduino Mega + sensores de temperatura + motor paso a paso + relé calentador.

## Esquema de conexiones

| Arduino Mega | Componente        | Observaciones        |
|--------------|-------------------|----------------------|
| 4, 5, 6      | MAX6675 (termopar K) | Boquilla             |
| 7            | DS18B20 (1-Wire)  | Cámara de mezcla     |
| 8, 9         | A4988 (STEP, DIR) | NEMA 17              |
| 10           | Relé              | Resistencia 220V 500W |
| SDA/SCL      | LCD 16x2 I2C (0x27) |                     |

## Materiales

- Arduino Mega 2560
- MAX6675 + termopar tipo K
- DS18B20 (precisión ±0.5°C)
- NEMA 17 (1.7A, 1.8°/paso) + A4988
- Resistencia calentadora 220V 500W + relé 220V
- Tornillo extrusor acero inox, paso 1.75 mm; boquilla 0.4 mm
- LCD 16x2 I2C; fuente 12V/5A

## Firmware

1. Instalar librerías (Arduino IDE): MAX6675, DallasTemperature, AccelStepper, LiquidCrystal I2C.
2. Subir `extrusora.ino` al Arduino Mega.
3. Comandos por Serial: `SET_TEMP 200`, `START_EXTRUSION`, `STOP_EXTRUSION`.

## Bridge MQTT (Raspberry Pi)

```bash
pip install paho-mqtt pyserial
export MQTT_BROKER=mqtt.castu-system.com
export EXTRUSORA_SERIAL=/dev/ttyACM0
python mqtt_integration.py
```

- Publica: `castu/extrusora/temp/boquilla`, `castu/extrusora/temp/camara`, `castu/extrusora/heat`.
- Suscrito a: `castu/extrusora/command` (SET_TEMP, START_EXTRUSION, STOP_EXTRUSION).

## Métricas Prometheus

Para que Grafana muestre datos, el backend (o un collector) debe exponer métricas desde MQTT, por ejemplo:

- `castu_extrusora_temp{sensor="boquilla|camara"}`
- `castu_extrusora_heat`
- `castu_extrusora_motor_speed`
- `castu_extrusora_power_consumption`

Importar el dashboard desde `grafana_extrusora_dashboard.json`.
