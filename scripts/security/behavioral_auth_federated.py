#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Autenticación por comportamiento con promediado federado (sin compartir datos crudos).
Modelo Transformer+LSTM; promediado de pesos por usuarios; registro en GaiaChain.
Uso: add_user <user_id> --events <json> --labels <json> | federated_average | predict <user_id> --events <json>
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from collections import defaultdict
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
    num = [
        float(event.get("time_since_last", 0)) / 10,
        float(event.get("keyboard_speed", event.get("speed", 0))) / 10,
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
    base = num + cat
    pad = [0.0] * max(0, EMBEDDING_DIM - len(base))
    return (base + pad)[:EMBEDDING_DIM]


def _build_keras_model():
    try:
        import tensorflow as tf
        from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, MultiHeadAttention, LayerNormalization
        from tensorflow.keras.models import Model
        from tensorflow.keras.optimizers import Adam

        inputs = Input(shape=(SEQUENCE_LENGTH, EMBEDDING_DIM))
        att = MultiHeadAttention(num_heads=4, key_dim=EMBEDDING_DIM)(inputs, inputs)
        att = Dropout(0.1)(att)
        att = LayerNormalization(epsilon=1e-6)(att + inputs)
        lstm = LSTM(64, return_sequences=True)(att)
        lstm = Dropout(0.1)(lstm)
        lstm = LSTM(64)(lstm)
        dense = Dense(64, activation="relu")(lstm)
        dense = Dropout(0.1)(dense)
        out = Dense(1, activation="sigmoid")(dense)
        model = Model(inputs, out)
        model.compile(optimizer=Adam(1e-4), loss="binary_crossentropy", metrics=["accuracy"])
        return model
    except ImportError:
        return None


def _average_weights(weight_list: list) -> list:
    import numpy as np
    avg = []
    for i in range(len(weight_list[0])):
        stacked = np.stack([w[i] for w in weight_list])
        avg.append(np.mean(stacked, axis=0))
    return avg


class FederatedBehavioralAuth:
    def __init__(self) -> None:
        self.global_model = _build_keras_model()
        self.user_models: dict[str, Any] = defaultdict(lambda: _build_keras_model())

    def add_user_data(self, user_id: str, events: list[dict], labels: list[bool]) -> None:
        if len(events) != len(labels):
            raise ValueError("Eventos y etiquetas deben tener la misma longitud")
        model = self.user_models[user_id]
        if model is None:
            return
        import numpy as np
        X, y = [], []
        buf = []
        for ev, lab in zip(events, labels):
            buf.append(_event_to_embedding(ev))
            if len(buf) == SEQUENCE_LENGTH:
                X.append(buf.copy())
                y.append(1 if lab else 0)
                buf = buf[1:]
        if not X:
            return
        X = np.array(X)
        y = np.array(y).astype(np.float32).reshape(-1, 1)
        model.fit(X, y, epochs=5, batch_size=8, verbose=0)
        self._log_training_to_gaiachain(user_id, len(events))

    def _log_training_to_gaiachain(self, user_id: str, data_points: int) -> None:
        msg = f"FEDERATED_TRAINING_{user_id}_{data_points}_{int(time.time())}".encode()
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
                    f"{GAIA_URL}/api/v1/federated_learning/log",
                    data=json.dumps({
                        "type": "FEDERATED_TRAINING",
                        "user_id": user_id,
                        "data_points": data_points,
                        "model_version": "TRANSFORMER-LSTM-FEDERATED-v1",
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

    def federated_average(self, user_ids: list[str]) -> Any:
        """Promedia pesos de los modelos de los usuarios y actualiza el modelo global."""
        models = [self.user_models[uid] for uid in user_ids if self.user_models[uid] is not None]
        if not models:
            return self.global_model
        weights_list = [m.get_weights() for m in models]
        avg_weights = _average_weights(weights_list)
        if self.global_model is not None:
            self.global_model.set_weights(avg_weights)
        for uid in user_ids:
            if self.user_models[uid] is not None:
                self.user_models[uid].set_weights(avg_weights)
        self._log_federated_update(user_ids)
        return self.global_model

    def _log_federated_update(self, user_ids: list[str]) -> None:
        msg = f"FEDERATED_UPDATE_{'_'.join(user_ids)}_{int(time.time())}".encode()
        sig = _sign_for_gaia(msg)
        if not sig or not self.global_model:
            return
        admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
        if not admin:
            return
        try:
            import urllib.request
            import json
            import numpy as np
            w = self.global_model.get_weights()
            global_hash = hashlib.sha256(np.array(w).tobytes()).hexdigest()
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/federated_learning/update",
                    data=json.dumps({
                        "type": "FEDERATED_AVERAGING",
                        "participants": user_ids,
                        "model_version": "TRANSFORMER-LSTM-FEDERATED-v1",
                        "timestamp": int(time.time()),
                        "global_model_hash": global_hash,
                        "signature": sig,
                    }).encode(),
                    headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=10,
            )
        except Exception:
            pass

    def predict_anomaly(self, user_id: str, events: list[dict]) -> tuple[bool, float]:
        model = self.user_models.get(user_id) or self.global_model
        if model is None:
            return False, 0.0
        import numpy as np
        X = np.array([_event_to_embedding(e) for e in events[-SEQUENCE_LENGTH:]])
        if len(X) < SEQUENCE_LENGTH:
            return False, 0.0
        X = X.reshape(1, SEQUENCE_LENGTH, EMBEDDING_DIM)
        score = float(model.predict(X, verbose=0)[0][0])
        is_anomaly = score > 0.99
        self._log_prediction_to_gaiachain(user_id, score, is_anomaly)
        return is_anomaly, score

    def _log_prediction_to_gaiachain(self, user_id: str, score: float, is_anomaly: bool) -> None:
        msg = f"FEDERATED_PREDICT_{user_id}_{score}_{int(time.time())}".encode()
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
                    f"{GAIA_URL}/api/v1/federated_learning/predict",
                    data=json.dumps({
                        "type": "FEDERATED_PREDICTION",
                        "user_id": user_id,
                        "anomaly_score": score,
                        "is_anomaly": is_anomaly,
                        "model_version": "TRANSFORMER-LSTM-FEDERATED-v1",
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: behavioral_auth_federated.py add_user <id> --events <file> --labels <file> | federated_average <id1> [id2] ... | predict <id> --events <file>")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    fba = FederatedBehavioralAuth()
    if cmd == "add_user":
        user_id = sys.argv[2] if len(sys.argv) > 2 else os.getenv("CASTUO_BEHAVIORAL_USER", "authorized_admin")
        events_file = labels_file = None
        for i, a in enumerate(sys.argv):
            if a == "--events" and i + 1 < len(sys.argv):
                events_file = sys.argv[i + 1]
            if a == "--labels" and i + 1 < len(sys.argv):
                labels_file = sys.argv[i + 1]
        if not events_file or not labels_file:
            print("add_user requiere --events <json> --labels <json>")
            sys.exit(1)
        import json
        with open(events_file) as f:
            events = json.load(f)
        with open(labels_file) as f:
            labels = json.load(f)
        fba.add_user_data(user_id, events, labels)
        print(f"Datos de {user_id} añadidos.")
    elif cmd == "federated_average":
        user_ids = [a for a in sys.argv[2:] if not a.startswith("--")]
        if not user_ids:
            user_ids = ["user1", "user2", "user3"]
        fba.federated_average(user_ids)
        print(f"Promediado federado con {user_ids}.")
    elif cmd == "predict":
        user_id = sys.argv[2] if len(sys.argv) > 2 else "authorized_admin"
        events_file = None
        for i, a in enumerate(sys.argv):
            if a == "--events" and i + 1 < len(sys.argv):
                events_file = sys.argv[i + 1]
                break
        if not events_file or not os.path.isfile(events_file):
            print("predict requiere --events <file>")
            sys.exit(1)
        import json
        with open(events_file) as f:
            events = json.load(f)
        events = events if isinstance(events, list) else [events]
        is_anomaly, score = fba.predict_anomaly(user_id, events)
        print(f"Predicción: {'ANOMALÍA' if is_anomaly else 'NORMAL'} (score: {score:.4f})")
    else:
        print("Comando no válido.")
        sys.exit(1)


if __name__ == "__main__":
    main()
