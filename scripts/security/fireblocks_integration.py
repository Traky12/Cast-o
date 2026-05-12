#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Integración con Fireblocks para custodia de fragmentos Shamir (MPC-CMP).
Cifrado AES-256-GCM con clave derivada por contraseña; almacenamiento vía API Fireblocks.
No se almacenan contraseñas en código. Uso: store [index] | retrieve <tx_id>
"""
from __future__ import annotations

import getpass
import os
import sys

# Configuración Fireblocks (solo env)
FIREBLOCKS_CONFIG = {
    "api_key": os.getenv("FIREBLOCKS_API_KEY"),
    "api_secret_path": os.getenv("FIREBLOCKS_API_SECRET_PATH"),  # ruta a clave privada
    "base_url": os.getenv("FIREBLOCKS_API_URL", "https://api.fireblocks.io/v1"),
    "vault_account_id": os.getenv("FIREBLOCKS_VAULT_ACCOUNT_ID", "0"),
    "asset_id": os.getenv("FIREBLOCKS_ASSET_ID", "CASTUO_EMERGENCY_FRAGMENT"),
}
GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")


def _derive_fireblocks_key(password: str, salt: bytes, fragment_id: int) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend(),
    )
    return kdf.derive(f"CASTUO-Fireblocks-Fragment-{fragment_id}-{password}".encode("utf-8"))


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
                import base64
                return base64.b64encode(r.stdout).decode()
        except Exception:
            pass
    key_path = os.path.join(CHAIN_DIR, "master_key.pem")
    if os.path.isfile(key_path):
        import subprocess
        p = subprocess.run(["openssl", "dgst", "-sha512", "-sign", key_path, "-"], input=message, capture_output=True, timeout=5)
        if p.returncode == 0 and p.stdout:
            import base64
            return base64.b64encode(p.stdout).decode()
    return None


def encrypt_for_fireblocks(plaintext: bytes, fragment_id: int, password: str) -> dict:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    salt = os.urandom(16)
    key = _derive_fireblocks_key(password, salt, fragment_id)
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    blob = salt + iv + tag + ciphertext
    return {
        "ciphertext": blob.hex(),
        "metadata": {
            "encryption": "AES-256-GCM",
            "key_derivation": "PBKDF2-SHA512",
            "salt_hex": salt.hex(),
            "fragment_id": fragment_id,
        },
    }


def decrypt_from_fireblocks(ciphertext_hex: str, fragment_id: int, password: str, metadata: dict) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    blob = bytes.fromhex(ciphertext_hex)
    if len(blob) < 16 + 12 + 16:
        raise ValueError("Payload cifrado demasiado corto")
    salt, iv, tag = blob[:16], blob[16:28], blob[28:44]
    ciphertext = blob[44:]
    key = _derive_fireblocks_key(password, salt, fragment_id)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def _fireblocks_request(method: str, path: str, body: dict | None = None) -> dict:
    """Llamada a API Fireblocks (JWT o API key según documentación)."""
    api_key = FIREBLOCKS_CONFIG.get("api_key")
    if not api_key:
        return {"id": None, "status": "SKIP", "error": "FIREBLOCKS_API_KEY no configurado"}
    import urllib.request
    import json

    url = f"{FIREBLOCKS_CONFIG['base_url'].rstrip('/')}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-API-Key", api_key)
    # En producción usar JWT firmado con api_secret; aquí se asume API key en header
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"id": None, "status": "ERROR", "error": str(e)}


def fireblocks_store_fragment(encrypted_data: dict, fragment_id: int) -> dict:
    """Almacena fragmento cifrado en Fireblocks (transacción interna o vault)."""
    # Fireblocks no expone un "store blob" directo; se usa internal transfer con note o API de vault.
    # Documentar: en producción usar Fireblocks "Transaction" con note = ciphertext o custom asset.
    payload = {
        "assetId": FIREBLOCKS_CONFIG["asset_id"],
        "amount": "0",
        "source": {"type": "VAULT_ACCOUNT", "id": FIREBLOCKS_CONFIG["vault_account_id"]},
        "destination": {"type": "VAULT_ACCOUNT", "id": FIREBLOCKS_CONFIG["vault_account_id"]},
        "note": encrypted_data["ciphertext"][:2000],  # nota limitada; para >2KB usar external storage
        "extraParameters": {
            "fragment_id": fragment_id,
            "encryption_metadata": encrypted_data["metadata"],
            "data": encrypted_data["ciphertext"],
        },
    }
    # Si la API no acepta extraParameters en transfer, guardar solo referencia; datos en nuestro backend.
    result = _fireblocks_request("POST", "/transactions", payload)
    if result.get("id"):
        sig = _sign_with_hsm_or_pem(f"FIREBLOCKS_FRAGMENT_{fragment_id}_{result['id']}".encode())
        admin = os.getenv("GAIA_CHAIN_ADMIN_KEY")
        if admin and sig:
            try:
                import urllib.request
                import json
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"{GAIA_URL}/api/v1/emergency_fragment/fireblocks",
                        data=json.dumps({
                            "fragment_id": fragment_id,
                            "fireblocks_tx_id": result["id"],
                            "fireblocks_asset_id": FIREBLOCKS_CONFIG["asset_id"],
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
    return result


def fireblocks_retrieve_fragment(tx_id: str, fragment_id: int, password: str) -> bytes:
    """Recupera fragmento desde Fireblocks por ID de transacción."""
    result = _fireblocks_request("GET", f"/transactions/{tx_id}")
    if not result or "id" not in result:
        raise ValueError("Transacción no encontrada")
    extra = result.get("extraParameters") or result.get("note") or {}
    data_hex = extra.get("data") or (result.get("note") if isinstance(result.get("note"), str) else None)
    if not data_hex:
        raise ValueError("Datos de fragmento no encontrados en la transacción")
    metadata = extra.get("encryption_metadata", {})
    return decrypt_from_fireblocks(data_hex, fragment_id, password, metadata)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: fireblocks_integration.py store [index] | retrieve <tx_id> [fragment_id]")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    password = getpass.getpass("Contraseña para cifrado Fireblocks: ")
    if not password:
        sys.exit(1)
    if cmd == "store":
        fragment_index = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        payload = sys.stdin.buffer.read()
        if len(payload) < 33:
            print("Proporciona fragmento por stdin (33 bytes).", file=sys.stderr)
            sys.exit(1)
        enc = encrypt_for_fireblocks(payload, fragment_index, password)
        result = fireblocks_store_fragment(enc, fragment_index)
        if result.get("id"):
            print(f"Fragmento {fragment_index} almacenado en Fireblocks: TX {result['id']}")
        else:
            print(result.get("error", result), file=sys.stderr)
            sys.exit(1)
    elif cmd == "retrieve":
        if len(sys.argv) < 3:
            print("Uso: fireblocks_integration.py retrieve <tx_id> [fragment_id]")
            sys.exit(1)
        tx_id, fragment_id = sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2
        data = fireblocks_retrieve_fragment(tx_id, fragment_id, password)
        sys.stdout.buffer.write(data)
    else:
        print("Comando no válido.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
