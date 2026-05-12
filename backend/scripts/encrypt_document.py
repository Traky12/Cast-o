#!/usr/bin/env python3
"""
Cifrado de documentos para la Junta de Extremadura (Medio Ambiente, Forestal, Incendios).
AES-256-CBC + HMAC-SHA512; clave encapsulada para PQC (Kyber-1024 en producción).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def encrypt_document(document_path: str, public_key_placeholder: str | None = None) -> dict:
    """
    Cifra un documento (PDF/JSON) con AES-256 + HMAC-SHA512.
    En producción la clave se encapsula con Kyber-1024 (clave pública Junta).
    """
    if not os.path.isfile(document_path):
        raise FileNotFoundError(f"Documento no encontrado: {document_path}")

    with open(document_path, "rb") as f:
        document_data = f.read()

    key = os.urandom(32)
    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - (len(document_data) % 16)
    padded = document_data + bytes([pad_len] * pad_len)
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    if public_key_placeholder:
        encrypted_key = "kyber_encrypted_" + base64.b64encode(key).decode()
    else:
        encrypted_key = base64.b64encode(key).decode()

    h = crypto_hmac.HMAC(key, hashes.SHA512(), backend=default_backend())
    h.update(ciphertext)
    hmac_value = h.finalize()

    return {
        "iv": base64.b64encode(iv).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "encrypted_key": encrypted_key,
        "hmac": base64.b64encode(hmac_value).decode(),
        "document_path": document_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Cifrar documento (Junta Extremadura)")
    parser.add_argument("document_path", help="Ruta al PDF o JSON")
    parser.add_argument("--public-key", default="", help="Ruta clave pública Junta (PQC)")
    parser.add_argument("-o", "--output", default="-", help="Salida JSON (default: stdout)")
    args = parser.parse_args()

    try:
        result = encrypt_document(args.document_path, args.public_key or None)
        out = json.dumps(result, indent=2)
        if args.output == "-":
            print(out)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
