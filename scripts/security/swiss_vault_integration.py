#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Integración con Swiss Vault (Zúrich) para custodia física de fragmentos Shamir.
Cifrado AES-256-GCM; clave derivada por contraseña (PBKDF2 200K iter). Sin contraseñas en código.
Uso: store [index] | retrieve <deposit_id> [fragment_id]
"""
from __future__ import annotations

import base64
import getpass
import os
import sys

SWISS_VAULT_CONFIG = {
    "api_base": os.getenv("SWISS_VAULT_API_URL", "https://api.swissvault.ch/v2"),
    "api_key": os.getenv("SWISS_VAULT_API_KEY"),
    "vault_id": os.getenv("SWISS_VAULT_ID", "CASTUO-2026"),
    "box_id": os.getenv("SWISS_VAULT_BOX_ID", "BOX-9876"),
}
GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")


def _derive_swissvault_key(password: str, salt: bytes, fragment_id: int) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=200_000,
        backend=default_backend(),
    )
    return kdf.derive(f"CASTUO-SwissVault-Fragment-{fragment_id}-{password}".encode("utf-8"))


def _sign_with_hsm_or_pem(message: bytes) -> str | None:
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        try:
            pin = getpass.getpass("HSM user PIN (o Enter para PEM): ") or None
        except Exception:
            pin = None
    if pin:
        try:
            import subprocess
            r = subprocess.run(
                ["pkcs11-tool", "--login", "--pin", pin, "--sign", "--mechanism", "CKM_SHA256_RSA_PKCS", "--id", "01", "-"],
                input=message,
                capture_output=True,
                timeout=10,
            )
            if r.returncode == 0 and r.stdout:
                import base64 as b64
                return b64.b64encode(r.stdout).decode()
        except Exception:
            pass
    key_path = os.path.join(CHAIN_DIR, "master_key.pem")
    if os.path.isfile(key_path):
        import subprocess
        p = subprocess.run(["openssl", "dgst", "-sha512", "-sign", key_path, "-"], input=message, capture_output=True, timeout=5)
        if p.returncode == 0 and p.stdout:
            import base64 as b64
            return b64.b64encode(p.stdout).decode()
    return None


def encrypt_for_swissvault(plaintext: bytes, fragment_id: int, password: str) -> dict:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    salt = os.urandom(16)
    key = _derive_swissvault_key(password, salt, fragment_id)
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    blob = salt + iv + tag + ciphertext
    return {
        "ciphertext": base64.b64encode(blob).decode("utf-8"),
        "metadata": {
            "encryption": "AES-256-GCM",
            "key_derivation": "PBKDF2-SHA512-200K",
            "fragment_id": fragment_id,
            "vault_id": SWISS_VAULT_CONFIG["vault_id"],
            "box_id": SWISS_VAULT_CONFIG["box_id"],
        },
    }


def decrypt_from_swissvault(ciphertext_b64: str, fragment_id: int, password: str) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    blob = base64.b64decode(ciphertext_b64)
    if len(blob) < 16 + 12 + 16:
        raise ValueError("Payload cifrado demasiado corto")
    salt, iv, tag = blob[:16], blob[16:28], blob[28:44]
    ciphertext = blob[44:]
    key = _derive_swissvault_key(password, salt, fragment_id)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def _get_yubikey_otp() -> str:
    return getpass.getpass("Toca tu YubiKey y pega el OTP: ").strip()


def _swissvault_request(method: str, path: str, token: str | None = None, json_body: dict | None = None) -> dict:
    import urllib.request
    import json

    url = f"{SWISS_VAULT_CONFIG['api_base'].rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(json_body).encode() if json_body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def swissvault_login(password: str, yubikey_otp: str) -> str | None:
    """Login a Swiss Vault (biometric_token opcional por env)."""
    body = {
        "api_key": SWISS_VAULT_CONFIG.get("api_key"),
        "vault_id": SWISS_VAULT_CONFIG["vault_id"],
        "yubikey_otp": yubikey_otp,
    }
    if os.getenv("SWISS_VAULT_BIOMETRIC_TOKEN"):
        body["biometric_token"] = os.getenv("SWISS_VAULT_BIOMETRIC_TOKEN")
    r = _swissvault_request("POST", "/auth/login", json_body=body)
    return r.get("session_token") if isinstance(r, dict) and "error" not in r else None


def store_fragment_in_swissvault(encrypted_data: dict, fragment_id: int, session_token: str) -> dict:
    import urllib.request
    import json

    url = f"{SWISS_VAULT_CONFIG['api_base'].rstrip('/')}/vaults/{SWISS_VAULT_CONFIG['vault_id']}/boxes/{SWISS_VAULT_CONFIG['box_id']}/deposits"
    body = {
        "items": [{
            "type": "DIGITAL_ASSET",
            "description": f"CASTUO Emergency Fragment {fragment_id}",
            "encrypted_data": encrypted_data["ciphertext"],
            "metadata": encrypted_data["metadata"],
            "access_policy": {"quorum": 3, "required_approvers": 5, "biometric_required": True, "yubikey_required": True},
        }]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return {"deposit_id": None, "status": "ERROR", "error": str(e)}
    items = data.get("items", [])
    deposit_id = items[0]["id"] if items else None
    if deposit_id:
        sig = _sign_with_hsm_or_pem(f"SWISSVAULT_FRAGMENT_{fragment_id}_{deposit_id}".encode())
        admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
        if admin and sig:
            try:
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"{GAIA_URL}/api/v1/emergency_fragment/swissvault",
                        data=json.dumps({
                            "fragment_id": fragment_id,
                            "swissvault_deposit_id": deposit_id,
                            "vault_id": SWISS_VAULT_CONFIG["vault_id"],
                            "box_id": SWISS_VAULT_CONFIG["box_id"],
                            "metadata": encrypted_data["metadata"],
                            "signature": sig,
                        }).encode(),
                        headers={"Authorization": f"Bearer {admin}", "Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=10,
                )
            except Exception:
                pass
    return {"deposit_id": deposit_id, "vault_id": SWISS_VAULT_CONFIG["vault_id"], "box_id": SWISS_VAULT_CONFIG["box_id"], "status": "STORED" if deposit_id else "ERROR"}


def retrieve_fragment_from_swissvault(deposit_id: str, fragment_id: int, password: str, session_token: str) -> bytes:
    import urllib.request
    import json

    url = f"{SWISS_VAULT_CONFIG['api_base'].rstrip('/')}/vaults/{SWISS_VAULT_CONFIG['vault_id']}/boxes/{SWISS_VAULT_CONFIG['box_id']}/deposits/{deposit_id}/access"
    req = urllib.request.Request(
        url,
        data=json.dumps({"reason": "Emergency recovery CASTUO fragment", "quorum_approvals": []}).encode(),
        headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        raise ValueError(f"Error recuperando depósito: {e}")
    enc_b64 = data.get("encrypted_data")
    if not enc_b64:
        raise ValueError("Depósito sin encrypted_data")
    return decrypt_from_swissvault(enc_b64, fragment_id, password)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: swiss_vault_integration.py store [index] | retrieve <deposit_id> [fragment_id]")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    password = getpass.getpass("Contraseña para cifrado Swiss Vault: ")
    if not password:
        sys.exit(1)
    if cmd == "store":
        fragment_id = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        payload = sys.stdin.buffer.read()
        if len(payload) < 33:
            print("Proporciona fragmento por stdin (33 bytes).", file=sys.stderr)
            sys.exit(1)
        enc = encrypt_for_swissvault(payload, fragment_id, password)
        otp = _get_yubikey_otp()
        token = swissvault_login(password, otp)
        if not token and SWISS_VAULT_CONFIG.get("api_key"):
            print("Login Swiss Vault fallido.", file=sys.stderr)
            sys.exit(1)
        if token:
            result = store_fragment_in_swissvault(enc, fragment_id, token)
            if result.get("deposit_id"):
                print(f"Fragmento {fragment_id} almacenado en Swiss Vault: deposit_id={result['deposit_id']}")
            else:
                print(result.get("error", result), file=sys.stderr)
                sys.exit(1)
        else:
            print("SWISS_VAULT_API_KEY no configurado o login no disponible. Cifrado listo para depósito manual.")
    elif cmd == "retrieve":
        if len(sys.argv) < 3:
            print("Uso: swiss_vault_integration.py retrieve <deposit_id> [fragment_id]")
            sys.exit(1)
        deposit_id, fragment_id = sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2
        otp = _get_yubikey_otp()
        token = swissvault_login(password, otp)
        if not token:
            print("Login Swiss Vault fallido.", file=sys.stderr)
            sys.exit(1)
        data = retrieve_fragment_from_swissvault(deposit_id, fragment_id, password, token)
        sys.stdout.buffer.write(data)
    else:
        print("Comando no válido.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
