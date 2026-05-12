#!/usr/bin/env python3
"""Publica eventos de auto-calibración PID por MQTT (desde salida Serial del Arduino)."""
import os
import re
import sys
import time
import json
import serial
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = "castu/extrusora/autotune"
SERIAL_PORT = os.environ.get("EXTRUSORA_SERIAL", "/dev/ttyACM0")
BAUD = 9600

RE_AUTOTUNE = re.compile(r"AUTOTUNE:Kp=([\d.]+),Ki=([\d.]+),Kd=([\d.]+)", re.I)
RE_PID_PARAMS = re.compile(r"Nuevos parámetros PID:\s*Kp[=:]?\s*([\d.]+).*Ki[=:]?\s*([\d.]+).*Kd[=:]?\s*([\d.]+)", re.S)


def on_connect(client, userdata, flags, rc):
    print("MQTT conectado para auto-calibración", flush=True)


def publish_autotune_status(client, kp, ki, kd):
    msg = f"Nuevos parámetros PID: Kp={kp:.3f}, Ki={ki:.3f}, Kd={kd:.3f}"
    client.publish(TOPIC, json.dumps({"kp": kp, "ki": ki, "kd": kd, "message": msg}))
    client.publish(TOPIC + "/message", msg)
    print(msg, flush=True)


def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.5)
    except Exception as e:
        print(f"Serial error: {e}", file=sys.stderr)
        return
    client = mqtt.Client()
    client.on_connect = on_connect
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"MQTT error: {e}", file=sys.stderr)
        ser.close()
        return
    client.loop_start()

    buffer = ""
    while True:
        try:
            if ser.in_waiting:
                buffer += ser.read(ser.in_waiting).decode("utf-8", errors="ignore")
            for line in buffer.split("\n"):
                line = line.strip()
                if not line:
                    continue
                m = RE_AUTOTUNE.search(line)
                if m:
                    kp, ki, kd = float(m.group(1)), float(m.group(2)), float(m.group(3))
                    publish_autotune_status(client, kp, ki, kd)
                else:
                    m2 = RE_PID_PARAMS.search(line)
                    if m2:
                        kp, ki, kd = float(m2.group(1)), float(m2.group(2)), float(m2.group(3))
                        publish_autotune_status(client, kp, ki, kd)
            if len(buffer) > 2048:
                buffer = buffer[-1024:]
        except serial.SerialException:
            break
        time.sleep(0.1)


if __name__ == "__main__":
    main()
