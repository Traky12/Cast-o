"""
Hybrid Encryption — CASTÚO-SYSTEM™ infrastructure (QSEC-001)
X25519 ECDH key agreement + HKDF-SHA-256 + AES-256-GCM authenticated encryption.

Rationale:
  Using `cryptography` (already in requirements) avoids a hard dependency on
  pqcrypto while providing strong forward-secrecy guarantees.  When Kyber-1024
  is ready in the target environment (pqcrypto installed), swap X25519 for
  Kyber in generate_x25519_keypair / encrypt / decrypt without changing the
  calling interface.

Reference:
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §3 (cifrado en tránsito)
  - DPIA-Robotics-2026 §4
  - QSEC-001
"""

from __future__ import annotations

import os
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

_HKDF_INFO = b"castuo-hybrid-encrypt-v1"


# ─── Standalone functional API (QSEC-001) ────────────────────────────────────

def generate_x25519_keypair() -> tuple[X25519PrivateKey, X25519PublicKey]:
    """
    Genera un par de claves X25519 efímeras.

    Returns:
        (private_key, public_key)
    """
    private_key = X25519PrivateKey.generate()
    return private_key, private_key.public_key()


def _derive_aes_key(shared_secret: bytes) -> bytes:
    """Deriva 32 bytes de clave AES-256 desde el secreto compartido ECDH."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_HKDF_INFO,
    ).derive(shared_secret)


def encrypt(data: bytes, recipient_public_key: X25519PublicKey) -> dict[str, bytes]:
    """
    Cifra `data` para el destinatario identificado por `recipient_public_key`.

    Esquema: X25519 ECDH efímero → HKDF-SHA-256 → AES-256-GCM.

    Args:
        data: Bytes en claro a cifrar.
        recipient_public_key: Clave pública X25519 del destinatario.

    Returns:
        dict con claves:
          - ephemeral_public_key (bytes): clave pública efímera, incluir en mensaje
          - nonce (bytes 12): nonce AES-GCM, incluir en mensaje
          - ciphertext (bytes): ciphertext + tag GCM concatenado
    """
    ephemeral_private, ephemeral_public = generate_x25519_keypair()
    shared_secret = ephemeral_private.exchange(recipient_public_key)
    aes_key = _derive_aes_key(shared_secret)

    nonce = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(nonce, data, None)

    return {
        "ephemeral_public_key": ephemeral_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ),
        "nonce": nonce,
        "ciphertext": ciphertext,
    }


def decrypt(encrypted: dict[str, bytes], recipient_private_key: X25519PrivateKey) -> bytes:
    """
    Descifra un mensaje cifrado con `encrypt()`.

    Args:
        encrypted: Dict retornado por `encrypt()`.
        recipient_private_key: Clave privada X25519 del destinatario.

    Returns:
        Bytes en claro.

    Raises:
        cryptography.exceptions.InvalidTag: Si el ciphertext fue alterado.
    """
    ephemeral_pub = X25519PublicKey.from_public_bytes(encrypted["ephemeral_public_key"])
    shared_secret = recipient_private_key.exchange(ephemeral_pub)
    aes_key = _derive_aes_key(shared_secret)
    return AESGCM(aes_key).decrypt(encrypted["nonce"], encrypted["ciphertext"], None)


# ─── Object-oriented API (QuantumSecure class) ────────────────────────────────

class QuantumSecure:
    """
    Cifrado híbrido para API.

    Nota: la pila de Python del proyecto no incluye Kyber-1024 nativo;
    se utiliza envoltura de clave con X25519 + HKDF y cifrado de datos
    con AES-256-GCM.
    """

    def __init__(self, private_key_hex: str | None = None):
        if private_key_hex:
            self._private_key = x25519.X25519PrivateKey.from_private_bytes(
                bytes.fromhex(private_key_hex)
            )
        else:
            self._private_key = x25519.X25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

    @property
    def public_key_hex(self) -> str:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()

    @property
    def private_key_hex(self) -> str:
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()

    @staticmethod
    def generate_keypair() -> dict[str, str]:
        key = x25519.X25519PrivateKey.generate()
        return {
            "private_key_hex": key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            ).hex(),
            "public_key_hex": key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            .hex(),
        }

    def encrypt(self, data: str, recipient_public_key_hex: str | None = None) -> dict[str, Any]:
        recipient_hex = recipient_public_key_hex or self.public_key_hex
        recipient_public = x25519.X25519PublicKey.from_public_bytes(
            bytes.fromhex(recipient_hex)
        )

        ephemeral_private = x25519.X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()
        shared_secret = ephemeral_private.exchange(recipient_public)

        key_encryption_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"castuo-quantum-wrap",
        ).derive(shared_secret)

        data_key = os.urandom(32)
        data_nonce = os.urandom(12)
        wrap_nonce = os.urandom(12)

        wrapped_data_key = AESGCM(key_encryption_key).encrypt(wrap_nonce, data_key, None)
        ciphertext = AESGCM(data_key).encrypt(data_nonce, data.encode("utf-8"), None)

        return {
            "ciphertext": ciphertext.hex(),
            "data_nonce": data_nonce.hex(),
            "wrap_nonce": wrap_nonce.hex(),
            "wrapped_data_key": wrapped_data_key.hex(),
            "ephemeral_public_key": ephemeral_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            ).hex(),
            "recipient_public_key": recipient_hex,
            "suite": "x25519-hkdf-sha256+aes256gcm",
        }

    def decrypt(self, encrypted_data: dict[str, Any]) -> str:
        ephemeral_public = x25519.X25519PublicKey.from_public_bytes(
            bytes.fromhex(encrypted_data["ephemeral_public_key"])
        )
        shared_secret = self._private_key.exchange(ephemeral_public)

        key_encryption_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"castuo-quantum-wrap",
        ).derive(shared_secret)

        data_key = AESGCM(key_encryption_key).decrypt(
            bytes.fromhex(encrypted_data["wrap_nonce"]),
            bytes.fromhex(encrypted_data["wrapped_data_key"]),
            None,
        )

        plaintext = AESGCM(data_key).decrypt(
            bytes.fromhex(encrypted_data["data_nonce"]),
            bytes.fromhex(encrypted_data["ciphertext"]),
            None,
        )
        return plaintext.decode("utf-8")
