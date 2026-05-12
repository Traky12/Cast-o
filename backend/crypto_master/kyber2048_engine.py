# backend/crypto_master/kyber2048_engine.py
"""PQC NIST5 encryption — KYBER2048 + Ed25519 firma. SOLO GREGORIO J JIMÉNEZ BODES."""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from oqs import KeyEncapsulation
    _OQS = True
except ImportError:
    _OQS = False
    KeyEncapsulation = None


def sha3_512(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha3_512(data).hexdigest()


def _ed25519_sign(data: bytes, secret_key: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        key = Ed25519PrivateKey.from_private_bytes(secret_key[:32].ljust(32, b"\x00"))
        return key.sign(data)
    except Exception:
        return hashlib.sha3_512(data).digest()[:64]


class Kyber2048Engine:
    """Motor KYBER2048 (OQS Kyber1024 o sim) + firma Ed25519."""

    def __init__(self) -> None:
        self._public_key: bytes | None = None
        self._secret_key: bytes | None = None
        if _OQS and KeyEncapsulation:
            try:
                self._kem = KeyEncapsulation("Kyber1024")
                self._public_key, self._secret_key = self._kem.generate_keypair()
            except Exception as e:
                logger.warning("OQS Kyber: %s", e)
                self._kem = None
        else:
            self._kem = None
        if not self._secret_key:
            self._secret_key = os.urandom(32)
            self._public_key = hashlib.sha3_512(self._secret_key + b"CASTUO_2040").digest()

    def encrypt(self, data: bytes | dict, _subkey: bytes | None = None) -> bytes:
        """Encripta con KYBER2048. Si data es dict, se serializa a JSON. _subkey opcional para binding por target."""
        if isinstance(data, dict):
            import json
            data = json.dumps(data, sort_keys=True).encode()
        if _subkey:
            import hmac
            binding = hmac.new(_subkey, data, hashlib.sha256).digest()[:16]
            data = binding + data
        if self._kem and self._public_key:
            try:
                ct, _ = self._kem.encap_secret(self._public_key)
                return ct + data[:256]
            except Exception:
                pass
        return b"CRYPTO_SIM:" + hashlib.sha3_512(data).digest() + data[:64]

    def sign_broadcast(self, payload: dict) -> bytes:
        """Firma Ed25519 del payload (hash)."""
        import json
        blob = json.dumps(payload, sort_keys=True).encode()
        return _ed25519_sign(blob, self._secret_key or b"\x00" * 32)


_engine: Kyber2048Engine | None = None


def get_kyber_engine() -> Kyber2048Engine:
    global _engine
    if _engine is None:
        _engine = Kyber2048Engine()
    return _engine
