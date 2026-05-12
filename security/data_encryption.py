# -*- coding: utf-8 -*-
"""
Cifrado de datos CASTUO 5.0 — AES-256-GCM, PBKDF2, TPM 2.0 opcional.
Normativas: GDPR Art. 32, ISO 27040, eIDAS.
"""
import base64
import os
from typing import Any, Optional, Tuple

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

backend = default_backend()

try:
    import tpm2_pytss  # type: ignore
    HAS_TPM = True
except ImportError:
    HAS_TPM = False
    tpm2_pytss = None  # type: ignore


class DataEncryption:
    """
    Cifrado AES-256-GCM en reposo; opcional sellado de claves en TPM 2.0.
    """

    def __init__(self) -> None:
        self.backend = default_backend()
        self.tpm = tpm2_pytss.TPM2() if HAS_TPM else None

    def generate_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Genera clave de cifrado con PBKDF2-HMAC-SHA512 (100.000 iteraciones)."""
        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=self.backend,
        )
        key = kdf.derive(password.encode())
        return key, salt

    def encrypt_data(self, data: str, key: bytes) -> str:
        """Cifra datos con AES-256-GCM (IV 96 bits + tag 128 bits)."""
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(128).padder()
        padded = padder.update(data.encode()) + padder.finalize()
        ct = encryptor.update(padded) + encryptor.finalize()
        tag = encryptor.tag
        return base64.b64encode(iv + tag + ct).decode()

    def decrypt_data(self, encrypted_data: str, key: bytes) -> str:
        """Descifra datos cifrados con AES-256-GCM."""
        raw = base64.b64decode(encrypted_data.encode())
        iv, tag, ct = raw[:12], raw[12:28], raw[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        padded = decryptor.update(ct) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return (unpadder.update(padded) + unpadder.finalize()).decode()

    def seal_key_in_tpm(self, key: bytes, description: str) -> Optional[int]:
        """Sella una clave en TPM 2.0 (requiere hardware). Retorna handle o None."""
        if not HAS_TPM or not self.tpm:
            return None
        try:
            primary = self.tpm.create_primary(
                tpm2_pytss.ESYS_TR_RH_OWNER,
                tpm2_pytss.TPM2_ALG_ECC,
                tpm2_pytss.TPM2_ALG_SHA256,
                None,
                None,
            )
            sealed = self.tpm.seal(key, primary, tpm2_pytss.TPM2_ALG_AES, 256, description.encode())
            return sealed
        except Exception:
            return None

    def unseal_key_from_tpm(self, sealed_key_handle: int, primary_key: Any) -> Optional[bytes]:
        """Recupera clave sellada desde TPM 2.0."""
        if not HAS_TPM or not self.tpm:
            return None
        try:
            return self.tpm.unseal(sealed_key_handle, primary_key)
        except Exception:
            return None
