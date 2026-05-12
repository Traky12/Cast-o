#!/usr/bin/env python3
"""
CASTÚO-SYSTEM — Edge agent: conexión MQTT + heartbeat al backend.
Para despliegue en RPi/finca o como servicio en Hetzner (TRL7 IoT).
"""
import os
import time

def main():
    mqtt_broker = os.getenv("MQTT_BROKER", "mqtt")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    backend_url = os.getenv("BACKEND_URL", "http://backend:8000")

    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client(client_id="castuo-edge-1")
        client.connect(mqtt_broker, mqtt_port, 60)
        client.loop_start()
        print(f"Edge agent: MQTT connected to {mqtt_broker}:{mqtt_port}")
    except Exception as e:
        print(f"Edge agent: MQTT optional — {e}")

    while True:
        time.sleep(30)

if __name__ == "__main__":
    main()
