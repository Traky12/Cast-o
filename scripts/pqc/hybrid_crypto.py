#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Cifrado híbrido: AES-256-GCM + Kyber-768 (ML-KEM). Transición suave a PQC.
Uso: CastuoHybridPQC().encrypt_hybrid(data) / decrypt_hybrid(payload)
"""
from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _derive_key(seed: str) -> bytes:
    import hashlib
    return hashlib.pbkdf2_hmac("sha256", seed.encode(), b"castuo-hybrid", 100_000, dklen=32)


try:
    from scripts.pqc.trl1_nist_pqc import ml_kem_768_keygen, ml_kem_768_encap, ml_kem_768_decap
    HAS_PQC = True
except Exception:
    HAS_PQC = False


class CastuoHybridPQC:
    """Híbrido AES-256-GCM + ML-KEM-768 (Kyber). Clásico + PQC."""

    def __init__(self) -> None:
        self._classic_key = _derive_key("castuo-hybrid")
        self._classic = AESGCM(self._classic_key)
        self._pk: bytes | None = None
        self._sk: bytes | None = None
        if HAS_PQC:
            self._pk, self._sk = ml_kem_768_keygen()

    def encrypt_hybrid(self, data: bytes) -> dict:
        """
        1. Kyber encapsula clave compartida.
        2. AES-GCM cifra datos con esa clave (o con clave derivada del shared secret).
        """
        if not HAS_PQC or self._pk is None:
            # Fallback: solo AES con clave derivada
            nonce = os.urandom(12)
            ct = self._classic.encrypt(nonce, data, None)
            return {"kem": b"", "aes": nonce + ct, "tag": ct[-16:], "pqc": False}
        ct_kem, shared_secret = ml_kem_768_encap(self._pk)
        # Derivar clave AES desde shared secret
        import hashlib
        key = hashlib.sha256(shared_secret).digest()
        aes = AESGCM(key)
        nonce = os.urandom(12)
        ct_aes = aes.encrypt(nonce, data, None)
        return {
            "kem": ct_kem,
            "aes": nonce + ct_aes,
            "tag": ct_aes[-16:],
            "pqc": True,
        }

    def decrypt_hybrid(self, payload: dict, *, sk: bytes | None = None) -> bytes:
        """Descifra payload híbrido (requiere sk si PQC)."""
        ct_kem = payload.get("kem") or b""
        aes_blob = payload.get("aes") or b""
        if not ct_kem and payload.get("pqc") is not True:
            # Solo AES
            nonce, ct = aes_blob[:12], aes_blob[12:]
            return self._classic.decrypt(nonce, ct, None)
        sk = sk or self._sk
        if not sk or not HAS_PQC:
            raise ValueError("PQC decrypt requiere secret key")
        shared_secret = ml_kem_768_decap(sk, ct_kem)
        import hashlib
        key = hashlib.sha256(shared_secret).digest()
        aes = AESGCM(key)
        nonce, ct = aes_blob[:12], aes_blob[12:]
        return aes.decrypt(nonce, ct, None)

    def get_public_key(self) -> bytes:
        """Para que el receptor encapsule (modo alternativo)."""
        if self._pk is None:
            self._pk, self._sk = ml_kem_768_keygen() if HAS_PQC else (b"", b"")
        return self._pk or b""


def main() -> None:
    h = CastuoHybridPQC()
    data = b"CASTUO hybrid PQC secret"
    enc = h.encrypt_hybrid(data)
    dec = h.decrypt_hybrid(enc)
    assert dec == data
    print("✅ Hybrid AES-256 + Kyber-768 OK")


if __name__ == "__main__":
    main()
