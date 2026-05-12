#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Almacenamiento de fragmentos Shamir en bóvedas bancarias (BBVA, Santander, CaixaBank).
Cada fragmento se encripta con AES-256; las claves se derivan con HSM si está disponible.
No se almacenan contraseñas; uso de variables de entorno para APIs.
Uso: python3 store_bank_vault_fragments.py
"""
from __future__ import annotations

import getpass
import os
import sys

# Añadir path para importar generate_emergency_keys
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# APIs bancarias (URLs y cuentas por entorno; sin credenciales en código)
BANK_APIS = {
    "bbva": {
        "url": os.getenv("BBVA_CUSTODY_URL", "https://api.bbva.com/valores/custody/v1/deposit"),
        "api_key": os.getenv("BBVA_API_KEY"),
        "client_id": os.getenv("BBVA_CLIENT_ID"),
        "account": os.getenv("BBVA_ACCOUNT", "ES9121000418401234567890"),
    },
    "santander": {
        "url": os.getenv("SANTANDER_CUSTODY_URL", "https://api.santander.es/global-custody/v2/deposit"),
        "api_key": os.getenv("SANTANDER_API_KEY"),
        "client_id": os.getenv("SANTANDER_CLIENT_ID"),
        "account": os.getenv("SANTANDER_ACCOUNT", "ES3300491234567890123456"),
    },
    "caixabank": {
        "url": os.getenv("CAIXABANK_SAFEBOX_URL", "https://api.caixabank.com/safebox/v1/deposit"),
        "api_key": os.getenv("CAIXABANK_API_KEY"),
        "client_id": os.getenv("CAIXABANK_CLIENT_ID"),
        "account": os.getenv("CAIXABANK_ACCOUNT", "ES7721000813611234567895"),
    },
}


def derive_bank_key(bank_name: str, master_password: str, salt: bytes) -> bytes:
    """Deriva clave AES por banco (PBKDF2-SHA512). En producción puede usar HSM."""
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
    return kdf.derive(f"{master_password}:CASTUO-Bank-{bank_name}".encode("utf-8"))


def encrypt_fragment(data: bytes, key: bytes) -> bytes:
    """Encripta con AES-256-CBC; devuelve iv || ciphertext."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    iv = os.urandom(16)
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len] * pad_len)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    return iv + enc.update(padded) + enc.finalize()


def deposit_to_bank(bank: str, encrypted_fragment: bytes, fragment_id: str) -> dict:
    """Deposita fragmento encriptado en la API del banco (stub si no hay API_KEY)."""
    cfg = BANK_APIS[bank]
    if not cfg.get("api_key"):
        return {"status": "SKIP", "reason": f"No {bank.upper()} API key", "deposit_id": None}

    try:
        import urllib.request
        import json

        payload = {
            "account": cfg["account"],
            "deposit": {
                "type": "DIGITAL_ASSET",
                "description": f"CASTUO-SYSTEM Fragment {fragment_id}",
                "data": encrypted_fragment.hex(),
                "metadata": {
                    "owner": os.getenv("CASTUO_VAULT_OWNER", "authorized_admin"),
                    "purpose": "Emergency Recovery Key Fragment",
                    "expiry": "2040-12-31",
                },
            },
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            cfg["url"],
            data=data,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "X-Client-ID": cfg.get("client_id", ""),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "deposit_id": None}


def main() -> None:
    print("Almacenamiento de fragmentos en bóvedas bancarias (BBVA, Santander, CaixaBank)")
    master_password = getpass.getpass("Introduce la contraseña maestra: ")
    if not master_password:
        print("Contraseña vacía.", file=sys.stderr)
        sys.exit(1)

    from generate_emergency_keys import (  # noqa: PLC0415
        generate_master_key,
        split_master_key,
        LOCATIONS,
    )

    salt = os.urandom(16)
    master_key = generate_master_key(master_password, salt)
    fragments = split_master_key(master_key, threshold=3, total=5)

    # Fragmentos 2, 3, 4 -> BBVA, Santander, CaixaBank (índices 1, 2, 3 en LOCATIONS: notario, yubikey, bbva_vault)
    # Usamos índices 2, 3, 4 del esquema (fragmentos 2, 3, 4) para los tres bancos
    bank_names = ["bbva", "santander", "caixabank"]
    for i, bank in enumerate(bank_names):
        idx, payload = fragments[i + 1]  # fragmento 2, 3, 4
        payload_full = bytes([idx]) + payload
        bank_salt = os.urandom(16)
        key = derive_bank_key(bank, master_password, bank_salt)
        encrypted = encrypt_fragment(payload_full, key)
        # Guardar salt localmente para recuperación (ruta segura)
        out_dir = os.environ.get("CASTUO_FRAGMENTS_DIR", "/opt/castuo/secure_fragments")
        os.makedirs(out_dir, mode=0o700, exist_ok=True)
        salt_file = os.path.join(out_dir, f"{bank}_vault.salt")
        with open(salt_file, "wb") as f:
            f.write(bank_salt)
        os.chmod(salt_file, 0o600)

        result = deposit_to_bank(bank, encrypted, f"CASTUO-{i+2}")
        if result.get("deposit_id"):
            print(f"Fragmento {i+2} almacenado en {bank.upper()}: deposit_id={result['deposit_id']}")
        else:
            print(f"Fragmento {i+2} ({bank.upper()}): {result.get('status', 'ERROR')} - {result.get('reason', result.get('error', ''))}")
            # Guardar localmente como respaldo si la API no está configurada
            local_path = os.path.join(out_dir, f"{bank}_vault_fragment.enc")
            with open(local_path, "wb") as f:
                f.write(bank_salt + encrypted)
            os.chmod(local_path, 0o600)
            print(f"  Respaldo local: {local_path}")

    print("Proceso finalizado. Configure BBVA_API_KEY, SANTANDER_API_KEY, CAIXABANK_API_KEY para depósito real.")


if __name__ == "__main__":
    main()
