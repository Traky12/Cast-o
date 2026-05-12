#!/usr/bin/env python3
"""
CASTUO-SYSTEM™ — Bridge Serial (Arduino) ↔ MQTT para extrusora de bio-compuestos.
Ejecutar en Raspberry Pi con Arduino por USB (/dev/ttyACM0).
"""
import os
import re
import time
import serial
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
SERIAL_PORT = os.environ.get("EXTRUSORA_SERIAL", "/dev/ttyACM0")
BAUD_RATE = 9600
TOPIC_TEMP_BOQUILLA = "castu/extrusora/temp/boquilla"
TOPIC_TEMP_CAMARA = "castu/extrusora/temp/camara"
TOPIC_HEAT = "castu/extrusora/heat"
TOPIC_CMD = "castu/extrusora/command"

ser = None
mqtt_client = None


def on_connect(client, userdata, flags, rc):
    print("Conectado a MQTT")
    client.subscribe(TOPIC_CMD)


def on_message(client, userdata, msg):
    if msg.topic != TOPIC_CMD:
        return
    try:
        payload = msg.payload.decode().strip()
        if payload.startswith("SET_TEMP") or payload in ("START_EXTRUSION", "STOP_EXTRUSION"):
            ser.write(f"{payload}\n".encode())
    except Exception as e:
        print("Error enviando a Arduino:", e)


def main():
    global ser, mqtt_client
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
    except Exception as e:
        print(f"No se pudo abrir {SERIAL_PORT}:", e)
        return
    time.sleep(2)

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print("MQTT connect failed:", e)
        ser.close()
        return
    mqtt_client.loop_start()

    re_temp_b = re.compile(r"TEMP_B:([\d.]+)")
    re_temp_c = re.compile(r"TEMP_C:([\d.]+)")
    re_heat = re.compile(r"HEAT:(\d)")

    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                if not line:
                    continue
                m = re_temp_b.match(line)
                if m:
                    mqtt_client.publish(TOPIC_TEMP_BOQUILLA, m.group(1))
                    continue
                m = re_temp_c.match(line)
                if m:
                    mqtt_client.publish(TOPIC_TEMP_CAMARA, m.group(1))
                    continue
                m = re_heat.match(line)
                if m:
                    mqtt_client.publish(TOPIC_HEAT, m.group(1))
        except serial.SerialException:
            break
        except Exception as e:
            print(e)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
