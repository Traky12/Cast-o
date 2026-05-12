# -*- coding: utf-8 -*-
"""Inserción y lectura de observaciones agrovoltaicas (Postgres); sin ORM."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from backend.database import get_db_connection, is_postgres_available

logger = logging.getLogger(__name__)


def insert_observation(
    zone_id: str,
    irradiance_wm2: float,
    shading_wm2: float,
    transpiration_mmol_m2_s: Optional[float] = None,
    source: str = "api",
) -> Optional[Dict[str, Any]]:
    if not is_postgres_available():
        logger.warning("agrovoltaic: postgres no disponible; observación no persistida")
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agrovoltaic_observations
                (zone_id, irradiance_wm2, shading_wm2, transpiration_mmol_m2_s, source)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, recorded_at
                """,
                (zone_id, float(irradiance_wm2), float(shading_wm2), transpiration_mmol_m2_s, source),
            )
            row = cur.fetchone()
        conn.commit()
        if row:
            return {"id": row["id"], "recorded_at": row["recorded_at"], "zone_id": zone_id}
    except Exception as e:
        logger.exception("agrovoltaic insert: %s", e)
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()
    return None


def latest_shadow_factor(zone_id: str) -> Optional[float]:
    """Factor de sombreado adimensional: shading_wm2 / irradiance_wm2 (última muestra)."""
    if not is_postgres_available():
        return None
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT irradiance_wm2, shading_wm2
                FROM agrovoltaic_observations
                WHERE zone_id = %s
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (zone_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        irr = float(row["irradiance_wm2"])
        if irr <= 0:
            return None
        return float(row["shading_wm2"]) / irr
    finally:
        conn.close()
