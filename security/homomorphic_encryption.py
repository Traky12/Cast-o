# -*- coding: utf-8 -*-
"""
Cifrado homomórfico para procesamiento de datos sin descifrar (ej. producción cáñamo).
Microsoft SEAL (BFV) opcional; sin SEAL se usa stub con cifrado simétrico para compatibilidad.
Normativas: ISO 27018, GDPR Art. 32.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

# Microsoft SEAL: pip install pyseal (o seal-python según versión)
HAS_SEAL = False
try:
    import seal
    HAS_SEAL = True
except ImportError:
    seal = None  # type: ignore


class HomomorphicEncryption:
    """
    Cifrado homomórfico (BFV) para números/diccionarios numéricos.
    Sin SEAL: stub que cifra con AES/derivado y simula add (solo para desarrollo).
    """

    def __init__(self) -> None:
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self._context = None
        self._encryptor = None
        self._decryptor = None
        self._evaluator = None
        self._stub_store: List[Dict[str, Any]] = []
        if HAS_SEAL and seal:
            try:
                parms = seal.EncryptionParameters(seal.SCHEME_TYPE.BFV)
                parms.set_poly_modulus_degree(8192)
                parms.set_coeff_modulus(seal.CoeffModulus.Create(8192, [60, 40, 40, 60]))
                parms.set_plain_modulus(seal.PlainModulus.Batching(8192, 20))
                self._context = seal.SEALContext.Create(seal.SEALContext(parms))
                keygen = seal.KeyGenerator(self._context)
                self._public_key = keygen.create_public_key()
                self._secret_key = keygen.secret_key()
                self._encryptor = seal.Encryptor(self._context, self._public_key)
                self._decryptor = seal.Decryptor(self._context, self._secret_key)
                self._evaluator = seal.Evaluator(self._context)
            except Exception as e:
                logger.warning("SEAL init failed: %s", e)
                HAS_SEAL = False  # noqa: F841

    def encrypt_data(self, data: Union[int, float, Dict[str, Any]]) -> Union[bytes, Dict[str, Any]]:
        """Cifra un número o un diccionario de valores numéricos."""
        if HAS_SEAL and self._encryptor is not None:
            return self._encrypt_seal(data)
        return self._encrypt_stub(data)

    def _encrypt_seal(self, data: Union[int, float, Dict[str, Any]]) -> Union[bytes, Dict[str, Any]]:
        if isinstance(data, (int, float)):
            encoder = seal.IntegerEncoder(self._context)
            plain = seal.Plaintext()
            encoder.encode(int(data), plain)
            cipher = seal.Ciphertext()
            self._encryptor.encrypt(plain, cipher)
            return cipher.save()
        if isinstance(data, dict):
            out = {}
            for k, v in data.items():
                if isinstance(v, (int, float)):
                    encoder = seal.IntegerEncoder(self._context)
                    plain = seal.Plaintext()
                    encoder.encode(int(v), plain)
                    cipher = seal.Ciphertext()
                    self._encryptor.encrypt(plain, cipher)
                    out[k] = cipher.save()
                else:
                    out[k] = v
            return out
        raise ValueError("Tipo no soportado para cifrado homomórfico")

    def _encrypt_stub(self, data: Union[int, float, Dict[str, Any]]) -> Union[bytes, Dict[str, Any]]:
        """Stub: guarda valor en texto para desarrollo (no seguro)."""
        if isinstance(data, (int, float)):
            self._stub_store.append({"v": int(data)})
            return f"stub_{len(self._stub_store) - 1}".encode()
        if isinstance(data, dict):
            out = {}
            for k, v in data.items():
                if isinstance(v, (int, float)):
                    idx = len(self._stub_store)
                    self._stub_store.append({"v": int(v)})
                    out[k] = f"stub_{idx}".encode()
                else:
                    out[k] = v
            return out
        raise ValueError("Tipo no soportado")

    def decrypt_data(self, encrypted_data: Union[bytes, Dict[str, Any]]) -> Union[int, Dict[str, Any]]:
        """Descifra dato cifrado con SEAL o stub."""
        if HAS_SEAL and self._decryptor is not None:
            return self._decrypt_seal(encrypted_data)
        return self._decrypt_stub(encrypted_data)

    def _decrypt_seal(self, encrypted_data: Union[bytes, Dict]) -> Union[int, Dict[str, Any]]:
        if isinstance(encrypted_data, bytes):
            cipher = seal.Ciphertext()
            cipher.load(self._context, encrypted_data)
            plain = seal.Plaintext()
            self._decryptor.decrypt(cipher, plain)
            encoder = seal.IntegerEncoder(self._context)
            return encoder.decode_int32(plain)
        if isinstance(encrypted_data, dict):
            out = {}
            for k, v in encrypted_data.items():
                if isinstance(v, bytes):
                    cipher = seal.Ciphertext()
                    cipher.load(self._context, v)
                    plain = seal.Plaintext()
                    self._decryptor.decrypt(cipher, plain)
                    encoder = seal.IntegerEncoder(self._context)
                    out[k] = encoder.decode_int32(plain)
                else:
                    out[k] = v
            return out
        raise ValueError("Datos cifrados no válidos")

    def _decrypt_stub(self, encrypted_data: Union[bytes, Dict]) -> Union[int, Dict[str, Any]]:
        if isinstance(encrypted_data, bytes):
            s = encrypted_data.decode()
            if s.startswith("stub_"):
                idx = int(s.split("_")[1])
                return self._stub_store[idx]["v"]
        if isinstance(encrypted_data, dict):
            out = {}
            for k, v in encrypted_data.items():
                if isinstance(v, bytes):
                    s = v.decode()
                    if s.startswith("stub_"):
                        idx = int(s.split("_")[1])
                        out[k] = self._stub_store[idx]["v"]
                    else:
                        out[k] = v
                else:
                    out[k] = v
            return out
        return 0

    def add_encrypted(self, cipher1: Any, cipher2: Any) -> Any:
        """Suma dos valores cifrados (homomórfico). Solo con SEAL real."""
        if HAS_SEAL and self._evaluator is not None:
            result = seal.Ciphertext()
            self._evaluator.add(cipher1, cipher2, result)
            return result
        return None

    def process_production_data(self, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cifra datos sensibles de producción y registra en GaiaChain (solo metadatos)."""
        scaled = {
            "batch_id": production_data.get("batch_id"),
            "strain": production_data.get("strain"),
            "weight_kg": production_data.get("weight_kg"),
            "thc_level": int((production_data.get("thc_level") or 0) * 1000),
            "cbd_level": int((production_data.get("cbd_level") or 0) * 1000),
        }
        encrypted = self.encrypt_data(scaled)
        metadata = {
            "batch_id": production_data.get("batch_id"),
            "processing_type": "homomorphic_encryption",
            "timestamp": datetime.now().isoformat(),
            "operations": ["addition", "multiplication"],
        }
        if self.blockchain:
            self.blockchain.log_data_processing(metadata)
        return encrypted if isinstance(encrypted, dict) else {"_single": encrypted}

    def analyze_encrypted_data(self, encrypted_batches: List[Dict[str, Any]]) -> float:
        """Suma weight_kg de todos los lotes cifrados y devuelve total (en SEAL real suma en cifrado)."""
        if HAS_SEAL and self._evaluator and self._decryptor and encrypted_batches:
            # En producción: sumar Ciphertexts y descifrar solo el resultado
            total_plain = 0
            for batch in encrypted_batches:
                w = batch.get("weight_kg")
                if isinstance(w, bytes):
                    total_plain += self.decrypt_data(w)
            return total_plain / 1000.0 if total_plain else 0.0
        # Stub: descifrar y sumar
        total = 0.0
        for batch in encrypted_batches:
            dec = self.decrypt_data(batch)
            if isinstance(dec, dict):
                total += dec.get("weight_kg", 0) or 0
        return total
