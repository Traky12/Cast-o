#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Autenticación por comportamiento con modelo Transformer + LSTM (opcional BERT).
Detección de anomalías; registro en GaiaChain. Sin contraseñas en código.
Uso: monitor --user <id> | train --user <id> --events <json>
"""
from __future__ import annotations

import os
import sys
import time
from collections import deque
from typing import Any

SEQUENCE_LENGTH = 20
EMBEDDING_DIM = 128
GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")


def _sign_for_gaia(message: bytes) -> str | None:
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        try:
            pin = __import__("getpass").getpass("HSM PIN (o Enter para PEM): ") or None
        except Exception:
            pin = None
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


def _event_to_embedding(event: dict) -> list[float]:
    """Embedding de 128 dims: numéricas + categóricas + padding (sin BERT por defecto)."""
    import numpy as np
    num = [
        float(event.get("time_since_last", 0)) / 10,
        float(event.get("keyboard_speed", 0)) / 10,
        float(event.get("mouse_speed", 0)) / 1000,
        float(event.get("time_of_day", 0)) / 24,
        float(event.get("geolocation_lat", 0)) / 90,
        float(event.get("geolocation_lon", 0)) / 180,
    ]
    cat = [0.0] * 10
    if event.get("type") == "keyboard":
        cat[0] = 1.0
    elif event.get("type") == "mouse":
        cat[1] = 1.0
    # Rellenar hasta EMBEDDING_DIM
    base = num + cat
    pad = [0.0] * max(0, EMBEDDING_DIM - len(base))
    return (base + pad)[:EMBEDDING_DIM]


class BehavioralAuthTransformer:
    def __init__(self, model_path: str | None = None):
        self.sequence_length = SEQUENCE_LENGTH
        self.embedding_dim = EMBEDDING_DIM
        self.user_buffers: dict[str, deque] = {}
        self.user_profiles: dict[str, dict] = {}
        self._model = None
        try:
            import tensorflow as tf  # noqa: F401
            from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, MultiHeadAttention, LayerNormalization
            from tensorflow.keras.models import Model
            from tensorflow.keras.optimizers import Adam

            inputs = Input(shape=(SEQUENCE_LENGTH, EMBEDDING_DIM))
            att = MultiHeadAttention(num_heads=4, key_dim=EMBEDDING_DIM)(inputs, inputs)
            att = Dropout(0.1)(att)
            att = LayerNormalization(epsilon=1e-6)(att + inputs)
            lstm = LSTM(64, return_sequences=True)(att)
            lstm = Dropout(0.1)(lstm)
            lstm = LSTM(32)(lstm)
            dense = Dense(16, activation="relu")(lstm)
            out = Dense(1, activation="sigmoid")(dense)
            self._model = Model(inputs, out)
            self._model.compile(optimizer=Adam(1e-4), loss="binary_crossentropy", metrics=["accuracy"])
            if model_path and os.path.isfile(model_path):
                self._model.load_weights(model_path)
        except ImportError:
            pass

    def add_event(self, user_id: str, event: dict) -> None:
        if user_id not in self.user_buffers:
            self.user_buffers[user_id] = deque(maxlen=self.sequence_length)
        self.user_buffers[user_id].append(_event_to_embedding(event))

    def is_ready(self, user_id: str) -> bool:
        return user_id in self.user_buffers and len(self.user_buffers[user_id]) == self.sequence_length

    def predict_anomaly(self, user_id: str) -> tuple[bool, float]:
        if not self.is_ready(user_id):
            raise ValueError("No hay suficientes eventos")
        threshold = self.user_profiles.get(user_id, {}).get("anomaly_threshold", 0.99)
        if self._model is not None:
            import numpy as np
            X = np.array(self.user_buffers[user_id]).reshape(1, self.sequence_length, self.embedding_dim)
            score = float(self._model.predict(X, verbose=0)[0][0])
        else:
            buf = list(self.user_buffers[user_id])
            avg = sum(b[1] + b[3] for b in buf) / len(buf)
            score = min(1.0, avg / 3.0) if avg else 0.0
        return score > threshold, score

    def log_to_gaiachain(self, user_id: str, event: dict, is_anomaly: bool, prediction: float) -> None:
        sig = _sign_for_gaia(f"BEHAVIORAL_AUTH_{user_id}_{int(time.time())}".encode())
        if not sig:
            return
        admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
        if not admin:
            return
        try:
            import urllib.request
            import json
            safe_event = {k: v for k, v in event.items() if k != "password"}
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/behavioral_auth/log",
                    data=json.dumps({
                        "user_id": user_id,
                        "event": safe_event,
                        "is_anomaly": is_anomaly,
                        "prediction_score": prediction,
                        "model_version": "TRANSFORMER-LSTM-v2",
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

    def train_on_user_data(self, user_id: str, events: list[dict], labels: list[bool]) -> None:
        if len(events) != len(labels):
            raise ValueError("Eventos y etiquetas deben tener la misma longitud")
        if self._model is None:
            return
        import numpy as np
        X, y = [], []
        buf = deque(maxlen=self.sequence_length)
        for ev, lab in zip(events, labels):
            buf.append(_event_to_embedding(ev))
            if len(buf) == self.sequence_length:
                X.append(np.array(buf))
                y.append(1 if lab else 0)
        if not X:
            return
        self._model.fit(np.array(X), np.array(y), epochs=5, batch_size=8, verbose=0)
        self.user_profiles[user_id] = self.user_profiles.get(user_id, {})
        self.user_profiles[user_id]["last_trained"] = time.time()


class BehavioralAuthMonitor:
    def __init__(self) -> None:
        self.model = BehavioralAuthTransformer()
        self.current_user: str | None = None
        self.last_event_time = 0.0
        self.anomaly_count = 0

    def start_monitoring(self, user_id: str) -> None:
        self.current_user = user_id
        self.last_event_time = time.time()
        self.anomaly_count = 0

    def add_event(self, event: dict) -> tuple[bool, float]:
        if not self.current_user:
            raise ValueError("No hay usuario en monitoreo")
        event["time_since_last"] = time.time() - self.last_event_time
        self.last_event_time = time.time()
        self.model.add_event(self.current_user, event)
        if self.model.is_ready(self.current_user):
            is_anomaly, score = self.model.predict_anomaly(self.current_user)
            self.model.log_to_gaiachain(self.current_user, event, is_anomaly, score)
            if is_anomaly:
                self.anomaly_count += 1
                if self.anomaly_count >= 3:
                    self._trigger_mfa()
                    self.anomaly_count = 0
            return is_anomaly, score
        return False, 0.0

    def _trigger_mfa(self) -> None:
        auth = "/opt/castuo/scripts/security/biometric_auth.py"
        if os.path.isfile(auth):
            import subprocess
            subprocess.run([sys.executable, auth], timeout=120)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: behavioral_auth_transformer.py monitor --user <id> | train --user <id> --events <json>")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    user_id = os.getenv("CASTUO_BEHAVIORAL_USER", "authorized_admin")
    for i, arg in enumerate(sys.argv):
        if arg == "--user" and i + 1 < len(sys.argv):
            user_id = sys.argv[i + 1]
            break
    events_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--events" and i + 1 < len(sys.argv):
            events_path = sys.argv[i + 1]
            break
    if cmd == "monitor":
        monitor = BehavioralAuthMonitor()
        monitor.start_monitoring(user_id)
        print(f"Monitoreando (Transformer+LSTM) para {user_id}. Envía eventos JSON por stdin.")
        try:
            import json
            for line in sys.stdin:
                ev = json.loads(line)
                is_anomaly, score = monitor.add_event(ev)
                if is_anomaly:
                    print(f"Anomalía (score: {score:.4f})")
        except (KeyboardInterrupt, EOFError):
            pass
    elif cmd == "train" and events_path and os.path.isfile(events_path):
        import json
        with open(events_path) as f:
            data = json.load(f)
        events = data if isinstance(data, list) else [data]
        labels = [False] * len(events)
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "label" in data[0]:
            labels = [bool(e.get("label")) for e in data]
        model = BehavioralAuthTransformer()
        for ev in events:
            model.add_event(user_id, ev)
        model.train_on_user_data(user_id, events, labels)
        print(f"Modelo entrenado para {user_id} con {len(events)} eventos.")
    else:
        print("Comando no válido o --events <file> requerido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
