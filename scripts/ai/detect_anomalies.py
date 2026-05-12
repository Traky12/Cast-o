#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASTÚO-SYSTEM™ — Detección de anomalías en tiempo real (anti-hacking v1.0).
Carga modelo Isolation Forest; si predicción == -1, registra en GaiaChain y notifica.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import joblib

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"


def generate_signature(data: dict) -> str:
    """Stub: en producción firmar con HSM."""
    import hashlib
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def detect_anomaly(metrics: List[float]) -> Tuple[bool, str | None]:
    """
    metrics: [cpu_usage, memory_usage, network_traffic, login_attempts]
    Returns: (is_anomaly, tx_hash or None)
    """
    model_path = MODEL_DIR / "anomaly_detection.pkl"
    if not model_path.exists():
        return False, None

    clf = joblib.load(model_path)
    X = [metrics]
    prediction = clf.predict(X)[0]
    score = float(clf.decision_function(X)[0])

    if prediction != -1:
        return False, None

    alert_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "anomaly_score": score,
        "status": "DETECTED",
    }

    tx_hash = None
    api_key = os.getenv("GAIA_CHAIN_API_KEY")
    if api_key:
        try:
            import urllib.request
            req = urllib.request.Request(
                os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com") + "/api/v1/alert",
                data=json.dumps({
                    "type": "ANOMALY_DETECTED",
                    "data": alert_data,
                    "signature": generate_signature(alert_data),
                }).encode(),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                out = json.load(r)
                tx_hash = out.get("tx_hash")
        except Exception:
            pass

    slack_url = os.getenv("SLACK_WEBHOOK")
    if slack_url:
        try:
            import urllib.request
            body = json.dumps({
                "text": (
                    f"*ALERTA DE ANOMALÍA*\n"
                    f"- Score: {score:.2f}\n"
                    f"- Métricas: CPU={metrics[0]:.2f}, Mem={metrics[1]:.2f}\n"
                    f"- GaiaChain TX: {tx_hash or 'N/A'}"
                )
            }).encode()
            urllib.request.urlopen(
                urllib.request.Request(slack_url, data=body, headers={"Content-Type": "application/json"}, method="POST"),
                timeout=5,
            )
        except Exception:
            pass

    return True, tx_hash


if __name__ == "__main__":
    import sys
    # Ejemplo: python detect_anomalies.py 0.9 0.95 0.8 10
    metrics = [float(x) for x in sys.argv[1:5]] if len(sys.argv) >= 5 else [0.5, 0.3, 0.1, 0]
    ok, tx = detect_anomaly(metrics)
    print("Anomaly:", ok, "TX:", tx)
