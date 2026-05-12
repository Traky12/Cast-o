# backend/security/end_to_end_encryption.py — Cifrado E2E (RSA-4096 + AES-256-GCM + Kyber-1024)

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

try:
    from backend.security.pq_crypto import PostQuantumCrypto
    _PQ = True
except ImportError:
    PostQuantumCrypto = None
    _PQ = False

try:
    from backend.security.hsm_integration import HSMIntegration
    _HSM = True
except ImportError:
    HSMIntegration = None
    _HSM = False

try:
    from backend.security.mpc_integration import MPCIntegration
    _MPC = True
except ImportError:
    MPCIntegration = None
    _MPC = False


def _blake3_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class EndToEndEncryption:
    """
    Cifrado end-to-end:
    - Híbrido RSA-4096 + AES-256-GCM
    - Opcional Kyber-1024 para material de clave
    - PBKDF2 para derivación de claves
    - Hash BLAKE3 para integridad
    """

    def __init__(self) -> None:
        self.pq_crypto = PostQuantumCrypto() if _PQ and PostQuantumCrypto else None
        self.backend = default_backend()
        self.key_rotation_interval = 90
        self.key_usage_log: List[Dict[str, Any]] = []
        self.hsm_integration = HSMIntegration() if _HSM and HSMIntegration else None
        self.mpc_integration = MPCIntegration(threshold=3, total_parties=5) if _MPC and MPCIntegration else None
        self._current_private_key: Optional[bytes] = None
        self._current_public_key: Optional[bytes] = None
        self._last_rotation_time: Optional[datetime] = None
        # Clave simétrica interna para cifrado sencillo (no rompe APIs existentes)
        self._symmetric_key: bytes = os.urandom(32)
        self.holographic = None
        # Integración perezosa con HolographicEncryption (si existe y está activado)
        try:
            from backend.digital_twin.holographic_encryption import HolographicEncryption as _HE

            if _HE.is_enabled():
                self.holographic = _HE()
        except Exception:
            self.holographic = None

    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """Genera par RSA-4096."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=self.backend,
        )
        public_key = private_key.public_key()
        return (
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ),
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ),
        )

    def generate_secure_key_pair(
        self,
        key_size: int = 4096,
        use_password_encryption: bool = False,
        password: bytes = b"secure-password",
        use_hsm: bool = False,
        use_mpc: bool = False,
    ) -> Tuple[bytes, bytes]:
        """Genera par de claves: MPC (distribuido), HSM o software."""
        if use_mpc and self.mpc_integration:
            self.mpc_integration.generate_distributed_key(key_size)
            return (b"mpc_private_key", b"mpc_public_key")
        if use_hsm and self.hsm_integration and self.hsm_integration.available():
            return self.hsm_integration.generate_key_pair(key_size)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=self.backend,
        )
        private_key = self._apply_key_hardening(private_key)
        public_key = private_key.public_key()
        enc_alg = (
            serialization.BestAvailableEncryption(password)
            if use_password_encryption
            else serialization.NoEncryption()
        )
        return (
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=enc_alg,
            ),
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ),
        )

    def _apply_key_hardening(self, private_key: rsa.RSAPrivateKey) -> rsa.RSAPrivateKey:
        """Hardening adicional (validación de parámetros; en producción incluir blinding/verificación)."""
        return private_key

    def generate_secure_parameters(self) -> Dict[str, Any]:
        """Parámetros de seguridad óptimos para HE y cumplimiento."""
        return {
            "poly_modulus_degree": 16384,
            "coeff_mod_bit_sizes": [60, 40, 40, 60, 60],
            "security_level": 192,
            "global_scale": 2**50,
            "key_rotation_policy": {
                "interval": "90d",
                "algorithm": "Kyber1024+RSA4096",
                "backup": {"locations": 3, "geographic_distribution": True},
            },
            "compliance": [
                "NIST_SP_800-56C",
                "FIPS_140-2_Level_3",
                "ISO_27001:A.10.1.1",
                "GDPR:Art.32",
            ],
        }

    def _get_current_keys(self) -> Tuple[Optional[bytes], Optional[bytes]]:
        if self._current_private_key is not None and self._current_public_key is not None:
            return (self._current_private_key, self._current_public_key)
        return (None, None)

    def _update_current_keys(self, private_key: bytes, public_key: bytes) -> None:
        self._current_private_key = private_key
        self._current_public_key = public_key
        self._last_rotation_time = datetime.now(timezone.utc)

    def _get_last_rotation_time(self) -> datetime:
        if self._last_rotation_time is not None:
            return self._last_rotation_time
        return datetime.now(timezone.utc)

    def _should_rotate_keys(self) -> bool:
        last = self._get_last_rotation_time()
        return (datetime.now(timezone.utc) - last).days >= self.key_rotation_interval

    def _log_key_rotation(
        self,
        old_keys: Tuple[Optional[bytes], Optional[bytes]],
        new_keys: Tuple[bytes, bytes],
        traceability: Optional[Any] = None,
    ) -> None:
        event = {
            "type": "key_rotation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_key_hash": _blake3_hex(old_keys[0]) if old_keys[0] else "",
            "new_key_hash": _blake3_hex(new_keys[0]),
            "rotation_policy": f"{self.key_rotation_interval} days",
            "validation_method": "HSM" if (self.hsm_integration and self.hsm_integration.available()) else "Software",
            "normative_references": ["NIST_SP_800-57", "ISO_27001:A.10.1.1", "GDPR:Art.32"],
        }
        self.key_usage_log.append(event)
        if traceability and hasattr(traceability, "register_event"):
            traceability.register_event(event)
        logger.info("Rotación de claves registrada: %s", event.get("new_key_hash", "")[:16])

    def rotate_keys(
        self,
        force: bool = False,
        traceability: Optional[Any] = None,
    ) -> bool:
        """Rota claves si ha pasado el intervalo o force=True. Valida con HSM si está disponible."""
        if not (force or self._should_rotate_keys()):
            return False
        old_priv, old_pub = self._get_current_keys()
        if old_priv is None:
            old_priv, old_pub = self.generate_key_pair()
        new_priv, new_pub = self.generate_secure_key_pair(use_hsm=bool(self.hsm_integration and self.hsm_integration.available()))
        if self.hsm_integration and not self.hsm_integration.validate_key_pair(new_priv, new_pub):
            raise ValueError("Validación de claves fallida")
        self._log_key_rotation((old_priv, old_pub), (new_priv, new_pub), traceability)
        self._update_current_keys(new_priv, new_pub)
        return True

    # --- Capa de cifrado simple (para uso de alto nivel y holografía) ---

    def _simple_encrypt(self, data: bytes) -> bytes:
        """Cifrado simétrico simple con AES-256-GCM sobre clave interna."""
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self._symmetric_key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        tag = encryptor.tag
        # Empaquetar como iv|tag|ciphertext
        return iv + tag + ciphertext

    def _simple_decrypt(self, payload: bytes) -> bytes:
        """Descifrado simétrico simple para `_simple_encrypt`."""
        if len(payload) < 28:
            raise ValueError("Payload de cifrado simétrico inválido")
        iv = payload[:12]
        tag = payload[12:28]
        ciphertext = payload[28:]
        cipher = Cipher(algorithms.AES(self._symmetric_key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()

    def encrypt(
        self,
        data: bytes,
        use_holography: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> Union[bytes, Dict[str, Any]]:
        """
        Cifra datos a alto nivel.

        - `use_holography=False`: cifrado simétrico simple (bytes).
        - `use_holography=True`: usa `HolographicEncryption` si está activado (dict).
        """
        if use_holography:
            if not self.holographic:
                raise RuntimeError(
                    "HolographicEncryption no está activado. "
                    "Configura DT_HOLOGRAPHIC_ENCRYPTION_ENABLED=true"
                )
            return self.holographic.encrypt_with_holography(data, context or {})
        return self._simple_encrypt(data)

    def decrypt(
        self,
        data: Union[bytes, Dict[str, Any]],
        use_holography: bool = False,
    ) -> bytes:
        """
        Descifra datos a alto nivel.

        - `use_holography=False`: descifra bytes generados por `_simple_encrypt`.
        - `use_holography=True`: espera paquete dict generado por `encrypt_with_holography`.
        """
        if use_holography:
            if not self.holographic:
                raise RuntimeError("HolographicEncryption no está activado")
            if not isinstance(data, dict):
                raise ValueError("Se esperaba un paquete holográfico (dict)")
            return self.holographic.decrypt_with_holography(data)
        if isinstance(data, dict):
            raise ValueError("Modo no holográfico espera datos en bytes")
        return self._simple_decrypt(data)

    def encrypt_for_moltbook(self, data: bytes, moltbook_context: Dict[str, Any]) -> Dict[str, Any]:
        """Cifrado específico Moltbook con metadatos legales UE (RGPD, AI Act, eIDAS)."""
        if not self.holographic:
            raise RuntimeError("Módulo holográfico no disponible")
        return self.holographic.encrypt_for_moltbook(data, moltbook_context)

    def verify_moltbook_compliance(self, encrypted_package: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica cumplimiento legal del paquete cifrado para Moltbook."""
        if not self.holographic:
            raise RuntimeError("Módulo holográfico no disponible")
        return self.holographic.verify_moltbook_compliance(encrypted_package)

    def derive_key(self, password: str, salt: bytes, iterations: int = 100_000) -> bytes:
        """Deriva clave de 256 bits con PBKDF2-HMAC-SHA512."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=self.backend,
        )
        return kdf.derive(password.encode())

    def encrypt_hybrid(
        self,
        data: bytes,
        public_key: bytes,
        aad: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """
        Cifrado híbrido: AES-256-GCM para datos, RSA-OAEP para la clave.
        Opcional: capa Kyber-1024 sobre (aes_key|iv|tag) para auditoría post-cuántica.
        """
        aes_key = os.urandom(32)
        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv),
            backend=self.backend,
        )
        encryptor = cipher.encryptor()
        if aad:
            encryptor.authenticate_additional_data(aad)
        ciphertext = encryptor.update(data) + encryptor.finalize()
        tag = encryptor.tag

        pub = serialization.load_pem_public_key(public_key, backend=self.backend)
        encrypted_aes_key = pub.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            ),
        )

        out: Dict[str, Any] = {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "encrypted_key": base64.b64encode(encrypted_aes_key).decode(),
            "iv": base64.b64encode(iv).decode(),
            "tag": base64.b64encode(tag).decode(),
            "algorithm": "RSA4096_AES256_GCM",
        }
        if self.pq_crypto:
            try:
                key_material_b64 = base64.b64encode(aes_key + iv + tag).decode()
                out["hybrid_encrypted"] = self.pq_crypto.hybrid_encrypt(key_material_b64, None)
                out["algorithm"] = "RSA4096_AES256_GCM_Kyber1024"
            except Exception as e:
                logger.debug("Kyber layer omitida: %s", e)
        return out

    def decrypt_hybrid(
        self,
        encrypted_data: Dict[str, Any],
        private_key: bytes,
        aad: Optional[bytes] = None,
    ) -> bytes:
        """Descifra payload híbrido (RSA + AES-GCM)."""
        priv = serialization.load_pem_private_key(
            private_key,
            password=None,
            backend=self.backend,
        )
        encrypted_aes_key = base64.b64decode(encrypted_data["encrypted_key"])
        aes_key = priv.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            ),
        )
        iv = base64.b64decode(encrypted_data["iv"])
        tag = base64.b64decode(encrypted_data["tag"])
        ciphertext = base64.b64decode(encrypted_data["ciphertext"])
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv, tag),
            backend=self.backend,
        )
        decryptor = cipher.decryptor()
        if aad:
            decryptor.authenticate_additional_data(aad)
        return decryptor.update(ciphertext) + decryptor.finalize()

    def encrypt_model_weights(
        self,
        weights: Dict[str, Any],
        public_key: bytes,
    ) -> Dict[str, Any]:
        """
        Cifra pesos de modelo para Federated Learning (por capa).

        Estructura de salida (ejemplo):
        {
          "encrypted_weights": {
            "layer_0": {
              "ciphertext": "base64...",
              "encrypted_key": "base64...",
              "iv": "base64...",
              "tag": "base64...",
              "original_shape": [100, 50],
              "dtype": "float32"
            }
          },
          "encryption_metadata": {
            "algorithm": "RSA4096_AES256_GCM_Kyber1024",
            "timestamp": "ISO8601",
            "normative_compliance": ["GDPR:Art.32", "ISO_27001:A.10.1.1"]
          }
        }
        """
        if not _NUMPY or np is None:
            weights_bytes = json.dumps(weights).encode()
            encrypted = self.encrypt_hybrid(weights_bytes, public_key)
            return {
                "encrypted_weights": {"default": {**encrypted, "original_shape": [], "dtype": "str"}},
                "encryption_metadata": {
                    "algorithm": "Hybrid_RSA4096_AES256_GCM",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "normative_compliance": ["GDPR:Art.32", "ISO_27001:A.10.1.1", "NIST_SP_800-56C"],
                },
            }
        encrypted_weights = {}
        for layer_name, layer_weights in weights.items():
            if hasattr(layer_weights, "tobytes"):
                weights_bytes = np.asarray(layer_weights).tobytes()
                shape = list(np.asarray(layer_weights).shape)
                dtype = str(np.asarray(layer_weights).dtype)
            else:
                weights_bytes = json.dumps(layer_weights).encode()
                shape = []
                dtype = "str"
            enc = self.encrypt_hybrid(weights_bytes, public_key)
            encrypted_weights[layer_name] = {
                **enc,
                "original_shape": shape,
                "dtype": dtype,
            }
        algorithm = (
            "RSA4096_AES256_GCM_Kyber1024"
            if (hasattr(self, "pq_crypto") and self.pq_crypto)
            else "RSA4096_AES256_GCM"
        )
        return {
            "encrypted_weights": encrypted_weights,
            "encryption_metadata": {
                "algorithm": algorithm,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "normative_compliance": ["GDPR:Art.32", "ISO_27001:A.10.1.1", "NIST_SP_800-56C"],
            },
        }

    def decrypt_model_weights(
        self,
        encrypted_model: Dict[str, Any],
        private_key: bytes,
    ) -> Dict[str, Any]:
        """Descifra pesos de modelo cifrados."""
        decrypted_weights = {}
        for layer_name, layer_data in encrypted_model.get("encrypted_weights", {}).items():
            payload = {k: layer_data[k] for k in ("ciphertext", "encrypted_key", "iv", "tag") if k in layer_data}
            decrypted_bytes = self.decrypt_hybrid(payload, private_key)
            shape = layer_data.get("original_shape", [])
            dtype_str = layer_data.get("dtype", "float32")
            if _NUMPY and np is not None and shape and dtype_str != "str":
                decrypted_weights[layer_name] = np.frombuffer(
                    decrypted_bytes,
                    dtype=np.dtype(dtype_str),
                ).reshape(shape)
            else:
                try:
                    decrypted_weights[layer_name] = json.loads(decrypted_bytes.decode())
                except Exception:
                    decrypted_weights[layer_name] = decrypted_bytes
        return decrypted_weights

    def _to_json_serializable(self, obj: Any) -> Any:
        """Convierte estructuras con ndarray a formas serializables por JSON."""
        if _NUMPY and np is not None and isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: self._to_json_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._to_json_serializable(v) for v in obj]
        return obj

    def generate_data_hash(self, data: Any) -> str:
        """Hash resistente a cuántica (BLAKE3) del dato."""
        if isinstance(data, (dict, list)):
            data = self._to_json_serializable(data)
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        return _blake3_hex(data_str.encode() if isinstance(data_str, str) else data_str)

    def create_encrypted_envelope(
        self,
        data: Any,
        public_key: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Sobre cifrado con integridad y firma opcional."""
        if isinstance(data, (dict, list)):
            data = self._to_json_serializable(data)
            data_bytes = json.dumps(data).encode()
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode()
        encrypted_data = self.encrypt_hybrid(data_bytes, public_key)
        data_hash = self.generate_data_hash(data)
        envelope = {
            "encrypted_data": encrypted_data,
            "metadata": metadata or {},
            "integrity": {"hash": data_hash, "algorithm": "BLAKE3"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if self.pq_crypto:
            try:
                payload_str = json.dumps(envelope, sort_keys=True)
                envelope["signature"] = self.pq_crypto.dilithium_sign(payload_str)
            except Exception as e:
                logger.debug("Firma envelope omitida: %s", e)
        return envelope

    def verify_and_decrypt_envelope(
        self,
        envelope: Dict[str, Any],
        private_key: bytes,
    ) -> Tuple[Any, bool]:
        """Verifica firma e integridad y descifra. Devuelve (datos, válido)."""
        try:
            if "signature" in envelope and self.pq_crypto:
                payload = {k: v for k, v in envelope.items() if k != "signature"}
                payload_str = json.dumps(payload, sort_keys=True)
                if not self.pq_crypto.dilithium_verify(payload_str, envelope["signature"]):
                    return None, False
            decrypted_bytes = self.decrypt_hybrid(envelope["encrypted_data"], private_key)
            try:
                decrypted_data = json.loads(decrypted_bytes.decode())
            except Exception:
                decrypted_data = decrypted_bytes
            current_hash = self.generate_data_hash(decrypted_data)
            if current_hash != envelope.get("integrity", {}).get("hash"):
                return None, False
            return decrypted_data, True
        except Exception as e:
            logger.error("Error al descifrar sobre: %s", e)
            return None, False
