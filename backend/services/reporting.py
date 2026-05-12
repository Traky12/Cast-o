# -*- coding: utf-8 -*-
"""Generación de informes de KPIs para el Consejo Asesor y dashboards (Grafana/Power BI)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

try:
    from backend.database import get_db_connection, is_postgres_available
except ImportError:
    get_db_connection = None
    is_postgres_available = lambda: False


def generate_kpi_report(days: int = 30) -> Dict[str, Any]:
    """Genera un informe de KPIs para el período indicado (por defecto último mes)."""
    if not is_postgres_available() or not get_db_connection:
        return _stub_kpi_report(days)

    end = datetime.utcnow()
    start = end - timedelta(days=days)
    period_label = f"{start.date().isoformat()} to {end.date().isoformat()}"

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # cannabis.cannabis_batches: total_batches, certified, avg weight, tiempo hasta certified
            cur.execute("""
                SELECT
                    COUNT(*) AS total_batches,
                    SUM(CASE WHEN status = 'certified' THEN 1 ELSE 0 END) AS certified_batches,
                    AVG(weight_kg) AS avg_yield_kg,
                    AVG(CASE WHEN status = 'certified' AND updated_at IS NOT NULL AND created_at IS NOT NULL
                        THEN EXTRACT(EPOCH FROM (updated_at - created_at)) ELSE NULL END) AS avg_certification_seconds
                FROM cannabis.cannabis_batches
                WHERE created_at >= %s AND created_at <= %s
            """, (start, end))
            row = cur.fetchone()
            total = certified = 0
            avg_yield = 0.0
            avg_cert_hours = None
            certification_rate = 0.0
            if row and (row.get("total_batches") or 0) > 0:
                total = int(row["total_batches"])
                certified = int(row["certified_batches"] or 0)
                avg_yield = float(row["avg_yield_kg"] or 0)
                avg_sec = row.get("avg_certification_seconds")
                avg_cert_hours = (float(avg_sec) / 3600.0) if avg_sec is not None else None
                certification_rate = (certified / total * 100) if total else 0.0
        finally:
            cur.close()
            conn.close()

        return {
            "period": period_label,
            "days": days,
            "kpis": {
                "total_batches": total,
                "certified_batches": certified,
                "certification_rate_pct": round(certification_rate, 2),
                "avg_yield_kg": round(avg_yield, 2),
                "avg_certification_time_hours": round(avg_cert_hours, 2) if avg_cert_hours is not None else None,
            },
        }
    except Exception as e:
        return {
            "period": period_label,
            "days": days,
            "error": str(e),
            "kpis": {},
        }


def _stub_kpi_report(days: int) -> Dict[str, Any]:
    """Respuesta cuando PostgreSQL no está disponible."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    return {
        "period": f"{start.date().isoformat()} to {end.date().isoformat()}",
        "days": days,
        "kpis": {
            "total_batches": 0,
            "certified_batches": 0,
            "certification_rate_pct": 0,
            "avg_yield_kg": 0,
            "avg_certification_time_hours": None,
        },
        "message": "PostgreSQL not configured or unavailable",
    }
