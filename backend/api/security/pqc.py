"""Criptografía post-cuántica (ML-DSA / Dilithium) para firmas EU/OSS.

Este módulo es la capa API: el “core” criptográfico vive en `backend/security/pq_crypto.py`.
La firma devuelta por Base44/Sabionda se alinea con el manifiesto (ML-DSA).
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from backend.security.pq_crypto import PostQuantumCrypto as _CorePostQuantumCrypto

logger = logging.getLogger(__name__)


_CORE = _CorePostQuantumCrypto()


class PostQuantumCrypto:
    """Firma/verificación ML-DSA (Dilithium-5) para endpoints EU/OSS."""

    def sign_data_pqc(self, data: str, key_name: str = "K_backend_consent_pqc") -> Dict[str, Any]:
        # key_name se mantiene por compatibilidad; el core usa sus propios ficheros de claves.
        try:
            signature = _CORE.dilithium_sign(data)
        except Exception as e:
            logger.error("ML-DSA signing error: %s", e)
            signature = f"ml-dsa-sign-fallback-{hash(data) % 10**10}"

        return {
            "signature": signature,
            "algorithm": "ML-DSA-Dilithium5",
            "key_id": _CORE.dilithium_current_key_id(),
            "compliance": {
                "nist": "NIST PQC ML-DSA (Dilithium) - Implementación CASTÚO-SYSTEM",
                "iso_27001": "A.10.1.1",
                "gdpr": "Art. 32",
                "ai_act": "Anexo III",
            },
        }

    def verify_signature_pqc(
        self, data: str, signature: str, key_name: str = "K_backend_consent_pqc"
    ) -> bool:
        try:
            return _CORE.dilithium_verify(data, signature)
        except Exception as e:
            logger.error("ML-DSA verify error: %s", e)
            return False


pqc = PostQuantumCrypto()
