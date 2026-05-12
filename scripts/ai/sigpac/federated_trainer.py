#!/usr/bin/env python3
"""
Lab: agregación federada (Flower) sobre vector 8D derivado de estadísticas GeoTIFF — no sube la matriz de píxeles.
TRL real depende de piloto multi-nodo, acuerdos de tratamiento y modelo objetivo; esto es plantilla reproducible.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

import numpy as np

from geotiff_stats import summarize_geotiff
from sigpac_features import summary_to_feature_vector


def load_parcel_features(data_dir: Path, parcel_id: str) -> Optional[np.ndarray]:
    r = summarize_geotiff(data_dir / f"{parcel_id}.tif")
    if "error" in r:
        return None
    return summary_to_feature_vector(r)


def _require_flwr():
    try:
        import flwr as fl
    except ImportError as e:
        raise SystemExit(
            "Instala dependencias lab: pip install -r scripts/ai/sigpac/requirements_sigpac_federated.txt"
        ) from e
    return fl


def _set_torch_params(model, parameters: List[np.ndarray]) -> None:
    import torch

    keys = list(model.state_dict().keys())
    model.load_state_dict(
        {k: torch.tensor(p) for k, p in zip(keys, parameters)},
        strict=True,
    )


def _get_torch_params(model) -> List[np.ndarray]:
    return [v.detach().cpu().numpy() for v in model.state_dict().values()]


def _build_model():
    import torch.nn as nn

    return nn.Sequential(
        nn.Linear(8, 16),
        nn.ReLU(),
        nn.Linear(16, 1),
    )


def run_server(address: str, rounds: int) -> None:
    fl = _require_flwr()
    strat = fl.server.strategy.FedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=2,
        min_evaluate_clients=2,
        min_available_clients=2,
    )
    fl.server.start_server(
        server_address=address,
        config=fl.server.ServerConfig(num_rounds=rounds),
        strategy=strat,
    )


def run_client(server: str, data_dir: Path, parcel_id: str) -> None:
    import torch
    import torch.nn as nn

    fl = _require_flwr()
    vec = load_parcel_features(data_dir, parcel_id)
    if vec is None:
        raise SystemExit(f"No hay GeoTIFF válido: {data_dir / (parcel_id + '.tif')}")

    class FedParcelClient(fl.client.NumPyClient):
        def __init__(self) -> None:
            self.model = _build_model()
            self._x = torch.from_numpy(vec).unsqueeze(0)
            self._y = torch.tensor([[float(vec[3]) * 0.01]], dtype=torch.float32)
            self._loss = nn.MSELoss()

        def get_parameters(self, config):  # noqa: ARG002
            return _get_torch_params(self.model)

        def fit(self, parameters, config):  # noqa: ARG002
            _set_torch_params(self.model, parameters)
            opt = torch.optim.SGD(self.model.parameters(), lr=0.05)
            loss_v = 0.0
            for _ in range(5):
                opt.zero_grad()
                out = self.model(self._x)
                loss = self._loss(out, self._y)
                loss.backward()
                opt.step()
                loss_v = float(loss.item())
            return _get_torch_params(self.model), 1, {"train_loss": loss_v}

        def evaluate(self, parameters, config):  # noqa: ARG002
            _set_torch_params(self.model, parameters)
            with torch.no_grad():
                out = self.model(self._x)
                loss = self._loss(out, self._y)
            return float(loss.item()), 1, {"eval_loss": float(loss.item())}

    fl.client.start_numpy_client(server_address=server, client=FedParcelClient())


def main() -> None:
    p = argparse.ArgumentParser(description="Flower lab sobre vectores SIGPAC (8D desde GeoTIFF).")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("server", help="Servidor FedAvg (espera ≥2 clientes)")
    ps.add_argument("--address", default="0.0.0.0:8080")
    ps.add_argument("--rounds", type=int, default=3)

    pc = sub.add_parser("client", help="Cliente con un parcel_id local")
    pc.add_argument("--server", default="127.0.0.1:8080")
    pc.add_argument("--data-dir", type=Path, default=Path("data/sigpac"))
    pc.add_argument("--parcel-id", required=True)

    args = p.parse_args()
    _require_flwr()
    if args.cmd == "server":
        run_server(args.address, args.rounds)
    else:
        run_client(args.server, args.data_dir, args.parcel_id)


if __name__ == "__main__":
    main()
