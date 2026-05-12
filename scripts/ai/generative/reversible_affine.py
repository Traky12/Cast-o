"""
Mapa afín invertible y=diag(s)*x+b (s_i != 0). Sirve como contrato mínimo encode/decode
en el territorio cuando aún no hay NF calibrado: misma semántica que una capa biyectiva perfecta.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np


@dataclass
class ReversibleAffine:
    scale: np.ndarray  # shape (d,)
    bias: np.ndarray  # shape (d,)

    @classmethod
    def from_dim(cls, dim: int, seed: int = 42) -> "ReversibleAffine":
        rng = np.random.default_rng(seed)
        s = rng.uniform(0.5, 1.5, size=(dim,)).astype(np.float64)
        b = rng.standard_normal(size=(dim,)).astype(np.float64) * 0.01
        return cls(scale=s, bias=b)

    def encode(self, x: np.ndarray) -> np.ndarray:
        return x * self.scale + self.bias

    def decode(self, z: np.ndarray) -> np.ndarray:
        return (z - self.bias) / self.scale

    def verify_roundtrip(self, x: np.ndarray) -> Tuple[float, np.ndarray]:
        z = self.encode(x)
        xr = self.decode(z)
        err = float(np.max(np.abs(x - xr)))
        return err, xr

    def state_dict(self) -> Dict[str, Any]:
        return {"scale": self.scale.tolist(), "bias": self.bias.tolist()}

    @classmethod
    def from_state_dict(cls, d: Dict[str, Any]) -> "ReversibleAffine":
        return cls(scale=np.asarray(d["scale"], dtype=np.float64), bias=np.asarray(d["bias"], dtype=np.float64))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.state_dict()), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ReversibleAffine":
        return cls.from_state_dict(json.loads(path.read_text(encoding="utf-8")))


def hash_latent(z: np.ndarray, meta: str = "") -> str:
    h = hashlib.sha256(z.astype(np.float64).tobytes())
    if meta:
        h.update(meta.encode("utf-8"))
    return h.hexdigest()
