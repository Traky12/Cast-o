# -*- coding: utf-8 -*-
"""Sincronización de acciones pendientes con Odoo cuando hay conexión."""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List

from .db import OfflineDB


class SyncManager:
    """Ejecuta acciones pendientes (riego, comandos robot, etc.) contra Odoo/API."""

    def __init__(self, db_path: str = None):
        self.offline_db = OfflineDB(db_path)
        self._handlers: Dict[str, Callable[[dict], Any]] = {
            "activate_riego": self._handle_riego,
            "robot_command": self._handle_robot,
        }

    def _handle_riego(self, payload: dict) -> None:
        """Envía activar_riego a la API (riego_id en path, duracion en body)."""
        api_url = os.environ.get("CASTUO_API_URL", "http://localhost:8000")
        riego_id = payload.get("riego_id")
        if not riego_id:
            return
        try:
            import urllib.request
            data = json.dumps({"duracion": payload.get("duracion", 30)}).encode("utf-8")
            req = urllib.request.Request(
                f"{api_url}/riego/{riego_id}/activar",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    def _handle_robot(self, payload: dict) -> None:
        """Reenvía comando a robot vía MQTT/API."""
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{os.environ.get('CASTUO_API_URL', 'http://localhost:8000')}/robotica/command",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def sync_all(self) -> List[int]:
        """Sincroniza todas las acciones pendientes; devuelve IDs procesados."""
        pending = self.offline_db.get_pending()
        processed = []
        for row in pending:
            action_id, action_type, payload_str, _ = row
            try:
                payload = json.loads(payload_str)
                handler = self._handlers.get(action_type)
                if handler:
                    handler(payload)
                self.offline_db.delete_pending(action_id)
                processed.append(action_id)
            except Exception:
                continue
        return processed
