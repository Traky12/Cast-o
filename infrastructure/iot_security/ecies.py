"""
ECIES for IoT — CASTÚO-SYSTEM™ infrastructure (QSEC-002)
ECDH P-384 + HKDF-SHA-384 + AES-256-GCM for device-to-backend secure channels.

Rationale:
  Raspberry Pi / Arduino-class devices have hardware accelerators for NIST P-384.
  This module provides encrypt/decrypt compatible with those constraints.
  Larger devices can upgrade to X25519 or Kyber via crypto.py.

Reference:
  - DPIA-Robotics-2026 §4 (cifrado en tránsito IoT)
  - QSEC-002
"""

from __future__ import annotations

import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDH,
    SECP384R1,
    EllipticCurvePrivateKey,
    EllipticCurvePublicKey,
    generate_private_key,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_CURVE = SECP384R1()
_HKDF_INFO = b"castuo-ecies-iot-v1"


def generate_p384_keypair() -> tuple[EllipticCurvePrivateKey, EllipticCurvePublicKey]:
    """Genera par de claves P-384 para un dispositivo IoT."""
    private_key = generate_private_key(_CURVE)
    return private_key, private_key.public_key()


def _derive_key(shared_secret: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA384(),
        length=32,
        salt=None,
        info=_HKDF_INFO,
    ).derive(shared_secret)


def encrypt(data: bytes, recipient_public_key: EllipticCurvePublicKey) -> dict[str, bytes]:
    """
    Cifra `data` con ECIES usando P-384 + HKDF-SHA-384 + AES-256-GCM.

    Args:
        data: Bytes en claro.
        recipient_public_key: Clave pública P-384 del dispositivo / backend destino.

    Returns:
        dict con:
          - ephemeral_public_key (bytes): punto efímero, codificado sin compresión
          - nonce (bytes 12): nonce AES-GCM
          - ciphertext (bytes): ciphertext + tag GCM
    """
    ephemeral_private = generate_private_key(_CURVE)
    shared_secret = ephemeral_private.exchange(ECDH(), recipient_public_key)
    aes_key = _derive_key(shared_secret)

    nonce = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, data, None)

    return {
        "ephemeral_public_key": ephemeral_private.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        ),
        "nonce": nonce,
        "ciphertext": ciphertext,
    }


def decrypt(encrypted: dict[str, bytes], recipient_private_key: EllipticCurvePrivateKey) -> bytes:
    """
    Descifra un mensaje cifrado con `encrypt()`.

    Args:
        encrypted: Dict retornado por `encrypt()`.
        recipient_private_key: Clave privada P-384 del destinatario.

    Returns:
        Bytes en claro.

    Raises:
        cryptography.exceptions.InvalidTag: Si el ciphertext fue alterado.
    """
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey
    from cryptography.hazmat.backends import default_backend

    ephemeral_pub = EllipticCurvePublicKey.from_encoded_point(
        _CURVE, encrypted["ephemeral_public_key"]
    )
    shared_secret = recipient_private_key.exchange(ECDH(), ephemeral_pub)
    aes_key = _derive_key(shared_secret)
    return AESGCM(aes_key).decrypt(encrypted["nonce"], encrypted["ciphertext"], None)
