# backend/ai/secure_aggregation.py — Agregación homomórfica para FL (GDPR Art.25)

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

_HE_AVAILABLE = False
HomomorphicAggregator = None

try:
    import tenseal as ts
    _HE_AVAILABLE = True
except ImportError:
    ts = None


class HomomorphicAggregator:
    """
    Agregación de pesos con cifrado homomórfico (CKKS) para FL.
    Si tenseal no está instalado, encrypt/aggregate/decrypt son no-ops (devuelve datos en claro).
    """

    def __init__(
        self,
        poly_modulus_degree: int = 8192,
        coeff_mod_bit_sizes: Optional[List[int]] = None,
        scale: int = 2**40,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.context: Any = None
        coeff = coeff_mod_bit_sizes if coeff_mod_bit_sizes is not None else [60, 40, 40, 60]
        if _HE_AVAILABLE and ts is not None:
            try:
                self.context = ts.context(
                    ts.SCHEME_TYPE.CKKS,
                    poly_modulus_degree=poly_modulus_degree,
                    coeff_mod_bit_sizes=coeff,
                )
                self.context.global_scale = scale
                self.context.generate_galois_keys()
            except Exception as e:
                self.logger.warning("Contexto CKKS no disponible: %s", e)
                self.context = None
        else:
            self.logger.debug("tenseal no instalado; agregación en claro")

    def encrypt_weights(self, weights: Any) -> Any:
        """Cifra pesos (lista o array). Si HE no está, devuelve los datos tal cual."""
        if not _NUMPY or np is None:
            return weights
        arr = np.array(weights, dtype=float) if not hasattr(weights, "tolist") else weights
        if self.context is None:
            return arr.tolist()
        try:
            return ts.ckks_vector(self.context, arr.tolist())
        except Exception as e:
            self.logger.debug("Cifrado HE fallido, usando plano: %s", e)
            return arr.tolist()

    def aggregate_encrypted(self, encrypted_weights: List[Any]) -> Any:
        """Promedia vectores cifrados. Si no son CKKS, promedia listas."""
        if not encrypted_weights:
            return None
        first = encrypted_weights[0]
        if hasattr(first, "decrypt"):
            total = first
            for v in encrypted_weights[1:]:
                total = total + v
            n = len(encrypted_weights)
            return total * (1.0 / n)
        if _NUMPY and np is not None:
            return np.mean(encrypted_weights, axis=0).tolist()
        n = len(encrypted_weights)
        return [sum(x) / n for x in zip(*encrypted_weights)]

    def decrypt_weights(self, encrypted: Any) -> Any:
        """Descifra o devuelve lista/array."""
        if hasattr(encrypted, "decrypt"):
            out = encrypted.decrypt()
            if _NUMPY and np is not None:
                return np.array(out)
            return list(out)
        if _NUMPY and np is not None:
            return np.array(encrypted)
        return encrypted
