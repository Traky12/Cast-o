# -*- coding: utf-8 -*-
"""API para cámaras (RTSP, detección de plagas YOLOv8)."""
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/cameras", tags=["cameras"])


class StreamStartBody(BaseModel):
    rtsp_url: str
    drone_id: Optional[int] = None


@router.post("/stream/start")
async def stream_start(body: StreamStartBody):
    """Inicia procesamiento de stream RTSP (placeholder; en prod: worker con YOLOv8)."""
    return {"status": "started", "rtsp_url": body.rtsp_url}


@router.post("/detect/plagas")
async def detect_plagas(image: UploadFile = File(...)):
    """Detección de plagas en imagen (YOLOv8; requiere modelo entrenado)."""
    # Placeholder: en producción cargar ultralytics YOLO y predecir
    contents = await image.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Imagen vacía")
    return {"detections": [], "message": "Modelo no cargado; añadir YOLOv8 en producción"}


@router.post("/camera/alert")
async def camera_alert(
    drone_id: int,
    tipo: str,
    confianza: float,
    coordenadas: Optional[str] = None,
):
    """Registra alerta de cámara (llamado por worker de detección)."""
    # En producción: crear registro en Odoo vía XML-RPC
    return {"status": "ok", "drone_id": drone_id, "tipo": tipo}
