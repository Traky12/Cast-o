"""
Persistencia local del stub PEI-002: tablas alineadas con SigpacValidationEnvelope / ParcelAuditPayload.
Migración suave: si existían `envelopes` / `parcels`, se copian una vez a las tablas nuevas.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

_conn: Optional[sqlite3.Connection] = None


def _default_db_path() -> Path:
    raw = (os.environ.get("PEI002_SQLITE_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parent / "data" / "pei002_stub.db"


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        path = _default_db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def _migrate_legacy_if_needed(c: sqlite3.Connection) -> None:
    for legacy, modern in (
        ("envelopes", "sigpac_validation_envelopes"),
        ("parcels", "parcel_validations"),
    ):
        cur = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (legacy,),
        )
        if not cur.fetchone():
            continue
        n_new = c.execute(f"SELECT COUNT(*) AS n FROM {modern}").fetchone()["n"]
        if n_new:
            continue
        c.execute(
            f"""
            INSERT OR IGNORE INTO {modern} (id, received_utc, payload_json)
            SELECT id, received_utc, payload_json FROM {legacy}
            """
        )


def init_schema() -> None:
    c = get_conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS sigpac_validation_envelopes (
            id TEXT PRIMARY KEY,
            received_utc TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS parcel_validations (
            id TEXT PRIMARY KEY,
            received_utc TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        """
    )
    _migrate_legacy_if_needed(c)
    c.commit()


def reset_conn_for_tests() -> None:
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
    _conn = None


def save_sigpac_envelope(envelope_id: str, payload: Dict[str, Any], received_utc: str) -> None:
    insert_envelope({"id": envelope_id, "received_utc": received_utc, "payload": payload})


def save_parcel_validation(parcel_id: str, payload: Dict[str, Any], received_utc: str) -> None:
    insert_parcel({"id": parcel_id, "received_utc": received_utc, "payload": payload})


def insert_envelope(rec: Dict[str, Any]) -> None:
    c = get_conn()
    c.execute(
        """
        INSERT INTO sigpac_validation_envelopes (id, received_utc, payload_json)
        VALUES (?,?,?)
        """,
        (rec["id"], rec["received_utc"], json.dumps(rec["payload"], ensure_ascii=False, default=str)),
    )
    c.commit()


def insert_parcel(rec: Dict[str, Any]) -> None:
    c = get_conn()
    c.execute(
        """
        INSERT INTO parcel_validations (id, received_utc, payload_json)
        VALUES (?,?,?)
        """,
        (rec["id"], rec["received_utc"], json.dumps(rec["payload"], ensure_ascii=False, default=str)),
    )
    c.commit()


def _rows_to_records(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [
        {"id": r["id"], "received_utc": r["received_utc"], "payload": json.loads(r["payload_json"])}
        for r in rows
    ]


def list_envelopes(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    c = get_conn()
    base = (
        "SELECT id, received_utc, payload_json FROM sigpac_validation_envelopes "
        "ORDER BY received_utc DESC"
    )
    if limit is not None and limit > 0:
        rows = c.execute(base + " LIMIT ?", (int(limit),)).fetchall()
    else:
        rows = c.execute(base).fetchall()
    return _rows_to_records(rows)


def list_parcels(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    c = get_conn()
    base = "SELECT id, received_utc, payload_json FROM parcel_validations ORDER BY received_utc DESC"
    if limit is not None and limit > 0:
        rows = c.execute(base + " LIMIT ?", (int(limit),)).fetchall()
    else:
        rows = c.execute(base).fetchall()
    return _rows_to_records(rows)


def get_sigpac_envelopes(limit: int = 100) -> List[Dict[str, Any]]:
    return list_envelopes(limit=limit)


def get_parcel_validations(limit: int = 100) -> List[Dict[str, Any]]:
    return list_parcels(limit=limit)
