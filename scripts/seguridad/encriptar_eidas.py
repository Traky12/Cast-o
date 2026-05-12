from __future__ import annotations

"""
Compatibilidad "eIDAS-like" (offline-first).

Este script NO implementa XAdES real. En su lugar:
- usa AES-256-GCM (si `cryptography` está disponible)
- deja el encaje para firma cualificada como placeholder.

Principio Sabionda-Omega: seguridad útil, sin dependencias obligatorias.
"""

import json
import os

from scripts.seguridad.encriptar_aes_gcm import EncryptedBlob, decrypt_text, encrypt_text


def main() -> int:
    key = os.urandom(32)
    payload = {"consentimiento": True, "territorio": "demo", "dato": "minimo"}
    blob: EncryptedBlob = encrypt_text(json.dumps(payload, ensure_ascii=False), key)
    recovered = decrypt_text(blob, key)

    print("algorithm:", blob.algorithm)
    print("blob:", json.dumps(blob.__dict__, ensure_ascii=False))
    print("recovered:", recovered)
    print("xades_signature:", "PLACEHOLDER: firma XAdES cualificada (si aplica)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

