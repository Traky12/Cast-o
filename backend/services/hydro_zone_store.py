# -*- coding: utf-8 -*-
"""
Estado de zonas hidropónicas (laboratorio / CTAEX): memoria procesal hasta persistencia en BD.
Los actuadores físicos confirman en MQTT; aquí se registra intención y ventana de seguridad (duración máx).
"""
from __future__ import annotations

import threading
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

_MAX_DURATION_S = int(__import__("os").getenv("HYDRO_ACTUATOR_MAX_DURATION_S", "3600"))


def _now_ts() -> float:
    return time.time()


class ZoneManager:
    """Registro en memoria de zonas, lecturas y actuadores (sin sustituir PLC ni riego real)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._zones: Dict[str, Dict[str, Any]] = {}
        self._readings: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        self._timers: Dict[str, threading.Timer] = {}
        self._seed_demo()

    def _seed_demo(self) -> None:
        demo_actuators = {
            "valvula_agua": {"state": False, "last_change_ts": _now_ts(), "last_activation_ts": 0.0, "locked_until": 0.0, "priority": 2},
            "valvula_nutrientes": {"state": False, "last_change_ts": _now_ts(), "last_activation_ts": 0.0, "locked_until": 0.0, "priority": 2},
            "ventilador": {"state": False, "last_change_ts": _now_ts(), "last_activation_ts": 0.0, "locked_until": 0.0, "priority": 1},
            "luz_led": {"state": False, "intensity": 0.0, "last_change_ts": _now_ts(), "last_activation_ts": 0.0, "locked_until": 0.0, "priority": 1},
        }
        self._zones["zone_cannabis_1"] = {
            "id": "zone_cannabis_1",
            "nombre": "Sala demostración cannabis (lab)",
            "cultivo_tipo": "cannabis",
            "sensores": ["temp_1", "hum_1", "ph_1", "ec_1"],
            "actuadores": deepcopy(demo_actuators),
            "parametros_ideales": {
                "temperatura_c": 24.0,
                "humedad_pct": 55.0,
                "ph": 5.9,
                "ec_ms": 1.4,
            },
        }
        self._zones["zone_microgreens_1"] = {
            "id": "zone_microgreens_1",
            "nombre": "Microgreens piloto",
            "cultivo_tipo": "microgreens",
            "sensores": ["temp_1", "hum_1"],
            "actuadores": deepcopy(demo_actuators),
            "parametros_ideales": {
                "temperatura_c": 20.0,
                "humedad_pct": 58.0,
                "ph": 6.0,
                "ec_ms": 1.0,
            },
        }
        for zid, z in self._zones.items():
            self._readings.setdefault(zid, {})
            for sid in z["sensores"]:
                self._readings[zid].setdefault(sid, [])
                unit = "°C"
                val = 22.0 + hash(zid + sid) % 5
                if "hum" in sid:
                    unit, val = "%", 52.0
                elif "ph" in sid:
                    unit, val = "", 5.9
                elif "ec" in sid:
                    unit, val = "mS/cm", 1.2
                self._append_reading(zid, sid, val, unit)

    def _append_reading(self, zone_id: str, sensor_id: str, value: float, unit: str) -> None:
        self._readings[zone_id][sensor_id].append(
            {"timestamp": _now_ts(), "value": value, "unit": unit}
        )
        hist = self._readings[zone_id][sensor_id]
        if len(hist) > 5000:
            self._readings[zone_id][sensor_id] = hist[-2000:]

    def get_zone_status(self, zone_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            z = self._zones.get(zone_id)
            return deepcopy(z) if z else None

    def update_zone(self, zone_id: str, updated_data: Dict[str, Any]) -> None:
        with self._lock:
            if zone_id not in self._zones:
                raise ValueError(f"Zona {zone_id} no encontrada")
            if "parametros_ideales" in updated_data:
                self._zones[zone_id]["parametros_ideales"] = deepcopy(updated_data["parametros_ideales"])

    def update_ideal_parameter(self, zone_id: str, parameter: str, value: float) -> None:
        with self._lock:
            if zone_id not in self._zones:
                raise ValueError(f"Zona {zone_id} no encontrada")
            params = self._zones[zone_id].get("parametros_ideales") or {}
            if parameter not in params:
                raise ValueError(f"Parámetro no válido: {parameter}")
            params[parameter] = value
            self._zones[zone_id]["parametros_ideales"] = params

    def add_sensor_reading(self, zone_id: str, sensor_id: str, value: float, unit: str) -> None:
        with self._lock:
            if zone_id not in self._zones:
                raise ValueError(f"Zona {zone_id} no encontrada")
            if sensor_id not in self._zones[zone_id]["sensores"]:
                self._zones[zone_id]["sensores"].append(sensor_id)
            self._readings.setdefault(zone_id, {}).setdefault(sensor_id, [])
            self._append_reading(zone_id, sensor_id, value, unit)

    def get_readings(
        self, zone_id: str, sensor_id: Optional[str], limit: int
    ) -> Tuple[str, List[Dict[str, Any]]]:
        with self._lock:
            if zone_id not in self._zones:
                raise ValueError(f"Zona {zone_id} no encontrada")
            if sensor_id:
                rows = list(self._readings.get(zone_id, {}).get(sensor_id, []))
                rows = rows[-limit:]
                return sensor_id, rows
            merged: List[Dict[str, Any]] = []
            for sid, rows in self._readings.get(zone_id, {}).items():
                for r in rows[-limit:]:
                    merged.append({**r, "sensor_id": sid})
            merged.sort(key=lambda x: x["timestamp"])
            return "", merged[-limit:]

    def _cancel_timer(self, key: str) -> None:
        t = self._timers.pop(key, None)
        if t:
            t.cancel()

    def control_actuator(
        self,
        zone_id: str,
        actuator_id: str,
        state: bool,
        duration_s: int = 0,
        intensity: Optional[float] = None,
    ) -> Dict[str, Any]:
        duration_s = max(0, min(int(duration_s), _MAX_DURATION_S))
        with self._lock:
            if zone_id not in self._zones:
                raise ValueError(f"Zona {zone_id} no encontrada")
            acts = self._zones[zone_id]["actuadores"]
            if actuator_id not in acts:
                raise ValueError(f"Actuador {actuator_id} no registrado en la zona")
            timer_key = f"{zone_id}:{actuator_id}"
            self._cancel_timer(timer_key)
            acts[actuator_id]["state"] = bool(state)
            acts[actuator_id]["last_change_ts"] = _now_ts()
            if intensity is not None and actuator_id == "luz_led":
                acts[actuator_id]["intensity"] = max(0.0, min(100.0, float(intensity)))

        def _off() -> None:
            with self._lock:
                if zone_id not in self._zones:
                    return
                a = self._zones[zone_id]["actuadores"].get(actuator_id)
                if a:
                    a["state"] = False
                    a["last_change_ts"] = _now_ts()
            self._timers.pop(timer_key, None)

        if duration_s > 0 and state:
            timer = threading.Timer(float(duration_s), _off)
            self._timers[timer_key] = timer
            timer.daemon = True
            timer.start()

        return {
            "zone_id": zone_id,
            "actuator_id": actuator_id,
            "state": state,
            "duration_scheduled_s": duration_s if state and duration_s > 0 else 0,
            "timestamp": _now_ts(),
        }

    def emergency_stop(self, zone_id: str) -> Dict[str, Any]:
        with self._lock:
            if zone_id not in self._zones:
                raise ValueError(f"Zona {zone_id} no encontrada")
            keys = [k for k in self._timers if k.startswith(f"{zone_id}:")]
            for k in keys:
                self._cancel_timer(k)
            for aid, meta in self._zones[zone_id]["actuadores"].items():
                meta["state"] = False
                meta["last_change_ts"] = _now_ts()
                if "intensity" in meta:
                    meta["intensity"] = 0.0
        return {"zone_id": zone_id, "status": "all_off", "timestamp": _now_ts()}


_store = ZoneManager()


def get_zone_manager() -> ZoneManager:
    return _store
