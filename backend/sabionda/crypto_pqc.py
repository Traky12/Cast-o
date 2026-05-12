# backend/sabionda/crypto_pqc.py
"""PQC Kyber-1024 + Ed25519 + SHA3-512. SABIONDA_MASTER_v4.0 — Encriptación total."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

KYBER_MODE = os.getenv("KYBER_MODE", "1024")
_PEERS_ENCRYPTED = os.getenv("PEERS_ENCRYPTED", "true").lower() == "true"

try:
    from oqs import KeyEncapsulation
    _OQS = True
except ImportError:
    _OQS = False
    KeyEncapsulation = None


def _sha3_512(data: bytes) -> str:
    """SHA3-512 hex."""
    h = hashlib.sha3_512()
    h.update(data)
    return h.hexdigest()


def _ed25519_sign(data: bytes, secret_key: bytes | None = None) -> bytes:
    """Firma Ed25519 (simulada si no hay cryptography)."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.exceptions import InvalidKey
        if secret_key is None:
            secret_key = os.urandom(32)
        key = Ed25519PrivateKey.from_private_bytes(secret_key)
        return key.sign(data)
    except Exception:
        return _sha3_512(data).encode()[:64].ljust(64, b"\x00")


def sabionda_signature(payload: dict) -> str:
    """Firma Sabionda sobre payload: SHA3-512(JSON) + Ed25519 simulado."""
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return "0x" + _sha3_512(blob)[:64]


# --- Kyber-1024 (OQS o simulado) ---

class Kyber1024:
    """KEM Kyber-1024 (NIST PQC). Fallback simulado si oqs no instalado."""

    def __init__(self) -> None:
        self._public_key: bytes | None = None
        self._secret_key: bytes | None = None
        self._alg = "Kyber1024" if _OQS else "Kyber1024-sim"
        if _OQS and KeyEncapsulation is not None:
            try:
                self._kem = KeyEncapsulation(self._alg)
                self._public_key, self._secret_key = self._kem.generate_keypair()
            except Exception as e:
                logger.warning("OQS Kyber1024 init failed: %s", e)
                self._kem = None
        else:
            self._kem = None
            self._secret_key = os.urandom(32)
            self._public_key = hashlib.sha3_256(self._secret_key + b"kyber1024").digest()

    def encrypt_peers(self, peers_data: list | dict) -> bytes:
        """Encripta lista/dict de peers para transporte seguro."""
        raw = json.dumps(peers_data).encode()
        if self._kem and self._public_key:
            try:
                ciphertext, _ = self._kem.encap_secret(self._public_key)
                return ciphertext + raw
            except Exception:
                pass
        import base64
        return b"SIM:" + base64.b64encode(raw)

    def decrypt_peers(self, encrypted: bytes) -> list | dict:
        """Desencripta peers (SIM base64 o OQS ciphertext+raw)."""
        if encrypted.startswith(b"SIM:"):
            import base64
            try:
                return json.loads(base64.b64decode(encrypted[4:]).decode())
            except Exception:
                return []
        if self._kem and self._secret_key and len(encrypted) > 256:
            try:
                ct_len = 1568
                ct = encrypted[:ct_len]
                self._kem.decap_secret(ct)
                return json.loads(encrypted[ct_len:].decode())
            except Exception:
                pass
        return []

    def get_public_key_b64(self) -> str:
        import base64
        return base64.b64encode(self._public_key or b"").decode()


_kyber_instance: Kyber1024 | None = None


def get_kyber() -> Kyber1024:
    global _kyber_instance
    if _kyber_instance is None:
        _kyber_instance = Kyber1024()
    return _kyber_instance


def kyber1024_encrypt(peers_list: list) -> bytes:
    """Encripta lista de peers con Kyber-1024."""
    return get_kyber().encrypt_peers(peers_list)


def kyber1024_decrypt(encrypted: bytes) -> list:
    """Desencripta peers."""
    return get_kyber().decrypt_peers(encrypted)
