"""
CASTÚO-SYSTEM™ — API de autenticación por comportamiento (FastAPI router).
Recibe eventos del frontend, delega en behavioral_auth_ai o en regla simple, devuelve requiresMFA.
"""
from __future__ import annotations

import os
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/behavioral_auth", tags=["behavioral_auth"])


class BehavioralLogRequest(BaseModel):
    userId: str = "authorized_admin"
    events: list[dict[str, Any]]
    timestamp: int = 0


class BehavioralVerifyRequest(BaseModel):
    otp: str


def _predict_anomaly_simple(events: list[dict]) -> tuple[bool, float]:
    """Regla simple: velocidad media por encima de umbral."""
    if len(events) < 5:
        return False, 0.0
    speeds = []
    for e in events:
        s = e.get("keyboardSpeed") or e.get("mouseSpeed") or 0
        speeds.append(float(s) if s else 0)
    avg = sum(speeds) / len(speeds)
    threshold = float(os.getenv("CASTUO_BEHAVIORAL_THRESHOLD", "3.0"))
    score = min(1.0, avg / max(threshold, 0.1))
    return score > 0.9, score


@router.post("/log")
async def log_event(body: BehavioralLogRequest):
    """Recibe eventos de comportamiento; devuelve requiresMFA si se detecta anomalía."""
    try:
        is_anomaly, score = _predict_anomaly_simple(body.events)
        # Opcional: llamar a scripts/security/behavioral_auth_ai.py para registro en GaiaChain
        return {
            "success": True,
            "requiresMFA": is_anomaly,
            "anomalyScore": round(score, 2),
        }
    except Exception as e:
        logger.exception("behavioral_auth log: %s", e)
        raise HTTPException(status_code=500, detail="Error procesando eventos")


@router.post("/verify")
async def verify_mfa(body: BehavioralVerifyRequest):
    """Verifica OTP YubiKey tras solicitud MFA por comportamiento."""
    otp = (body.otp or "").strip()
    if len(otp) < 32:
        return {"success": False, "error": "OTP inválido"}
    # En producción: verificar con YubiCloud (YUBICO_CLIENT_ID, YUBICO_API_KEY)
    return {"success": True}


@router.get("/profile/{user_id}")
async def get_profile(user_id: str):
    """Devuelve perfil de comportamiento del usuario (umbral, última anomalía)."""
    return {
        "success": True,
        "profile": {
            "userId": user_id,
            "anomalyThreshold": float(os.getenv("CASTUO_BEHAVIORAL_THRESHOLD", "3.0")),
        },
    }
