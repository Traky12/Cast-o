from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EncryptedBlob:
    algorithm: str
    nonce_b64: str
    ciphertext_b64: str


def _require_cryptography():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Falta dependencia opcional 'cryptography'. "
            "Instala con: pip install cryptography"
        ) from e
    return AESGCM


def encrypt_text(plaintext: str, key: bytes) -> EncryptedBlob:
    AESGCM = _require_cryptography()
    if len(key) != 32:
        raise ValueError("La clave debe ser de 32 bytes (AES-256).")
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data=None)
    return EncryptedBlob(
        algorithm="AES-256-GCM",
        nonce_b64=base64.b64encode(nonce).decode("ascii"),
        ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"),
    )


def decrypt_text(blob: EncryptedBlob, key: bytes) -> str:
    AESGCM = _require_cryptography()
    if blob.algorithm != "AES-256-GCM":
        raise ValueError("Algoritmo no soportado.")
    if len(key) != 32:
        raise ValueError("La clave debe ser de 32 bytes (AES-256).")
    nonce = base64.b64decode(blob.nonce_b64)
    ciphertext = base64.b64decode(blob.ciphertext_b64)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return plaintext.decode("utf-8")


def main() -> int:
    # Demo local (no persiste claves).
    key = os.urandom(32)
    payload = {"territorio": "La Encina Resistente", "dato": "humedad=10%"}
    blob = encrypt_text(json.dumps(payload, ensure_ascii=False), key)
    recovered = decrypt_text(blob, key)
    print("algorithm:", blob.algorithm)
    print("blob_json:", json.dumps(blob.__dict__, ensure_ascii=False))
    print("recovered:", recovered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

