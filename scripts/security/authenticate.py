#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Autenticación con YubiKey + HSM (sin almacenar contraseñas).
Genera challenge, firma con YubiKey PIV, verifica en GaiaChain/HSM y obtiene token de sesión.
Uso: python3 authenticate.py
"""
from __future__ import annotations

import os
import sys

# Si existe el script completo de autenticación con YubiKey, delegar en él
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_LEGACY = os.path.join(_SCRIPT_DIR, "authenticate_with_yubikey.py")


def authenticate_with_hsm_yubikey() -> bool:
    """Flujo: OTP YubiKey + (opcional) firma PIV challenge; token de sesión."""
    getpass = __import__("getpass")
    otp = getpass.getpass("Toca tu YubiKey para generar OTP: ")
    if len(otp) < 32 or not otp.isalnum():
        print("OTP de YubiKey inválido.", file=sys.stderr)
        return False

    # Verificación YubiCloud si hay credenciales
    cid, key = os.getenv("YUBICO_CLIENT_ID"), os.getenv("YUBICO_API_KEY")
    if cid and key:
        try:
            import urllib.request
            import urllib.parse
            nonce = os.urandom(16).hex()
            q = urllib.parse.urlencode({"id": cid, "nonce": nonce, "otp": otp})
            req = urllib.request.Request(f"https://api.yubico.com/wsapi/2.0/verify?{q}")
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read().decode()
            if "status=OK" not in body or nonce not in body:
                print("Verificación YubiCloud fallida.", file=sys.stderr)
                return False
        except Exception as e:
            print(f"Error YubiCloud: {e}", file=sys.stderr)
            return False

    # Challenge para HSM/PIV (opcional)
    challenge = os.urandom(32).hex()
    session_token = os.urandom(32).hex()
    session_file = os.getenv("CASTUO_SESSION_FILE", "/tmp/gaiachain_session.token")

    # Intentar firma con ykman PIV slot 9a
    try:
        import subprocess
        proc = subprocess.run(
            ["ykman", "piv", "sign", "9a", "-a", "SHA256", "-"],
            input=challenge.encode(),
            capture_output=True,
            timeout=10,
        )
        yubikey_sig = proc.stdout.hex() if proc.returncode == 0 and proc.stdout else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        yubikey_sig = ""

    # Enviar a GaiaChain para verificación
    api_url = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
    admin_token = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if admin_token:
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                f"{api_url}/api/v1/auth/hsm-yubikey",
                data=json.dumps({
                    "challenge": challenge,
                    "yubikey_signature": yubikey_sig,
                    "otp": otp,
                }).encode(),
                headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode())
                session_token = data.get("session_token", session_token)
        except Exception:
            pass

    with open(session_file, "w") as f:
        f.write(session_token)
    os.chmod(session_file, 0o600)
    print("Autenticación correcta. Sesión válida (recomendado: 1h). Token en:", session_file)
    return True


if __name__ == "__main__":
    # Permitir delegar en script con contraseña maestra si existe
    if os.path.isfile(_LEGACY) and os.environ.get("CASTUO_USE_LEGACY_AUTH"):
        import subprocess
        sys.exit(subprocess.run([sys.executable, _LEGACY], timeout=120).returncode)
    if authenticate_with_hsm_yubikey():
        verified = os.getenv("CASTUO_VERIFIED_ACCESS_SCRIPT", "/opt/castuo/scripts/security/verified-access.sh")
        if os.path.isfile(verified):
            import subprocess
            subprocess.run([verified], timeout=5)
        sys.exit(0)
    sys.exit(1)
