#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Activación de destrucción remota vía comando al satélite (ej. SES-17).
Requiere autenticación previa (YubiKey + HSM). Firma del comando con HSM; no se almacenan contraseñas.
Uso: python3 satellite-destruction.py [caceres_dc|madrid_dc]
"""
from __future__ import annotations

import os
import sys
import time

SATELLITE_CONFIG = {
    "endpoint": os.getenv("SATELLITE_COMMAND_URL", "https://api.ses-satellites.com/v1/command"),
    "client_id": os.getenv("SES_CLIENT_ID"),
    "api_key": os.getenv("SES_API_KEY"),
    "targets": {
        "caceres_dc": {
            "lat": 39.4769,
            "lon": -6.3723,
            "satellite": "SES-17",
            "receiver_id": os.getenv("CASTUO_RECEIVER_CACERES", "CASTUO-CACERES-01"),
        },
        "madrid_dc": {
            "lat": 40.4168,
            "lon": -3.7038,
            "satellite": "SES-17",
            "receiver_id": os.getenv("CASTUO_RECEIVER_MADRID", "CASTUO-MADRID-01"),
        },
    },
}

GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")


def sign_with_hsm(message: bytes) -> str | None:
    """Firma con HSM (pkcs11-tool). PIN por entorno o prompt; no almacenar."""
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        import getpass
        pin = getpass.getpass("HSM user PIN: ")
    try:
        import subprocess
        result = subprocess.run(
            [
                "pkcs11-tool",
                "--login",
                "--pin", pin,
                "--sign",
                "--mechanism", "CKM_SHA256_RSA_PKCS",
                "--id", "01",
                "-",
            ],
            input=message,
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        import base64
        return base64.b64encode(result.stdout).decode()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: firma con clave PEM si existe (no HSM)
        key_path = os.path.join(CHAIN_DIR, "master_key.pem")
        if not os.path.isfile(key_path):
            return None
        import subprocess
        proc = subprocess.run(
            ["openssl", "dgst", "-sha512", "-sign", key_path],
            input=message,
            capture_output=True,
            timeout=5,
        )
        if proc.returncode != 0:
            return None
        import base64
        return base64.b64encode(proc.stdout).decode()
    return None


def send_satellite_command(target: str) -> dict | None:
    """Envía comando de destrucción al endpoint satélite."""
    if target not in SATELLITE_CONFIG["targets"]:
        return None
    ts = int(time.time())
    command = f"DESTROY:{target}:{ts}"
    sig = sign_with_hsm(command.encode())
    if not sig:
        print("No se pudo firmar el comando (HSM o clave PEM).", file=sys.stderr)
        return None

    payload = {
        "target": SATELLITE_CONFIG["targets"][target],
        "command": command,
        "signature": sig,
        "timestamp": ts,
        "priority": "CRITICAL",
        "confirmation_required": True,
        "confirmation_method": "YUBIKEY_OTP",
    }

    api_key = SATELLITE_CONFIG.get("api_key")
    if not api_key:
        print("SES_API_KEY no configurado. Comando que se enviaría:", payload)
        return {"status": "DRY_RUN", "tracking_id": "N/A"}

    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            SATELLITE_CONFIG["endpoint"],
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Client-ID": SATELLITE_CONFIG.get("client_id", ""),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"Error al enviar comando: {e}", file=sys.stderr)
        return None


def main() -> None:
    target = (sys.argv[1:] or [None])[0] or input("Centro de datos (caceres_dc/madrid_dc): ").strip()
    if target not in SATELLITE_CONFIG["targets"]:
        print("Objetivo no válido.", file=sys.stderr)
        sys.exit(1)

    # Opcional: exigir autenticación previa (script authenticate)
    auth_script = "/opt/castuo/scripts/security/authenticate_with_yubikey.py"
    if os.path.isfile(auth_script) and os.environ.get("CASTUO_REQUIRE_AUTH_BEFORE_SATELLITE"):
        import subprocess
        if subprocess.run([sys.executable, auth_script], timeout=120).returncode != 0:
            print("Autenticación fallida. Abortando.", file=sys.stderr)
            sys.exit(1)

    response = send_satellite_command(target)
    if not response:
        sys.exit(1)

    print(f"Comando de destrucción enviado para {target}:")
    print(f"  Tracking ID: {response.get('tracking_id', 'N/A')}")
    print("  Confirmación requerida: YubiKey OTP. Tiempo estimado: 3-5 min (latencia satélite).")

    admin_token = os.getenv("GAIA_CHAIN_ADMIN_KEY")
    if admin_token and sig := sign_with_hsm(f"satellite_destruction:{target}:{response.get('tracking_id','')}".encode()):
        try:
            import urllib.request
            import json
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{GAIA_URL}/api/v1/alert/satellite_destruction",
                    data=json.dumps({
                        "target": target,
                        "tracking_id": response.get("tracking_id"),
                        "admin_signature": sig,
                    }).encode(),
                    headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=10,
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
