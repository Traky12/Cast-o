# backend/security/hsm_integration.py — Integración HSM (stub para validación de claves)

from __future__ import annotations

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    _CRYPTO = True
except ImportError:
    _CRYPTO = False


class HSMIntegration:
    """
    Integración con HSM (Hardware Security Module).
    Stub: en producción conectar con HSM real (PKCS#11, CloudHSM, etc.).
    """

    def __init__(self) -> None:
        self._available = False
        try:
            self._available = bool(__import__("os").environ.get("CASTUO_HSM_ENABLED", "").lower() in ("1", "true", "yes"))
        except Exception:
            pass

    def available(self) -> bool:
        """Indica si el HSM está disponible y configurado."""
        return self._available

    def generate_key_pair(self, key_size: int = 4096) -> Tuple[bytes, bytes]:
        """Genera par de claves en HSM si está disponible; si no, fallback software."""
        if not _CRYPTO:
            raise RuntimeError("cryptography no disponible")
        backend = default_backend()
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=backend,
        )
        public_key = private_key.public_key()
        return (
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ),
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ),
        )

    def validate_key_pair(self, private_key: bytes, public_key: bytes) -> bool:
        """Valida que el par de claves sea consistente (en producción: validación HSM)."""
        if not private_key or not public_key:
            return False
        try:
            if _CRYPTO:
                priv = serialization.load_pem_private_key(private_key, password=None, backend=default_backend())
                pub = serialization.load_pem_public_key(public_key, backend=default_backend())
                return priv.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ) == public_key
            return True
        except Exception as e:
            logger.debug("Validación de par de claves: %s", e)
            return False
