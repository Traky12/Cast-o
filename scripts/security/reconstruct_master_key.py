#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Reconstrucción de la llave maestra desde 3/5 fragmentos (Shamir).
Solo el administrador puede ejecutar esto con los fragmentos y la contraseña.
Uso: python3 reconstruct_master_key.py [ruta1.enc ruta2.enc ruta3.enc]
"""
from __future__ import annotations

import getpass
import os
import sys


def decrypt_aes_cbc(salt: bytes, iv: bytes, ciphertext: bytes, password: str) -> bytes:
    """Desencripta AES-256-CBC (mismo esquema que generate_emergency_keys)."""
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend(),
    )
    key = kdf.derive(password.encode("utf-8"))
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    dec = cipher.decryptor()
    padded = dec.update(ciphertext) + dec.finalize()
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Padding inválido")
    return padded[:-pad_len]


def load_fragment(path: str, password: str) -> tuple[int, bytes]:
    """Carga y desencripta un fragmento; devuelve (índice, 32 bytes)."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 16 + 16 + 33:
        raise ValueError(f"Archivo de fragmento demasiado corto: {path}")
    salt, iv, ct = data[:16], data[16:32], data[32:]
    payload = decrypt_aes_cbc(salt, iv, ct, password)
    if len(payload) != 33:
        raise ValueError(f"Payload de fragmento inválido (esperado 33 bytes): {path}")
    index = payload[0]
    fragment_32 = payload[1:33]
    return index, fragment_32


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    password = getpass.getpass("Introduce la contraseña maestra: ")
    if not password:
        print("Contraseña vacía.", file=sys.stderr)
        sys.exit(1)

    paths = sys.argv[1:]
    if len(paths) < 3:
        print("Uso: reconstruct_master_key.py <fragment1.enc> <fragment2.enc> <fragment3.enc>", file=sys.stderr)
        print("Ejemplo: junta_extremadura_fragment.enc notario_madrid_fragment.enc yubikey_fragment.enc", file=sys.stderr)
        sys.exit(1)

    fragments = []
    for path in paths[:3]:
        path = path.strip()
        if not os.path.isfile(path):
            print(f"No existe: {path}", file=sys.stderr)
            sys.exit(1)
        idx, payload = load_fragment(path, password)
        fragments.append((idx, payload))

    from generate_emergency_keys import combine_master_key as _combine  # noqa: PLC0415

    master_key = _combine(fragments)
    print(f"Llave maestra reconstruida: {master_key.hex()}")

    # Exportar para sesión (opcional)
    export = os.environ.get("CASTUO_EXPORT_RECONSTRUCTED_KEY", "")
    if export.lower() in ("1", "true", "yes"):
        os.environ["GAIA_CHAIN_MASTER_KEY_HEX"] = master_key.hex()
        print("Variable GAIA_CHAIN_MASTER_KEY_HEX exportada para esta sesión.")

    print("Puedes usar esta llave para: desbloquear HSM, acceder a GaiaChain, restaurar backups.")


if __name__ == "__main__":
    main()
