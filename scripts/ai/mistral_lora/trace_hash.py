#!/usr/bin/env python3
"""
Huella SHA-256 de eventos de inferencia (prompt + respuesta + metadatos) para auditoría.
Opcional: POST al witness GaiaChain si existen GAIA_CHAIN_API_KEY y CASTUO_GAIA_WITNESS_URL (o GAIA_CHAIN_API_URL).
Reutiliza el criterio canónico de backend/energy_audit/witness_minimal.py.
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


def canonical_hash(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def log_inference_event(
    *,
    engine: str,
    question: str,
    answer: str,
    model_ref: str,
    coop_id: str = "castuo-ai-lab",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    stamp = datetime.now(timezone.utc).isoformat()
    body: Dict[str, Any] = {
        "kind": "inference_faq",
        "engine": engine,
        "model_ref": model_ref,
        "question_len": len(question),
        "answer_len": len(answer),
        "question_sha256": hashlib.sha256(question.encode("utf-8")).hexdigest(),
        "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "timestamp_utc": stamp,
    }
    if extra:
        body["extra"] = extra
    h = canonical_hash(body)
    out = {"hash": h, "payload": body, "coop_id": coop_id}

    api_key = os.environ.get("GAIA_CHAIN_API_KEY", "").strip()
    base = os.environ.get("CASTUO_GAIA_WITNESS_URL", "").strip() or os.environ.get(
        "GAIA_CHAIN_API_URL",
        "https://gaiachain.castuo-system.eu/api/v1/witness",
    ).rstrip("/")
    url = base if base.endswith("witness") else f"{base.rstrip('/')}/witness"

    if not api_key or requests is None:
        logger.info("trace inference hash=%s (sin POST GaiaChain)", h)
        return {**out, "witness": {"skipped": True}}

    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"hash": h, "coop_id": coop_id, "ipfs_cid": None},
            timeout=30,
        )
        return {**out, "witness": {"http_status": r.status_code, "ok": r.ok}}
    except requests.RequestException as e:
        logger.warning("witness POST falló: %s", e)
        return {**out, "witness": {"error": str(e)}}
