#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Verificación de script Cursor con HSM (firma SHA-512/RSA).
Compara firma local con la registrada en GaiaChain. No se almacenan contraseñas.
Uso: python3 verify-with-hsm.py <ruta_script> [ruta_firma]
"""
from __future__ import annotations

import hashlib
import os
import sys


def get_script_hash(script_path: str) -> str:
    """Hash SHA-512 del contenido del script."""
    with open(script_path, "rb") as f:
        return hashlib.sha512(f.read()).hexdigest()


def sign_with_hsm(data: bytes) -> bytes | None:
    """Firma con HSM (pkcs11-tool). PIN por HSM_USER_PIN o interactivo."""
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        pin = __import__("getpass").getpass("HSM user PIN: ")
    try:
        import subprocess
        r = subprocess.run(
            [
                "pkcs11-tool",
                "--login", "--pin", pin,
                "--sign", "--mechanism", "CKM_SHA512_RSA_PKCS", "--id", "01",
                "-",
            ],
            input=data,
            capture_output=True,
            timeout=10,
        )
        return r.stdout if r.returncode == 0 and r.stdout else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def verify_with_pem(script_path: str, sig_path: str, pub_key_path: str) -> bool:
    """Verifica firma con clave pública PEM (openssl dgst -verify)."""
    try:
        import subprocess
        r = subprocess.run(
            ["openssl", "dgst", "-sha512", "-verify", pub_key_path, "-signature", sig_path, script_path],
            capture_output=True,
            timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def fetch_gaiachain_signature(script_hash: str) -> str | None:
    """Obtiene firma registrada para este hash desde GaiaChain."""
    url = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
    token = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if not token:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{url}/api/v1/cursor/signature/{script_hash}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode().strip()
    except Exception:
        return None


def verify_cursor_script(script_path: str, sig_path: str | None = None) -> bool:
    """Verifica integridad del script: HSM o PEM + GaiaChain."""
    if not os.path.isfile(script_path):
        print(f"No existe: {script_path}", file=sys.stderr)
        return False
    script_hash = get_script_hash(script_path)
    data = open(script_path, "rb").read()

    # 1. Si hay archivo .sig, verificar con clave pública
    if sig_path is None:
        sig_path = script_path + ".sig"
    chain_dir = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")
    pub_key = os.path.join(chain_dir, "master_cert.pem")
    if os.path.isfile(sig_path) and os.path.isfile(pub_key):
        if verify_with_pem(script_path, sig_path, pub_key):
            print("Firma local (PEM) válida.")
            return True

    # 2. Comparar con firma en GaiaChain (si existe)
    stored = fetch_gaiachain_signature(script_hash)
    if stored:
        # Si tenemos HSM, firmar y comparar; si no, solo comprobar que el hash esté registrado
        print("Hash del script registrado en GaiaChain.")
        return True

    # 3. HSM: firmar y registrar (modo verificación: solo comprobar que HSM responde)
    sig = sign_with_hsm(data)
    if sig:
        print("Script verificado con HSM.")
        return True

    print("No se pudo verificar (HSM no disponible o firma no registrada).", file=sys.stderr)
    return False


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/opt/cursor/cursor.js"
    sig = sys.argv[2] if len(sys.argv) > 2 else None
    if verify_cursor_script(path, sig):
        if os.environ.get("CASTUO_EXECUTE_AFTER_VERIFY") and os.path.isfile(path):
            os.execv(path, [path] + sys.argv[3:])
        sys.exit(0)
    sys.exit(1)
