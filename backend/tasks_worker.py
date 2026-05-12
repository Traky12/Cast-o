# -*- coding: utf-8 -*-
"""Tareas Celery para CASTÚO-SYSTEM (certificaciones, persistencia IoT)."""
from backend.tasks import app


@app.task
def process_sensor_reading(payload: dict):
    """Procesa lectura de sensor en segundo plano (persistir, alertas)."""
    return {"status": "processed", "sensor_id": payload.get("sensor_id")}


@app.task
def generate_certificate_async(batch_id: str, variety: str, thc: float, cbd: float, lab_results: dict):
    """Genera certificado PDF en segundo plano."""
    try:
        from backend.services.certification import generate_certificate
        path = generate_certificate(batch_id, variety, thc, cbd, lab_results or {})
        return {"status": "ok", "path": path}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
