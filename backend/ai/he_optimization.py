# backend/ai/he_optimization.py — Parámetros HE para equilibrio seguridad/rendimiento

from __future__ import annotations

import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

_TS = None
try:
    import tenseal as ts
    _TS = ts
except ImportError:
    ts = None


class HEPerformanceOptimizer:
    """Sugiere parámetros HE según tamaño de datos, memoria y latencia."""

    @staticmethod
    def get_secure_parameters() -> Dict[str, Any]:
        """Parámetros CKKS optimizados para seguridad máxima (post-cuántica 192-bit)."""
        return {
            "poly_modulus_degree": 16384,
            "coeff_mod_bit_sizes": [60, 40, 40, 60, 60],
            "security_level": "192-bit post-quantum",
            "global_scale": 2**50,
        }

    @staticmethod
    def find_optimal_parameters(
        data_size: int,
        max_memory: int = 512,
        target_latency: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Prueba conjuntos de parámetros CKKS y devuelve el que mejor equilibra
        memoria y latencia dentro de límites.
        """
        if not _TS or not _NUMPY or np is None:
            return {
                "poly_modulus_degree": 8192,
                "coeff_mod_bit_sizes": [60, 40, 40, 60],
                "score": 0.0,
                "measured_latency": 0.0,
                "estimated_memory_mb": 0.0,
            }
        best_params: Dict[str, Any] = {}
        best_score = -float("inf")
        candidates = [
            {"poly_modulus_degree": 4096, "coeff_mod_bit_sizes": [40, 20, 20, 40]},
            {"poly_modulus_degree": 8192, "coeff_mod_bit_sizes": [60, 40, 40, 60]},
            {"poly_modulus_degree": 16384, "coeff_mod_bit_sizes": [40, 40, 40, 40]},
        ]
        for params in candidates:
            try:
                ctx = ts.context(
                    ts.SCHEME_TYPE.CKKS,
                    poly_modulus_degree=params["poly_modulus_degree"],
                    coeff_mod_bit_sizes=params["coeff_mod_bit_sizes"],
                )
                ctx.global_scale = 2**40
                ctx.generate_galois_keys()
                size = min(data_size, ctx.poly_modulus_degree // 2)
                test_data = np.random.randn(size).tolist()
                vec = ts.ckks_vector(ctx, test_data)
                start = time.perf_counter()
                _ = vec + vec
                latency = time.perf_counter() - start
                deg = params["poly_modulus_degree"]
                coeff_bits = sum(params["coeff_mod_bit_sizes"])
                mem_mb = (deg * coeff_bits / 8) / (1024 * 1024)
                mem_score = 1 - min(mem_mb / max_memory, 1.0)
                lat_score = 1 - min(latency / target_latency, 1.0)
                score = 0.6 * mem_score + 0.4 * lat_score
                if score > best_score:
                    best_score = score
                    best_params = {
                        **params,
                        "score": score,
                        "measured_latency": latency,
                        "estimated_memory_mb": mem_mb,
                    }
            except Exception as e:
                logger.debug("Parámetros %s omitidos: %s", params, e)
        if not best_params:
            best_params = {
                "poly_modulus_degree": 8192,
                "coeff_mod_bit_sizes": [60, 40, 40, 60],
                "score": 0.0,
                "measured_latency": 0.0,
                "estimated_memory_mb": 0.0,
            }
        logger.info("Parámetros HE sugeridos: %s", best_params)
        return best_params

    @staticmethod
    def create_optimized_context(data_size: int) -> Any:
        """Crea un contexto CKKS con parámetros sugeridos para data_size."""
        params = HEPerformanceOptimizer.find_optimal_parameters(data_size)
        if not _TS:
            return None
        ctx = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=params["poly_modulus_degree"],
            coeff_mod_bit_sizes=params["coeff_mod_bit_sizes"],
        )
        ctx.global_scale = 2**40
        ctx.generate_galois_keys()
        return ctx
