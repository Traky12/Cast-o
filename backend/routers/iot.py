# -*- coding: utf-8 -*-
"""Microservicio IoT: datos sensores Libelium (MQTT/WebSocket) para CTAEX — Barreras v6.1."""
import json
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

try:
    from backend.security.input_validation import validate_input_payload, validate_iot_payload
except ImportError:
    validate_input_payload = validate_iot_payload = None

router = APIRouter()


class SensorData(BaseModel):
    sensor_id: str
    batch_id: str
    temperature: float
    humidity: float
    ph: float
    ec: float
    light: int
    timestamp: str


@router.websocket("/ws/iot")
async def websocket_iot(websocket: WebSocket):
    """WebSocket para datos IoT en tiempo real (sensores Libelium)."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                sensor_data = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"error": "Invalid JSON"})
                )
                continue

            # Barreras v6.1: validación de patrones bloqueados
            if validate_input_payload:
                ok, reason = validate_input_payload(sensor_data)
                if not ok:
                    await websocket.send_text(json.dumps({"error": reason or "Input blocked"}))
                    continue
            if validate_iot_payload:
                ok, errs, _ = validate_iot_payload(sensor_data)
                if not ok:
                    await websocket.send_text(
                        json.dumps({"error": "IoT schema validation failed", "details": errs})
                    )
                    continue
            if not (0 <= sensor_data.get("temperature", -1) <= 50):
                await websocket.send_text(
                    json.dumps({"error": "Temperature out of range (0-50°C)"})
                )
                continue

            # En producción: persistir en BD y/o publicar a MQTT
            # await save_sensor_reading(sensor_data)
            # await mqtt_publish("iot/readings", sensor_data)

            await websocket.send_text(
                json.dumps({
                    "status": "received",
                    "timestamp": datetime.now().isoformat(),
                    "data": sensor_data,
                })
            )
    except WebSocketDisconnect:
        pass


@router.post("/ingest")
async def ingest_sensor_data(payload: Dict[str, Any]):
    """Ingesta REST de datos de sensores (Barreras v6.1: schema + regex block)."""
    if validate_input_payload:
        ok, reason = validate_input_payload(payload)
        if not ok:
            raise HTTPException(400, detail=reason or "Input blocked (security)")
    if validate_iot_payload:
        ok, errs, _ = validate_iot_payload(payload)
        if not ok:
            raise HTTPException(422, detail={"message": "IoT schema validation failed", "errors": errs})
    temp = payload.get("temperature")
    if temp is not None and not (0 <= float(temp) <= 50):
        raise HTTPException(400, "Temperature out of range (0-50°C)")
    return {
        "status": "received",
        "timestamp": datetime.now().isoformat(),
        "sensor_id": payload.get("sensor_id"),
    }
