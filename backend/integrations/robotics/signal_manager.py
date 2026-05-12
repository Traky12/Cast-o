from __future__ import annotations

import base64
import json
import logging
import math
import os
import time
from typing import Any, Dict, List, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SignalSnapshot(BaseModel):
    """Huella serializable de una muestra; el cuerpo va en base64 (no geometrías ni PII)."""

    signal_type: str
    frequency_hz: float
    data_b64: str
    timestamp_unix: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def _strip_risky_keys(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        banned = {"geometry", "wkt", "geojson", "image_raw"}
        return {k: val for k, val in v.items() if k.lower() not in banned}


def _symmetric_key_32() -> bytes:
    raw = os.getenv("ROBOT_SIGNAL_SYMMETRIC_KEY", "").strip()
    if raw:
        if len(raw) == 64 and all(c in "0123456789abcdefABCDEF" for c in raw):
            return bytes.fromhex(raw)
        try:
            k = base64.b64decode(raw)
            if len(k) == 32:
                return k
        except Exception:
            pass
        raise ValueError("ROBOT_SIGNAL_SYMMETRIC_KEY debe ser hex de 64 chars o base64 de 32 bytes")
    if os.getenv("CASTUO_ROBOTICS_LAB", "").strip() == "1":
        logger.warning(
            "CASTUO_ROBOTICS_LAB=1 sin ROBOT_SIGNAL_SYMMETRIC_KEY: clave efímera en RAM (no reproduzca en campo)."
        )
        return os.urandom(32)
    raise ValueError(
        "Falta ROBOT_SIGNAL_SYMMETRIC_KEY (o exporta CASTUO_ROBOTICS_LAB=1 solo en laboratorio)."
    )


def _encrypt_aes_gcm(key: bytes, plaintext: bytes) -> bytes:
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    enc = cipher.encryptor()
    ct = enc.update(plaintext) + enc.finalize()
    return iv + enc.tag + ct


def _decrypt_aes_gcm(key: bytes, blob: bytes) -> bytes:
    if len(blob) < 12 + 16:
        raise ValueError("blob cifrado inválido")
    iv, tag, ct = blob[:12], blob[12:28], blob[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    dec = cipher.decryptor()
    return dec.update(ct) + dec.finalize()


def synthesize_pcm_sine(
    frequency_hz: float,
    duration_s: float = 0.05,
    sample_rate: int = 48_000,
) -> bytes:
    """Sinusoide PCM16 para banco de pruebas (sustituir por GNU Radio / SDR en despliegue real)."""
    n = max(1, int(sample_rate * duration_s))
    out = bytearray(2 * n)
    for i in range(n):
        t = i / sample_rate
        sample = int(max(-32768, min(32767, 32767.0 * math.sin(2 * math.pi * frequency_hz * t))))
        out[2 * i] = sample & 0xFF
        out[2 * i + 1] = (sample >> 8) & 0xFF
    return bytes(out)


class SignalManager:
    """
    Orquesta muestras y sellado simétrico (GCM). Para comandos cortos y metadatos, usar RobotSecurityLayer + pq_crypto.
    """

    def __init__(self, robot_id: str) -> None:
        self.robot_id = robot_id
        self._key = _symmetric_key_32()
        self._history: List[Dict[str, Any]] = []

    def snapshot_from_pcm(self, signal_type: str, frequency_hz: float, pcm: bytes, **meta: Any) -> SignalSnapshot:
        payload = {
            **meta,
            "robot_id": self.robot_id,
            "pcm_bytes": len(pcm),
        }
        return SignalSnapshot(
            signal_type=signal_type,
            frequency_hz=frequency_hz,
            data_b64=base64.b64encode(pcm).decode("ascii"),
            timestamp_unix=time.time(),
            metadata=payload,
        )

    def encrypt_snapshot(self, snap: SignalSnapshot) -> SignalSnapshot:
        raw = base64.b64decode(snap.data_b64.encode("ascii"))
        sealed = _encrypt_aes_gcm(self._key, raw)
        meta = dict(snap.metadata)
        meta["sealed"] = True
        return SignalSnapshot(
            signal_type=snap.signal_type,
            frequency_hz=snap.frequency_hz,
            data_b64=base64.b64encode(sealed).decode("ascii"),
            timestamp_unix=snap.timestamp_unix,
            metadata=meta,
        )

    def decrypt_snapshot(self, snap: SignalSnapshot) -> SignalSnapshot:
        if not snap.metadata.get("sealed"):
            return snap
        raw = _decrypt_aes_gcm(self._key, base64.b64decode(snap.data_b64.encode("ascii")))
        meta = {k: v for k, v in snap.metadata.items() if k != "sealed"}
        return SignalSnapshot(
            signal_type=snap.signal_type,
            frequency_hz=snap.frequency_hz,
            data_b64=base64.b64encode(raw).decode("ascii"),
            timestamp_unix=snap.timestamp_unix,
            metadata=meta,
        )

    def simulated_radio_sample(self, frequency_hz: float = 433_920_000.0) -> SignalSnapshot:
        # En MHz de banda ISM el audio baseband aquí es solo análogo de laboratorio.
        pcm = synthesize_pcm_sine(1_000.0, duration_s=0.02, sample_rate=48_000)
        return self.snapshot_from_pcm("radio_lab", frequency_hz, pcm, source="simulated")

    def simulated_ultrasonic_sample(self) -> SignalSnapshot:
        pcm = synthesize_pcm_sine(40_000.0, duration_s=0.01, sample_rate=192_000)
        return self.snapshot_from_pcm("ultrasonic_lab", 40_000.0, pcm, source="simulated")

    def log_snapshot(self, snap: SignalSnapshot) -> None:
        meta = dict(snap.metadata)
        hint = None
        try:
            from backend.integrations.robotics.neuromorphic_edge import neuromorphic_hint_from_metadata

            hint = neuromorphic_hint_from_metadata(meta)
        except Exception:
            hint = None
        if hint:
            meta["neuromorphic_inference"] = hint
        self._history.append(
            {
                "timestamp_unix": snap.timestamp_unix,
                "signal_type": snap.signal_type,
                "frequency_hz": snap.frequency_hz,
                "data_b64_len": len(snap.data_b64),
                "metadata": meta,
            }
        )

    def history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def save_history_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2)
