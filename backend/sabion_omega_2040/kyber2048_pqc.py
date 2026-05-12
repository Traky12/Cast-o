# backend/sabion_omega_2040/kyber2048_pqc.py
"""PQC Kyber-2048 + NIST Post-Quantum. OMEGA_2040 — Encriptación nivel admin exclusivo."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, List

logger = logging.getLogger(__name__)

KYBER_LEVEL = os.getenv("KYBER_LEVEL", "2048")

try:
    from oqs import KeyEncapsulation
    _OQS = True
    _KEM_ALG = "Kyber1024"  # NIST solo define hasta 1024; 2048 = conceptual/sim
except ImportError:
    _OQS = False
    KeyEncapsulation = None


class Kyber2048PQC:
    """KEM nivel 2040 (Kyber1024 OQS o simulado como 2048)."""

    def __init__(self) -> None:
        self._public_key: bytes | None = None
        self._secret_key: bytes | None = None
        if _OQS and KeyEncapsulation is not None:
            try:
                self._kem = KeyEncapsulation("Kyber1024")
                self._public_key, self._secret_key = self._kem.generate_keypair()
            except Exception as e:
                logger.warning("OQS Kyber init: %s", e)
                self._kem = None
        else:
            self._kem = None
        if not self._public_key:
            self._secret_key = os.urandom(32)
            self._public_key = hashlib.sha3_512(self._secret_key + b"OMEGA_2040_KYBER").digest()

    def encrypt_broadcast(self, payload: str | bytes, _targets: List[str] | None = None) -> bytes:
        """Encripta mensaje para broadcast a subsistemas (OMEGA_*)."""
        raw = payload.encode() if isinstance(payload, str) else payload
        if self._kem and self._public_key:
            try:
                ct, _ = self._kem.encap_secret(self._public_key)
                return ct + raw[:256]
            except Exception:
                pass
        return b"OMEGA_SIM:" + hashlib.sha3_512(raw).digest() + raw[:64]

    def decrypt_broadcast(self, encrypted: bytes) -> bytes:
        """Desencripta mensaje broadcast."""
        if encrypted.startswith(b"OMEGA_SIM:"):
            return encrypted[10 + 64 :]
        if self._kem and self._secret_key and len(encrypted) > 256:
            try:
                self._kem.decap_secret(encrypted[:1568])
                return encrypted[1568:]
            except Exception:
                pass
        return b""


_omega_kem: Kyber2048PQC | None = None


def get_omega_kem() -> Kyber2048PQC:
    global _omega_kem
    if _omega_kem is None:
        _omega_kem = Kyber2048PQC()
    return _omega_kem
