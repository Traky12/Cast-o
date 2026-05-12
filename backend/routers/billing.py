# -*- coding: utf-8 -*-
"""
Router Facturación — Billing engine N cooperativas (€140/ha/mes SaaS agrovoltaico, escalable).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/billing", tags=["Facturación"])

COOP_HECTAREAS_FALLBACK = {1: 2.5, 2: 5.0, 3: 3.0}
PRECIO_HA_MES = 140.0
_DB_PATH = Path(__file__).resolve().parents[1] / "billing.db"


def _hectareas_coop(coop_id: int) -> float | None:
    """Hectáreas de la cooperativa desde lista viva (cooperativas) o fallback estático."""
    try:
        from .cooperativas import COOPERATIVAS_MVP
        for c in COOPERATIVAS_MVP:
            if c.id == coop_id:
                return sum(p.hectares for p in c.parcelas)
    except Exception:
        pass
    return COOP_HECTAREAS_FALLBACK.get(coop_id)


def _conn():
    c = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coop_id INTEGER NOT NULL,
            hectareas REAL NOT NULL,
            precio_ha REAL NOT NULL,
            total_eur REAL NOT NULL,
            estado TEXT NOT NULL DEFAULT 'PENDIENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.commit()
    return c


@router.post("/invoice/{coop_id}")
async def crear_factura(coop_id: int, hectareas: float | None = None, firmado: bool = False):
    """Generar factura mensual para la cooperativa (€140/ha/mes). Escalable a N coops (id desde POST /cooperativas)."""
    ha_default = _hectareas_coop(coop_id)
    if ha_default is None:
        raise HTTPException(status_code=400, detail="coop_id no encontrado; registrar antes con POST /cooperativas")
    ha_facturar = hectareas if hectareas is not None else ha_default
    total = round(ha_facturar * PRECIO_HA_MES, 2)
    estado = "FIRMADO" if firmado else "PENDIENTE"
    conn = _conn()
    try:
        conn.execute(
            "INSERT INTO invoices (coop_id, hectareas, precio_ha, total_eur, estado) VALUES (?,?,?,?,?)",
            (coop_id, ha_facturar, PRECIO_HA_MES, total, estado),
        )
        conn.commit()
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"invoice_id": row_id, "coop_id": coop_id, "hectareas": ha_facturar, "total_eur": total, "estado": estado}
    finally:
        conn.close()


@router.get("/facturacion")
async def dashboard_facturacion():
    """Dashboard facturación: últimas facturas (último mes)."""
    conn = _conn()
    try:
        rows = conn.execute("""
            SELECT id, coop_id, hectareas, precio_ha, total_eur, estado, created_at
            FROM invoices
            WHERE created_at >= date('now', '-1 month')
            ORDER BY created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
