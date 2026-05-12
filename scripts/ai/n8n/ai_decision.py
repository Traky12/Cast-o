#!/usr/bin/env python3
"""
Umbral / score para ramas de workflow (alerta vs normal). Sin modelo entrenado: heurística documentada.
Opcional: `torch` + fichero `.pt` (mismo orden de features que DEFAULT_KEYS).
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List, Tuple

DEFAULT_KEYS: Tuple[str, ...] = ("humedad", "temperatura", "ph", "ec", "co2")


def decide_numpy(features: Dict[str, float], keys: Tuple[str, ...] = DEFAULT_KEYS) -> Tuple[bool, float]:
    """Score en [0,1] aprox.; alerta si supera umbral (lab / staging)."""
    if not keys:
        return False, 0.0
    vals: List[float] = []
    for k in keys:
        v = float(features.get(k, 0.0))
        vals.append(max(0.0, min(1.0, v)))
    score = sum(vals) / len(vals)
    threshold = float(os.environ.get("CASTUO_N8N_ALERT_THRESHOLD", "0.65"))
    return score >= threshold, score


def decide_torch(model_path: str, features: Dict[str, float], keys: Tuple[str, ...] = DEFAULT_KEYS) -> Tuple[bool, float]:
    import torch

    vec = [float(features.get(k, 0.0)) for k in keys]
    x = torch.tensor([vec], dtype=torch.float32)
    m = torch.jit.load(model_path, map_location="cpu")
    m.eval()
    with torch.no_grad():
        out = m(x)
        p = float(torch.sigmoid(out).squeeze().item())
    return p > 0.5, p


def decide(
    features: Dict[str, float],
    *,
    keys: Tuple[str, ...] = DEFAULT_KEYS,
    model_path: str | None = None,
) -> Tuple[bool, float]:
    path = model_path or os.environ.get("CASTUO_N8N_DECISION_MODEL", "").strip() or None
    if path and os.path.isfile(path):
        return decide_torch(path, features, keys)
    return decide_numpy(features, keys)


def main() -> None:
    p = argparse.ArgumentParser(description="Decisión binaria para workflows (heurística o TorchScript).")
    p.add_argument("--data", required=True, help='JSON objeto, ej. {"humedad":0.7,"temperatura":25}')
    p.add_argument("--model", default=None, help="Ruta .pt TorchScript (opcional)")
    args = p.parse_args()
    data = json.loads(args.data)
    if not isinstance(data, dict):
        raise SystemExit("--data debe ser un objeto JSON")
    feat = {str(k): float(v) for k, v in data.items()}
    alert, score = decide(feat, model_path=args.model)
    out = {"alert": alert, "score": score, "label": "alerta" if alert else "normal"}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
