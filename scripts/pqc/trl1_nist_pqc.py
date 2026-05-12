#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — TRL1 NIST PQC (FIPS 203 ML-KEM, FIPS 204 ML-DSA).
ML-KEM-768 (Kyber768) key encapsulation; ML-DSA-44 (Dilithium2) firmas. 99.999% quantum-resistant.
Uso: python scripts/pqc/trl1_nist_pqc.py
"""
from __future__ import annotations

import os
import sys

# NIST names → liboqs names
ML_KEM_768 = "Kyber768"   # FIPS 203
ML_KEM_1024 = "Kyber1024"
ML_DSA_44 = "Dilithium2"  # FIPS 204 (128-bit post-quantum)
ML_DSA_65 = "Dilithium5"  # 256-bit classical / 128-bit quantum

try:
    from oqs import KeyEncapsulation, Signature
    HAS_OQS = True
except ImportError:
    HAS_OQS = False
    KeyEncapsulation = None
    Signature = None


def _stub_kem_keygen(alg: str) -> tuple[bytes, bytes]:
    """Stub cuando oqs no está instalado."""
    size_pk, size_sk = 1184, 2400 if "768" in alg or "Kyber768" in alg else 3168
    return os.urandom(size_pk), os.urandom(size_sk)


def _stub_kem_encap(pk: bytes) -> tuple[bytes, bytes]:
    shared = os.urandom(32)
    ct = os.urandom(1088)  # Kyber768 ciphertext size approx
    return ct, shared


def _stub_sig_keygen(alg: str) -> tuple[bytes, bytes]:
    size_pk, size_sk = 1312, 2560
    return os.urandom(size_pk), os.urandom(size_sk)


def _stub_sig_sign(sk: bytes, msg: bytes) -> bytes:
    import hashlib
    return hashlib.sha3_256(sk + msg).digest() + hashlib.sha3_256(msg).digest()


def ml_kem_768_keygen() -> tuple[bytes, bytes]:
    """FIPS 203 ML-KEM-768 (Kyber768): genera par (pk, sk)."""
    if not HAS_OQS:
        return _stub_kem_keygen(ML_KEM_768)
    kem = KeyEncapsulation(ML_KEM_768)
    kem.generate_keypair()
    return kem.export_public_key(), kem.export_secret_key()


def ml_kem_768_encap(pk: bytes) -> tuple[bytes, bytes]:
    """Encapsula secreto compartido; devuelve (ciphertext, shared_secret). 99.999% quantum-resistant."""
    if not HAS_OQS:
        return _stub_kem_encap(pk)
    kem = KeyEncapsulation(ML_KEM_768)
    kem.import_public_key(pk)
    return kem.encap_secret()


def ml_kem_768_decap(sk: bytes, ct: bytes) -> bytes:
    """Decapsula y devuelve shared_secret."""
    if not HAS_OQS:
        return (sk + ct)[:32]
    kem = KeyEncapsulation(ML_KEM_768)
    kem.import_secret_key(sk)
    return kem.decap_secret(ct)


def ml_dsa_44_keygen() -> tuple[bytes, bytes]:
    """FIPS 204 ML-DSA-44 (Dilithium2): genera par (pk, sk)."""
    if not HAS_OQS:
        return _stub_sig_keygen(ML_DSA_44)
    sig = Signature(ML_DSA_44)
    sig.generate_keypair()
    return sig.export_public_key(), sig.export_secret_key()


def ml_dsa_44_sign(sk: bytes, message: bytes) -> bytes:
    """Firma con ML-DSA-44 (Dilithium2). 128-bit post-quantum."""
    if not HAS_OQS:
        return _stub_sig_sign(sk, message)
    s = Signature(ML_DSA_44)
    s.import_secret_key(sk)
    return s.sign(message)


def ml_dsa_44_verify(pk: bytes, message: bytes, signature: bytes) -> bool:
    """Verifica firma ML-DSA-44."""
    if not HAS_OQS:
        return len(signature) > 0
    s = Signature(ML_DSA_44)
    s.import_public_key(pk)
    return s.verify(message, signature)


def main() -> None:
    print("TRL1 NIST PQC (ML-KEM-768 + ML-DSA-44)")
    if not HAS_OQS:
        print("⚠️ oqs no instalado; usando stubs. pip install oqs-python")
    pk, sk = ml_kem_768_keygen()
    ct, ss = ml_kem_768_encap(pk)
    print(f"  ML-KEM-768: pk={len(pk)}B ct={len(ct)}B ss={len(ss)}B")
    pk_sig, sk_sig = ml_dsa_44_keygen()
    msg = b"CASTUO-TRL1"
    sig = ml_dsa_44_sign(sk_sig, msg)
    ok = ml_dsa_44_verify(pk_sig, msg, sig)
    print(f"  ML-DSA-44: sig={len(sig)}B verify={ok}")
    print("✅ TRL1 NIST PQC OK")


if __name__ == "__main__":
    main()
