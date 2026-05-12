# -*- coding: utf-8 -*-
"""Routers FastAPI para control ambiental, microgreens y tratamiento de agua."""
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from production.environment_control import EnvironmentalControlSystem
from production.microgreens_manager import MicrogreensManager
from production.water_treatment import WaterTreatmentSystem
from production.models.water_treatment import WaterQualityData, WaterTreatmentLog

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


def get_gaiachain():
    """Dependencia GaiaChain (inyección desde env)."""
    if GaiaChainClient is None:
        return None
    return GaiaChainClient(rpc_url=os.getenv("GAIA_CHAIN_RPC_URL", ""))


def get_environment_system(
    gaiachain: GaiaChainClient = Depends(get_gaiachain),
) -> EnvironmentalControlSystem:
    return EnvironmentalControlSystem(gaiachain)


def get_microgreens_manager(
    gaiachain: GaiaChainClient = Depends(get_gaiachain),
) -> MicrogreensManager:
    return MicrogreensManager(gaiachain)


def get_water_system(
    gaiachain: GaiaChainClient = Depends(get_gaiachain),
) -> WaterTreatmentSystem:
    return WaterTreatmentSystem(gaiachain)


# --- Control ambiental ---
environment_router = APIRouter()


@environment_router.post("/data", summary="Procesar datos ambientales (ozono, UV, nutrientes)")
async def process_environmental_data(
    data: Dict[str, Any],
    system: EnvironmentalControlSystem = Depends(get_environment_system),
):
    """Procesa datos ambientales y genera comandos para actuadores."""
    result = system.process_environmental_data(data)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@environment_router.get("/thresholds/{crop_type}", summary="Umbrales por tipo de cultivo")
async def get_crop_thresholds(
    crop_type: str,
    system: EnvironmentalControlSystem = Depends(get_environment_system),
):
    """Devuelve los umbrales ambientales para un tipo de cultivo."""
    thresholds = system.get_crop_thresholds(crop_type)
    return {"crop_type": crop_type, "thresholds": thresholds}


# --- Microgreens ---
microgreens_router = APIRouter()


@microgreens_router.post("/batches", summary="Crear lote de microgreens")
async def create_microgreen_batch(
    variety_name: str,
    tray_id: str,
    quantity: float,
    manager: MicrogreensManager = Depends(get_microgreens_manager),
):
    """Crea un nuevo lote de microgreens con trazabilidad."""
    result = manager.create_batch(variety_name, tray_id, quantity)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@microgreens_router.put("/batches/{batch_id}", summary="Actualizar estado de lote")
async def update_microgreen_batch(
    batch_id: str,
    status: str,
    data: Optional[Dict] = None,
    manager: MicrogreensManager = Depends(get_microgreens_manager),
):
    """Actualiza el estado de un lote de microgreens."""
    result = manager.update_batch_status(batch_id, status, data)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@microgreens_router.post("/batches/{batch_id}/environment", summary="Añadir datos ambientales al lote")
async def add_microgreen_environmental_data(
    batch_id: str,
    data: Dict[str, Any],
    manager: MicrogreensManager = Depends(get_microgreens_manager),
):
    """Añade datos ambientales a un lote de microgreens."""
    result = manager.add_environmental_data(batch_id, data)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@microgreens_router.post("/batches/{batch_id}/certificate", summary="Generar certificado de calidad")
async def generate_microgreen_certificate(
    batch_id: str,
    manager: MicrogreensManager = Depends(get_microgreens_manager),
):
    """Genera un certificado de calidad para un lote de microgreens."""
    result = manager.generate_certificate(batch_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@microgreens_router.get("/batches/{batch_id}", summary="Historial de lote")
async def get_microgreen_batch_history(
    batch_id: str,
    manager: MicrogreensManager = Depends(get_microgreens_manager),
):
    """Obtiene el historial completo de un lote de microgreens."""
    result = manager.get_batch_history(batch_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", "No encontrado"))
    return result


# --- Tratamiento de agua ---
water_router = APIRouter()


@water_router.post("/treatments", summary="Registrar tratamiento de agua")
async def log_water_treatment(
    treatment_data: WaterTreatmentLog,
    system: WaterTreatmentSystem = Depends(get_water_system),
):
    """Registra un tratamiento de agua en GaiaChain."""
    payload = treatment_data.model_dump() if hasattr(treatment_data, "model_dump") else treatment_data.dict()
    result = system.log_water_treatment(payload)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@water_router.post("/analysis", summary="Analizar calidad del agua")
async def analyze_water_quality(
    water_data: WaterQualityData,
    crop_type: str,
    system: WaterTreatmentSystem = Depends(get_water_system),
):
    """Analiza la calidad del agua y recomienda tratamientos."""
    payload = water_data.model_dump() if hasattr(water_data, "model_dump") else water_data.dict()
    result = system.analyze_water_quality(payload, crop_type)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@water_router.get("/treatments/{treatment_id}", summary="Historial de tratamiento")
async def get_water_treatment_history(
    treatment_id: str,
    system: WaterTreatmentSystem = Depends(get_water_system),
):
    """Obtiene el historial de un tratamiento de agua."""
    result = system.get_treatment_history(treatment_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", "No encontrado"))
    return result
