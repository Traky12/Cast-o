# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter

from backend.database import get_db_connection, is_postgres_available
from backend.services.gaia_chain import GaiaChainService

router = APIRouter(prefix="/hydroponics-saas", tags=["hydroponics-saas"])


def _get_allowed_api_keys() -> List[str]:
    # Compatibilidad con integraciones: permite usar N8N_API_KEY si no hay una clave dedicada.
    raw = os.getenv("HYDROPONICS_SAAS_API_KEYS", "").strip()
    if raw:
        return [x.strip() for x in raw.split(",") if x.strip()]
    k = os.getenv("N8N_API_KEY", "").strip()
    if k:
        return [k]
    # Dev fallback (no ideal en prod): mantener para que el equipo pueda “end-to-end” sin fricción.
    return ["default_n8n_key_123"]


def _validate_api_key(x_api_key: Optional[str]) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY")
    if x_api_key not in set(_get_allowed_api_keys()):
        raise HTTPException(status_code=403, detail="Invalid API key")


def _require_x_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    x_api_key_alt: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    key = x_api_key or x_api_key_alt or ""
    _validate_api_key(key)
    return key


HYDROPONICS_SAAS_READINGS_TOTAL = Counter(
    "hydroponics_saas_readings_total",
    "Total hydroponics sensor readings",
    ["sensor_type"],
)
HYDROPONICS_SAAS_ALERTS_TOTAL = Counter(
    "hydroponics_saas_alerts_total",
    "Total hydroponics alerts",
    ["alert_type"],
)
HYDROPONICS_SAAS_ANALYSIS_TOTAL = Counter(
    "hydroponics_saas_analysis_total",
    "Total hydroponics daily analysis",
    ["status"],
)

HYDROPONICS_SAAS_CROPS_TOTAL = Counter(
    "hydroponics_saas_crops_total",
    "Total hydroponics crops",
    ["status"],
)
HYDROPONICS_SAAS_HARVESTS_TOTAL = Counter(
    "hydroponics_saas_harvests_total",
    "Total hydroponics harvests",
    ["quality"],
)


class SensorReading(BaseModel):
    sensor_id: str
    sensor_type: str  # ph/ec/temperature/humidity
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: str
    unit: str
    zone_id: str


class DailyAnalysis(BaseModel):
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    zone_id: str
    overall_status: str
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    trends: List[Dict[str, Any]] = Field(default_factory=list)
    priority: str = "medium"


class CropRecord(BaseModel):
    crop_id: str
    zone_id: str
    plant_type: str
    planting_date: datetime = Field(default_factory=datetime.utcnow)
    growth_stage: str = "vegetative"
    quantity: int = 1
    status: str = "active"
    metadata: Optional[Dict[str, Any]] = None


class HarvestRecord(BaseModel):
    harvest_date: datetime = Field(default_factory=datetime.utcnow)
    weight: float
    quality: str  # optimal/good/poor
    notes: Optional[str] = None
    zone_id: str


