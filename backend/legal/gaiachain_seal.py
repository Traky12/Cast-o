# -*- coding: utf-8 -*-
"""Sellos electrónicos cualificados según eIDAS 2 con registro en GaiaChain."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))
_EIDAS_PRIVATE_KEY_PATH = os.getenv("EIDAS_PRIVATE_KEY_PATH", "certs/eidas_private_key.pem")
_EIDAS_CERT_PATH = os.getenv("EIDAS_CERT_PATH", "certs/eidas_cert.pem")

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    _CRYPTO = True
except ImportError:
    _CRYPTO = False


class GaiaChainSeal:
    """Genera sellos electrónicos cualificados (eIDAS 2) y los registra en GaiaChain."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI
        self.private_key_path = _EIDAS_PRIVATE_KEY_PATH
        self.cert_path = _EIDAS_CERT_PATH

    def generate_qualified_seal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un sello electrónico cualificado según eIDAS 2.
        Si no hay clave/certificado eIDAS, devuelve sello con hash y firma simulada.
        """
        data_str = json.dumps(data, sort_keys=True).encode("utf-8")
        data_hash = hashlib.sha256(data_str).hexdigest()
        signature = self._sign_data(data_str)
        cert_preview = self._read_certificate()[:50] + "..." if self._read_certificate() else "no-cert"
        tx_data = {
            "type": "eidas_seal",
            "data": {
                "hash": data_hash,
                "signature": signature[:64] + "..." if len(signature) > 64 else signature,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "certificate_preview": cert_preview,
            },
        }
        tx_hash = self._register_in_gaiachain(tx_data)
        return {
            "seal": {
                "hash": data_hash,
                "signature": signature[:64] + "..." if len(signature) > 64 else signature,
                "certificate": cert_preview,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "gaiachain_tx": tx_hash,
            "eidas_compliant": bool(signature and signature != "no-eidas-key"),
        }

    def _sign_data(self, data: bytes) -> str:
        """Firma datos con clave privada eIDAS si existe; si no, devuelve marcador."""
        if not _CRYPTO or not os.path.isfile(self.private_key_path):
            return "no-eidas-key"
        try:
            with open(self.private_key_path, "rb") as key_file:
                private_key = load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend(),
                )
            signature = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
            return signature.hex()
        except Exception as e:
            logger.warning("Firma eIDAS no disponible: %s", e)
            return "no-eidas-key"

    def _read_certificate(self) -> str:
        if not os.path.isfile(self.cert_path):
            return ""
        try:
            with open(self.cert_path, "r", encoding="utf-8") as cert_file:
                return cert_file.read()
        except Exception:
            return ""

    def _register_in_gaiachain(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "eidas_seal", "--data", json.dumps(data)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain eidas_seal: %s", e)
            return f"Error: {e}"

    def verify_seal(self, seal_hash: str) -> Dict[str, Any]:
        """Verifica un sello en GaiaChain (requiere CLI con query)."""
        if not os.path.isfile(self.gaiachain_cli):
            return {"valid": False, "error": "gaiachain-no-cli"}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "eidas_seal", "--hash", seal_hash],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not r.stdout.strip():
                return {"valid": False, "error": r.stderr or "not found"}
            return {"valid": True, "data": json.loads(r.stdout)}
        except Exception as e:
            return {"valid": False, "error": str(e)}
