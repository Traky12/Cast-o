#!/usr/bin/env python3
"""
IoT Growth Monitor — 3 Cooperativas Production.
Sabionda SAT + Cooperativa #2 + Cooperativa #3 → NFT growth ~10%/día.
Uso: python3 iot_monitor_3_coops.py [--coop 1|2|3] [--interval 3600]
  Sin --coop: monitoriza las 3 en un solo proceso (round-robin).
  Con --coop N: solo cooperativa N (para systemd castuo-iot-coopN.service).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

COOPS = [
    {"id": 1, "nombre": "Sabionda Educa SAT", "ha": 2.5, "token": 1, "cultivo": "lechuga"},
    {"id": 2, "nombre": "Cooperativa #2", "ha": 5.0, "token": 2, "cultivo": "vid"},
    {"id": 3, "nombre": "Cooperativa #3", "ha": 3.0, "token": 3, "cultivo": "tomate"},
]

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
GROWTH_RATE_PCT = float(os.getenv("IOT_GROWTH_RATE_PCT", "10.0"))
INTERVAL_DEFAULT = int(os.getenv("IOT_INTERVAL_SECONDS", "86400"))
LOG_FILE = os.getenv("IOT_MONITOR_LOG")  # ej. backend/logs/iot-monitor.log


def _mqtt_publish(topic: str, payload: str) -> bool:
    try:
        import paho.mqtt.client as mqtt
        client = mqtt.Client()
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.publish(topic, payload)
        client.disconnect()
        return True
    except Exception:
        return False


def _post_growth(token_id: int, growth: float) -> dict | None:
    try:
        import requests
        r = requests.post(
            f"{BACKEND_URL}/nft/growth",
            json={"token_id": token_id, "growth": growth},
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def monitor_one(coop: dict, interval: int, growth_rate: float) -> None:
    """Un ciclo de lectura sensores, MQTT y actualización NFT para una cooperativa."""
    token_id = coop["token"]
    nombre = coop["nombre"]
    cultivo = coop["cultivo"]
    seed = hash(nombre) % 1000

    sensors = {
        "ec": round(1.8 + (seed % 10) / 100.0, 2),
        "ph": round(6.2 + (token_id * 3 % 10) / 100.0, 2),
        "do": 7.5,
        "temp": 24.5,
        "growth": growth_rate,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    slug = nombre.lower().replace(" ", "_").replace("#", "")
    topic = f"hidroponia/{slug}/sensors"
    payload = json.dumps(sensors)
    if _mqtt_publish(topic, payload):
        mqtt_status = "MQTT ok"
    else:
        mqtt_status = "MQTT skip"

    result = _post_growth(token_id, growth_rate)
    line = ""
    if result:
        tx = result.get("tx_hash", result.get("tx", ""))
        line = f"🟢 {nombre} → Growth: {growth_rate:.1f}% | EC: {sensors['ec']:.2f} | {mqtt_status} | tx: {tx[:18]}..."
    else:
        line = f"🟡 {nombre} → Growth: {growth_rate:.1f}% | EC: {sensors['ec']:.2f} | {mqtt_status} | NFT update skip (backend?)"
    print(line)
    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{datetime.utcnow().isoformat()}Z {line}\n")
        except Exception:
            pass


def _coop_for_id(coop_id: int) -> dict:
    """Devuelve entrada coop por id; si no está en lista, entrada sintética para escalado."""
    for c in COOPS:
        if c["id"] == coop_id:
            return c
    return {
        "id": coop_id,
        "nombre": f"Cooperativa #{coop_id}",
        "ha": 0.0,
        "token": coop_id,
        "cultivo": "mixto",
    }


def run_monitor(coop_id: int | None, interval: int, growth_rate: float) -> None:
    if coop_id is not None:
        coops_to_run = [_coop_for_id(coop_id)]
    else:
        coops_to_run = list(COOPS)
    if not coops_to_run:
        print("Indicar --coop N (N=1,2,3,...) o ejecutar sin --coop para las 3 por defecto.", file=sys.stderr)
        sys.exit(1)

    current_growth = {c["id"]: 0.0 for c in coops_to_run}
    while True:
        for coop in coops_to_run:
            cid = coop["id"]
            current_growth[cid] = min(100.0, current_growth[cid] + growth_rate)
            monitor_one(coop, interval, current_growth[cid])
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="IoT Growth Monitor 3 Cooperativas")
    parser.add_argument("--coop", type=int, default=None, help="Solo esta cooperativa (1,2,3,... para systemd escalable)")
    parser.add_argument("--interval", type=int, default=INTERVAL_DEFAULT, help="Segundos entre actualizaciones (default 86400)")
    parser.add_argument("--growth-rate", type=float, default=GROWTH_RATE_PCT, help="Incremento growth %% por ciclo (default 10)")
    args = parser.parse_args()

    run_monitor(args.coop, args.interval, args.growth_rate)


if __name__ == "__main__":
    main()
