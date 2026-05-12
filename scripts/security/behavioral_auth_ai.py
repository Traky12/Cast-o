#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Autenticación por comportamiento con IA (detección de anomalías).
Modelo LSTM opcional (TensorFlow); sin TF usa umbral simple. Registro en GaiaChain.
No almacena contraseñas; firma con HSM/PEM por env.
Uso: entrenar: python3 behavioral_auth_ai.py train --user <id> --events <json_file>
     monitorear: python3 behavioral_auth_ai.py monitor --user <id>
"""
from __future__ import annotations

import os
import sys
import time
from collections import deque
from typing import Any

GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")
SEQUENCE_LENGTH = 10
FEATURE_SIZE = 12


def _sign_for_gaia(message: bytes) -> str | None:
    pin = os.getenv("HSM_USER_PIN")
    if pin:
        try:
            import subprocess
            r = subprocess.run(
                ["pkcs11-tool", "--login", "--pin", pin, "--sign", "--mechanism", "CKM_SHA256_RSA_PKCS", "--id", "01", "-"],
                input=message,
                capture_output=True,
                timeout=10,
            )
            if r.returncode == 0 and r.stdout:
                import base64
                return base64.b64encode(r.stdout).decode()
        except Exception:
            pass
    key_path = os.path.join(CHAIN_DIR, "master_key.pem")
    if os.path.isfile(key_path):
        import subprocess
        p = subprocess.run(["openssl", "dgst", "-sha512", "-sign", key_path, "-"], input=message, capture_output=True, timeout=5)
        if p.returncode == 0 and p.stdout:
            import base64
            return base64.b64encode(p.stdout).decode()
    return None


def _extract_features(event: dict) -> list[float]:
    return [
        float(event.get("time_since_last", 0)),
        float(event.get("keyboard_speed", 0)),
        float(event.get("keyboard_pressure", 0)),
        float(event.get("mouse_speed", 0)),
        float(event.get("mouse_acceleration", 0)),
        float(event.get("geolocation_lat", 0)),
        float(event.get("geolocation_lon", 0)),
        float(event.get("device_orientation_x", 0)),
        float(event.get("device_orientation_y", 0)),
        float(event.get("device_orientation_z", 0)),
        float(event.get("network_latency", 0)),
        float(event.get("time_of_day", 0)),
    ]


class BehavioralAuthModel:
    """Modelo de detección de anomalías (LSTM si hay TensorFlow; si no, umbral simple)."""

    def __init__(self, model_path: str | None = None):
        self.sequence_length = SEQUENCE_LENGTH
        self.feature_size = FEATURE_SIZE
        self.event_buffer: deque = deque(maxlen=SEQUENCE_LENGTH)
        self.user_threshold: dict[str, float] = {}
        self._model = None
        if model_path and os.path.isfile(model_path):
            self._load_keras(model_path)

    def _load_keras(self, path: str) -> None:
        try:
            import tensorflow as tf  # noqa: F401
            from tensorflow.keras.models import load_model
            self._model = load_model(path)
        except ImportError:
            pass

    def add_event(self, event: dict) -> None:
        self.event_buffer.append(_extract_features(event))

    def is_ready(self) -> bool:
        return len(self.event_buffer) == self.sequence_length

    def predict_anomaly(self, user_id: str) -> tuple[bool, float]:
        if not self.is_ready():
            raise ValueError("No hay suficientes eventos")
        threshold = self.user_threshold.get(user_id, 0.9)
        if self._model is not None:
            import numpy as np
            X = np.array(self.event_buffer).reshape(1, self.sequence_length, self.feature_size)
            score = float(self._model.predict(X, verbose=0)[0][0])
        else:
            # Regla simple: velocidad media anormal
            avg = sum(r[1] + r[3] for r in self.event_buffer) / len(self.event_buffer)
            score = min(1.0, avg / 3.0) if avg else 0.0
        return score > threshold, score

    def log_to_gaiachain(self, user_id: str, event: dict, is_anomaly: bool, prediction: float) -> None:
        msg = f"BEHAVIORAL_AUTH_{user_id}_{int(time.time())}".encode()
        sig = _sign_for_gaia(msg)
        if not sig:
            return
        admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
        if not admin:
            return
        try:
            import urllib.request
            import json
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/behavioral_auth/log",
                    data=json.dumps({
                        "user_id": user_id,
                        "event": {k: v for k, v in event.items() if k != "password"},
                        "is_anomaly": is_anomaly,
                        "prediction_score": prediction,
                        "timestamp": int(time.time()),
                        "signature": sig,
                    }).encode(),
                    headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=10,
            )
        except Exception:
            pass


class BehavioralAuthMonitor:
    def __init__(self) -> None:
        self.model = BehavioralAuthModel()
        self.current_user: str | None = None
        self.last_event_time = 0.0

    def start_monitoring(self, user_id: str) -> None:
        self.current_user = user_id
        self.last_event_time = time.time()

    def add_event(self, event: dict) -> tuple[bool, float]:
        if not self.current_user:
            raise ValueError("No hay usuario en monitoreo")
        event["time_since_last"] = time.time() - self.last_event_time
        self.last_event_time = time.time()
        self.model.add_event(event)
        if self.model.is_ready():
            is_anomaly, score = self.model.predict_anomaly(self.current_user)
            self.model.log_to_gaiachain(self.current_user, event, is_anomaly, score)
            return is_anomaly, score
        return False, 0.0

    def trigger_mfa(self) -> None:
        auth_script = "/opt/castuo/scripts/security/biometric_auth.py"
        if os.path.isfile(auth_script):
            import subprocess
            subprocess.run([sys.executable, auth_script], timeout=120)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: behavioral_auth_ai.py monitor --user <id> | train --user <id> --events <json>")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    user_id = os.getenv("CASTUO_BEHAVIORAL_USER", "authorized_admin")
    for i, arg in enumerate(sys.argv):
        if arg == "--user" and i + 1 < len(sys.argv):
            user_id = sys.argv[i + 1]
            break
    if cmd == "monitor":
        monitor = BehavioralAuthMonitor()
        monitor.start_monitoring(user_id)
        print(f"Monitoreando comportamiento de {user_id}. Envía eventos (JSON) por stdin o usa API.")
        # Ejemplo: leer eventos desde stdin (uno por línea JSON)
        try:
            import json
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                event = json.loads(line)
                is_anomaly, score = monitor.add_event(event)
                if is_anomaly:
                    print(f"Anomalía detectada (score: {score:.2f})")
                    monitor.trigger_mfa()
                    break
        except (KeyboardInterrupt, EOFError):
            pass
    elif cmd == "train":
        events_path = None
        for i, arg in enumerate(sys.argv):
            if arg == "--events" and i + 1 < len(sys.argv):
                events_path = sys.argv[i + 1]
                break
        if not events_path or not os.path.isfile(events_path):
            print("train requiere --events <archivo_json>")
            sys.exit(1)
        import json
        with open(events_path) as f:
            events = json.load(f) if f.read(1) == "[" else []
        if not isinstance(events, list):
            events = [events]
        model = BehavioralAuthModel()
        for ev in events:
            model.add_event(ev)
        print(f"Entrenamiento con {len(events)} eventos para {user_id} (umbral por defecto).")
    else:
        print("Comando no válido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
