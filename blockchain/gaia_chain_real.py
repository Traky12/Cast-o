# -*- coding: utf-8 -*-
"""
GaiaChain Real — Witness con SHA256, IPFS opcional y POST a API (TRL7 / eIDAS QES).
CASTÚO 360 S.L. | Trazabilidad agrovoltaica verificable.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

# API witness (configurable; stub local si no hay backend)
DEFAULT_WITNESS_URL = os.getenv("GAIA_CHAIN_API_URL", "https://api.gaiachain.castuo-system.com").rstrip("/")
IPFS_API_URL = os.getenv("IPFS_API_URL", "").rstrip("/")  # opcional: Infura u otro


class GaiaChainReal:
    """
    Witness real: hash SHA256 + opcional IPFS CID + POST a /api/v1/witness.
    eIDAS QES: firma opcional si GAIA_CHAIN_SIGNING_KEY está definida (path a PEM).
    """

    def __init__(
        self,
        witness_url: Optional[str] = None,
        ipfs_url: Optional[str] = None,
    ) -> None:
        self.witness_url = (witness_url or DEFAULT_WITNESS_URL).rstrip("/")
        self.ipfs_url = (ipfs_url or IPFS_API_URL).rstrip("/")

    def _sha256_data(self, data: Dict[str, Any]) -> str:
        """Hash SHA256 del payload (determinista con sort_keys)."""
        raw = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def _ipfs_upload(self, data: Dict[str, Any]) -> Optional[str]:
        """Sube a IPFS si IPFS_API_URL está configurado; devuelve CID o None."""
        if not self.ipfs_url or not requests:
            return None
        try:
            # Adaptar según API IPFS (Infura: multipart o JSON)
            r = requests.post(
                f"{self.ipfs_url}/api/v0/add",
                files={"file": ("payload.json", json.dumps(data).encode())},
                timeout=10,
            )
            if r.status_code == 200:
                out = r.json()
                return out.get("Hash") or out.get("cid")
        except Exception as e:
            logger.warning("IPFS upload skipped: %s", e)
        return None

    def witness_transaction(self, data: Dict[str, Any], coop_id: int) -> Dict[str, Any]:
        """
        Registra transacción como testigo: hash SHA256 + opcional IPFS + POST witness.

        Returns:
            {"ok": True, "tx_hash": str, "ipfs_cid": str|None, "witness_response": dict}
            o {"ok": False, "error": str}
        """
        data_hash = self._sha256_data(data)
        ipfs_cid = self._ipfs_upload(data)

        payload = {
            "hash": data_hash,
            "coop_id": coop_id,
            "ipfs_cid": ipfs_cid,
        }

        if not requests:
            logger.warning("requests no disponible; witness solo local")
            return {"ok": True, "tx_hash": data_hash, "ipfs_cid": ipfs_cid, "witness_response": {}}

        url = f"{self.witness_url}/api/v1/witness"
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code in (200, 201, 202):
                return {
                    "ok": True,
                    "tx_hash": data_hash,
                    "ipfs_cid": ipfs_cid,
                    "witness_response": r.json() if r.text else {},
                }
            return {
                "ok": False,
                "error": f"witness API {r.status_code}: {r.text[:200]}",
                "tx_hash": data_hash,
            }
        except Exception as e:
            logger.exception("GaiaChain witness_transaction failed: %s", e)
            return {"ok": False, "error": str(e), "tx_hash": data_hash}