@router.post("/sensor-readings")
async def create_sensor_reading(
    reading: SensorReading,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO hydroponics_sensor_readings
                (sensor_id, sensor_type, value, timestamp, location, unit, zone_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sensor_id, timestamp, zone_id) DO UPDATE
                SET value = EXCLUDED.value,
                    sensor_type = EXCLUDED.sensor_type,
                    location = EXCLUDED.location,
                    unit = EXCLUDED.unit
                """,
                (
                    reading.sensor_id,
                    reading.sensor_type,
                    float(reading.value),
                    reading.timestamp,
                    reading.location,
                    reading.unit,
                    reading.zone_id,
                ),
            )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()

    # Anclaje: no requiere espectros completos; se registra evidencia minimizada.
    payload = reading.model_dump(mode="json")
    payload["timestamp"] = int(reading.timestamp.timestamp())
    try:
        tx = await GaiaChainService().register_batch(
            {
                "batch_id": f"hydro-reading-{reading.zone_id}",
                "strain_id": f"sensor:{reading.sensor_id}",
                "thc_percentage": 0,
                "cbd_percentage": 0,
                "weight_kg": 0,
                "lab_results": {
                    "event_type": "HYDROPONICS_SENSOR_READING",
                    "data": payload,
                    "status": "RECORDED",
                },
                "account_id": os.getenv("HYDROPONICS_SAAS_ACCOUNT_ID", "hydroponics-saas"),
            }
        )
        gaiachain_tx = tx.get("transaction_hash") if isinstance(tx, dict) else None
    except Exception:
        gaiachain_tx = None

    HYDROPONICS_SAAS_READINGS_TOTAL.labels(sensor_type=reading.sensor_type).inc()
    return {
        "status": "success",
        "sensor_reading": reading.model_dump(mode="json"),
        "gaiachain_tx": gaiachain_tx,
    }


@router.post("/daily-analysis")
async def create_daily_analysis(
    analysis: DailyAnalysis,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO hydroponics_daily_analysis
                (analysis_date, zone_id, overall_status, issues, recommendations, trends, priority)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                ON CONFLICT (analysis_date, zone_id) DO UPDATE
                SET overall_status = EXCLUDED.overall_status,
                    issues = EXCLUDED.issues,
                    recommendations = EXCLUDED.recommendations,
                    trends = EXCLUDED.trends,
                    priority = EXCLUDED.priority
                """,
                (
                    analysis.analysis_date,
                    analysis.zone_id,
                    analysis.overall_status,
                    json.dumps(analysis.issues),
                    json.dumps(analysis.recommendations),
                    json.dumps(analysis.trends),
                    analysis.priority,
                ),
            )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()

    payload = analysis.model_dump(mode="json")
    payload["analysis_date"] = int(analysis.analysis_date.timestamp())
    try:
        tx = await GaiaChainService().register_batch(
            {
                "batch_id": f"hydro-analysis-{analysis.zone_id}-{int(analysis.analysis_date.timestamp())}",
                "strain_id": f"zone:{analysis.zone_id}",
                "thc_percentage": 0,
                "cbd_percentage": 0,
                "weight_kg": 0,
                "lab_results": {
                    "event_type": "HYDROPONICS_DAILY_ANALYSIS",
                    "data": payload,
                    "status": analysis.overall_status,
                },
                "account_id": os.getenv("HYDROPONICS_SAAS_ACCOUNT_ID", "hydroponics-saas"),
            }
        )
        gaiachain_tx = tx.get("transaction_hash") if isinstance(tx, dict) else None
    except Exception:
        gaiachain_tx = None

    HYDROPONICS_SAAS_ANALYSIS_TOTAL.labels(status=analysis.overall_status).inc()
    return {
        "status": "success",
        "analysis": analysis.model_dump(mode="json"),
        "gaiachain_tx": gaiachain_tx,
    }


