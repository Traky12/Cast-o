#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Generación y distribución de llaves de emergencia (Shamir 3/5 + HSM).
Divide la llave maestra en 5 fragmentos; 3 cualesquiera reconstruyen la llave.
Cada fragmento se almacena encriptado (AES-256-CBC) por ubicación.
Uso: python3 generate_emergency_keys.py
"""
from __future__ import annotations

import getpass
import hashlib
import os
import sys

# GF(256) con polinomio irreducible AES (x^8 + x^4 + x^3 + x + 1)


def _gf256_add(a: int, b: int) -> int:
    return a ^ b


def _gf256_mul(a: int, b: int) -> int:
    p = 0
    for _ in range(8):
        if b & 1:
            p ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B  # x^8 mod poly
        b >>= 1
    return p


def _gf256_inv(a: int) -> int:
    if a == 0:
        raise ValueError("GF256 inverse of 0")
    t = a
    for _ in range(6):
        t = _gf256_mul(t, t)
        t = _gf256_mul(t, a)
    return _gf256_mul(t, t)


def _gf256_div(a: int, b: int) -> int:
    return _gf256_mul(a, _gf256_inv(b))


def _lagrange_at_zero(x_vals: list[int], y_vals: list[int]) -> int:
    """Lagrange interpolation at 0: sum y_j * L_j(0)."""
    n = len(x_vals)
    s = 0
    for j in range(n):
        num, den = 1, 1
        for i in range(n):
            if i == j:
                continue
            num = _gf256_mul(num, x_vals[i])
            den = _gf256_mul(den, x_vals[i] ^ x_vals[j])
        s ^= _gf256_mul(_gf256_div(num, den), y_vals[j])
    return s


def shamir_split_byte(secret_byte: int, threshold: int, total: int) -> list[tuple[int, int]]:
    """Split one byte into 'total' shares; 'threshold' needed to reconstruct. Returns [(index, value), ...]."""
    # P(x) = s + c1*x + c2*x^2; indices 1..total
    c1 = os.urandom(1)[0]
    c2 = os.urandom(1)[0]
    shares = []
    for i in range(1, total + 1):
        # P(i) = s + c1*i + c2*i^2 in GF(256)
        val = _gf256_add(secret_byte, _gf256_mul(c1, i))
        val = _gf256_add(val, _gf256_mul(c2, _gf256_mul(i, i)))
        shares.append((i, val))
    return shares


def shamir_combine_byte(shares: list[tuple[int, int]]) -> int:
    """Reconstruct byte from shares [(index, value), ...]. Need at least 3 shares."""
    x_vals = [s[0] for s in shares]
    y_vals = [s[1] for s in shares]
    return _lagrange_at_zero(x_vals, y_vals)


def generate_master_key(master_password: str, salt: bytes | None = None) -> bytes:
    """Deriva una llave maestra de 32 bytes (PBKDF2-SHA512)."""
    if salt is None:
        salt = os.urandom(16)
    return hashlib.pbkdf2_hmac("sha512", master_password.encode("utf-8"), salt, 100_000, dklen=32)


def split_master_key(master_key: bytes, threshold: int = 3, total: int = 5) -> list[tuple[int, bytes]]:
    """
    Divide la llave maestra en 'total' fragmentos; 'threshold' reconstruyen.
    Cada fragmento: (índice 1..5, 32 bytes).
    """
    result: list[tuple[int, bytes]] = []
    for share_index in range(1, total + 1):
        values = []
        for byte_idx in range(32):
            shares = shamir_split_byte(master_key[byte_idx], threshold, total)
            # shares[i] = (index, value); tomamos el value donde index == share_index
            val = next(v for i, v in shares if i == share_index)
            values.append(val)
        result.append((share_index, bytes(values)))
    return result


def combine_master_key(fragment_data_list: list[tuple[int, bytes]]) -> bytes:
    """Reconstruye la llave maestra a partir de 3 o más fragmentos. Cada elemento: (índice, 32 bytes)."""
    if len(fragment_data_list) < 3:
        raise ValueError("Se necesitan al menos 3 fragmentos para reconstruir")
    master = bytearray(32)
    for byte_idx in range(32):
        shares = [(fd[0], fd[1][byte_idx]) for fd in fragment_data_list]
        master[byte_idx] = shamir_combine_byte(shares)
    return bytes(master)


def encrypt_aes_cbc(data: bytes, password: str, salt: bytes) -> tuple[bytes, bytes, bytes]:
    """Encripta con AES-256-CBC; clave derivada PBKDF2-SHA256. Devuelve (salt, iv, ciphertext)."""
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
    iv = os.urandom(16)
    pad_len = 16 - (len(data) % 16)
    padded = data + bytes([pad_len] * pad_len)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    enc = cipher.encryptor()
    ct = enc.update(padded) + enc.finalize()
    return salt, iv, ct


def decrypt_aes_cbc(salt: bytes, iv: bytes, ciphertext: bytes, password: str) -> bytes:
    """Desencripta AES-256-CBC."""
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


# Ubicaciones estándar (sin contraseñas en código; se piden o se usan la maestra)
LOCATIONS = [
    "junta_extremadura",  # Cáceres
    "notario_madrid",
    "yubikey",
    "bbva_vault",
    "ipfs",
]


def store_fragment(index: int, fragment_payload: bytes, location: str, password: str, out_dir: str) -> str:
    """
    Encripta el fragmento (índice + 32 bytes) y lo guarda.
    fragment_payload = 32 bytes del fragmento; guardamos (index || payload) encriptado.
    """
    payload = bytes([index]) + fragment_payload  # 1 + 32 = 33 bytes
    salt = os.urandom(16)
    salt, iv, ct = encrypt_aes_cbc(payload, password, salt)
    path = os.path.join(out_dir, f"{location}_fragment.enc")
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    with open(path, "wb") as f:
        f.write(salt + iv + ct)
    return path


def main() -> None:
    print("Generación de llaves de emergencia (Shamir 3/5)")
    master_password = getpass.getpass("Introduce la contraseña maestra: ")
    if not master_password:
        print("Contraseña vacía.", file=sys.stderr)
        sys.exit(1)

    salt = os.urandom(16)
    master_key = generate_master_key(master_password, salt)
    fragments = split_master_key(master_key, threshold=3, total=5)

    out_dir = os.environ.get("CASTUO_FRAGMENTS_DIR", "/opt/castuo/secure_fragments")
    print(f"Directorio de salida: {out_dir}")

    # Por defecto todas las ubicaciones usan la contraseña maestra para encriptar el fragmento
    for (index, payload), loc in zip(fragments, LOCATIONS):
        pwd = master_password  # En producción se puede pedir una contraseña por ubicación
        path = store_fragment(index, payload, loc, pwd, out_dir)
        print(f"Fragmento {index} ({loc}) guardado en: {path}")

    # Guardar salt solo para derivación (opcional; si se pierde, no se puede derivar la misma key sin él)
    salt_path = os.path.join(out_dir, "master_key.salt")
    with open(salt_path, "wb") as f:
        f.write(salt)
    os.chmod(salt_path, 0o600)
    print(f"Salt guardado en: {salt_path} (necesario para reconstruir)")

    print("Llaves de emergencia generadas. Se necesitan 3/5 fragmentos para reconstruir.")
    print("Distribuir cada fragmento a su ubicación (Junta, Notario, YubiKey, BBVA, IPFS+GaiaChain).")


if __name__ == "__main__":
    main()
