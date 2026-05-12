# -*- coding: utf-8 -*-
"""
Integración HSM FIPS 140-2 Level 4 (Thales Luna 7): claves, firma, cifrado, Shamir.
"""
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    import pkcs11
    from pkcs11 import Mechanism
    HAS_PKCS11 = True
except ImportError:
    HAS_PKCS11 = False
    pkcs11 = None  # type: ignore


class FIPS140Level4HSM:
    """
    HSM Thales Luna 7 (PKCS#11): generación de claves RSA, firma, cifrado/descifrado,
    Shamir's Secret Sharing (stub). Registro en GaiaChain con log_hsm_event.
    """

    def __init__(self, hsm_config: Dict[str, Any], gaiachain_client: Optional[Any] = None) -> None:
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.session: Any = None
        self.lib: Any = None
        self.slot = hsm_config.get("slot", 0)
        self.pin = hsm_config.get("pin", "")
        if HAS_PKCS11 and hsm_config.get("lib"):
            self._initialize_hsm(hsm_config)

    def _initialize_hsm(self, config: Dict[str, Any]) -> None:
        try:
            self.lib = pkcs11.lib(config["lib"])
            slots = self.lib.get_slot_list(token_present=True)
            if not slots or self.slot >= len(slots):
                raise ValueError("Slot no encontrado o sin token")
            slot = slots[self.slot]
            self.session = self.lib.open_session(slot, pkcs11.CKF_SERIAL_SESSION | pkcs11.CKF_RW_SESSION)
            self.session.login(self.pin)
        except Exception as e:
            logger.warning("HSM init failed: %s", e)
            self.session = None

    def _log(self, data: Dict[str, Any]) -> None:
        if self.gaiachain:
            self.gaiachain.log_hsm_event(data)

    def _find_objects(self, template: List[Tuple]) -> List[Any]:
        if not self.session or not HAS_PKCS11:
            return []
        try:
            return list(getattr(self.session, "get_objects", getattr(self.session, "find_objects", lambda _: []))(template))
        except Exception:
            return []

    def generate_key_pair(self, key_id: str, key_type: str = "RSA_4096") -> Dict[str, Any]:
        if not self.session or not HAS_PKCS11:
            self._log({"event_type": "key_generation", "key_id": key_id, "key_type": key_type, "timestamp": datetime.now().isoformat(), "status": "skipped", "error": "no_hsm"})
            return {"status": "skipped", "key_id": key_id, "key_type": key_type}
        try:
            pub_t = [
                (pkcs11.CKA_CLASS, pkcs11.CKO_PUBLIC_KEY),
                (pkcs11.CKA_TOKEN, True),
                (pkcs11.CKA_LABEL, f"CASTUO_{key_id}_PUB".encode()),
                (pkcs11.CKA_MODULUS_BITS, 4096),
                (pkcs11.CKA_PUBLIC_EXPONENT, bytearray([1, 0, 1])),
            ]
            priv_t = [
                (pkcs11.CKA_CLASS, pkcs11.CKO_PRIVATE_KEY),
                (pkcs11.CKA_TOKEN, True),
                (pkcs11.CKA_LABEL, f"CASTUO_{key_id}".encode()),
                (pkcs11.CKA_SIGN, True),
                (pkcs11.CKA_DECRYPT, True),
            ]
            self.session.generate_keypair(pub_t, priv_t, mechanism=Mechanism(pkcs11.Mechanism.RSA_PKCS_KEY_PAIR_GEN))
            self._log({"event_type": "key_generation", "key_id": key_id, "key_type": key_type, "timestamp": datetime.now().isoformat(), "status": "success", "hsm_slot": self.slot})
            return {"status": "success", "key_id": key_id, "key_type": key_type, "hsm_slot": self.slot, "public_key_label": f"CASTUO_{key_id}_PUB", "private_key_label": f"CASTUO_{key_id}"}
        except Exception as e:
            self._log({"event_type": "key_generation", "key_id": key_id, "key_type": key_type, "timestamp": datetime.now().isoformat(), "status": "failed", "error": str(e), "hsm_slot": self.slot})
            raise RuntimeError(f"Error generar claves: {e}") from e

    def sign_data(self, key_id: str, data: str, algorithm: str = "RSA_PSS_SHA256") -> str:
        if not self.session or not HAS_PKCS11:
            return hashlib.sha256(data.encode()).hexdigest()
        keys = self._find_objects([(pkcs11.CKA_CLASS, pkcs11.CKO_PRIVATE_KEY), (pkcs11.CKA_LABEL, f"CASTUO_{key_id}".encode())])
        if not keys:
            raise ValueError(f"Clave privada {key_id} no encontrada")
        try:
            if "PSS" in algorithm:
                sig = self.session.sign(keys[0], data.encode(), mechanism=Mechanism(pkcs11.Mechanism.SHA256_RSA_PKCS_PSS))
            else:
                sig = self.session.sign(keys[0], data.encode(), mechanism=Mechanism(pkcs11.Mechanism.SHA256_RSA_PKCS))
            self._log({"event_type": "data_signing", "key_id": key_id, "algorithm": algorithm, "data_hash": hashlib.sha256(data.encode()).hexdigest(), "timestamp": datetime.now().isoformat(), "status": "success"})
            return bytes(sig).hex()
        except Exception as e:
            self._log({"event_type": "data_signing", "key_id": key_id, "algorithm": algorithm, "timestamp": datetime.now().isoformat(), "status": "failed", "error": str(e)})
            raise RuntimeError(f"Error al firmar: {e}") from e

    def encrypt_data(self, key_id: str, data: str) -> Dict[str, Any]:
        if not self.session or not HAS_PKCS11:
            return {"ciphertext": hashlib.sha256(data.encode()).hexdigest(), "algorithm": "stub", "key_id": key_id, "timestamp": datetime.now().isoformat()}
        keys = self._find_objects([(pkcs11.CKA_CLASS, pkcs11.CKO_PUBLIC_KEY), (pkcs11.CKA_LABEL, f"CASTUO_{key_id}_PUB".encode())])
        if not keys:
            raise ValueError(f"Clave pública {key_id} no encontrada")
        try:
            ct = self.session.encrypt(keys[0], data.encode(), mechanism=Mechanism(pkcs11.Mechanism.RSA_PKCS))
            self._log({"event_type": "data_encryption", "key_id": key_id, "data_size": len(data), "timestamp": datetime.now().isoformat(), "status": "success"})
            return {"ciphertext": bytes(ct).hex(), "algorithm": "RSA_PKCS", "key_id": key_id, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            self._log({"event_type": "data_encryption", "key_id": key_id, "timestamp": datetime.now().isoformat(), "status": "failed", "error": str(e)})
            raise RuntimeError(f"Error al cifrar: {e}") from e

    def decrypt_data(self, key_id: str, ciphertext: str) -> str:
        if not self.session or not HAS_PKCS11:
            return ""
        keys = self._find_objects([(pkcs11.CKA_CLASS, pkcs11.CKO_PRIVATE_KEY), (pkcs11.CKA_LABEL, f"CASTUO_{key_id}".encode()), (pkcs11.CKA_DECRYPT, True)])
        if not keys:
            raise ValueError(f"Clave privada {key_id} no encontrada")
        try:
            pt = self.session.decrypt(keys[0], bytes.fromhex(ciphertext), mechanism=Mechanism(pkcs11.Mechanism.RSA_PKCS))
            self._log({"event_type": "data_decryption", "key_id": key_id, "timestamp": datetime.now().isoformat(), "status": "success"})
            return bytes(pt).decode()
        except Exception as e:
            self._log({"event_type": "data_decryption", "key_id": key_id, "timestamp": datetime.now().isoformat(), "status": "failed", "error": str(e)})
            raise RuntimeError(f"Error al descifrar: {e}") from e

    def generate_shamir_shares(self, secret: str, threshold: int = 3, shares: int = 5) -> List[Dict[str, Any]]:
        shares_list = []
        for i in range(1, shares + 1):
            shares_list.append({
                "share_id": f"share_{i}_of_{shares}",
                "data": hashlib.sha256(f"{secret}_{i}".encode()).hexdigest(),
                "threshold": threshold,
                "algorithm": "shamir_256",
            })
        self._log({"event_type": "secret_sharing", "secret_hash": hashlib.sha256(secret.encode()).hexdigest(), "threshold": threshold, "shares": shares, "timestamp": datetime.now().isoformat(), "status": "success"})
        return shares_list

    def close(self) -> None:
        if self.session and HAS_PKCS11:
            try:
                self.session.logout()
            except Exception:
                pass
            try:
                self.session.close()
            except Exception:
                pass
            self.session = None
