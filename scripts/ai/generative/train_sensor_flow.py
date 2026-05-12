#!/usr/bin/env python3
"""
Entrenamiento mínimo de Normalizing Flow (nflows) cuando torch+nflows están instalados.
Sin datos reales no entrena nada útil para campo; sirve como plantilla para CTAEX/CICYTEX.

Uso:
  pip install -r scripts/ai/generative/requirements_rgi.txt
  python scripts/ai/generative/train_sensor_flow.py --dim 20 --epochs 50 --out models/rg/sensor_flow.pt
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _train(args: argparse.Namespace) -> None:
    import torch
    from nflows import distributions, flows, transforms

    dim = args.dim
    data = torch.randn(args.samples, dim, dtype=torch.float32) * args.noise_std

    base = distributions.StandardNormal(shape=[dim])
    transform = transforms.CompositeTransform(
        [
            transforms.MaskedAffineAutoregressiveTransform(features=dim, hidden_features=args.hidden),
            transforms.RandomPermutation(features=dim),
        ]
    )
    flow = flows.Flow(transform, base)
    opt = torch.optim.Adam(flow.parameters(), lr=args.lr)

    flow.train()
    for epoch in range(args.epochs):
        opt.zero_grad()
        loss = -flow.log_prob(data).mean()
        loss.backward()
        opt.step()
        if epoch % max(1, args.epochs // 10) == 0:
            print(f"epoch {epoch} nll_bits ~ {loss.item() / float(dim) / 0.69314718056:.4f}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": flow.state_dict(), "dim": dim}, out)
    print(f"guardado {out}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dim", type=int, default=20)
    p.add_argument("--samples", type=int, default=4096)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--hidden", type=int, default=64)
    p.add_argument("--noise_std", type=float, default=1.0)
    p.add_argument("--out", type=str, default="models/rg/sensor_flow.pt")
    args = p.parse_args()
    try:
        _train(args)
    except ImportError as e:
        raise SystemExit(
            "Faltan dependencias RGI. Instala: pip install -r scripts/ai/generative/requirements_rgi.txt\n" f"Detalle: {e}"
        ) from e


if __name__ == "__main__":
    main()
