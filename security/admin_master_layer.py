# -*- coding: utf-8 -*-
"""
Capa clave maestra del administrador general del sistema.
Todo el material sensible puede cifrarse bajo esta única clave; sin ella no se accede a secretos.
Clave desde: ADMIN_MASTER_KEY (env), /run/secrets/admin_master_key (Docker), o security/.admin_master_key (local, no versionar).
"""
from __future__ import annotations

import base64
import os
from pathlib import Path

_SALT = b"castuo-admin-layer-v1.7"
_INFO = b"CASTUO_ADMIN_MASTER_DERIVE"


def _get_admin_master_key() -> bytes:
    """Obtiene la clave maestra del administrador (bytes). Prioridad: env, Docker secret, archivo local."""
    raw = os.environ.get("ADMIN_MASTER_KEY")
    if raw:
        return raw.encode("utf-8") if isinstance(raw, str) else raw
    secret_path = Path("/run/secrets/admin_master_key")
    if secret_path.is_file():
        return secret_path.read_bytes().strip()
    local_path = Path(__file__).resolve().parent / ".admin_master_key"
    if local_path.is_file():
        return local_path.read_bytes().strip()
    raise RuntimeError(
        "Clave maestra administrador no configurada: export ADMIN_MASTER_KEY, "
        "montar secret admin_master_key, o crear security/.admin_master_key (no versionar)"
    )


def _derive_key(master: bytes) -> bytes:
    """Deriva clave AES-256 (32 bytes) desde la clave maestra (HKDF)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.backends import default_backend
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        info=_INFO,
        backend=default_backend(),
    )
    return hkdf.derive(master)


def encrypt(plaintext: bytes) -> bytes:
    """Cifra plaintext con AES-256-GCM bajo la clave maestra del administrador. Devuelve base64(nonce || ct)."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    key = _derive_key(_get_admin_master_key())
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ct = aes.encrypt(nonce, plaintext, None)
    return base64.b64encode(nonce + ct)


def decrypt(payload_b64: bytes | str) -> bytes:
    """Descifra payload (base64 de nonce||ciphertext+tag) con la clave maestra."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if isinstance(payload_b64, str):
        payload_b64 = payload_b64.encode("utf-8")
    raw = base64.b64decode(payload_b64)
    if len(raw) < 12 + 16:
        raise ValueError("Payload cifrado inválido")
    nonce, ct = raw[:12], raw[12:]
    key = _derive_key(_get_admin_master_key())
    aes = AESGCM(key)
    return aes.decrypt(nonce, ct, None)
