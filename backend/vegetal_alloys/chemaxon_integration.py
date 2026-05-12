from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any

import requests

try:
    from backend.energy_audit.witness_minimal import witness_event
except ImportError:
    witness_event = None  # type: ignore[misc, assignment]


def _witness(payload: dict[str, Any], coop_id: str) -> str | None:
    if witness_event is None:
        return None
    try:
        return witness_event(payload, coop_id)
    except Exception:
        return None


class ChemAxonClient:
    """
    Cliente ChemAxon: sin clave o sin red -> mock determinista (el territorio no se bloquea por un vendor).
    CHEMAXON_BASE_URL y CHEMAXON_API_KEY segun contrato/licencia real.
    """

    def __init__(self) -> None:
        self.base_url = (os.getenv("CHEMAXON_BASE_URL") or "").rstrip("/")
        self.api_key = os.getenv("CHEMAXON_API_KEY", "").strip()
        self.timeout = float(os.getenv("CHEMAXON_TIMEOUT_SEC", "15"))

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _mock_properties(self, smiles: str) -> dict[str, Any]:
        h = hashlib.sha256(smiles.encode("utf-8")).hexdigest()[:16]
        return {
            "mode": "mock",
            "smiles": smiles,
            "logP": round((int(h[:8], 16) % 1000) / 200.0, 3),
            "molecular_weight": round(50 + (int(h[8:], 16) % 500), 3),
            "solubility_g_l": round((int(h[:4], 16) % 200) / 100.0, 3),
            "fingerprint": h,
        }

    def calculate_properties(self, smiles: str) -> dict[str, Any]:
        if not self.base_url or not self.api_key:
            data = self._mock_properties(smiles)
            _witness(
                {
                    "action": "chemaxon_properties",
                    "smiles": smiles,
                    "properties": data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "coop_id": "CASTUO-ENERGY-01",
                },
                "CASTUO-CHEMAXON-01",
            )
            return data

        endpoint = f"{self.base_url}/properties"
        payload = {"smiles": smiles, "properties": ["logP", "solubility", "molecular_weight"]}
        try:
            r = requests.post(endpoint, json=payload, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "failed"}

        _witness(
            {
                "action": "chemaxon_properties",
                "smiles": smiles,
                "properties": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "CASTUO-CHEMAXON-01",
        )
        return data

    def generate_3d_structure(self, smiles: str) -> str | None:
        if not self.base_url or not self.api_key:
            cid = "Qm" + hashlib.sha256(smiles.encode()).hexdigest()[:44]
            _witness(
                {
                    "action": "chemaxon_3d_structure",
                    "smiles": smiles,
                    "ipfs_cid_placeholder": cid,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "CASTUO-CHEMAXON-01",
            )
            return cid

        endpoint = f"{self.base_url}/convert"
        payload = {"input": smiles, "input_format": "smiles", "output_format": "mol"}
        try:
            r = requests.post(endpoint, json=payload, headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            _ = r.content
        except requests.RequestException:
            return None

        cid = "Qm" + hashlib.sha256(smiles.encode()).hexdigest()[:44]
        _witness(
            {
                "action": "chemaxon_3d_structure",
                "smiles": smiles,
                "ipfs_cid_placeholder": cid,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "CASTUO-CHEMAXON-01",
        )
        return cid
