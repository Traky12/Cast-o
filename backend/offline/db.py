# -*- coding: utf-8 -*-
"""Base de datos local SQLite para modo offline (72h sin conexión)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "offline.db"


class OfflineDB:
    """Almacena acciones pendientes para sincronizar cuando haya conexión."""

    def __init__(self, db_path: str | Path = None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def store_action(self, action_type: str, payload: dict | str) -> int:
        """Guarda una acción pendiente."""
        cur = self.conn.cursor()
        payload_str = payload if isinstance(payload, str) else json.dumps(payload)
        cur.execute(
            "INSERT INTO pending_actions (action_type, payload) VALUES (?, ?)",
            (action_type, payload_str),
        )
        self.conn.commit()
        return cur.lastrowid or 0

    def get_pending(self) -> List[Tuple[int, str, str, str]]:
        """Devuelve todas las acciones pendientes (id, action_type, payload, created_at)."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, action_type, payload, created_at FROM pending_actions ORDER BY id ASC"
        )
        return cur.fetchall()

    def delete_pending(self, action_id: int) -> None:
        """Elimina una acción pendiente tras sincronizar."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM pending_actions WHERE id = ?", (action_id,))
        self.conn.commit()

    def clear_pending(self) -> int:
        """Elimina todas las pendientes; devuelve cantidad eliminada."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pending_actions")
        n = cur.fetchone()[0]
        cur.execute("DELETE FROM pending_actions")
        self.conn.commit()
        return n

    def close(self) -> None:
        self.conn.close()
