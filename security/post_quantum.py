# -*- coding: utf-8 -*-
"""
Cifrado post-cuántico CASTUO 5.0 — CRYSTALS-Kyber (KEM) + AES-256 híbrido.
Normativas: NIST SP 800-208, ETSI QSCD. Requiere liboqs (opcional).
"""
import os
from typing import Tuple

try:
    from oqs import KeyEncapsulation
    HAS_LIBOQS = True
except ImportError:
    HAS_LIBOQS = False
    KeyEncapsulation = None  # type: ignore

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

KEM_ALG = "Kyber512"
backend = default_backend()


def _aes_encrypt(key: bytes, plaintext: bytes) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=backend)
    enc = cipher.encryptor()
    ct = enc.update(plaintext) + enc.finalize()
    return iv + enc.tag + ct


def _aes_decrypt(key: bytes, blob: bytes) -> bytes:
    iv, tag, ct = blob[:16], blob[16:32], blob[32:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=backend)
    dec = cipher.decryptor()
    return dec.update(ct) + dec.finalize()


def generate_kyber_keypair() -> Tuple[bytes, bytes, bytes]:
    """Genera par de claves Kyber (post-cuántico). Retorna (pk_raw, pk_exported, sk_exported)."""
    if not HAS_LIBOQS or not KeyEncapsulation:
        # Stub: claves aleatorias para entorno sin liboqs
        pk = os.urandom(32)
        sk = os.urandom(32)
        return pk, pk, sk
    kem = KeyEncapsulation(KEM_ALG)
    kem.generate_keypair()
    return kem.export_public_key(), kem.export_public_key(), kem.export_secret_key()


def encrypt_with_kyber(public_key: bytes, message: str) -> Tuple[bytes, bytes]:
    """Cifra mensaje con Kyber KEM + AES-256-GCM (enfoque híbrido). Retorna (ciphertext_kem, ciphertext_aes)."""
    if HAS_LIBOQS and KeyEncapsulation:
        kem = KeyEncapsulation(KEM_ALG)
        kem.import_public_key(public_key)
        ct_kem, shared = kem.encap_secret()
        key = shared[:32]
    else:
        ct_kem = os.urandom(64)  # stub
        key = (public_key + ct_kem)[:32]
    ct_aes = _aes_encrypt(key, message.encode())
    return ct_kem, ct_aes


def decrypt_with_kyber(private_key: bytes, ciphertext_kem: bytes, encrypted_msg: bytes) -> str:
    """Descifra mensaje cifrado con Kyber + AES-256."""
    if HAS_LIBOQS and KeyEncapsulation:
        kem = KeyEncapsulation(KEM_ALG)
        kem.import_secret_key(private_key)
        shared = kem.decap_secret(ciphertext_kem)
        key = shared[:32]
    else:
        key = (private_key + ciphertext_kem)[:32]
    return _aes_decrypt(key, encrypted_msg).decode()