@router.get("/history/sensor-readings")
async def get_sensor_readings_history(
    zone_id: str,
    sensor_type: Optional[str] = None,
    days: int = 7,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if sensor_type:
                cur.execute(
                    """
                    SELECT * FROM hydroponics_sensor_readings
                    WHERE zone_id = %s
                      AND timestamp >= NOW() - INTERVAL '%s days'
                      AND sensor_type = %s
                    ORDER BY timestamp DESC
                    """,
                    (zone_id, days, sensor_type),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM hydroponics_sensor_readings
                    WHERE zone_id = %s
                      AND timestamp >= NOW() - INTERVAL '%s days'
                    ORDER BY timestamp DESC
                    """,
                    (zone_id, days),
                )
            rows = cur.fetchall()
        # RealDictCursor: rows ya son dicts; si no, convertimos.
        data = [dict(r) for r in rows]  # type: ignore[arg-type]
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()


@router.get("/history/daily-analysis")
async def get_daily_analysis_history(
    zone_id: str,
    days: int = 30,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM hydroponics_daily_analysis
                WHERE zone_id = %s
                  AND analysis_date >= NOW() - INTERVAL '%s days'
                ORDER BY analysis_date DESC
                """,
                (zone_id, days),
            )
            rows = cur.fetchall()
        data = [dict(r) for r in rows]  # type: ignore[arg-type]
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()


@router.post("/crops")
async def create_crop(
    crop: CropRecord,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO hydroponics_crops
                (crop_id, zone_id, plant_type, planting_date, growth_stage, quantity, status, metadata, end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, NULL)
                ON CONFLICT (crop_id) DO UPDATE
                SET zone_id = EXCLUDED.zone_id,
                    plant_type = EXCLUDED.plant_type,
                    planting_date = EXCLUDED.planting_date,
                    growth_stage = EXCLUDED.growth_stage,
                    quantity = EXCLUDED.quantity,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata
                """,
                (
                    crop.crop_id,
                    crop.zone_id,
                    crop.plant_type,
                    crop.planting_date,
                    crop.growth_stage,
                    int(crop.quantity),
                    crop.status,
                    json.dumps(crop.metadata) if crop.metadata else None,
                ),
            )
        conn.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()

    try:
        payload = crop.model_dump(mode="json")
        payload["timestamp"] = int(crop.planting_date.timestamp())
        tx = await GaiaChainService().register_batch(
            {
                "batch_id": f"hydro-crop-{crop.crop_id}",
                "strain_id": f"crop:{crop.crop_id}",
                "thc_percentage": 0,
                "cbd_percentage": 0,
                "weight_kg": 0,
                "lab_results": {
                    "event_type": "HYDROPONICS_CROP_CREATED",
                    "data": payload,
                    "status": crop.status,
                },
                "account_id": os.getenv("HYDROPONICS_SAAS_ACCOUNT_ID", "hydroponics-saas"),
            }
        )
        gaiachain_tx = tx.get("transaction_hash") if isinstance(tx, dict) else None
    except Exception:
        gaiachain_tx = None

    HYDROPONICS_SAAS_CROPS_TOTAL.labels(status=crop.status).inc()

    return {"status": "success", "crop": crop.model_dump(mode="json"), "gaiachain_tx": gaiachain_tx}


@router.put("/crops/{crop_id}/harvest")
async def record_harvest(
    crop_id: str,
    harvest: HarvestRecord,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1) crop existe?
            cur.execute("SELECT crop_id FROM hydroponics_crops WHERE crop_id = %s", (crop_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Crop not found")

            # 2) insert harvest
            cur.execute(
                """
                INSERT INTO hydroponics_harvests
                (crop_id, harvest_date, weight, quality, notes, zone_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    crop_id,
                    harvest.harvest_date,
                    float(harvest.weight),
                    harvest.quality,
                    harvest.notes,
                    harvest.zone_id,
                ),
            )

            # 3) update crop state
            cur.execute(
                """
                UPDATE hydroponics_crops
                SET status = 'harvested', end_date = %s
                WHERE crop_id = %s
                """,
                (harvest.harvest_date, crop_id),
            )

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()

    try:
        payload = harvest.model_dump(mode="json")
        payload["crop_id"] = crop_id
        payload["timestamp"] = int(harvest.harvest_date.timestamp())
        tx = await GaiaChainService().register_batch(
            {
                "batch_id": f"hydro-harvest-{crop_id}-{int(harvest.harvest_date.timestamp())}",
                "strain_id": f"harvest:{crop_id}",
                "thc_percentage": 0,
                "cbd_percentage": 0,
                "weight_kg": float(harvest.weight),
                "lab_results": {
                    "event_type": "HYDROPONICS_HARVEST",
                    "data": payload,
                    "status": "RECORDED",
                },
                "account_id": os.getenv("HYDROPONICS_SAAS_ACCOUNT_ID", "hydroponics-saas"),
            }
        )
        gaiachain_tx = tx.get("transaction_hash") if isinstance(tx, dict) else None
    except Exception:
        gaiachain_tx = None

    HYDROPONICS_SAAS_HARVESTS_TOTAL.labels(quality=harvest.quality).inc()

    return {
        "status": "success",
        "harvest": {**harvest.model_dump(mode="json"), "crop_id": crop_id},
        "gaiachain_tx": gaiachain_tx,
    }


@router.get("/history/crops")
async def get_crops_history(
    zone_id: str,
    days: int = 365,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM hydroponics_crops
                WHERE zone_id = %s
                  AND planting_date >= NOW() - INTERVAL '%s days'
                ORDER BY planting_date DESC
                """,
                (zone_id, days),
            )
            rows = cur.fetchall()
        data = [dict(r) for r in rows]  # type: ignore[arg-type]
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()


@router.get("/history/harvests")
async def get_harvests_history(
    zone_id: str,
    days: int = 365,
    _: str = Depends(_require_x_api_key),
):
    if not is_postgres_available():
        raise HTTPException(status_code=503, detail="PostgreSQL no configurado")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  h.*,
                  c.plant_type,
                  c.crop_id
                FROM hydroponics_harvests h
                JOIN hydroponics_crops c ON h.crop_id = c.crop_id
                WHERE h.zone_id = %s
                  AND h.harvest_date >= NOW() - INTERVAL '%s days'
                ORDER BY h.harvest_date DESC
                """,
                (zone_id, days),
            )
            rows = cur.fetchall()
        data = [dict(r) for r in rows]  # type: ignore[arg-type]
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        conn.close()

