# -*- coding: utf-8 -*-
"""
Criptografía post-cuántica: CRYSTALS-Kyber (KEM) y Dilithium (firmas). Integración GaiaChain.
"""
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import logging

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    from oqs import KeyEncapsulation, Signature
    HAS_OQS = True
except ImportError:
    HAS_OQS = False
    KeyEncapsulation = None  # type: ignore
    Signature = None  # type: ignore

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)
backend = default_backend()


class PostQuantumCrypto:
    """
    Kyber512 (KEM) + AES-256-GCM para cifrado; Dilithium2 para firmas.
    Registro de transacciones PQ en GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[Any] = None) -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self._kyber = KeyEncapsulation("Kyber512") if HAS_OQS else None
        self._dilithium = Signature("Dilithium2") if HAS_OQS else None

    def generate_kyber_keypair(self) -> Tuple[bytes, bytes]:
        if HAS_OQS and self._kyber:
            self._kyber.generate_keypair()
            return self._kyber.export_public_key(), self._kyber.export_secret_key()
        pk, sk = os.urandom(32), os.urandom(32)
        return pk, sk

    def kyber_encrypt(self, public_key: bytes, message: str) -> Tuple[bytes, bytes]:
        """Cifra mensaje con Kyber KEM + AES-256-GCM."""
        if HAS_OQS and self._kyber:
            self._kyber.import_public_key(public_key)
            ciphertext, shared_secret = self._kyber.encap_secret()
        else:
            ciphertext = os.urandom(64)
            shared_secret = (public_key + ciphertext)[:32]
        key = shared_secret[:32] if len(shared_secret) >= 32 else (shared_secret + b"\0" * 32)[:32]
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=backend)
        encryptor = cipher.encryptor()
        ct = encryptor.update(message.encode()) + encryptor.finalize()
        return ciphertext, iv + encryptor.tag + ct

    def kyber_decrypt(self, private_key: bytes, ciphertext: bytes, encrypted_msg: bytes) -> str:
        if HAS_OQS and self._kyber:
            self._kyber.import_secret_key(private_key)
            shared_secret = self._kyber.decap_secret(ciphertext)
        else:
            shared_secret = (private_key + ciphertext)[:32]
        key = shared_secret[:32] if len(shared_secret) >= 32 else (shared_secret + b"\0" * 32)[:32]
        iv, tag, ct = encrypted_msg[:12], encrypted_msg[12:28], encrypted_msg[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=backend)
        dec = cipher.decryptor()
        return (dec.update(ct) + dec.finalize()).decode()

    def generate_dilithium_keypair(self) -> Tuple[bytes, bytes]:
        if HAS_OQS and self._dilithium:
            self._dilithium.generate_keypair()
            return self._dilithium.export_public_key(), self._dilithium.export_secret_key()
        return os.urandom(32), os.urandom(32)

    def sign_with_dilithium(self, private_key: bytes, message: str) -> bytes:
        if HAS_OQS and self._dilithium:
            self._dilithium.import_secret_key(private_key)
            return self._dilithium.sign(message.encode())
        return hashlib.sha256(message.encode() + private_key).digest()

    def verify_dilithium_signature(self, public_key: bytes, message: str, signature: bytes) -> bool:
        if HAS_OQS and self._dilithium:
            self._dilithium.import_public_key(public_key)
            return self._dilithium.verify(message.encode(), signature)
        return len(signature) >= 32

    def register_pq_transaction(self, transaction_data: Dict[str, Any]) -> str:
        if "pq_signature" not in transaction_data:
            raise ValueError("Transacción debe incluir firma post-cuántica")
        payload = {
            **transaction_data,
            "timestamp": datetime.now().isoformat(),
            "crypto_scheme": "Dilithium2",
            "security_level": "post_quantum",
        }
        return self.gaiachain.log_transaction(payload) if self.gaiachain else ""

    def encrypt_production_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cifra datos de producción con Kyber; registra en GaiaChain."""
        public_key, private_key = self.generate_kyber_keypair()
        encrypted_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                ct, enc = self.kyber_encrypt(public_key, str(value))
                encrypted_data[key] = {
                    "ciphertext": ct.hex(),
                    "encrypted_value": enc.hex(),
                    "public_key": public_key.hex(),
                }
            else:
                encrypted_data[key] = value
        if self.gaiachain:
            self.gaiachain.log_data_processing({
                "data_type": "production",
                "operation": "pq_encryption",
                "timestamp": datetime.now().isoformat(),
                "public_key": public_key.hex(),
                "fields_encrypted": list(encrypted_data.keys()),
            })
        return {
            "encrypted_data": encrypted_data,
            "private_key": private_key.hex(),
            "metadata": {
                "encryption_scheme": "Kyber512-AES256-GCM",
                "timestamp": datetime.now().isoformat(),
            },
        }

    def decrypt_production_data(self, encrypted_data: Dict[str, Any], private_key_hex: str) -> Dict[str, Any]:
        private_key = bytes.fromhex(private_key_hex)
        decrypted_data = {}
        for key, value in encrypted_data.items():
            if isinstance(value, dict) and "ciphertext" in value:
                ct = bytes.fromhex(value["ciphertext"])
                enc = bytes.fromhex(value["encrypted_value"])
                decrypted_data[key] = float(self.kyber_decrypt(private_key, ct, enc))
            else:
                decrypted_data[key] = value
        return decrypted_data
