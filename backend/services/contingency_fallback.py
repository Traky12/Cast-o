# -*- coding: utf-8 -*-
"""
Protocolos de contingencia global — CASTÚO-SYSTEM™ v10.0.
Fallback por región: USDA (América), SAHPRA (África), MHLW (Asia), etc.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict

try:
    import httpx
except ImportError:
    httpx = None


def log_to_gaiachain(batch_id: str, event: str, payload: Dict[str, Any]) -> str:
    """Registra en GaiaChain (stub: en producción usar API blockchain)."""
    # POST /blockchain/register_batch con event + payload
    return f"0x{hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:40]}..."


def send_alert(message: str, target: str | list[str]) -> None:
    """Envía alerta a equipo (Slack, PagerDuty, etc.)."""
    print(f"[ALERT {target}] {message}")


def usda_fallback(batch_id: str) -> Dict[str, Any]:
    """Protocolo de contingencia si cae USDA (América): usar datos FDA."""
    if not httpx:
        return {"batch_id": batch_id, "status": "stub", "data": {}}
    try:
        r = httpx.get(
            f"https://api.fda.gov/v1/batch/{batch_id}",
            timeout=10.0,
        )
        fda_data = r.json() if r.status_code == 200 else {}
    except Exception:
        fda_data = {}
    tx_hash = log_to_gaiachain(
        batch_id,
        "USDA_FALLBACK",
        {"data": fda_data, "timestamp": datetime.utcnow().isoformat()},
    )
    send_alert(
        f"USDA fallback activated for batch {batch_id}. Using FDA data. GaiaChain TX: {tx_hash}",
        "security-team",
    )
    return {"batch_id": batch_id, "status": "fallback", "data": fda_data, "gaiachain_tx": tx_hash}


def sahpra_fallback(batch_id: str) -> Dict[str, Any]:
    """Protocolo de contingencia si cae SAHPRA (Sudáfrica): usar DAFF."""
    if not httpx:
        return {"batch_id": batch_id, "status": "stub", "data": {}}
    try:
        r = httpx.get(
            f"https://api.daff.gov.za/v1/batch/{batch_id}",
            timeout=10.0,
        )
        daff_data = r.json() if r.status_code == 200 else {}
    except Exception:
        daff_data = {}
    doc_hash = hashlib.sha256(json.dumps(daff_data, sort_keys=True).encode()).hexdigest()
    tx_hash = log_to_gaiachain(
        batch_id,
        "SAHPRA_FALLBACK",
        {
            "data": daff_data,
            "timestamp": datetime.utcnow().isoformat(),
            "authority": "DAFF",
            "document_hash": doc_hash,
        },
    )
    send_alert(
        f"SAHPRA fallback activated for batch {batch_id}. Using DAFF data. GaiaChain TX: {tx_hash}",
        ["legal-team", "sahpra-contact"],
    )
    return {
        "status": "fallback",
        "data": daff_data,
        "gaiachain_tx": tx_hash,
        "next_audit": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    }


def mhlw_fallback(batch_id: str) -> Dict[str, Any]:
    """Protocolo de contingencia si cae MHLW (Japón): usar JAS + PMDA."""
    jas_data = {}
    pmda_status = {}
    if httpx:
        api_key = os.getenv("JAS_API_KEY")
        try:
            r = httpx.get(
                f"https://api.jas-maff.go.jp/v1/batch/{batch_id}",
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
                timeout=10.0,
            )
            jas_data = r.json() if r.status_code == 200 else {}
        except Exception:
            pass
        try:
            r = httpx.get(
                f"https://api.pmda.go.jp/v1/batch/{batch_id}/status",
                timeout=10.0,
            )
            pmda_status = r.json() if r.status_code == 200 else {}
        except Exception:
            pass
    if pmda_status.get("status") != "APPROVED" and pmda_status:
        raise ValueError("PMDA rejection during MHLW fallback")
    tx_hash = log_to_gaiachain(
        batch_id,
        "MHLW_FALLBACK",
        {"jas_data": jas_data, "pmda_status": pmda_status, "timestamp": datetime.utcnow().isoformat()},
    )
    return {
        "status": "fallback_approved",
        "data": jas_data,
        "gaiachain_tx": tx_hash,
        "next_audit": (datetime.utcnow() + timedelta(days=5)).isoformat(),
    }
