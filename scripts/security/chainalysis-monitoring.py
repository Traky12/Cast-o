#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASTÚO-SYSTEM™ — Monitoreo de alertas de acceso maestro + Chainalysis (opcional).
Consulta alertas GaiaChain tipo MASTER_ACCESS_VIOLATION; opcional análisis Chainalysis y bloqueo.
"""
from __future__ import annotations

import os
import time
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

CHAINALYSIS_API_KEY = os.getenv("CHAINALYSIS_API_KEY")
GAIA_CHAIN_API_KEY = os.getenv("GAIA_CHAIN_API_KEY")
GAIA_CHAIN_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")


def monitor_master_access() -> None:
    last_check = datetime.utcnow().isoformat()
    while True:
        try:
            if not GAIA_CHAIN_API_KEY or not requests:
                time.sleep(60)
                continue
            r = requests.get(
                f"{GAIA_CHAIN_URL}/api/v1/alerts",
                headers={"Authorization": f"Bearer {GAIA_CHAIN_API_KEY}"},
                params={"since": last_check, "type": "MASTER_ACCESS_VIOLATION"},
                timeout=10,
            )
            alerts = r.json() if r.status_code == 200 else []
            for alert in alerts:
                risk_score = 0.0
                if CHAINALYSIS_API_KEY:
                    ar = requests.post(
                        "https://api.chainalysis.com/api/v1/analysis",
                        headers={"Authorization": f"Bearer {CHAINALYSIS_API_KEY}"},
                        json={"event": alert, "rules": [{"type": "ip_reputation", "threshold": 0.9}]},
                        timeout=10,
                    )
                    if ar.status_code == 200:
                        risk_score = float(ar.json().get("risk_score", 0))
                if risk_score > 0.9:
                    ip = alert.get("ip", "")
                    if ip:
                        os.system(f"ufw deny from {ip} comment 'CASTUO: Master access violation' 2>/dev/null || true")
                slack_url = os.getenv("SLACK_WEBHOOK")
                if slack_url:
                    requests.post(
                        slack_url,
                        json={
                            "text": f"ALERTA CRÍTICA: Acceso no autorizado sistema maestro. IP: {alert.get('ip')}, Riesgo: {risk_score}"
                        },
                        timeout=5,
                    )
            last_check = datetime.utcnow().isoformat()
        except Exception as e:
            print(f"Error monitoreo: {e}")
        time.sleep(60)


if __name__ == "__main__":
    monitor_master_access()
