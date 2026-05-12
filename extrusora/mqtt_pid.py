#!/usr/bin/env python3
"""
Bridge MQTT para control PID remoto de la extrusora.
Suscribe: castu/extrusora/pid/command (JSON: set_temp, set_pid, autotune).
Publica: castu/extrusora/pid/telemetry (JSON: boquilla, camara, pid_output, setpoint).
"""
import json
import os
import re
import time
import serial
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
SERIAL_PORT = os.environ.get("EXTRUSORA_SERIAL", "/dev/ttyACM0")
BAUD = 9600
TOPIC_CMD = "castu/extrusora/pid/command"
TOPIC_TELEMETRY = "castu/extrusora/pid/telemetry"

ser = None
client = None

RE_LINE = re.compile(
    r"Boquilla:([\d.]+),\s*Camara:([\d.]+),\s*PID Output:([\d.]+),\s*Setpoint:([\d.]+)"
)


def on_connect(c, userdata, flags, rc):
    c.subscribe(TOPIC_CMD)


def on_message(c, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        t = payload.get("type")
        if t == "set_temp":
            ser.write(f"SET_TEMP {payload['value']}\n".encode())
        elif t == "set_pid":
            ser.write(
                f"SET_PID {payload['kp']} {payload['ki']} {payload['kd']}\n".encode()
            )
        elif t == "autotune":
            ser.write(b"START_AUTOTUNE\n")
    except Exception as e:
        print("on_message error:", e)


def publish_telemetry():
    if ser.in_waiting == 0:
        return
    line = ser.readline().decode().strip()
    m = RE_LINE.match(line)
    if not m:
        return
    data = {
        "boquilla": float(m.group(1)),
        "camara": float(m.group(2)),
        "pid_output": float(m.group(3)),
        "setpoint": float(m.group(4)),
    }
    client.publish(TOPIC_TELEMETRY, json.dumps(data))


def main():
    global ser, client
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.1)
    except Exception as e:
        print(f"Serial error: {e}")
        return
    time.sleep(2)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"MQTT error: {e}")
        ser.close()
        return
    client.loop_start()

    while True:
        try:
            publish_telemetry()
        except serial.SerialException:
            break
        time.sleep(0.1)


if __name__ == "__main__":
    main()
