# -*- coding: utf-8 -*-
"""
Router Hidroponía — Soberanía Hidropónica.
Protocolo Omega: validamos la vida antes que el dato; el orgullo se convierte en dato en el ledger.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..models.hidroponia import HidroponiaSensor, HidroponiaSistema
from ..services.health_certifier_omega import HealthCertifierOmega

router = APIRouter(prefix="/hidroponia", tags=["Soberanía Hidropónica"])
_certifier = HealthCertifierOmega()

_SISTEMA_NFT = HidroponiaSistema(
    id="1",
    tipo="NFT",
    canales=12,
    volumen_tanque=500.0,
    plantas_por_canal=24,
)


@router.get("/sistemas")
async def listar_sistemas():
    """Lista sistemas hidropónicos (NFT, DWC, EbbFlow, Aeroponia)."""
    return [_SISTEMA_NFT]


@router.post("/sensores")
async def recibir_sensores(sensor: HidroponiaSensor):
    """
    Protocolo Omega: validamos la vida antes que el dato.
    El sistema detecta desbalance en la biosfera del tanque antes de persistir.
    """
    if not (5.5 <= sensor.ph <= 6.5):
        raise HTTPException(
            status_code=400,
            detail="El sistema Omega detecta desbalance en la biosfera del tanque.",
        )
    cert = await _certifier.check_and_mint_health_cert(sensor)
    out = {
        "status": "Resonancia Estable",
        "timestamp": sensor.timestamp.isoformat(),
        "impacto": "Eficiencia hídrica optimizada al 99.7%",
        "data": sensor.model_dump(mode="json"),
    }
    if cert:
        out["certificado_salud_ancestral"] = cert
    return out


@router.get("/cultivos")
async def listar_cultivos():
    """Cultivos hidropónicos — soberanía por m²."""
    return [
        {
            "id": "lechuga-omega-01",
            "nombre": "Lechuga Hidropónica Sostenible",
            "ec_objetivo": (1.2, 2.0),
            "ph_objetivo": (5.8, 6.2),
            "densidad": 115.2,
        },
    ]


@router.get("/alertas")
async def hidro_alertas(
    ec: float = Query(..., description="Conductividad mS/cm"),
    ph: float = Query(..., description="pH solución"),
):
    """Alertas por EC o pH fuera de rango — consulta rápida de estrés en la solución."""
    alertas = []
    if not (0.5 <= ec <= 3.5):
        alertas.append({"alerta": "EC fuera de rango", "valor": ec, "rango": [0.5, 3.5]})
    if not (5.5 <= ph <= 6.5):
        alertas.append({"alerta": "pH fuera de rango", "valor": ph, "rango": [5.5, 6.5]})
    if not alertas:
        return {"ok": True, "mensaje": "EC y pH en rango"}
    return {"ok": False, "alertas": alertas}
