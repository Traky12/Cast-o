#!/usr/bin/env python3
"""
read_sensors.py

Lectura de sensores reales con fallback soberano.
Si no existe un origen de datos configurado, devuelve un payload stub
para que los flujos de auditoría/monetización no se rompan.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.request import Request, urlopen


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_sensors() -> Dict[str, Any]:
    """
    Retorna un diccionario normalizado:
      - timestamp
      - sensors: {temperature_c, humidity_pct, soil_moisture_pct, ...}
      - source: "env" | "http" | "stub"
    """
    # Fuente HTTP opcional (air-gapped / endpoint interno)
    sensors_url = os.getenv("CASTUO_SENSORS_URL", "").strip()
    if sensors_url:
        try:
            req = Request(sensors_url, headers={"User-Agent": "castuo-sensors-agent"})
            with urlopen(req, timeout=8) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            return {"timestamp": _now_iso(), "sensors": payload, "source": "http"}
        except Exception:
            # Si falla, no interrumpimos el ecosistema.
            pass

    # Fuente por variables de entorno opcional
    temp = os.getenv("CASTUO_SENSOR_TEMPERATURE_C", "").strip()
    hum = os.getenv("CASTUO_SENSOR_HUMIDITY_PCT", "").strip()
    soil = os.getenv("CASTUO_SENSOR_SOIL_MOISTURE_PCT", "").strip()
    if temp or hum or soil:
        sensors: Dict[str, Any] = {}
        if temp:
            sensors["temperature_c"] = float(temp)
        if hum:
            sensors["humidity_pct"] = float(hum)
        if soil:
            sensors["soil_moisture_pct"] = float(soil)
        return {"timestamp": _now_iso(), "sensors": sensors, "source": "env"}

    # Fallback stub (resiliencia operativa)
    return {
        "timestamp": _now_iso(),
        "sensors": {
            "temperature_c": 0.0,
            "humidity_pct": 0.0,
            "soil_moisture_pct": 0.0,
        },
        "source": "stub",
    }


if __name__ == "__main__":
    out = read_sensors()
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()

