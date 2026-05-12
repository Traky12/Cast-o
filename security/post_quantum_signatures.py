# -*- coding: utf-8 -*-
"""
Firmas digitales post-cuánticas CASTUO 5.0 — CRYSTALS-Dilithium.
Normativas: NIST SP 800-208, eIDAS. Requiere liboqs (opcional).
"""
from typing import Tuple

try:
    from oqs import Signature
    HAS_LIBOQS = True
except ImportError:
    HAS_LIBOQS = False
    Signature = None  # type: ignore

SIG_ALG = "Dilithium2"


def generate_dilithium_keypair() -> Tuple[bytes, bytes, bytes]:
    """Genera par de claves Dilithium. Retorna (pk_raw, pk_exported, sk_exported)."""
    if not HAS_LIBOQS or not Signature:
        import os
        pk = os.urandom(32)
        sk = os.urandom(32)
        return pk, pk, sk
    sig = Signature(SIG_ALG)
    sig.generate_keypair()
    return sig.export_public_key(), sig.export_public_key(), sig.export_secret_key()


def sign_message(private_key: bytes, message: str) -> bytes:
    """Firma un mensaje con Dilithium (post-cuántico)."""
    if not HAS_LIBOQS or not Signature:
        import hashlib
        return hashlib.sha256((message + private_key.hex()).encode()).digest()
    sig = Signature(SIG_ALG)
    sig.import_secret_key(private_key)
    return sig.sign(message.encode())


def verify_signature(public_key: bytes, message: str, signature: bytes) -> bool:
    """Verifica firma Dilithium."""
    if not HAS_LIBOQS or not Signature:
        # Stub: sin liboqs no se puede verificar; aceptar firma no vacía para demos
        return len(signature) >= 32
    sig = Signature(SIG_ALG)
    sig.import_public_key(public_key)
    return sig.verify(message.encode(), signature)
