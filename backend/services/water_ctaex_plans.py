# -*- coding: utf-8 -*-
"""Cuotas mensuales y trazabilidad (SQLite) para monetización SaaS de /water/ctaex/analyze."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_DB_DIR = _BACKEND_ROOT / "db"
_DB_PATH = _DB_DIR / "water_ctaex_usage.db"
_LEGACY_DB = _BACKEND_ROOT / "water_ctaex_usage.db"

_LOG_PAYLOAD_MAX = 1800

PUBLIC_PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_eur_month": 0,
        "max_requests": 50,
        "features": ["basic_analysis", "historical_data_7d"],
        "ollama": False,
        "automaton": False,
        "description": "Prueba del sistema con análisis por umbrales y cuota reducida.",
    },
    "basic": {
        "id": "basic",
        "name": "Basic",
        "price_eur_month": 49,
        "max_requests": 500,
        "features": ["basic_analysis", "historical_data_30d", "ollama_analysis"],
        "ollama": True,
        "automaton": False,
        "description": "Agricultura de precisión con IA (Ollama) según plan.",
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_eur_month": 149,
        "max_requests": 5000,
        "features": [
            "basic_analysis",
            "historical_data_90d",
            "ollama_analysis",
            "automaton_analysis",
            "priority_alerts",
        ],
        "ollama": True,
        "automaton": True,
        "description": "Alto volumen, alertas prioritarias y bandera Automatón en catálogo.",
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_eur_month": None,
        "max_requests": -1,
        "features": ["all"],
        "ollama": True,
        "automaton": True,
        "description": "Presupuesto y SLA; requests ilimitados en cuota.",
    },
}


def _key_hash(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def hash_api_key(api_key: str) -> str:
    """Hash SHA-256 de la API key (facturación / informes sin almacenar la clave)."""
    return _key_hash(api_key)


def _ensure_db_dir() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)


def _migrate_legacy_sqlite() -> None:
    if _DB_PATH.exists():
        return
    if _LEGACY_DB.is_file():
        try:
            _ensure_db_dir()
            shutil.copy2(_LEGACY_DB, _DB_PATH)
            logger.info("Migrado %s -> %s", _LEGACY_DB, _DB_PATH)
        except OSError as e:
            logger.warning("No se pudo migrar SQLite legado: %s", e)


def _conn() -> sqlite3.Connection:
    _migrate_legacy_sqlite()
    _ensure_db_dir()
    c = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_usage (
            key_hash TEXT NOT NULL,
            period TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (key_hash, period)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            period TEXT NOT NULL,
            request_timestamp TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            input_summary TEXT NOT NULL,
            http_status INTEGER NOT NULL
        )
        """
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_period ON usage_logs (period)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_key_hash ON usage_logs (key_hash)"
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_customers (
            key_hash TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'pending',
            last_payment_date TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            key_hash TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            period_yyyymm TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            tax_rate REAL NOT NULL DEFAULT 0.21,
            total_cents INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            due_date TEXT NOT NULL,
            paid_at TEXT,
            UNIQUE (key_hash, period_yyyymm)
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices (status)")
    c.commit()
    return c


def quota_enforcement_enabled() -> bool:
    return os.getenv("WATER_CTAEX_ENFORCE_QUOTA", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def resolve_plan_for_api_key(api_key: str) -> str | None:
    raw = os.getenv("WATER_API_KEY_TO_PLAN", "").strip()
    if not raw:
        return None
    try:
        mapping: dict[str, str] = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("WATER_API_KEY_TO_PLAN no es JSON válido: %s", e)
        return None
    return mapping.get(api_key)


def current_period_yyyymm() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m")


def get_usage_count(key_hash: str, period: str) -> int:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT count FROM monthly_usage WHERE key_hash = ? AND period = ?",
            (key_hash, period),
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def increment_usage(key_hash: str, period: str) -> int:
    conn = _conn()
    try:
        conn.execute(
            """
            INSERT INTO monthly_usage (key_hash, period, count) VALUES (?, ?, 1)
            ON CONFLICT(key_hash, period) DO UPDATE SET count = count + 1
            """,
            (key_hash, period),
        )
        conn.commit()
        row = conn.execute(
            "SELECT count FROM monthly_usage WHERE key_hash = ? AND period = ?",
            (key_hash, period),
        ).fetchone()
        return int(row[0]) if row else 1
    finally:
        conn.close()


def _truncate_payload(payload: dict[str, Any]) -> str:
    try:
        s = json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        s = str(payload)
    if len(s) > _LOG_PAYLOAD_MAX:
        return s[: _LOG_PAYLOAD_MAX] + "…"
    return s


def append_usage_log(
    *,
    api_key: str,
    plan_id: str,
    endpoint: str,
    input_payload: dict[str, Any],
    http_status: int,
) -> None:
    """Registro de trazabilidad: solo key_hash, nunca la clave en claro."""
    kh = _key_hash(api_key)
    period = current_period_yyyymm()
    ts = datetime.now(timezone.utc).isoformat()
    summary = _truncate_payload(input_payload)
    conn = _conn()
    try:
        conn.execute(
            """
            INSERT INTO usage_logs
            (key_hash, plan_id, period, request_timestamp, endpoint, input_summary, http_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (kh, plan_id, period, ts, endpoint, summary, http_status),
        )
        conn.commit()
    finally:
        conn.close()


def consume_quota_or_raise(api_key: str) -> tuple[str, int, int | None]:
    """
    Resuelve plan, comprueba límite mensual e incrementa contador.
    Devuelve (plan_id, usados_este_mes, restantes o None si ilimitado).
    """
    plan_id = resolve_plan_for_api_key(api_key)
    if not plan_id or plan_id not in PUBLIC_PLANS:
        raise ValueError("unknown_api_key")

    cfg = PUBLIC_PLANS[plan_id]
    max_r = int(cfg["max_requests"])
    kh = _key_hash(api_key)
    period = current_period_yyyymm()
    used_before = get_usage_count(kh, period)

    if max_r > 0 and used_before >= max_r:
        raise OverflowError("quota_exceeded")

    new_count = increment_usage(kh, period)
    remaining: int | None
    if max_r < 0:
        remaining = None
    else:
        remaining = max_r - new_count

    return plan_id, new_count, remaining


def plan_allows_ollama(plan_id: str) -> bool:
    if plan_id not in PUBLIC_PLANS:
        return True
    return bool(PUBLIC_PLANS[plan_id].get("ollama"))


def clear_usage_records() -> tuple[int, int]:
    """Vacía monthly_usage y usage_logs (pruebas). Devuelve (filas_usage, filas_logs)."""
    conn = _conn()
    try:
        u = conn.execute("SELECT COUNT(*) FROM monthly_usage").fetchone()
        l = conn.execute("SELECT COUNT(*) FROM usage_logs").fetchone()
        nu, nl = int(u[0]) if u else 0, int(l[0]) if l else 0
        conn.execute("DELETE FROM monthly_usage")
        conn.execute("DELETE FROM usage_logs")
        conn.commit()
        return nu, nl
    finally:
        conn.close()


def reset_all_quotas() -> int:
    """Pone a cero los contadores mensuales (no borra usage_logs). Idempotente."""
    conn = _conn()
    try:
        row = conn.execute("SELECT COUNT(*) FROM monthly_usage").fetchone()
        n = int(row[0]) if row else 0
        conn.execute("DELETE FROM monthly_usage")
        conn.commit()
        return n
    finally:
        conn.close()


def get_usage_report(
    *,
    limit: int = 500,
    plan_id: str | None = None,
) -> list[dict[str, Any]]:
    """Últimas trazas (key_hash, no clave)."""
    limit = max(1, min(limit, 5000))
    conn = _conn()
    try:
        conn.row_factory = sqlite3.Row
        if plan_id:
            rows = conn.execute(
                """
                SELECT id, key_hash, plan_id, period, request_timestamp, endpoint,
                       input_summary, http_status
                FROM usage_logs
                WHERE plan_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (plan_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, key_hash, plan_id, period, request_timestamp, endpoint,
                       input_summary, http_status
                FROM usage_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def db_path() -> Path:
    return _DB_PATH


def connection() -> sqlite3.Connection:
    """Conexión SQLite con esquema de cuotas + facturación."""
    return _conn()
