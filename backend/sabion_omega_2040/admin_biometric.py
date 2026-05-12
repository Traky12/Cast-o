# backend/sabion_omega_2040/admin_biometric.py
"""Verificación ADMIN EXCLUSIVO — SOLO GREGORIO J JIMÉNEZ BODES. Token + SHA3-512 biométrico."""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Tuple

logger = logging.getLogger(__name__)

ADMIN_TOKEN_EXPECTED = os.getenv("ADMIN_TOKEN", "CASTUO_360_GREGORIO_2040_KYBER2048_TRL9")
BIOMETRIC_SALT = "Gregorio_J_Jimenez_Bodes_16Mar2026"
BIOMETRIC_HASH_EXPECTED = os.getenv(
    "BIOMETRIC_HASH",
    hashlib.sha3_512(BIOMETRIC_SALT.encode()).hexdigest(),
)


def sha3_512_biometric(value: str) -> str:
    """SHA3-512 del valor biométrico."""
    return hashlib.sha3_512(value.encode()).hexdigest()


def verify_admin(token: str, biometric: str | None = None) -> Tuple[bool, str]:
    """
    Verifica token ADMIN y opcionalmente hash biométrico.
    Returns (ok, admin_identity).
    """
    if not token or token.strip() != ADMIN_TOKEN_EXPECTED.strip():
        logger.warning("Omega admin: token mismatch")
        return False, ""

    identity = "GREGORIO_J_JIMENEZ_BODES"
    if biometric:
        expected = BIOMETRIC_HASH_EXPECTED
        if hashlib.sha3_512(biometric.encode()).hexdigest() != expected and biometric != expected:
            logger.warning("Omega admin: biometric mismatch")
            return False, ""
    return True, identity


def get_expected_biometric_hash() -> str:
    """Hash SHA3-512 esperado para verificación (solo referencia doc)."""
    return sha3_512_biometric(BIOMETRIC_SALT)
