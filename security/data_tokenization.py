# -*- coding: utf-8 -*-
"""
Tokenización de datos sensibles (GDPR): reemplazo de PII por tokens con auditoría en GaiaChain.
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Union

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

logger = logging.getLogger(__name__)


class DataTokenization:
    """
    Genera tokens para datos sensibles (NIF, email, teléfono, etc.);
    detokenización con registro de solicitante y propósito (auditoría).
    En producción usar Vault o BD cifrada para el mapeo token -> original.
    """

    def __init__(self, salt: str = "CASTUA_SALT_2026") -> None:
        self.token_map: Dict[str, Dict[str, Any]] = {}
        self.salt = salt
        self.blockchain = GaiaChainClient() if GaiaChainClient else None

    def generate_token(self, data: Any, data_type: str = "generic") -> str:
        """Genera token para un dato sensible. Registra en GaiaChain."""
        if isinstance(data, str):
            token = hashlib.sha256((data + self.salt).encode()).hexdigest()
        else:
            token = str(uuid.uuid4())
        self.token_map[token] = {
            "original_data": data,
            "data_type": data_type,
            "created_at": datetime.now().isoformat(),
            "access_log": [],
        }
        if self.blockchain:
            self.blockchain.log_tokenization({
                "token": token[:32],
                "data_type": data_type,
                "timestamp": datetime.now().isoformat(),
                "action": "token_created",
            })
        return token

    def detokenize(self, token: str, requester: str, purpose: str) -> Any:
        """Recupera dato original y registra acceso (auditoría)."""
        if token not in self.token_map:
            raise ValueError("Token no válido o expirado")
        self.token_map[token]["access_log"].append({
            "requester": requester,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat(),
        })
        if self.blockchain:
            self.blockchain.log_tokenization({
                "token": token[:32],
                "action": "token_used",
                "requester": requester,
                "purpose": purpose,
                "timestamp": datetime.now().isoformat(),
            })
        return self.token_map[token]["original_data"]

    def tokenize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Tokeniza campos sensibles (nif, dni, cif, email, phone, address)."""
        out = {}
        sensitive_keys = {"nif", "dni", "cif", "email", "phone", "address", "telefono", "direccion", "correo"}
        for key, value in document.items():
            if key.lower() in sensitive_keys and value is not None:
                out[key] = self.generate_token(str(value), key.lower())
            elif isinstance(value, dict):
                out[key] = self.tokenize_document(value)
            elif isinstance(value, list):
                out[key] = [
                    self.tokenize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                out[key] = value
        return out

    def detokenize_document(
        self,
        tokenized_doc: Dict[str, Any],
        requester: str,
        purpose: str,
    ) -> Dict[str, Any]:
        """Recupera documento reemplazando tokens por valores originales."""
        out = {}
        for key, value in tokenized_doc.items():
            if isinstance(value, str) and (len(value) == 64 or value in self.token_map):
                try:
                    out[key] = self.detokenize(value, requester, purpose)
                except ValueError:
                    out[key] = value
            elif isinstance(value, dict):
                out[key] = self.detokenize_document(value, requester, purpose)
            elif isinstance(value, list):
                out[key] = [
                    self.detokenize_document(item, requester, purpose) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                out[key] = value
        return out
