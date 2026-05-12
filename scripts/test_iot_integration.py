# -*- coding: utf-8 -*-
"""
Prueba de integración IoT: envío de datos de bandeja al backend (HTTP).
Opcional: envío por MQTT si paho-mqtt está instalado y el broker corre.
Ejecutar desde la raíz: python scripts/test_iot_integration.py
"""
from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import time
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

try:
    import paho.mqtt.client as mqtt
    import json as _json
    _MQTT_AVAILABLE = True
except ImportError:
    mqtt = None
    _MQTT_AVAILABLE = False


BASE_URL = "http://localhost:8000"
IOT_DATA_URL = BASE_URL + "/api/iot/data"
IOT_AUTH_URL = BASE_URL + "/api/iot/auth/iot"


def test_iot_http():
    """Envía datos de sensores vía HTTP al endpoint /api/iot/data."""
    if not requests:
        print("requests no instalado; omitiendo prueba HTTP.")
        return
    print("Obteniendo session_id (auth IoT)...")
    try:
        r_auth = requests.post(
            IOT_AUTH_URL,
            json={
                "tray_id": "CASTUO-TRAY-001",
                "device_type": "raspberry_pi",
                "location": "Invernadero Piloto, Caceres",
            },
            timeout=5,
        )
        r_auth.raise_for_status()
        session_id = r_auth.json().get("session_id", "test-session-123")
        print("  session_id:", session_id)
    except Exception as e:
        print("  (Backend no disponible, usando session de prueba):", e)
        session_id = "test-session-123"

    print("\nEnviando 3 lecturas de sensores a /api/iot/data...")
    for i in range(3):
        payload = {
            "session_id": session_id,
            "tray_id": "CASTUO-TRAY-001",
            "timestamp": datetime.now().isoformat(),
            "sensors": {
                "temperature": 22 + (i * 0.5),
                "humidity": 65 - (i * 1),
                "co2": 400 + (i * 20),
                "ec": 1.2 + (i * 0.1),
                "ph": 6.0 - (i * 0.05),
            },
            "metadata": {
                "location": "Invernadero Piloto, Caceres",
                "crop_type": "Cannabis medicinal (Futura 75)",
                "growth_stage": "Vegetativo",
            },
        }
        try:
            r = requests.post(IOT_DATA_URL, json=payload, timeout=5)
            r.raise_for_status()
            data = r.json()
            print("  Iteracion %d: status=%s gaiachain_tx=%s commands=%s" % (
                i + 1,
                data.get("status"),
                data.get("gaiachain_tx", "")[:12] + "..." if data.get("gaiachain_tx") else "N/A",
                list(data.get("commands", {}).keys()),
            ))
        except Exception as e:
            print("  Iteracion %d: Error - %s" % (i + 1, e))
        time.sleep(1)
    print("OK: Prueba HTTP completada.")


def test_iot_mqtt():
    """Opcional: publicar en MQTT castuo/data/CASTUO-TRAY-001 (requiere broker)."""
    if not _MQTT_AVAILABLE:
        print("paho-mqtt no instalado; omitiendo prueba MQTT.")
        return
    client = mqtt.Client(client_id="test-iot-client")
    client.username_pw_set("castuo_iot", "castuo_password_123")
    try:
        client.connect("localhost", 1883, 60)
    except Exception as e:
        print("Broker MQTT no disponible:", e)
        return
    tray_id = "CASTUO-TRAY-001"
    topic = "castuo/data/" + tray_id
    payload = {
        "session_id": "test-session-123",
        "tray_id": tray_id,
        "timestamp": datetime.now().isoformat(),
        "sensors": {"temperature": 22.5, "humidity": 65, "co2": 500, "ec": 1.4, "ph": 5.9},
        "metadata": {"location": "Caceres", "growth_stage": "Vegetativo"},
    }
    client.publish(topic, _json.dumps(payload), qos=1)
    print("Publicado 1 mensaje en %s" % topic)
    client.disconnect()
    print("OK: Prueba MQTT completada.")


if __name__ == "__main__":
    test_iot_http()
    if _MQTT_AVAILABLE:
        test_iot_mqtt()
