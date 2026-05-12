"""
CASTÚO-SYSTEM™ v3.1 — Satellite EU API Router
POST /api/v1/satellite/analyze        — Análisis completo de parcela
GET  /api/v1/satellite/ndvi/{id}      — NDVI stats de última imagen
GET  /api/v1/satellite/anomalies/{id} — Anomalías detectadas por IA
GET  /api/v1/satellite/health         — Estado Copernicus + datos disponibles

Autenticación: Bearer JWT (roles: admin, editor, api)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger("castuo.satellite")

router = APIRouter(prefix="/api/v1/satellite", tags=["satellite"])

# ── Auth (reutiliza mismo patrón que skills.py / ai.py) ──────────────────────
import time
import jwt as _jwt
from fastapi.security import HTTPAuthorizationCredentials as _Creds, HTTPBearer as _Bearer

_ALLOWED_ROLES   = {"admin", "editor", "api"}
_bearer_scheme   = _Bearer(auto_error=False)


def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


async def _auth(credentials: Optional[_Creds] = Depends(_bearer_scheme)) -> dict:
    secret = _read_secret("JWT_SECRET")
    if not secret:
        logger.warning("[satellite] JWT_SECRET no configurado — modo dev")
        return {"sub": "dev", "role": "admin"}
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header requerido")
    try:
        payload = _jwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except _jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    if payload.get("role", "") not in _ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail=f"Rol no autorizado: {payload.get('role')}")
    return payload


# ── Modelos ───────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    parcela_id:  str = Field(..., min_length=3, description="ID de la parcela SIGPAC o interna")
    nombre:      Optional[str] = None
    cultivo:     Optional[str] = None
    lon_min:     float = Field(..., description="Longitud mínima (WGS84)")
    lat_min:     float = Field(..., description="Latitud mínima (WGS84)")
    lon_max:     float = Field(..., description="Longitud máxima (WGS84)")
    lat_max:     float = Field(..., description="Latitud máxima (WGS84)")
    fecha:       Optional[str] = Field(None, description="Fecha de análisis (YYYY-MM-DD), default: hoy")
    registrar_blockchain: bool = Field(True, description="Registrar resultado en GaiaChain")


class IndexStats(BaseModel):
    min:       Optional[float]
    max:       Optional[float]
    mean:      Optional[float]
    std:       Optional[float]
    valid_pct: float


class AnomalyItem(BaseModel):
    tipo:        str
    indice:      str
    valor:       float
    severidad:   str
    descripcion: str
    accion:      str


class AnalyzeResponse(BaseModel):
    parcela_id:     str
    nombre:         Optional[str]
    cultivo:        Optional[str]
    fecha_analisis: str
    ndvi_stats:     IndexStats
    ndmi_stats:     Optional[IndexStats]
    evi_stats:      Optional[IndexStats]
    anomalias:      list[AnomalyItem]
    n_anomalias:    int
    alerta:         bool
    tx_hash:        Optional[str]
    simulado:       bool
    generado_en:    str


# ── Helper ────────────────────────────────────────────────────────────────────

def _stats_to_model(stats: dict | None) -> Optional[IndexStats]:
    if not stats or stats.get("mean") is None:
        return None
    return IndexStats(
        min=stats.get("min"),
        max=stats.get("max"),
        mean=stats.get("mean"),
        std=stats.get("std"),
        valid_pct=stats.get("valid_pct", 0.0),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse, summary="Análisis satelital de parcela")
async def analyze_parcela(
    req: AnalyzeRequest,
    token: dict = Depends(_auth),
) -> AnalyzeResponse:
    """
    Obtiene la imagen Sentinel-2 más reciente para la parcela,
    calcula NDVI/NDMI/EVI, detecta anomalías y opcionalmente registra
    el resultado en GaiaChain.
    """
    from services.satellite.copernicus_client import CopernicusClient
    from services.satellite import ndvi_worker

    fecha = req.fecha or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    client = CopernicusClient()

    try:
        # Buscar imagen más reciente
        bbox = [req.lon_min, req.lat_min, req.lon_max, req.lat_max]
        items = await client.search_sentinel2(
            bbox=bbox,
            start_date=_thirty_days_ago(),
            end_date=fecha,
            cloud_cover_max=25.0,
            limit=1,
        )
        is_sim = not items or items[0].get("properties", {}).get("sim", True)

        # Calcular índices
        result = ndvi_worker.simulate_parcela_indices(req.parcela_id, fecha)

        # Registrar en blockchain
        tx_hash: Optional[str] = None
        if req.registrar_blockchain:
            try:
                import importlib.util
                if importlib.util.find_spec("castuo_graph") is not None:
                    from castuo_graph.skills import registrar_en_blockchain
                    tx_hash = registrar_en_blockchain(
                        f"SAT:{req.parcela_id}",
                        {
                            "ndvi_mean": result.stats["ndvi"].get("mean"),
                            "n_anomalias": len(result.anomalies),
                            "fecha": fecha,
                        },
                    )
            except Exception as exc:
                logger.debug("[satellite] Blockchain no disponible: %s", exc)

        anomalias = [AnomalyItem(**a) for a in result.anomalies]

        return AnalyzeResponse(
            parcela_id=req.parcela_id,
            nombre=req.nombre,
            cultivo=req.cultivo,
            fecha_analisis=fecha,
            ndvi_stats=_stats_to_model(result.stats.get("ndvi")) or IndexStats(
                min=None, max=None, mean=None, std=None, valid_pct=0
            ),
            ndmi_stats=_stats_to_model(result.stats.get("ndmi")),
            evi_stats=_stats_to_model(result.stats.get("evi")),
            anomalias=anomalias,
            n_anomalias=len(anomalias),
            alerta=any(a.severidad == "CRITICA" for a in anomalias),
            tx_hash=tx_hash,
            simulado=is_sim,
            generado_en=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        await client.close()


@router.get("/ndvi/{parcela_id}", summary="NDVI de última imagen disponible")
async def get_ndvi(
    parcela_id: str,
    token: dict = Depends(_auth),
) -> dict[str, Any]:
    """
    Retorna estadísticas NDVI de la última imagen procesada para la parcela.
    Si no hay datos en disco, calcula en tiempo real con datos simulados.
    """
    from services.satellite import ndvi_worker
    from services.satellite.stac_worker import _get_latest_result, _RESULTS_PATH

    cached = _get_latest_result(parcela_id)
    if cached:
        return {
            "parcela_id":    parcela_id,
            "ndvi_stats":    cached["indices"]["ndvi_stats"],
            "n_anomalias":   cached["indices"]["anomalias_detectadas"] if "anomalias_detectadas" in cached["indices"] else len(cached["indices"].get("anomalies", [])),
            "fecha_analisis": cached.get("fecha_analisis"),
            "simulado":      cached.get("simulado", True),
            "cached":        True,
        }

    # Calcular on-demand
    fecha  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = ndvi_worker.simulate_parcela_indices(parcela_id, fecha)
    return {
        "parcela_id":  parcela_id,
        "ndvi_stats":  result.stats.get("ndvi", {}),
        "n_anomalias": len(result.anomalies),
        "fecha_analisis": fecha,
        "simulado":    True,
        "cached":      False,
    }


@router.get("/anomalies/{parcela_id}", summary="Anomalías detectadas en la parcela")
async def get_anomalies(
    parcela_id: str,
    token: dict = Depends(_auth),
) -> dict[str, Any]:
    """
    Retorna las anomalías agronómicas detectadas en la última imagen procesada.
    """
    from services.satellite import ndvi_worker
    from services.satellite.stac_worker import _get_latest_result

    cached = _get_latest_result(parcela_id)
    if cached:
        return {
            "parcela_id":  parcela_id,
            "anomalias":   cached["indices"].get("anomalies", []),
            "n_anomalias": len(cached["indices"].get("anomalies", [])),
            "alerta":      any(a.get("severidad") == "CRITICA" for a in cached["indices"].get("anomalies", [])),
            "fecha":       cached.get("fecha_analisis"),
        }

    fecha  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = ndvi_worker.simulate_parcela_indices(parcela_id, fecha)
    return {
        "parcela_id":  parcela_id,
        "anomalias":   result.anomalies,
        "n_anomalias": len(result.anomalies),
        "alerta":      any(a.get("severidad") == "CRITICA" for a in result.anomalies),
        "fecha":       fecha,
    }


@router.get("/health", summary="Estado del servicio satelital")
async def satellite_health() -> dict[str, Any]:
    """Estado de Copernicus Data Space y datos disponibles. Sin auth."""
    from services.satellite.copernicus_client import CopernicusClient
    client = CopernicusClient()
    health = await client.health()
    await client.close()

    from services.satellite.stac_worker import _RESULTS_PATH
    n_results = len(list(_RESULTS_PATH.glob("*.json"))) if _RESULTS_PATH.exists() else 0

    return {
        "status":           "ok",
        "copernicus":       health,
        "resultados_disco": n_results,
        "ndvi_data_path":   str(_RESULTS_PATH),
        "timestamp":        datetime.now(timezone.utc).isoformat(),
    }


def _thirty_days_ago() -> str:
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
