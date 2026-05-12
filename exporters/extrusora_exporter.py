#!/usr/bin/env python3
"""
Exporter Prometheus para la extrusora CASTUO.
Expone: temperatura boquilla/cámara, setpoint, salida PID, velocidad motor.
Lee desde MQTT (castu/extrusora/pid/telemetry) o desde Serial.
"""
import json
import os
import re
import time
from prometheus_client import start_http_server, Gauge, Counter

PORT = int(os.environ.get("EXTRUSORA_EXPORTER_PORT", "9100"))
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
TOPIC_TELEMETRY = "castu/extrusora/pid/telemetry"
SERIAL_PORT = os.environ.get("EXTRUSORA_SERIAL", "/dev/ttyACM0")
BAUD = 9600

RE_LINE = re.compile(
    r"Boquilla:([\d.]+),\s*Camara:([\d.]+),\s*PID Output:([\d.]+),\s*Setpoint:([\d.]+)"
)

temp_boquilla = Gauge("castu_extrusora_temp", "Temperatura (°C)", ["sensor"])
temp_camara = Gauge("castu_extrusora_camara_temp", "Temperatura cámara de mezcla (°C)")
pid_output = Gauge("castu_extrusora_pid_output", "Salida del PID (PWM)")
setpoint = Gauge("castu_extrusora_setpoint", "Temperatura objetivo (°C)")
pid_kp = Gauge("castu_extrusora_pid_kp", "Ganancia Kp")
pid_ki = Gauge("castu_extrusora_pid_ki", "Ganancia Ki")
pid_kd = Gauge("castu_extrusora_pid_kd", "Ganancia Kd")
motor_speed = Gauge("castu_extrusora_motor_speed", "Velocidad motor (pasos/s)")
energy_consumption = Counter("castu_extrusora_energy_consumption_total", "Consumo energético (kWh)")
production_kg = Counter("castu_extrusora_production_kg_total", "kg producidos", ["material_type"])


def update_from_mqtt(payload_bytes):
    try:
        data = json.loads(payload_bytes.decode())
        temp_boquilla.labels(sensor="boquilla").set(float(data.get("boquilla", 0)))
        temp_camara.set(float(data.get("camara", 0)))
        pid_output.set(float(data.get("pid_output", 0)))
        setpoint.set(float(data.get("setpoint", 0)))
    except Exception:
        pass


def update_from_serial_line(line):
    m = RE_LINE.match(line)
    if not m:
        return
    temp_boquilla.labels(sensor="boquilla").set(float(m.group(1)))
    temp_camara.set(float(m.group(2)))
    pid_output.set(float(m.group(3)))
    setpoint.set(float(m.group(4)))


def run_mqtt():
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        return False
    client = mqtt.Client()
    client.on_connect = lambda c, u, f, r: c.subscribe(TOPIC_TELEMETRY)
    client.on_message = lambda c, u, msg: update_from_mqtt(msg.payload)
    try:
        client.connect(MQTT_BROKER, 1883, 60)
    except Exception:
        return False
    client.loop_start()
    while True:
        time.sleep(60)


def run_serial():
    try:
        import serial
    except ImportError:
        return False
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=0.5)
    except Exception:
        return False
    while True:
        if ser.in_waiting:
            line = ser.readline().decode().strip()
            update_from_serial_line(line)
        time.sleep(0.1)


def main():
    start_http_server(PORT)
    # Valores por defecto para Kp/Ki/Kd (PLA)
    pid_kp.set(2.0)
    pid_ki.set(0.05)
    pid_kd.set(0.1)
    motor_speed.set(0)

    import threading
    t = threading.Thread(target=lambda: run_mqtt() or run_serial(), daemon=True)
    t.start()
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
