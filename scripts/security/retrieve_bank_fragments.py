#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Recuperación de fragmentos Shamir desde bóvedas bancarias.
Uso: python3 retrieve_bank_fragments.py [deposit_id_bbva] [deposit_id_santander] [deposit_id_caixabank]
O introducir deposit_ids de forma interactiva.
"""
from __future__ import annotations

import getpass
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

BANK_APIS = {
    "bbva": {
        "url_get": os.getenv("BBVA_CUSTODY_GET_URL", "https://api.bbva.com/valores/custody/v1/deposit/{deposit_id}"),
        "api_key": os.getenv("BBVA_API_KEY"),
        "client_id": os.getenv("BBVA_CLIENT_ID"),
    },
    "santander": {
        "url_get": os.getenv("SANTANDER_CUSTODY_GET_URL", "https://api.santander.es/global-custody/v2/deposit/{deposit_id}"),
        "api_key": os.getenv("SANTANDER_API_KEY"),
        "client_id": os.getenv("SANTANDER_CLIENT_ID"),
    },
    "caixabank": {
        "url_get": os.getenv("CAIXABANK_SAFEBOX_GET_URL", "https://api.caixabank.com/safebox/v1/deposit/{deposit_id}"),
        "api_key": os.getenv("CAIXABANK_API_KEY"),
        "client_id": os.getenv("CAIXABANK_CLIENT_ID"),
    },
}


def derive_bank_key(bank_name: str, master_password: str, salt: bytes) -> bytes:
    """Misma derivación que en store_bank_vault_fragments."""
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


def decrypt_fragment(iv_ct: bytes, key: bytes) -> bytes:
    """Desencripta AES-256-CBC (iv || ciphertext)."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    iv, ct = iv_ct[:16], iv_ct[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    dec = cipher.decryptor()
    padded = dec.update(ct) + dec.finalize()
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Padding inválido")
    return padded[:-pad_len]


def retrieve_from_bank(bank: str, deposit_id: str) -> bytes | None:
    """Recupera datos del depósito desde la API del banco."""
    cfg = BANK_APIS[bank]
    if not cfg.get("api_key"):
        # Intentar leer respaldo local
        out_dir = os.environ.get("CASTUO_FRAGMENTS_DIR", "/opt/castuo/secure_fragments")
        path = os.path.join(out_dir, f"{bank}_vault_fragment.enc")
        if os.path.isfile(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    try:
        import urllib.request

        url = cfg["url_get"].format(deposit_id=deposit_id)
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {cfg['api_key']}",
                "X-Client-ID": cfg.get("client_id", ""),
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            import json
            data = json.loads(r.read().decode())
        raw = data.get("deposit", {}).get("data") or data.get("data")
        if isinstance(raw, str):
            return bytes.fromhex(raw)
        return raw
    except Exception:
        return None


def main() -> None:
    master_password = getpass.getpass("Introduce la contraseña maestra: ")
    if not master_password:
        print("Contraseña vacía.", file=sys.stderr)
        sys.exit(1)

    deposit_ids = list(sys.argv[1:4]) if len(sys.argv) >= 4 else []
    banks = ["bbva", "santander", "caixabank"]
    while len(deposit_ids) < 3:
        for b in banks[len(deposit_ids) : len(deposit_ids) + 1]:
            deposit_ids.append(input(f"ID de depósito en {b.upper()} (o ruta a .enc local): ").strip())

    out_dir = os.environ.get("CASTUO_FRAGMENTS_DIR", "/opt/castuo/secure_fragments")
    fragments_for_reconstruct = []

    for bank, dep in zip(banks, deposit_ids):
        if os.path.isfile(dep):
            with open(dep, "rb") as f:
                raw = f.read()
        else:
            raw = retrieve_from_bank(bank, dep)

        if not raw or len(raw) < 16 + 16:
            print(f"No se pudo recuperar fragmento de {bank}.", file=sys.stderr)
            continue

        salt = raw[:16]
        iv_ct = raw[16:]
        key = derive_bank_key(bank, master_password, salt)
        try:
            payload = decrypt_fragment(iv_ct, key)
        except Exception as e:
            print(f"Error al desencriptar {bank}: {e}", file=sys.stderr)
            continue

        if len(payload) >= 33:
            index, frag = payload[0], payload[1:33]
            fragments_for_reconstruct.append((index, frag))
            print(f"Fragmento recuperado de {bank.upper()} (índice {index}).")

    if len(fragments_for_reconstruct) < 3:
        print("Se necesitan al menos 3 fragmentos para reconstruir.", file=sys.stderr)
        sys.exit(1)

    from generate_emergency_keys import combine_master_key  # noqa: PLC0415

    master_key = combine_master_key(fragments_for_reconstruct)
    print(f"Llave maestra reconstruida: {master_key.hex()}")
    if os.environ.get("CASTUO_EXPORT_RECONSTRUCTED_KEY"):
        os.environ["GAIA_CHAIN_MASTER_KEY_HEX"] = master_key.hex()
        print("Variable GAIA_CHAIN_MASTER_KEY_HEX exportada para esta sesión.")


if __name__ == "__main__":
    main()
