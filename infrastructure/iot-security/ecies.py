from __future__ import annotations

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
import os


class ECIES:
    """ECIES con ECDH P-384 + HKDF(SHA-384) + AES-256-GCM."""

    def __init__(self, private_key_pem: str | None = None):
        if private_key_pem:
            self.private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None,
            )
        else:
            self.private_key = ec.generate_private_key(ec.SECP384R1())

    @property
    def public_key_pem(self) -> str:
        return self.private_key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

    @property
    def private_key_pem(self) -> str:
        return self.private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        ).decode("utf-8")

    @staticmethod
    def generate_keypair() -> dict[str, str]:
        key = ec.generate_private_key(ec.SECP384R1())
        return {
            "private_key_pem": key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            ).decode("utf-8"),
            "public_key_pem": key.public_key()
            .public_bytes(
                encoding=Encoding.PEM,
                format=PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8"),
        }

    def encrypt(self, data: str, recipient_public_key_pem: str) -> bytes:
        recipient_public_key = serialization.load_pem_public_key(
            recipient_public_key_pem.encode("utf-8")
        )
        ephemeral_private = ec.generate_private_key(ec.SECP384R1())

        shared_key = ephemeral_private.exchange(ec.ECDH(), recipient_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA384(),
            length=32,
            salt=None,
            info=b"ecies-iot-castuo",
        ).derive(shared_key)

        nonce = os.urandom(12)
        ciphertext = AESGCM(derived_key).encrypt(nonce, data.encode("utf-8"), None)

        ephemeral_public_pem = ephemeral_private.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        )

        eph_len = len(ephemeral_public_pem).to_bytes(2, "big")
        return eph_len + ephemeral_public_pem + nonce + ciphertext

    def decrypt(self, encrypted_data: bytes) -> str:
        eph_len = int.from_bytes(encrypted_data[:2], "big")
        eph_start = 2
        eph_end = eph_start + eph_len

        ephemeral_public_pem = encrypted_data[eph_start:eph_end]
        nonce = encrypted_data[eph_end:eph_end + 12]
        ciphertext = encrypted_data[eph_end + 12:]

        ephemeral_public_key = serialization.load_pem_public_key(ephemeral_public_pem)
        shared_key = self.private_key.exchange(ec.ECDH(), ephemeral_public_key)

        derived_key = HKDF(
            algorithm=hashes.SHA384(),
            length=32,
            salt=None,
            info=b"ecies-iot-castuo",
        ).derive(shared_key)

        plaintext = AESGCM(derived_key).decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
