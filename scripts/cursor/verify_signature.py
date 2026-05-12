#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASTÚO-SYSTEM™ — Verificación de firma de scripts Cursor (RSA + opcional TPM).
Uso: python verify_signature.py [script_path] [signature_path] [public_key_path]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path("/opt/cursor/cursor.js")
SIGNATURE_PATH = Path("/etc/cursor/signatures/cursor.sig")
PUBLIC_KEY_PATH = Path("/etc/cursor/signatures/cursor_pub.pem")


def verify_cursor_script(
    script_path: Path,
    signature_path: Path,
    public_key_path: Path,
) -> bool:
    if not script_path.exists() or not signature_path.exists() or not public_key_path.exists():
        print("Archivo de script, firma o clave pública no encontrado.")
        return False
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        print("Instalar: pip install cryptography")
        return False

    with open(script_path, "rb") as f:
        script_content = f.read()
    with open(signature_path, "rb") as f:
        signature = f.read()
    with open(public_key_path, "rb") as f:
        public_key = load_pem_public_key(f.read(), backend=default_backend())

    try:
        public_key.verify(signature, script_content, padding.PKCS1v15(), hashes.SHA512())
        print("Firma válida: script verificado.")
        return True
    except Exception as e:
        print(f"Firma inválida: {e}")
        return False


def verify_tpm_integrity() -> bool:
    verifier = Path("/usr/local/bin/tpm_firmware_verifier")
    fw_bin = Path("/firmware/bin/cursor.bin")
    fw_pub = Path("/firmware/keys/cursor.pub.pem")
    fw_sig = Path("/firmware/bin/cursor.sig")
    if not verifier.exists() or not fw_bin.exists():
        print("Verificador TPM o firmware no presente; omitiendo TPM.")
        return True
    result = subprocess.run(
        [str(verifier), str(fw_bin), str(fw_pub), str(fw_sig)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Verificación TPM fallida: {result.stderr}")
        return False
    print("Integridad TPM verificada.")
    return True


def main() -> int:
    script = Path(sys.argv[1]) if len(sys.argv) > 1 else SCRIPT_PATH
    sig = Path(sys.argv[2]) if len(sys.argv) > 2 else SIGNATURE_PATH
    pub = Path(sys.argv[3]) if len(sys.argv) > 3 else PUBLIC_KEY_PATH
    if not verify_cursor_script(script, sig, pub):
        return 1
    if not verify_tpm_integrity():
        return 1
    print("Cursor verificado y listo para ejecución segura.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
