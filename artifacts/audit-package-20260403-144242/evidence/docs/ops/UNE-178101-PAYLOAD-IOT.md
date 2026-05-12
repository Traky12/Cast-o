# Especificacion tecnica de payload IoT (alineacion UNE 178101-1:2020)

Version: 1.0

## Objetivo
Definir un payload interoperable, versionado y validable para telemetria agricola.

## Estructura recomendada

```json
{
  "schema_version": "1.0",
  "sensor_id": "greenhouse-001",
  "timestamp": "2026-04-03T10:30:00Z",
  "source": "mqtt-bridge",
  "readings": {
    "temperature_c": 22.4,
    "humidity_pct": 61.2,
    "ph": 6.1,
    "ec_ms_cm": 2.4,
    "vpd_kpa": 1.2
  },
  "quality": {
    "validated": true,
    "validator": "iso8000-basic-ranges"
  }
}
```

## Reglas minimas
- sensor_id obligatorio.
- timestamp en ISO 8601 UTC.
- readings como objeto de pares clave-valor.
- pH en rango [0, 14].
- EC en rango [0, 20] mS/cm.
- VPD en rango [0, 5] kPa.

## Compatibilidad
Para mantener retrocompatibilidad, el backend acepta payloads legacy sin `schema_version`, pero se recomienda enviar siempre versionado.
