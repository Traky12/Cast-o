# backend/maya_segura/multi_crypto_engine.py
# 7 algoritmos simultáneos: KYBER2048, Ed25519, AES256-GCM, SHA3, HKDF, ChaCha20, Merkle.

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Dict, List

CRYPTO_LAYERS = 7


def layer_kyber_sim(data: bytes) -> bytes:
    return b"KYBER:" + hashlib.sha3_512(data).digest()[:32]


def layer_ed25519_sim(data: bytes) -> bytes:
    return hashlib.sha3_512(data + b"ED25519").digest()[:64]


def layer_aes_gcm_sim(data: bytes) -> bytes:
    return hashlib.sha3_256(data + b"AES256GCM").digest()


def layer_sha3(data: bytes) -> bytes:
    return hashlib.sha3_512(data).digest()


def layer_hkdf_sim(data: bytes, salt: bytes = b"MAYA_TORUS") -> bytes:
    return hmac.new(salt, data, hashlib.sha256).digest()


def layer_chacha_sim(data: bytes) -> bytes:
    return hashlib.sha3_256(data + b"CHACHA20").digest()


def layer_merkle_sim(data: bytes) -> bytes:
    return hashlib.sha256(data + b"MERKLE").digest()


def encrypt_multi(data: bytes | dict) -> bytes:
    """Aplica 7 capas cripto (simuladas)."""
    if isinstance(data, dict):
        import json
        data = json.dumps(data, sort_keys=True).encode()
    d = data
    for fn in (layer_kyber_sim, layer_ed25519_sim, layer_aes_gcm_sim, layer_sha3, layer_hkdf_sim, layer_chacha_sim, layer_merkle_sim):
        d = fn(d)
    return d
