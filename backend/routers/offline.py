# -*- coding: utf-8 -*-
"""Modo offline 72h: almacenar acciones y sincronizar cuando hay conexión."""
import os
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/offline", tags=["offline"])

# Lazy init to avoid creating DB at import time
_sync_manager = None


def _get_sync():
    global _sync_manager
    if _sync_manager is None:
        from ..offline import SyncManager
        _sync_manager = SyncManager(os.environ.get("OFFLINE_DB_PATH"))
    return _sync_manager


class StoreActionBody(BaseModel):
    action_type: str
    payload: Dict[str, Any]


@router.post("/store")
async def store_action(body: StoreActionBody):
    """Guarda una acción para ejecutar cuando haya conexión (Castuo Gate / app móvil)."""
    sync = _get_sync()
    row_id = sync.offline_db.store_action(body.action_type, body.payload)
    return {"id": row_id, "status": "stored"}


@router.post("/sync")
async def sync_pending():
    """Sincroniza todas las acciones pendientes con Odoo/API (llamar cuando vuelva la red)."""
    sync = _get_sync()
    processed = sync.sync_all()
    return {"processed": processed, "count": len(processed)}


@router.get("/pending")
async def list_pending():
    """Lista acciones pendientes (solo lectura)."""
    sync = _get_sync()
    rows = sync.offline_db.get_pending()
    return {
        "pending": [
            {"id": r[0], "action_type": r[1], "payload": r[2], "created_at": r[3]}
            for r in rows
        ]
    }
