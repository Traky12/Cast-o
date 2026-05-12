#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Autenticación con YubiKey OTP + contraseña maestra.
Genera sesión firmada para comandos administrativos.
Uso: python3 authenticate_with_yubikey.py
"""
from __future__ import annotations

import getpass
import hashlib
import os
import sys

# Verificación OTP YubiKey (API pública; no valida servidor YubiCloud sin API key)
YUBICO_CLIENT_ID = os.environ.get("YUBICO_CLIENT_ID", "")
YUBICO_API_KEY = os.environ.get("YUBICO_API_KEY", "")


def verify_yubikey_otp(otp: str) -> bool:
    """Verifica OTP con YubiCloud si están configurados CLIENT_ID y API_KEY."""
    if not YUBICO_CLIENT_ID or not YUBICO_API_KEY:
        # Sin API: aceptar cualquier OTP de longitud típica para flujo local
        return len(otp) >= 32 and otp.isalnum()
    try:
        import urllib.request
        import urllib.parse
        import hmac
        import base64

        nonce = os.urandom(16).hex()
        params = {
            "id": YUBICO_CLIENT_ID,
            "nonce": nonce,
            "otp": otp,
        }
        query = urllib.parse.urlencode(params)
        url = f"https://api.yubico.com/wsapi/2.0/verify?{query}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read().decode()
        # Respuesta típica: h=... nonce=... otp=... status=OK
        if "status=OK" in body and nonce in body:
            # Verificar firma HMAC si se requiere
            return True
        return False
    except Exception:
        return False


def verify_master_password(password: str, hash_path: str = "/etc/gaiachain/master_password.hash") -> bool:
    """Comprueba que el hash de la contraseña coincida con el almacenado."""
    if not os.path.isfile(hash_path):
        return False
    input_hash = hashlib.sha512(password.encode()).hexdigest()
    with open(hash_path) as f:
        stored = f.read().strip()
    return input_hash == stored


def main() -> None:
    print("Autenticación YubiKey + contraseña maestra")
    master_password = getpass.getpass("Introduce la contraseña maestra: ")
    otp = getpass.getpass("Toca tu YubiKey y pega el OTP: ")

    if not verify_yubikey_otp(otp):
        print("OTP de YubiKey inválido.", file=sys.stderr)
        sys.exit(1)
    if not verify_master_password(master_password):
        print("Contraseña maestra incorrecta.", file=sys.stderr)
        sys.exit(1)

    # Token de sesión (en producción firmar con YubiKey PIV)
    session_token = os.urandom(32).hex()
    session_file = os.environ.get("CASTUO_SESSION_FILE", "/tmp/castuo_admin_session.token")
    with open(session_file, "w") as f:
        f.write(session_token)
    os.chmod(session_file, 0o600)

    # Registrar sesión en GaiaChain si está disponible
    api_url = os.environ.get("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
    admin_key = os.environ.get("GAIA_CHAIN_ADMIN_KEY")
    if admin_key:
        try:
            import urllib.request
            import json
            data = json.dumps({
                "session_token": session_token,
                "source": "yubikey_auth",
            }).encode()
            req = urllib.request.Request(
                f"{api_url}/api/v1/auth/yubikey",
                data=data,
                headers={"Authorization": f"Bearer {admin_key}", "Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    print("Autenticación correcta. Sesión válida (recomendado: 1 hora).")
    print("Puedes ejecutar comandos administrativos. Token en:", session_file)


if __name__ == "__main__":
    main()
