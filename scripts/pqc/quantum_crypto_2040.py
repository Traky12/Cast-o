#!/usr/bin/env python3
"""
SABIONDA_OMEGA_GLOBAL_2040 — QuantumCrypto2040.
Cifrado híbrido: Kyber-1024/768 + AES-256-GCM + HMAC-SHA512 (AES-512 conceptual 2040).
"""
from __future__ import annotations

import os
import sys
import time

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from cryptography.hazmat.primitives import hashes, hmac as hmacc
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

backend = default_backend()

# PQC: oqs or stubs
try:
    from oqs import KeyEncapsulation, Signature
    HAS_OQS = True
except ImportError:
    HAS_OQS = False
    KeyEncapsulation = None
    Signature = None

# Geo adapter for region config
try:
    from scripts.omega.geo.universal_adapter import UniversalGeoAdapter
except ImportError:
    try:
        sys.path.insert(0, REPO_ROOT)
        from scripts.omega.geo.universal_adapter import UniversalGeoAdapter
    except ImportError:
        UniversalGeoAdapter = None


class GaiaLegalOracle:
    def register_crypto_keys(self, metadata: dict) -> str:
        return f"tx_gaia_keys_{int(time.time())}"


def _kem_keygen(alg: str) -> tuple[bytes, bytes]:
    if HAS_OQS and KeyEncapsulation:
        kem = KeyEncapsulation(alg)
        kem.generate_keypair()
        return kem.export_public_key(), kem.export_secret_key()
    return os.urandom(1184), os.urandom(2400)


def _kem_encap(pk: bytes, alg: str) -> tuple[bytes, bytes]:
    if HAS_OQS and KeyEncapsulation:
        kem = KeyEncapsulation(alg)
        kem.import_public_key(pk)
        return kem.encap_secret()
    return os.urandom(1568), os.urandom(32)


def _kem_decap(sk: bytes, ct: bytes, alg: str) -> bytes:
    if HAS_OQS and KeyEncapsulation:
        kem = KeyEncapsulation(alg)
        kem.import_secret_key(sk)
        return kem.decap_secret(ct)
    return (sk + ct)[:32]


def _sig_keygen(alg: str) -> tuple[bytes, bytes]:
    if HAS_OQS and Signature:
        sig = Signature(alg)
        sig.generate_keypair()
        return sig.export_public_key(), sig.export_secret_key()
    return os.urandom(1312), os.urandom(2560)


class QuantumCrypto2040:
    def __init__(self) -> None:
        self.backend = backend
        self.gaia_oracle = GaiaLegalOracle()

    def generate_quantum_keys(self, region: str) -> dict:
        config = (UniversalGeoAdapter().adapt(region) if UniversalGeoAdapter else {}) or {
            "encryption": "AES-512+Kyber-1024",
            "norms": [],
        }
        enc = config.get("encryption", "AES-256+Kyber-768")

        kem_alg = "Kyber1024" if "Kyber-1024" in enc or "1024" in enc else "Kyber768"
        sig_alg = "Dilithium5" if "ML-DSA-65" in enc or "65" in enc else "Dilithium2"

        kem_pk, kem_sk = _kem_keygen(kem_alg)
        sig_pk, sig_sk = _sig_keygen(sig_alg)

        key_metadata = {
            "region": region,
            "kem_algorithm": kem_alg,
            "sig_algorithm": sig_alg,
            "generated_at": int(time.time()),
            "compliance": config.get("norms", []),
        }
        tx_hash = self.gaia_oracle.register_crypto_keys(key_metadata)

        return {
            "kem_public": kem_pk,
            "kem_private": kem_sk,
            "sig_public": sig_pk,
            "sig_private": sig_sk,
            "metadata": key_metadata,
            "gaiachain_tx": tx_hash,
        }

    def hybrid_encrypt(self, data: bytes, public_keys: dict) -> dict:
        kem_pk = public_keys.get("kem_public")
        if not kem_pk:
            raise ValueError("kem_public required")
        kem_alg = "Kyber1024" if len(kem_pk) > 1200 else "Kyber768"
        ciphertext_kem, shared_secret = _kem_encap(kem_pk, kem_alg)

        kdf = HKDF(
            algorithm=hashes.SHA512(),
            length=96,
            salt=None,
            info=b"castuo_quantum_2040",
            backend=self.backend,
        )
        keys = kdf.derive(shared_secret[:32] if len(shared_secret) >= 32 else shared_secret + b"\0" * 32)
        aes_key = keys[:32]
        hmac_key = keys[32:64]

        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ct = encryptor.update(data) + encryptor.finalize()
        tag = encryptor.tag

        h = hmacc.HMAC(hmac_key, hashes.SHA512(), backend=self.backend)
        h.update(iv + ct + tag)
        hmac_value = h.finalize()

        return {
            "kem_ciphertext": ciphertext_kem,
            "aes_iv": iv,
            "aes_ct": ct,
            "aes_tag": tag,
            "hmac": hmac_value,
            "algorithm": "Hybrid_PQC_2040",
        }

    def hybrid_decrypt(self, payload: dict, private_keys: dict) -> bytes:
        kem_sk = private_keys.get("kem_private")
        if not kem_sk:
            raise ValueError("kem_private required")
        kem_alg = "Kyber1024" if len(kem_sk) > 2000 else "Kyber768"
        shared_secret = _kem_decap(kem_sk, payload["kem_ciphertext"], kem_alg)

        kdf = HKDF(
            algorithm=hashes.SHA512(),
            length=96,
            salt=None,
            info=b"castuo_quantum_2040",
            backend=self.backend,
        )
        keys = kdf.derive(shared_secret[:32] if len(shared_secret) >= 32 else shared_secret + b"\0" * 32)
        aes_key = keys[:32]
        hmac_key = keys[32:64]

        h = hmacc.HMAC(hmac_key, hashes.SHA512(), backend=self.backend)
        h.update(payload["aes_iv"] + payload["aes_ct"] + payload["aes_tag"])
        try:
            h.verify(payload["hmac"])
        except Exception:
            raise ValueError("HMAC verification failed (possible tampering)")

        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(payload["aes_iv"], payload["aes_tag"]),
            backend=self.backend,
        )
        decryptor = cipher.decryptor()
        return decryptor.update(payload["aes_ct"]) + decryptor.finalize()
