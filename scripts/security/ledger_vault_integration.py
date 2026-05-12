#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Integración con Ledger Vault para custodia de fragmentos Shamir.
Almacena/recupera fragmento 2 en Ledger Vault (API REST). Cifrado AES-256-GCM; clave derivada
con PBKDF2 desde contraseña o HSM. No se almacenan contraseñas en código.
Uso: almacenar: python3 ledger_vault_integration.py store [fragment_index]
     recuperar: python3 ledger_vault_integration.py retrieve <fragment_id>
"""
from __future__ import annotations

import getpass
import os
import sys

# Configuración Ledger Vault (solo env; sin credenciales en código)
LEDGER_VAULT_API = {
    "base_url": os.getenv("LEDGER_VAULT_API_URL", "https://api.ledger.com/vault/v1"),
    "api_key": os.getenv("LEDGER_VAULT_API_KEY"),
    "policy_id": os.getenv("LEDGER_VAULT_POLICY_ID"),
    "asset_type": os.getenv("LEDGER_VAULT_ASSET_TYPE", "CASTUO_EMERGENCY_FRAGMENT"),
}
GAIA_URL = os.getenv("GAIA_CHAIN_API_URL", "https://gaiachain.castuo-system.com")
CHAIN_DIR = os.getenv("GAIA_CHAIN_DIR", "/etc/gaiachain")


def _derive_ledger_key(password: str, salt: bytes) -> bytes:
    """Deriva clave AES para Ledger desde contraseña (PBKDF2-SHA512)."""
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
    return kdf.derive(f"CASTUO-LedgerVault-{password}".encode("utf-8"))


def _sign_with_hsm_or_pem(message: bytes) -> str | None:
    """Firma con HSM (PIN por env) o con clave PEM local."""
    pin = os.getenv("HSM_USER_PIN")
    if not pin:
        pin = getpass.getpass("HSM user PIN (o Enter para usar clave PEM): ") or None
    if pin:
        try:
            import subprocess
            r = subprocess.run(
                [
                    "pkcs11-tool", "--login", "--pin", pin,
                    "--sign", "--mechanism", "CKM_SHA256_RSA_PKCS", "--id", "01", "-",
                ],
                input=message,
                capture_output=True,
                timeout=10,
            )
            if r.returncode == 0 and r.stdout:
                import base64
                return base64.b64encode(r.stdout).decode()
        except (FileNotFoundError, Exception):
            pass
    key_path = os.path.join(CHAIN_DIR, "master_key.pem")
    if os.path.isfile(key_path):
        import subprocess
        p = subprocess.run(
            ["openssl", "dgst", "-sha512", "-sign", key_path, "-"],
            input=message,
            capture_output=True,
            timeout=5,
        )
        if p.returncode == 0 and p.stdout:
            import base64
            return base64.b64encode(p.stdout).decode()
    return None


def encrypt_for_ledger(plaintext: bytes, password: str) -> dict:
    """Cifra datos con AES-256-GCM; devuelve dict con ciphertext (hex), salt, iv, tag."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    salt = os.urandom(16)
    key = _derive_ledger_key(password, salt)
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag
    # Formato: salt(16) + iv(12) + tag(16) + ciphertext
    blob = salt + iv + tag + ciphertext
    return {
        "ciphertext": blob.hex(),
        "metadata": {
            "encryption": "AES-256-GCM",
            "key_derivation": "PBKDF2-SHA512",
            "salt_hex": salt.hex(),
        },
    }


