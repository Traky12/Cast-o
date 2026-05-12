# backend/scripts/benchmark_federated_learning.py — Benchmark de agregación FL

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List

# Raíz del proyecto para imports
root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from backend.ai.federated_learning import FederatedLearningCoordinator


def get_memory_usage_mb() -> float:
    """Uso de memoria del proceso actual en MB (opcional: psutil)."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def generate_test_models(
    num_models: int = 10,
    weight_size: int = 1000,
    num_layers: int = 3,
) -> List[dict]:
    """Genera modelos de prueba para benchmarking."""
    try:
        import numpy as np
        rng = np.random.default_rng(42)
    except ImportError:
        np = None
    models = []
    for i in range(num_models):
        if np is not None:
            weights = {
                f"layer_{j}": rng.standard_normal(weight_size).tolist()
                for j in range(num_layers)
            }
            confidence = float(rng.uniform(0.7, 1.0))
        else:
            weights = {
                f"layer_{j}": [float(i + j + k) for k in range(weight_size)]
                for j in range(num_layers)
            }
            confidence = 0.7 + (i % 4) * 0.1
        models.append({
            "weights": weights,
            "confidence": confidence,
            "metadata": {"source": f"node_{i}"},
        })
    return models


def benchmark(
    coordinator: FederatedLearningCoordinator | None = None,
    num_models: int = 50,
    iterations: int = 20,
    weight_size: int = 1000,
    warmup: int = 3,
) -> dict:
    """Ejecuta benchmark de agregación de modelos."""
    if coordinator is None:
        coordinator = FederatedLearningCoordinator()
    models = generate_test_models(num_models=num_models, weight_size=weight_size)
    for _ in range(warmup):
        coordinator._weighted_average_models(models)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        coordinator._weighted_average_models(models)
        times.append(time.perf_counter() - start)
    total_time = sum(times)
    try:
        import numpy as np
        avg_ms = float(np.mean(times)) * 1000
        std_ms = float(np.std(times)) * 1000
    except ImportError:
        avg_ms = (total_time / len(times)) * 1000
        std_ms = 0.0
    return {
        "avg_time_ms": avg_ms,
        "std_dev_ms": std_ms,
        "models_per_second": num_models * iterations / total_time if total_time > 0 else 0,
        "memory_usage_mb": get_memory_usage_mb(),
        "iterations": iterations,
        "n_models": num_models,
    }


def main() -> None:
    import argparse
    import json
    p = argparse.ArgumentParser(description="Benchmark agregación Federated Learning")
    p.add_argument("--iterations", type=int, default=20, help="Número de iteraciones")
    p.add_argument("--models", "--n-models", dest="num_models", type=int, default=50, help="Número de modelos")
    p.add_argument("--layer-size", type=int, default=1000, help="Tamaño de cada capa de pesos")
    p.add_argument("--format", choices=("text", "json"), default="text", help="Formato de salida")
    args = p.parse_args()
    coord = FederatedLearningCoordinator()
    results = benchmark(
        coordinator=coord,
        num_models=args.num_models,
        iterations=args.iterations,
        weight_size=args.layer_size,
    )
    if args.format == "json":
        out = {k: round(v, 2) if isinstance(v, float) else v for k, v in results.items()}
        print(json.dumps(out, indent=2))
    else:
        print("""
Benchmark Federated Learning:
  - Tiempo promedio: {avg_time_ms:.2f} ms
  - Desviación estándar: {std_dev_ms:.2f} ms
  - Modelos/segundo: {models_per_second:.2f}
  - Uso de memoria: {memory_usage_mb:.2f} MB
  - Iteraciones: {iterations}
  - Modelos por ronda: {n_models}
""".format(**results).strip())


if __name__ == "__main__":
    main()
