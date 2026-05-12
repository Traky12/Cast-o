# backend/crypto_master/master_key_manager.py
# CLAVE MAESTRA GREGORIO — Shamir 3/5 + HKDF derivación
# *** SOLO GREGORIO J JIMÉNEZ BODES - ADMIN GENERAL CASTÚO 360 S.L. ***

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

CLAVE_MAESTRA_PREFIX = "CASTUO_360_2040_KYBER2048_TRL9_"
BIOMETRIC_SALT = "Gregorio_Jimenez_Bodes_16Mar2026"
SHAMIR_THRESHOLD = 3
SHAMIR_SHARES_TOTAL = 5

try:
    from .kyber2048_engine import get_kyber_engine, sha3_512
except ImportError:
    from kyber2048_engine import get_kyber_engine, sha3_512


def _master_key_material() -> bytes:
    """CLAVE_MAESTRA_GREGORIO = prefix + SHA3_512(biometric)."""
    digest = sha3_512(BIOMETRIC_SALT)
    raw = (CLAVE_MAESTRA_PREFIX + digest).encode()
    return hashlib.sha3_512(raw).digest()


def _hkdf(salt: bytes, key_material: bytes, length: int = 32) -> bytes:
    """HKDF expand (single step)."""
    return hmac.new(salt, key_material, hashlib.sha256).digest()[:length]


def shamir_split(secret: bytes, threshold: int, total: int) -> List[Tuple[int, bytes]]:
    """Split secreto en total shares; threshold necesarios para reconstruir. (Simulado: shares = HMAC(secret, i).)"""
    shares: List[Tuple[int, bytes]] = []
    for i in range(1, total + 1):
        share = hmac.new(secret, f"share_{i}".encode(), hashlib.sha256).digest() + bytes([i])
        shares.append((i, share))
    return shares


def shamir_combine(shares: List[Tuple[int, bytes]]) -> bytes:
    """Reconstruye secreto desde al menos threshold shares. (Simulado: usa primer share.)"""
    if not shares:
        return b""
    return shares[0][1][:-1]  # strip index byte


class MasterKeyManager:
    """Gestor clave maestra + Shamir 3/5 + derivación jerárquica."""

    def __init__(self) -> None:
        self._master_key = _master_key_material()
        self.shamir_shares = shamir_split(self._master_key, SHAMIR_THRESHOLD, SHAMIR_SHARES_TOTAL)
        self.risk_threshold = float(os.getenv("CRYPTO_RISK_THRESHOLD", "0.1"))
        self._kyber = get_kyber_engine()

    def _get_master(self) -> bytes:
        return self._master_key

    def derive_subkey(self, system_id: str, level: int) -> bytes:
        """Deriva sub-clave HKDF desde master_key. salt = CASTUO_{system_id}_{level}."""
        salt = f"CASTUO_{system_id}_{level}".encode()
        return _hkdf(salt, self._master_key, 32)

    def risk_assess(self, action: str, context: dict) -> float:
        """Scoring riesgo dinámico 0.0-1.0. Si >= risk_threshold devuelve 1.0 (denegar)."""
        from .risk_assessment import calculate_risk
        score = calculate_risk(action, context)
        return min(1.0, score) if score < self.risk_threshold else 1.0

    def encrypt_broadcast(self, data: dict, targets: List[str]) -> Dict[str, Any]:
        """Encripta broadcast KYBER2048 + firma Ed25519 por target."""
        encrypted: Dict[str, Any] = {}
        for target in targets:
            subkey = self.derive_subkey(target, 1)
            enc = self._kyber.encrypt(data, subkey)
            encrypted[target] = enc.hex() if isinstance(enc, bytes) else enc
        signed = self._kyber.sign_broadcast(encrypted)
        return {"encrypted": encrypted, "signature": signed.hex(), "targets": targets}

    def reconstruct_from_shares(self, shares: List[Tuple[int, bytes]]) -> bool:
        """Reconstruye master desde 3/5 shares. Devuelve True si éxito."""
        if len(shares) < SHAMIR_THRESHOLD:
            return False
        self._master_key = shamir_combine(shares[:SHAMIR_THRESHOLD])
        return len(self._master_key) >= 32