def decrypt_from_ledger(ciphertext_hex: str, password: str, metadata: dict) -> bytes:
    """Descifra payload desde Ledger (salt en metadata o al inicio del blob)."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    blob = bytes.fromhex(ciphertext_hex)
    # Formato: salt(16) + iv(12) + tag(16) + ciphertext
    if len(blob) < 16 + 12 + 16:
        raise ValueError("Payload cifrado demasiado corto")
    salt = blob[:16]
    iv = blob[16:28]
    tag = blob[28:44]
    ciphertext = blob[44:]
    key = _derive_ledger_key(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def ledger_api_create_asset(name: str, data_hex: str, metadata: dict) -> dict:
    """Crea activo en Ledger Vault (API REST). Requiere LEDGER_VAULT_API_KEY."""
    api_key = LEDGER_VAULT_API.get("api_key")
    if not api_key:
        return {"id": None, "status": "SKIP", "error": "LEDGER_VAULT_API_KEY no configurado"}
    import urllib.request
    import json

    payload = {
        "asset_type": LEDGER_VAULT_API["asset_type"],
        "name": name,
        "metadata": metadata,
        "data": data_hex,
        "policy_id": LEDGER_VAULT_API.get("policy_id"),
    }
    req = urllib.request.Request(
        f"{LEDGER_VAULT_API['base_url']}/assets",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"id": None, "status": "ERROR", "error": str(e)}


def ledger_api_get_asset(asset_id: str) -> dict | None:
    """Obtiene activo por ID desde Ledger Vault."""
    api_key = LEDGER_VAULT_API.get("api_key")
    if not api_key:
        return None
    import urllib.request
    import json

    req = urllib.request.Request(
        f"{LEDGER_VAULT_API['base_url']}/assets/{asset_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def store_fragment_in_ledger(fragment_index: int, fragment_payload: bytes, password: str) -> dict:
    """Cifra el fragmento y lo almacena en Ledger Vault; registra en GaiaChain."""
    enc = encrypt_for_ledger(fragment_payload, password)
    name = f"CASTUO_Fragment_{fragment_index}"
    metadata = {
        "fragment_id": fragment_index,
        "organization": "CASTUO-SYSTEM",
        "purpose": "Emergency Recovery Key Fragment",
        **enc["metadata"],
    }
    result = ledger_api_create_asset(name, enc["ciphertext"], metadata)
    if result.get("id"):
        sig = _sign_with_hsm_or_pem(f"LEDGER_FRAGMENT_{fragment_index}_{result['id']}".encode())
        admin_token = os.getenv("GAIA_CHAIN_ADMIN_KEY")
        if admin_token and sig:
            try:
                import urllib.request
                import json
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"{GAIA_URL}/api/v1/emergency_fragment/ledger",
                        data=json.dumps({
                            "fragment_id": fragment_index,
                            "ledger_asset_id": result["id"],
                            "metadata": enc["metadata"],
                            "signature": sig,
                        }).encode(),
                        headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=10,
                )
            except Exception:
                pass
    return result


def retrieve_fragment_from_ledger(asset_id: str, password: str) -> bytes:
    """Recupera y descifra un fragmento desde Ledger Vault."""
    asset = ledger_api_get_asset(asset_id)
    if not asset or "data" not in asset:
        raise ValueError("Fragmento no encontrado o sin datos")
    metadata = asset.get("metadata", {})
    return decrypt_from_ledger(asset["data"], password, metadata)


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: ledger_vault_integration.py store [index] | retrieve <asset_id>")
        sys.exit(1)
    cmd = sys.argv[1].lower()
    password = getpass.getpass("Contraseña para cifrado Ledger: ")
    if not password:
        sys.exit(1)

    if cmd == "store":
        fragment_index = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        # Leer fragmento desde stdin (bytes) para no pasarlo por argumentos
        payload = sys.stdin.buffer.read()
        if len(payload) < 33:
            print("Proporciona fragmento por stdin (33 bytes: index + 32 bytes).", file=sys.stderr)
            sys.exit(1)
        result = store_fragment_in_ledger(fragment_index, payload, password)
        if result.get("id"):
            print(f"Fragmento {fragment_index} almacenado en Ledger Vault: {result['id']}")
        else:
            print(result.get("error", result), file=sys.stderr)
            sys.exit(1)
    elif cmd == "retrieve":
        if len(sys.argv) < 3:
            print("Uso: ledger_vault_integration.py retrieve <asset_id>")
            sys.exit(1)
        asset_id = sys.argv[2]
        data = retrieve_fragment_from_ledger(asset_id, password)
        sys.stdout.buffer.write(data)
    else:
        print("Comando no válido.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
