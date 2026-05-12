# -*- coding: utf-8 -*-
"""API para sensores IoT (MQTT/LoRa -> actualización en Odoo)."""
import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/sensors", tags=["sensors"])


class SensorUpdateBody(BaseModel):
    sensor_id: str
    valor: float
    granja_id: Optional[int] = None


@router.post("/update")
async def update_sensor(body: SensorUpdateBody):
    """Actualiza valor de sensor (Odoo: castu.drone.sensor.update_from_mqtt)."""
    odoo_url = os.environ.get("ODOO_URL", "")
    if odoo_url:
        try:
            import xmlrpc.client
            db = os.environ.get("ODOO_DB", "castu-system")
            uid = int(os.environ.get("ODOO_UID", "0"))
            password = os.environ.get("ODOO_PASSWORD", "")
            common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
            models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")
            models.execute_kw(
                db, uid, password,
                "castu.drone.sensor", "update_from_mqtt",
                [body.sensor_id, body.valor],
            )
        except Exception:
            pass
    return {"status": "success"}
