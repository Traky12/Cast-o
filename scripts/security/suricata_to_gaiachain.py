#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASTÚO-SYSTEM™ — Integración Suricata → GaiaChain (alertas en tiempo real).
Observa eve.json y envía alertas al API de GaiaChain.
Requiere: watchdog, requests (opcional). GAIA_CHAIN_API_KEY, GAIA_CHAIN_ALERT_URL.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

GAIA_CHAIN_API_KEY = os.getenv("GAIA_CHAIN_API_KEY")
GAIA_CHAIN_ALERT_URL = os.getenv(
    "GAIA_CHAIN_ALERT_URL",
    "https://gaiachain.castuo-system.com/api/v1/suricata_alert",
)
EVE_LOG_PATH = os.getenv("SURICATA_EVE_LOG", "/var/log/suricata/eve.json")


class SuricataAlertHandler:
    def __init__(self):
        self._last_offset = 0

    def process_alerts(self) -> None:
        if not os.path.isfile(EVE_LOG_PATH):
            return
        try:
            with open(EVE_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(self._last_offset)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if event.get("event_type") == "alert":
                            self.send_to_gaiachain(event)
                    except json.JSONDecodeError:
                        continue
                self._last_offset = f.tell()
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error leyendo {EVE_LOG_PATH}: {e}")

    def send_to_gaiachain(self, event: dict) -> None:
        if not GAIA_CHAIN_API_KEY or not requests:
            return
        alert = event.get("alert", {})
        payload = {
            "type": "SURICATA_ALERT",
            "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
            "src_ip": event.get("src_ip"),
            "dest_ip": event.get("dest_ip"),
            "proto": event.get("proto"),
            "alert": {
                "signature": alert.get("signature"),
                "category": alert.get("category"),
                "severity": alert.get("severity"),
            },
            "http": event.get("http", {}),
            "tls": event.get("tls", {}),
            "payload": (event.get("payload_printable") or "")[:500],
        }
        try:
            r = requests.post(
                GAIA_CHAIN_ALERT_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {GAIA_CHAIN_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=5,
            )
            if r.status_code == 200:
                out = r.json()
                print(f"Alerta enviada a GaiaChain: {out.get('tx_hash', 'OK')}")
            else:
                print(f"Error enviando alerta: {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"Error en la solicitud: {e}")


def main() -> None:
    handler = SuricataAlertHandler()
    interval = float(os.getenv("SURICATA_POLL_INTERVAL", "5"))
    print(f"Monitoreando {EVE_LOG_PATH} cada {interval}s...")
    while True:
        handler.process_alerts()
        time.sleep(interval)


if __name__ == "__main__":
    main()
