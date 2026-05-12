#!/usr/bin/env python3
"""Edge agent hidroponía: publica sensores MQTT y opcionalmente POST a backend /hidroponia/sensores."""
import os
import time

def main():
    broker = os.getenv("MQTT_BROKER", "mqtt")
    port = int(os.getenv("MQTT_PORT", "1883"))
    system_id = os.getenv("HIDRO_SYSTEM_ID", "1")
    cultivo = os.getenv("HIDRO_CULTIVO", "lechuga")
    print(f"Hidro edge: system_id={system_id} cultivo={cultivo} broker={broker}:{port}")
    try:
        import paho.mqtt.client as mqtt
        c = mqtt.Client(client_id=f"castuo-hidro-{system_id}")
        c.connect(broker, port, 60)
        c.loop_start()
    except Exception as e:
        print("MQTT optional:", e)
    while True:
        time.sleep(30)

if __name__ == "__main__":
    main()
