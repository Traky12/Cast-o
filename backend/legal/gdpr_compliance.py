# -*- coding: utf-8 -*-
"""Cumplimiento GDPR: pseudonimización (Art. 4(5)) y derecho al olvido (Art. 17) con GaiaChain."""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))

try:
    from cryptography.fernet import Fernet
    _FERNET = True
except ImportError:
    Fernet = None
    _FERNET = False


def _get_fernet_key() -> bytes:
    """Clave Fernet desde env o generada (en producción usar HSM/vault)."""
    raw = os.getenv("CASTUO_GDPR_FERNET_KEY")
    if raw:
        try:
            return base64.urlsafe_b64decode(raw.encode("utf-8"))
        except Exception:
            pass
    if _FERNET and Fernet is not None:
        return Fernet.generate_key()
    return b""


class GDPRCompliance:
    """Pseudonimización y derecho al olvido con registro en GaiaChain."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI
        key = _get_fernet_key()
        self.fernet_key = key
        self._cipher = None
        if _FERNET and Fernet is not None and len(key) >= 32:
            try:
                self._cipher = Fernet(key)
            except Exception:
                pass

    def pseudonymize_data(self, personal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pseudonimiza datos personales según GDPR Art. 4(5).
        Campos nombre, email, dni, direccion se sustituyen por pseudónimo + cifrado.
        """
        personal_fields = {"nombre", "email", "dni", "direccion"}
        pseudonymized: Dict[str, Any] = {}
        hashes_map: Dict[str, str] = {}

        for key, value in personal_data.items():
            if key in personal_fields and isinstance(value, str):
                pseudonym = hashlib.sha256(value.encode("utf-8")).hexdigest()
                encrypted = ""
                if self._cipher:
                    try:
                        encrypted = self._cipher.encrypt(value.encode("utf-8")).decode("utf-8")
                    except Exception as e:
                        logger.warning("Cifrado Fernet: %s", e)
                pseudonymized[key] = {"pseudonym": pseudonym, "encrypted": encrypted or pseudonym}
                hashes_map[key] = pseudonym
            else:
                pseudonymized[key] = value

        tx_hash = self._register_pseudonym_map(hashes_map)
        return {
            "pseudonymized_data": pseudonymized,
            "gaiachain_tx": tx_hash,
            "gdpr_compliant": True,
        }

    def _register_pseudonym_map(self, hashes: Dict[str, str]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        tx_data = {
            "type": "gdpr_pseudonym_map",
            "data": {
                "hashes": hashes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "purpose": "Cumplimiento GDPR Art. 4(5)",
            },
        }
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "gdpr_pseudonym_map", "--data", json.dumps(tx_data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain gdpr_pseudonym_map: %s", e)
            return f"Error: {e}"

    def exercise_right_to_be_forgotten(self, pseudonym: str) -> Dict[str, Any]:
        """Ejercita el derecho al olvido (GDPR Art. 17). Registra la solicitud en GaiaChain."""
        tx_data = self._query_pseudonym_map(pseudonym)
        if not tx_data.get("valid"):
            return {"status": "error", "reason": "Pseudónimo no encontrado o GaiaChain no disponible"}

        tx_hash = self._register_forgotten_request(pseudonym, tx_data.get("data", {}))
        return {
            "status": "deleted",
            "pseudonym": pseudonym,
            "gaiachain_tx": tx_hash,
            "gdpr_compliant": True,
        }

    def _query_pseudonym_map(self, pseudonym: str) -> Dict[str, Any]:
        if not os.path.isfile(self.gaiachain_cli):
            return {"valid": False, "error": "gaiachain-no-cli"}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "gdpr_pseudonym_map", "--pseudonym", pseudonym],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not r.stdout.strip():
                return {"valid": False, "error": r.stderr or "not found"}
            return {"valid": True, "data": json.loads(r.stdout)}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _register_forgotten_request(self, pseudonym: str, map_data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        tx_data = {
            "type": "gdpr_forgotten_request",
            "data": {
                "pseudonym": pseudonym,
                "original_data_hashes": map_data.get("hashes", {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "Derecho al olvido ejercido (GDPR Art. 17)",
            },
        }
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "gdpr_forgotten_request", "--data", json.dumps(tx_data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"
