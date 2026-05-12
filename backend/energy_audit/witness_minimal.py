"""
Witness GaiaChain minimal (hash, coop_id, ipfs_cid) alineado con scripts/ops/research.
Si faltan credenciales, no falla el pipeline de procesado: solo registra en log.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None


def _canonical_sha256_hex(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def witness_energy_event(evidence: Dict[str, Any], coop_id: str) -> Optional[Dict[str, Any]]:
    """
    Calcula hash del JSON canonico de evidence y POST al witness si GAIA_CHAIN_API_KEY existe.
    """
    api_key = os.environ.get("GAIA_CHAIN_API_KEY", "").strip()
    base = os.environ.get(
        "GAIA_CHAIN_API_URL",
        "https://gaiachain.castuo-system.eu/api/v1/witness",
    ).rstrip("/")
    url = base if base.endswith("witness") else f"{base}/api/v1/witness"

    h = _canonical_sha256_hex(evidence)
    body = {"hash": h, "coop_id": coop_id, "ipfs_cid": None}

    stamp = datetime.now(timezone.utc).isoformat()
    if not api_key or requests is None:
        logger.info(
            "witness_energy_event skip POST (sin API o requests): coop=%s hash=%s ts=%s",
            coop_id,
            h,
            stamp,
        )
        return {"skipped": True, "hash": h, "coop_id": coop_id, "timestamp": stamp}

    try:
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=30,
        )
        return {"status_code": r.status_code, "text": r.text[:2000], "hash": h}
    except OSError as e:
        logger.warning("witness_energy_event red: %s", e)
        return {"error": str(e), "hash": h}


witness_event = witness_energy_event
