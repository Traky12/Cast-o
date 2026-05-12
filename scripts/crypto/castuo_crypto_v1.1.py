#!/usr/bin/env python3
"""
CASTÚO-SYSTEM™ — Cifrado E2E v1.1: AES-256-GCM + Shamir 3/5 (5 shards).
Shards: hsm, swiss, gaia, rpi, quantum. Se requieren 3 de 5 para recuperar la clave.
Sin claves ni PINs en código; uso por contraseña/env o recuperación desde shards.
"""
from __future__ import annotations

import os
import sys

# Importar Shamir desde el módulo de emergencia (mismo repo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_SCRIPTS = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
if REPO_SCRIPTS not in sys.path:
    sys.path.insert(0, REPO_SCRIPTS)

try:
    from security.generate_emergency_keys import (
        combine_master_key,
        split_master_key,
    )
except ImportError:
    combine_master_key = None
    split_master_key = None


def _derive_master_key(password: str, salt: bytes | None = None) -> bytes:
    """Deriva clave maestra de 32 bytes (PBKDF2-SHA512)."""
    import hashlib
    if salt is None:
        salt = os.urandom(16)
    return hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, 100_000, dklen=32)


class CastuoCrypto:
    """Cifrado v1.1: 5 shards (hsm, swiss, gaia, rpi, quantum), 3 requeridos para recuperar clave."""

    SHARD_NAMES = ("hsm", "swiss", "gaia", "rpi", "quantum")

    def __init__(
        self,
        *,
        shards: dict[str, tuple[int, bytes]] | None = None,
        master_key: bytes | None = None,
        password: str | None = None,
        salt: bytes | None = None,
    ):
        """
        Inicialización.
        - shards: dict nombre -> (índice 1..5, 32 bytes). Si hay al menos 3, se usa recover_key().
        - master_key: clave ya recuperada (32 bytes).
        - password + salt: derivan clave maestra (para tests o cuando no hay shards).
        """
        self._master_key: bytes | None = master_key
        self._shards = shards or {}
        self._salt = salt
        if password is not None and master_key is None and not self._shards:
            self._master_key = _derive_master_key(password, salt)

    def set_shards(self, shards: dict[str, tuple[int, bytes]]) -> None:
        """Establece los shards por nombre (ej. hsm, swiss, gaia, rpi, quantum)."""
        self._shards = shards
        self._master_key = None

    def recover_key(self) -> bytes:
        """Recupera la clave maestra desde al menos 3 shards. Requiere combine_master_key del módulo Shamir."""
        if self._master_key is not None:
            return self._master_key
        if combine_master_key is None:
            raise RuntimeError("generate_emergency_keys no disponible para combinar shards")
        # Construir lista (index, 32 bytes) con al menos 3 shards
        fragment_list = list(self._shards.values())
        if len(fragment_list) < 3:
            raise ValueError("Se necesitan al menos 3 shards para recuperar la clave")
        self._master_key = combine_master_key(fragment_list[:3])
        return self._master_key

    def encrypt_data(self, data: bytes) -> dict:
        """Cifra con AES-256-GCM; requiere clave recuperada (3/5 shards o password)."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = self.recover_key()
        if len(key) != 32:
            raise ValueError("Clave debe ser 32 bytes")
        nonce = os.urandom(12)
        aes = AESGCM(key)
        ct = aes.encrypt(nonce, data, None)  # ciphertext || tag (16 bytes)
        return {"nonce": nonce, "ct": ct}

    def decrypt_data(self, payload: dict) -> bytes:
        """Descifra payload con 'nonce' y 'ct' (ct = ciphertext || tag)."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key = self.recover_key()
        nonce = payload["nonce"]
        ct = payload.get("ct") or (payload.get("ciphertext", b"") + payload.get("tag", b""))
        aes = AESGCM(key)
        return aes.decrypt(nonce, ct, None)


def create_shards_from_password(password: str, salt: bytes | None = None) -> tuple[bytes, dict[str, tuple[int, bytes]]]:
    """
    Deriva clave maestra con password, la divide en 5 shards (3/5) y devuelve (salt, dict nombre -> (idx, bytes)).
    Útil para bootstrap: luego distribuir cada shard a hsm, swiss, gaia, rpi, quantum.
    """
    if split_master_key is None:
        raise RuntimeError("generate_emergency_keys no disponible")
    if salt is None:
        salt = os.urandom(16)
    master = _derive_master_key(password, salt)
    fragments = split_master_key(master, threshold=3, total=5)
    shards = {name: fragments[i] for i, name in enumerate(CastuoCrypto.SHARD_NAMES)}
    return salt, shards


def main() -> None:
    """Ejemplo: cifrar/descifrar con password (sin shards)."""
    import getpass
    pwd = getpass.getpass("Contraseña (ejemplo): ")
    crypto = CastuoCrypto(password=pwd)
    plain = b"CASTUO TRL11 secret"
    enc = crypto.encrypt_data(plain)
    dec = crypto.decrypt_data(enc)
    assert dec == plain
    print("✅ Cifrado v1.1 OK: encrypt_data/decrypt_data con password.")


if __name__ == "__main__":
    main()
