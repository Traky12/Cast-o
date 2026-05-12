"""
Cifrado híbrido orientado a soberanía de datos: KEM Kyber768 (liboqs / oqs) + AES-256-GCM.

El paquete PyPI `pqcrypto` citado en borradores no es el estándar de mantenimiento del ecosistema OQS;
aquí se usa `oqs` cuando está instalado y compilado contra liboqs. Sin `oqs`, solo están disponibles
helpers AES-GCM con clave explícita (32 bytes) para pruebas locales.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any, Dict, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_NONCE_LEN = 12
_AES_KEY_LEN = 32
_KEM_ALG = "Kyber768"
_INFO = b"castuo-hybrid-kyber768-aes256gcm-v1"


def _hkdf_key(shared_secret: bytes) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=_AES_KEY_LEN,
        salt=None,
        info=_INFO,
        backend=default_backend(),
    )
    return hkdf.derive(shared_secret)


def _try_oqs():
    try:
        import oqs  # type: ignore

        return oqs
    except ImportError:
        return None


def generate_kyber_keypair() -> Tuple[bytes, bytes]:
    """Genera par Kyber768 (pública, secreta) en binario crudo."""
    oqs = _try_oqs()
    if oqs is None:
        raise ImportError(
            "Kyber768 requiere el paquete `oqs` (liboqs-python) y liboqs en el sistema. "
            "Ver scripts/crypto/requirements.txt y documentación OQS."
        )
    with oqs.KeyEncapsulation(_KEM_ALG) as kem:
        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()
    return public_key, secret_key


def encrypt_hybrid_bundle(plaintext: str, recipient_public_key: bytes) -> str:
    """
    Cifra `plaintext` con AES-256-GCM; la clave sale de un encapsulado Kyber768 hacia la clave pública dada.
    Devuelve JSON (texto) con campos base64url-safe.
    """
    oqs = _try_oqs()
    if oqs is None:
        raise ImportError("Instala `oqs` (liboqs-python) para encapsulado Kyber768.")

    data = plaintext.encode("utf-8")
    with oqs.KeyEncapsulation(_KEM_ALG) as kem:
        ciphertext_kem, shared_secret = kem.encap_secret(recipient_public_key)

    aes_key = _hkdf_key(shared_secret)
    nonce = secrets.token_bytes(_NONCE_LEN)
    aes = AESGCM(aes_key)
    ct = aes.encrypt(nonce, data, associated_data=ciphertext_kem)

    bundle: Dict[str, Any] = {
        "v": 1,
        "kem": _KEM_ALG,
        "kem_ciphertext": base64.b64encode(ciphertext_kem).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ct).decode("ascii"),
    }
    return json.dumps(bundle, separators=(",", ":"))


def decrypt_hybrid_bundle(bundle_json: str, secret_key: bytes) -> str:
    """Descifra el bundle generado por `encrypt_hybrid_bundle`."""
    oqs = _try_oqs()
    if oqs is None:
        raise ImportError("Instala `oqs` (liboqs-python) para decapsulado Kyber768.")

    bundle = json.loads(bundle_json)
    ciphertext_kem = base64.b64decode(bundle["kem_ciphertext"])
    nonce = base64.b64decode(bundle["nonce"])
    ct = base64.b64decode(bundle["ciphertext"])

    with oqs.KeyEncapsulation(_KEM_ALG, secret_key) as kem:
        shared_secret = kem.decap_secret(ciphertext_kem)

    aes_key = _hkdf_key(shared_secret)
    aes = AESGCM(aes_key)
    plain = aes.decrypt(nonce, ct, associated_data=ciphertext_kem)
    return plain.decode("utf-8")


def encrypt_aes_gcm(plaintext: str, key32: bytes) -> str:
    """AES-256-GCM autónomo (sin PQC); clave de 32 bytes. Útil cuando Kyber no está en el runtime."""
    if len(key32) != _AES_KEY_LEN:
        raise ValueError("La clave AES debe tener 32 bytes.")
    nonce = secrets.token_bytes(_NONCE_LEN)
    aes = AESGCM(key32)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    out = {"v": 1, "mode": "aes-256-gcm", "nonce": base64.b64encode(nonce).decode("ascii"), "c": base64.b64encode(ct).decode("ascii")}
    return json.dumps(out, separators=(",", ":"))


def decrypt_aes_gcm(bundle_json: str, key32: bytes) -> str:
    if len(key32) != _AES_KEY_LEN:
        raise ValueError("La clave AES debe tener 32 bytes.")
    bundle = json.loads(bundle_json)
    nonce = base64.b64decode(bundle["nonce"])
    ct = base64.b64decode(bundle["c"])
    aes = AESGCM(key32)
    plain = aes.decrypt(nonce, ct, associated_data=None)
    return plain.decode("utf-8")


def generate_aes_key32_from_env(env_name: str = "CASTUO_SYMMETRIC_KEY32_B64") -> bytes:
    """Lee clave simétrica desde variable de entorno (base64 de 32 bytes)."""
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        raise KeyError(f"Falta {env_name} para operaciones AES locales.")
    key = base64.b64decode(raw)
    if len(key) != _AES_KEY_LEN:
        raise ValueError(f"{env_name} debe decodificar a exactamente 32 bytes.")
    return key


# Alias legibles para integraciones que esperan nombres cortos
encrypt = encrypt_hybrid_bundle
decrypt = decrypt_hybrid_bundle
