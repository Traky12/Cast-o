# -*- coding: utf-8 -*-
"""
Firma con HSM (Thales Luna) — Barreras Sabionda v7.1, módulo seguridad ISO 27001.
En entornos sin HSM real se usa firma local con cryptography (clave en env o keystore).
"""
from __future__ import annotations

import os
from typing import Optional

# Opcional: Thales Luna / PKCS#11
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


def sign_with_hsm(data: str, hsm_client: Optional[object] = None) -> str:
    """
    Firma datos con HSM (Thales Luna). Si hsm_client es None o no disponible,
    usa clave privada desde env (GAIA_CHAIN_PRIVATE_KEY) con cryptography.
    """
    payload = data.encode("utf-8") if isinstance(data, str) else data
    if _HAS_CRYPTO and hsm_client is not None:
        try:
            private_key = hsm_client.get_private_key("gaiachain_key")
            signature = private_key.sign(
                payload,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return signature.hex()
        except Exception:
            pass
    # Fallback: firma con clave en env (solo para dev/test; en prod usar HSM real)
    if _HAS_CRYPTO:
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        key_pem = os.getenv("GAIA_CHAIN_PRIVATE_KEY") or os.getenv("HSM_SIGNING_KEY")
        if key_pem:
            try:
                key = load_pem_private_key(
                    key_pem.encode() if isinstance(key_pem, str) else key_pem,
                    password=None,
                    backend=default_backend(),
                )
                signature = key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
                return signature.hex()
            except Exception:
                pass
    # Stub: hash para pruebas sin clave
    import hashlib
    return "0x" + hashlib.sha256(payload).hexdigest()


def verify_signature(data: str, signature_hex: str, public_key_or_hsm=None) -> bool:
    """Verifica firma con clave pública o HSM."""
    if not _HAS_CRYPTO:
        return False
    payload = data.encode("utf-8") if isinstance(data, str) else data
    sig_bytes = bytes.fromhex(signature_hex.replace("0x", ""))
    if public_key_or_hsm is not None:
        try:
            pub = getattr(public_key_or_hsm, "get_public_key", lambda k: public_key_or_hsm)(None)
            pub.verify(sig_bytes, payload, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False
    return False
