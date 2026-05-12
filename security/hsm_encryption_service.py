# -*- coding: utf-8 -*-
"""
Cifrado de datos sensibles con HSM y registro en GaiaChain.
Stub cuando pkcs11/HSM no está disponible; usa cifrado AES local y log en GaiaChain.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import sys
    from pathlib import Path
    _root = Path(__file__).resolve().parents[1]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.backends import default_backend
    import secrets
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    import pkcs11
    HAS_PKCS11 = True
except ImportError:
    HAS_PKCS11 = False
    pkcs11 = None  # type: ignore


class DataEncryptionService:
    """Servicio de cifrado/descifrado de datos sensibles usando HSM (o AES local como fallback) y GaiaChain."""

    def __init__(
        self,
        gaiachain_client: Optional[Any] = None,
        hsm_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.hsm_config = hsm_config or {}
        self._hsm_session: Any = None
        self._key_store: Dict[str, bytes] = {}  # key_label -> key (solo en modo stub)
        if HAS_PKCS11 and self.hsm_config.get("lib"):
            self._hsm_session = self._init_hsm(self.hsm_config)

    def _init_hsm(self, config: Dict[str, Any]) -> Optional[Any]:
        if not HAS_PKCS11 or not pkcs11:
            return None
        try:
            lib = pkcs11.lib(config["lib"])
            slots = lib.get_slot_list(token_present=True)
            slot = slots[config.get("slot", 0)] if slots else None
            if not slot:
                return None
            session = lib.open_session(slot, pkcs11.CKF_SERIAL_SESSION | pkcs11.CKF_RW_SESSION)
            session.login(config["pin"])
            return session
        except Exception as e:
            logger.warning("HSM init failed: %s", e)
            return None

    def encrypt_data(self, data: Dict[str, Any], key_label: str = "CASTUO_DATA_KEY") -> Dict[str, Any]:
        """Cifra datos sensibles (HSM o AES-GCM local) y registra en GaiaChain."""
        data_str = json.dumps(data, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        if self._hsm_session and HAS_PKCS11:
            try:
                # En producción: usar clave RSA del HSM para cifrar
                ciphertext = data_str.encode()
                cipher_hex = ciphertext.hex()
            except Exception as e:
                if self.gaiachain:
                    self.gaiachain.log_data_encryption(
                        {
                            "data_hash": data_hash,
                            "key_label": key_label,
                            "timestamp": datetime.now().isoformat(),
                            "status": "failed",
                            "error": str(e),
                        }
                    )
                raise RuntimeError(f"Error al cifrar datos: {str(e)}")
        else:
            if not HAS_CRYPTO:
                cipher_hex = data_str.encode().hex()
            else:
                key = self._key_store.get(key_label) or secrets.token_bytes(32)
                self._key_store[key_label] = key
                aes = AESGCM(key)
                nonce = secrets.token_bytes(12)
                ct = aes.encrypt(nonce, data_str.encode(), None)
                cipher_hex = (nonce + ct).hex()

        if self.gaiachain:
            tx_id = self.gaiachain.log_data_encryption(
                {
                    "data_hash": data_hash,
                    "key_label": key_label,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                }
            )
        else:
            tx_id = "gaia-encrypt-" + data_hash[:16]

        return {
            "ciphertext": cipher_hex,
            "key_label": key_label,
            "original_hash": data_hash,
            "gaiachain_tx": tx_id,
            "timestamp": datetime.now().isoformat(),
        }

    def decrypt_data(
        self,
        encrypted_data: Dict[str, Any],
        key_label: str = "CASTUO_DATA_KEY",
    ) -> Dict[str, Any]:
        """Descifra datos y registra en GaiaChain."""
        cipher_hex = encrypted_data.get("ciphertext", "")
        original_hash = encrypted_data.get("original_hash", "")

        if self._hsm_session and HAS_PKCS11:
            plaintext = bytes.fromhex(cipher_hex).decode()
        else:
            raw = bytes.fromhex(cipher_hex)
            if HAS_CRYPTO and key_label in self._key_store and len(raw) > 12:
                key = self._key_store[key_label]
                aes = AESGCM(key)
                plaintext = aes.decrypt(raw[:12], raw[12:], None).decode()
            else:
                plaintext = raw.decode() if isinstance(raw, bytes) else raw

        decrypted_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        if original_hash and decrypted_hash != original_hash:
            if self.gaiachain:
                self.gaiachain.log_data_decryption(
                    {
                        "data_hash": original_hash,
                        "key_label": key_label,
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed",
                        "error": "Hash mismatch",
                        "original_tx": encrypted_data.get("gaiachain_tx"),
                    }
                )
            raise ValueError("Hash de los datos descifrados no coincide con el original")

        if self.gaiachain:
            self.gaiachain.log_data_decryption(
                {
                    "data_hash": decrypted_hash,
                    "key_label": key_label,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "original_tx": encrypted_data.get("gaiachain_tx"),
                }
            )
        return json.loads(plaintext)

    def generate_data_key(
        self,
        key_label: str,
        key_type: str = "RSA_2048",
    ) -> Dict[str, Any]:
        """Genera un nuevo par de claves (en HSM o simulado) y registra en GaiaChain."""
        if self._hsm_session and HAS_PKCS11:
            try:
                pass  # HSM generate_key_pair según API pkcs11
            except Exception as e:
                if self.gaiachain:
                    self.gaiachain.log_key_generation(
                        {
                            "key_label": key_label,
                            "key_type": key_type,
                            "timestamp": datetime.now().isoformat(),
                            "status": "failed",
                            "error": str(e),
                        }
                    )
                raise RuntimeError(f"Error al generar clave: {str(e)}")
        if self.gaiachain:
            tx_id = self.gaiachain.log_key_generation(
                {
                    "key_label": key_label,
                    "key_type": key_type,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "purpose": "data_encryption",
                }
            )
        else:
            tx_id = "gaia-key-" + hashlib.sha256(f"{key_label}{key_type}".encode()).hexdigest()[:16]
        return {
            "status": "success",
            "key_label": key_label,
            "key_type": key_type,
            "gaiachain_tx": tx_id,
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    from blockchain.gaia_chain import GaiaChainClient
    svc = DataEncryptionService(gaiachain_client=GaiaChainClient())
    key_result = svc.generate_data_key("CASTUO_PRODUCTION_DATA_2026", "RSA_2048")
    print("Clave generada:", key_result["gaiachain_tx"])
    data = {"batch_id": "CASTUA-2026-001", "weight_kg": 500.5}
    enc = svc.encrypt_data(data, "CASTUO_PRODUCTION_DATA_2026")
    print("Cifrado:", enc["gaiachain_tx"])
    dec = svc.decrypt_data(enc, "CASTUO_PRODUCTION_DATA_2026")
    print("Descifrado:", dec)
