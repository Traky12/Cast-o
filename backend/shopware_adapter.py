from __future__ import annotations

import base64
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from backend.security.end_to_end_encryption import EndToEndEncryption


router = APIRouter(prefix="/storefront", tags=["Shopware Facade"])
_core = EndToEndEncryption()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def serialize_encrypted_result(result: Any) -> Any:
    """Convierte la salida criptográfica a JSON seguro para frontend/Shopware."""
    if isinstance(result, bytes):
        return _b64(result)
    if isinstance(result, dict):
        normalized: Dict[str, Any] = {}
        for key, value in result.items():
            if key in {"encrypted_data", "holographic_key"} and isinstance(value, bytes):
                normalized[f"{key}_b64"] = _b64(value)
                continue
            normalized[key] = serialize_encrypted_result(value)
        return normalized
    if isinstance(result, list):
        return [serialize_encrypted_result(item) for item in result]
    return result


def build_agrivoltaic_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Construye una respuesta demo para análisis agrivoltaico."""
    finca_id = payload.get("finca_id", "CTAEX_001")
    sensores = payload.get("sensores") or {}
    solar = float(sensores.get("solar", 2450))
    humedad = float(sensores.get("humedad", 42))
    temp = float(sensores.get("temperatura", 18.5))
    kwh_ha = round(solar * 0.00506, 1)
    eur_ha = round(12.4 * (temp / 18) + (humedad / 10), 0)
    return {
        "status": "success",
        "finca_id": finca_id,
        "message": "Análisis en vivo",
        "kwh_ha": kwh_ha,
        "kwh_ha_label": f"{kwh_ha}kWh/ha",
        "paneles_temp": temp,
        "eur_ha_extra": int(eur_ha),
        "eur_ha_label": f"+€{int(eur_ha)}/ha",
        "predicted_yield_pct": 35,
        "water_savings_pct": 20,
    }


def build_farmer_dashboard(finca_id: str) -> Dict[str, Any]:
    """Resumen listo para QR / portal farmer-first."""
    lan_ip = os.getenv("CASTUO_LAN_IP", "192.168.1.132")
    return {
        "status": "success",
        "finca_id": finca_id,
        "kwh_ha": 12.4,
        "water_savings": 23,
        "model_version": "fed_1.2",
        "peers_online": 8472,
        "qr_url": f"http://{lan_ip}:8000/docs",
    }


@router.get("/health")
async def shopware_health() -> Dict[str, Any]:
    holographic = "ACTIVE" if (_core.holographic and _core.holographic.is_enabled()) else "inactive"
    return {"status": "TRL9_LIVE", "platform": "CASTUO+SHOPWARE", "holographic": holographic}


@router.post("/holographic/encrypt")
async def shopware_encrypt(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    data = payload.get("data")
    if data is None:
        raise HTTPException(status_code=400, detail="Campo 'data' requerido")
    context = payload.get("context") or {}
    try:
        result = _core.encrypt(data.encode("utf-8"), use_holography=True, context=context)
        return {
            "status": "success",
            "result": serialize_encrypted_result(result),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/farmer/dashboard")
async def farmer_dashboard(finca_id: str) -> Dict[str, Any]:
    return build_farmer_dashboard(finca_id)


@router.post("/agrivoltaic/analyze")
async def shopware_analyze(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    return build_agrivoltaic_analysis(payload)

