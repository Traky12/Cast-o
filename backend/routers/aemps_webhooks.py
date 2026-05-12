# -*- coding: utf-8 -*-
"""
AEMPS Webhook receiver (verificado contra estructura real del repo).

Endpoint:
  POST /api/aemps/webhook

Verifica firma (sha256(payload_text + secret)) y:
  - registra evidencia local en SQLite (LocalResilienceDB.system_events)
  - registra un witness GaiaChain con la evidencia (si GaiaChain esta disponible)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/api/aemps", tags=["aemps"])


@router.post("/webhook")
async def handle_aemps_webhook(
    request: Request,
    X_AEMPS_Signature: Optional[str] = Header(None),
    X_AEMPS_Event: Optional[str] = Header(None),
) -> Dict[str, Any]:
    import os

    secret = os.environ.get("AEMPS_WEBHOOK_SECRET") or ""
    if not secret:
        raise HTTPException(status_code=500, detail="AEMPS_WEBHOOK_SECRET not configured")

    body_bytes = await request.body()
    if not body_bytes:
        raise HTTPException(status_code=400, detail="Empty request body")

    # Firma esperada (conforme tu plan): sha256(payload.decode() + secret)
    payload_text = body_bytes.decode("utf-8", errors="replace")
    expected_signature = hashlib.sha256((payload_text + secret).encode("utf-8")).hexdigest()
    if X_AEMPS_Signature is None:
        raise HTTPException(status_code=400, detail="Missing X-AEMPS-Signature header")
    if X_AEMPS_Signature != expected_signature:
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = X_AEMPS_Event or data.get("event_type") or data.get("type") or ""
    if not str(event_type).strip():
        raise HTTPException(status_code=400, detail="Missing event_type")

    # Severidad: adaptada a los tipos mas comunes (no rompe el flujo si cambian).
    et = str(event_type).lower()
    severity = "warning" if et in ("compliance_alert", "compliance") else "info"

    # 1) Registro local
    try:
        from backend.database.local_db import local_db

        event_id = local_db.log_system_event(
            event_type=f"aemps_webhook_{event_type}",
            details=json.dumps(data, ensure_ascii=False),
            severity=severity,
        )
    except Exception:
        event_id = -1

    # 1b) (Opcional) verificacion interna si el evento lo requiere.
    certificate_status: Optional[Dict[str, Any]] = None
    et_norm = str(event_type).lower()
    if et_norm in ("certificate_verification", "certificate_verification_result", "certificate"):
        tx_id = data.get("tx_id") or data.get("certificate_tx") or data.get("gaiachain_tx") or ""
        if str(tx_id).strip():
            try:
                from backend.main_certifier import MainCertifier

                certificate_status = MainCertifier().get_certificate_status(str(tx_id))
            except Exception:
                certificate_status = None

    # 2) Witness GaiaChain (hash SHA256 del payload canonical en el service)
    witness_tx_hash: Optional[str] = None
    try:
        from backend.services.gaia_chain_witness import GaiaChainReal

        gaia = GaiaChainReal()
        witness_data = {
            "event_type": str(event_type),
            "payload": data,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        witness_res = gaia.witness_transaction(witness_data, coop_id=1)
        witness_tx_hash = witness_res.get("tx_hash")
    except Exception:
        witness_tx_hash = None

    return {
        "status": "success",
        "event_id": event_id,
        "event_type": str(event_type),
        "certificate_status": certificate_status,
        "witness_tx_hash": witness_tx_hash,
    }

