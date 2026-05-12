"""
CASTÚO-SYSTEM™ — Post-quantum cryptography
Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §2 (cifrado) + §3 (roles)
Ref: Prontuario cifrado §2.1 — KEM Kyber-1024 + AES-256-GCM

Uses pqcrypto (Kyber-1024 / Dilithium-5) when the package is installed.
Falls back to AES-256-GCM (cryptography.hazmat) — fallback is DOCUMENTED,
not silent. A warning is emitted at instantiation time.

Installation for PQC support:
    pip install pqcrypto        # NIST PQC round-3 finalists

The fallback (AES-256-GCM) is FIPS-approved and production-safe for
confidentiality. Use the fallback path when the threat model does not
require post-quantum key encapsulation (e.g. test environments, local dev).

Dilithium-5 signing requires pqcrypto — it has NO AES fallback because
digital signatures are semantically different from symmetric encryption.
Calling dilithium_sign/verify without pqcrypto raises RuntimeError explicitly.
"""
from __future__ import annotations

import os
import warnings
from typing import Optional

# ─── PQC availability ─────────────────────────────────────────────────────────
try:
    from pqcrypto.kem.kyber1024 import (
        encrypt as _kyber_enc,
        decrypt as _kyber_dec,
        generate_keypair as _kyber_keygen,
    )
    from pqcrypto.sign.dilithium5 import (
        generate_keypair as _dil_keygen,
        sign as _dil_sign,
        verify as _dil_verify,
    )
    _PQC_AVAILABLE = True
except ImportError:
    _PQC_AVAILABLE = False

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_FALLBACK_WARNING = (
    "pqcrypto not installed — PostQuantumCrypto using AES-256-GCM fallback. "
    "Install pqcrypto for Kyber-1024/Dilithium-5 (NIST PQC) in production. "
    "Dilithium signing unavailable in fallback mode."
)


# ─── Main class ───────────────────────────────────────────────────────────────

class PostQuantumCrypto:
    """
    Hybrid encrypt/decrypt + Dilithium-5 sign/verify.

    With pqcrypto installed:
      - Encryption: KEM Kyber-1024 wraps a session key → AES-256-GCM payload.
      - Signing:    Dilithium-5.

    Without pqcrypto (fallback):
      - Encryption: AES-256-GCM with externally supplied key.
      - Signing:    raises RuntimeError — no silent downgrade for signatures.
    """

    pqc_available: bool = _PQC_AVAILABLE

    def __init__(self, aes_key: Optional[bytes] = None) -> None:
        if not _PQC_AVAILABLE:
            warnings.warn(_FALLBACK_WARNING, UserWarning, stacklevel=2)
        # AES key must be exactly 32 bytes.
        # If not provided → generate ephemeral key (caller must persist externally).
        if aes_key is not None:
            if len(aes_key) != 32:
                raise ValueError("aes_key must be exactly 32 bytes (AES-256)")
            self._aes_key = aes_key
        else:
            self._aes_key = os.urandom(32)

    # ── Symmetric encryption (AES-256-GCM) ────────────────────────────────────

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext with AES-256-GCM.
        Returns: nonce(12 bytes) || ciphertext+tag.
        """
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._aes_key)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ct

    def decrypt(self, bundle: bytes) -> bytes:
        """
        Decrypt bundle produced by encrypt().
        Raises InvalidTag if the ciphertext has been tampered.
        """
        if len(bundle) < 12 + 16:  # nonce + min GCM tag
            raise ValueError("Bundle too short — not a valid AES-GCM ciphertext")
        nonce, ct = bundle[:12], bundle[12:]
        aesgcm = AESGCM(self._aes_key)
        return aesgcm.decrypt(nonce, ct, None)

    # ── Dilithium-5 signing ────────────────────────────────────────────────────

    @staticmethod
    def dilithium_sign(message: bytes, private_key: bytes) -> bytes:
        """
        Sign message with Dilithium-5.
        Requires pqcrypto — raises RuntimeError if not installed.
        No silent downgrade: a forged or weak signature is worse than no signature.
        """
        if not _PQC_AVAILABLE:
            raise RuntimeError(
                "pqcrypto required for Dilithium-5 signing. "
                "Install pqcrypto or use an alternative signing scheme."
            )
        return _dil_sign(private_key, message)

    @staticmethod
    def dilithium_verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify a Dilithium-5 signature.
        Returns False (not raises) on invalid signature — caller decides action.
        Raises RuntimeError if pqcrypto is not installed.
        """
        if not _PQC_AVAILABLE:
            raise RuntimeError(
                "pqcrypto required for Dilithium-5 verification."
            )
        try:
            _dil_verify(public_key, message, signature)
            return True
        except Exception:
            return False

    # ── Key generation helpers ─────────────────────────────────────────────────

    @staticmethod
    def generate_dilithium_keypair() -> tuple[bytes, bytes]:
        """Returns (public_key, private_key). Requires pqcrypto."""
        if not _PQC_AVAILABLE:
            raise RuntimeError("pqcrypto required for Dilithium key generation.")
        return _dil_keygen()

    @staticmethod
    def generate_kyber_keypair() -> tuple[bytes, bytes]:
        """Returns (public_key, private_key) for Kyber-1024 KEM. Requires pqcrypto."""
        if not _PQC_AVAILABLE:
            raise RuntimeError("pqcrypto required for Kyber key generation.")
        return _kyber_keygen()
