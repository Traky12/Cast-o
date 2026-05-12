#!/usr/bin/env python3
"""Luces LED: MQTT con intensidad opcional; PWM si hay RPi.GPIO."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_IOT = Path(__file__).resolve().parent
if str(_IOT) not in sys.path:
    sys.path.insert(0, str(_IOT))

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("pip install paho-mqtt", file=sys.stderr)
    raise

try:
    import RPi.GPIO as GPIO  # type: ignore[import-not-found]

    _HAS_GPIO = True
except ImportError:
    GPIO = None  # type: ignore[assignment]
    _HAS_GPIO = False

from mqtt_actuator_common import build_client, parse_zone_actuator_topic, publish_status


def main() -> None:
    led_id = os.getenv("CASTUO_LED_ID", "luz_led")
    pin = int(os.getenv("CASTUO_GPIO_PIN", "27"))
    host = os.getenv("CASTUO_MQTT_HOST", "127.0.0.1")
    port = int(os.getenv("CASTUO_MQTT_PORT", "1883"))
    user = os.getenv("CASTUO_MQTT_USER")
    pwd = os.getenv("CASTUO_MQTT_PASS")
    ca = os.getenv("CASTUO_MQTT_CA") or None

    pwm = None
    if _HAS_GPIO:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        pwm = GPIO.PWM(pin, 1000)
        pwm.start(0)

    client = build_client(f"led_{led_id}", user, pwd, ca)

    def on_connect(c: mqtt.Client, _u: object, _f: object, rc: int) -> None:
        print(f"MQTT rc={rc}")
        c.subscribe(f"zones/+/actuators/{led_id}")

    def on_message(c: mqtt.Client, _u: object, msg: mqtt.MQTTMessage) -> None:
        try:
            parsed = parse_zone_actuator_topic(msg.topic)
            if not parsed:
                return
            zone_id, aid = parsed
            if aid != led_id:
                return
            payload = json.loads(msg.payload.decode())
            state = payload.get("state")
            if state is None:
                return
            intensity = float(payload.get("intensity", 100 if state else 0))
            duty = max(0.0, min(100.0, intensity if state else 0.0))
            if pwm:
                pwm.ChangeDutyCycle(duty)
            else:
                print(f"[simulación] LED duty={duty}%")
            publish_status(
                c,
                zone_id,
                led_id,
                {"status": "active" if state else "inactive", "intensity": duty, "timestamp": int(time.time())},
            )
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, 60)
    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        if pwm:
            pwm.stop()
        if _HAS_GPIO:
            GPIO.cleanup()


if __name__ == "__main__":
    main()
