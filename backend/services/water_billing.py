# -*- coding: utf-8 -*-
"""Facturación y clientes (SQLite) para agua CTAEX — indexado por hash de API key, nunca clave en claro."""

from __future__ import annotations

import calendar
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.services.water_ctaex_plans import (
    PUBLIC_PLANS,
    connection,
    db_path,
    hash_api_key,
)

logger = logging.getLogger(__name__)


def register_billing_customer(
    *,
    api_key: str,
    plan_id: str,
    customer_name: str,
    customer_email: str,
) -> dict[str, Any]:
    if plan_id not in PUBLIC_PLANS:
        raise ValueError("invalid_plan")
    kh = hash_api_key(api_key)
    ts = datetime.now(timezone.utc).isoformat()
    conn = connection()
    try:
        conn.execute(
            """
            INSERT INTO billing_customers
            (key_hash, plan_id, customer_name, customer_email, payment_status, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
            ON CONFLICT(key_hash) DO UPDATE SET
                plan_id = excluded.plan_id,
                customer_name = excluded.customer_name,
                customer_email = excluded.customer_email,
                updated_at = excluded.updated_at
            """,
            (kh, plan_id, customer_name.strip(), customer_email.strip(), ts),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "key_hash": kh,
        "plan_id": plan_id,
        "customer_name": customer_name.strip(),
        "customer_email": customer_email.strip(),
    }


def count_requests_in_period(key_hash: str, period_yyyymm: str) -> int:
    conn = connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM usage_logs WHERE key_hash = ? AND period = ?",
            (key_hash, period_yyyymm),
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def generate_invoices_for_month(year: int, month: int) -> list[dict[str, Any]]:
    """Borradores de factura por cliente registrado (planes de pago fijo en EUR)."""
    if month < 1 or month > 12:
        raise ValueError("invalid_month")
    period_yyyymm = f"{year}{month:02d}"
    start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end = f"{year}-{month:02d}-{last_day:02d}"

    out: list[dict[str, Any]] = []
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        customers = conn.execute("SELECT * FROM billing_customers").fetchall()
        for row in customers:
            c = dict(row)
            pid = c["plan_id"]
            cfg = PUBLIC_PLANS.get(pid)
            if not cfg:
                continue
            price = cfg.get("price_eur_month")
            if price is None or not isinstance(price, (int, float)) or int(price) <= 0:
                continue
            kh = c["key_hash"]
            req_n = count_requests_in_period(kh, period_yyyymm)
            amount_cents = int(price) * 100
            tax_rate = 0.21
            total_cents = int(round(amount_cents * (1 + tax_rate)))
            inv_no = f"INV-{period_yyyymm}-{kh[:8]}"
            now = datetime.now(timezone.utc).isoformat()
            due = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            try:
                conn.execute(
                    """
                    INSERT INTO invoices
                    (invoice_number, key_hash, plan_id, customer_name, customer_email,
                     period_yyyymm, period_start, period_end, amount_cents, tax_rate, total_cents,
                     status, created_at, due_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    """,
                    (
                        inv_no,
                        kh,
                        pid,
                        c["customer_name"],
                        c["customer_email"],
                        period_yyyymm,
                        start,
                        end,
                        amount_cents,
                        tax_rate,
                        total_cents,
                        now,
                        due,
                    ),
                )
                conn.commit()
                out.append(
                    {
                        "invoice_number": inv_no,
                        "key_hash": kh,
                        "plan_id": pid,
                        "plan_name": cfg.get("name", pid),
                        "customer_name": c["customer_name"],
                        "customer_email": c["customer_email"],
                        "period_yyyymm": period_yyyymm,
                        "period_start": start,
                        "period_end": end,
                        "due_date": due,
                        "requests_in_period": req_n,
                        "amount_cents": amount_cents,
                        "tax_rate": tax_rate,
                        "total_cents": total_cents,
                        "amount_eur": amount_cents / 100.0,
                        "total_eur": total_cents / 100.0,
                        "status": "draft",
                    }
                )
            except sqlite3.IntegrityError:
                conn.rollback()
                logger.info("Factura ya existía: %s %s", inv_no, period_yyyymm)
    finally:
        conn.close()
    return out


def list_invoices(
    *,
    status: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 2000))
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute(
                """
                SELECT * FROM invoices WHERE status = ?
                ORDER BY id DESC LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM invoices ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_overdue_invoices(*, min_days_overdue: int = 0) -> list[dict[str, Any]]:
    """Facturas no pagadas con vencimiento pasado; opcionalmente solo las llevan ≥ N días vencidas (SQLite)."""
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        if min_days_overdue <= 0:
            rows = conn.execute(
                """
                SELECT * FROM invoices
                WHERE status NOT IN ('paid', 'cancelled')
                AND due_date < ?
                ORDER BY due_date ASC
                """,
                (now,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM invoices
                WHERE status NOT IN ('paid', 'cancelled')
                AND due_date < ?
                AND (julianday('now') - julianday(due_date)) >= ?
                ORDER BY due_date ASC
                """,
                (now, float(min_days_overdue)),
            ).fetchall()
        return [_enrich_invoice_row(dict(r)) for r in rows]
    finally:
        conn.close()


def _enrich_invoice_row(d: dict[str, Any]) -> dict[str, Any]:
    kh = d.get("key_hash")
    per = d.get("period_yyyymm")
    if isinstance(kh, str) and isinstance(per, str):
        d["requests_in_period"] = count_requests_in_period(kh, per)
    return d


def get_invoice_by_number(invoice_number: str) -> dict[str, Any] | None:
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM invoices WHERE invoice_number = ?",
            (invoice_number.strip(),),
        ).fetchone()
        return _enrich_invoice_row(dict(row)) if row else None
    finally:
        conn.close()


def list_invoices_for_period_yyyymm(period_yyyymm: str) -> list[dict[str, Any]]:
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM invoices WHERE period_yyyymm = ?
            ORDER BY id ASC
            """,
            (period_yyyymm,),
        ).fetchall()
        return [_enrich_invoice_row(dict(r)) for r in rows]
    finally:
        conn.close()


def _plans_aggregate_from_customers() -> list[dict[str, Any]]:
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT plan_id FROM billing_customers").fetchall()
    finally:
        conn.close()
    by_pid: dict[str, dict[str, Any]] = {}
    for row in rows:
        pid = row["plan_id"]
        cfg = PUBLIC_PLANS.get(pid)
        if not cfg:
            continue
        if pid not in by_pid:
            by_pid[pid] = {
                "plan_id": pid,
                "plan_name": cfg.get("name", pid),
                "customer_count": 0,
                "total_monthly_eur": 0.0,
            }
        by_pid[pid]["customer_count"] += 1
        p = cfg.get("price_eur_month")
        if isinstance(p, (int, float)) and p > 0:
            by_pid[pid]["total_monthly_eur"] += float(p)
    return list(by_pid.values())


def monthly_billing_summary(year: int, month: int) -> dict[str, Any]:
    """Resumen operativo: clientes, agregado por plan (desde PUBLIC_PLANS), totales de facturas del mes."""
    if month < 1 or month > 12:
        raise ValueError("invalid_month")
    period_yyyymm = f"{year}{month:02d}"
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT b.key_hash, b.plan_id, b.customer_name, b.customer_email, b.payment_status
            FROM billing_customers b
            """,
        ).fetchall()
        customers: list[dict[str, Any]] = []
        for row in rows:
            d = dict(row)
            cfg = PUBLIC_PLANS.get(d["plan_id"], {})
            d["plan_name"] = cfg.get("name", d["plan_id"])
            d["requests_in_period"] = count_requests_in_period(d["key_hash"], period_yyyymm)
            d["period_yyyymm"] = period_yyyymm
            customers.append(d)
    finally:
        conn.close()

    conn_inv = connection()
    try:
        cnt_total = conn_inv.execute(
            """
            SELECT COUNT(*) AS c, COALESCE(SUM(total_cents), 0) AS t
            FROM invoices WHERE period_yyyymm = ?
            """,
            (period_yyyymm,),
        ).fetchone()
        inv_count = int(cnt_total[0]) if cnt_total else 0
        total_cents = int(cnt_total[1]) if cnt_total and cnt_total[1] is not None else 0
    finally:
        conn_inv.close()

    return {
        "period": f"{year}-{month:02d}",
        "period_yyyymm": period_yyyymm,
        "customers": customers,
        "plans": _plans_aggregate_from_customers(),
        "invoices": {
            "count": inv_count,
            "total_eur": round(total_cents / 100.0, 2),
        },
    }


def list_usage_logs_for_period(
    period_yyyymm: str,
    *,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 20000))
    conn = connection()
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, key_hash, plan_id, period, request_timestamp, endpoint,
                   input_summary, http_status
            FROM usage_logs
            WHERE period = ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (period_yyyymm, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_invoices_by_period(year: int, month: int) -> list[dict[str, Any]]:
    if month < 1 or month > 12:
        raise ValueError("invalid_month")
    return list_invoices_for_period_yyyymm(f"{year}{month:02d}")


def generate_certification_report(year: int, month: int) -> dict[str, Any]:
    """Informe agregado para revisión interna (SQLite + PUBLIC_PLANS; sin tabla SQL `plans`)."""
    if month < 1 or month > 12:
        raise ValueError("invalid_month")
    period_yyyymm = f"{year}{month:02d}"
    invoices = list_invoices_for_period_yyyymm(period_yyyymm)
    inv_out: list[dict[str, Any]] = []
    total_cents = 0
    for inv in invoices:
        d = dict(inv)
        tc = int(d.get("total_cents") or 0)
        total_cents += tc
        d["total_eur"] = round(tc / 100.0, 2)
        ac = int(d.get("amount_cents") or 0)
        d["amount_eur"] = round(ac / 100.0, 2)
        pid = d.get("plan_id")
        if pid and "plan_name" not in d and isinstance(pid, str) and pid in PUBLIC_PLANS:
            d["plan_name"] = PUBLIC_PLANS[pid].get("name", pid)
        inv_out.append(d)
    summary = monthly_billing_summary(year, month)
    logs = list_usage_logs_for_period(period_yyyymm, limit=10000)
    return {
        "certification": {
            "period": f"{year}-{month:02d}",
            "period_yyyymm": period_yyyymm,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "system": "CASTÚO-SYSTEM",
            "water_ctaex_version": "1.7",
            "database": str(db_path()),
        },
        "summary": {
            "plans": summary["plans"],
            "billing_customers": summary["customers"],
            "invoices_count": summary["invoices"]["count"],
            "invoices_total_eur": summary["invoices"]["total_eur"],
            "usage_log_rows_in_period": len(logs),
            "total_revenue_cents": total_cents,
            "total_revenue_eur": round(total_cents / 100.0, 2),
        },
        "invoices": inv_out,
        "usage_logs_sample": logs[:500],
        "signature_note": "Informe operativo desde SQLite; no sustituye auditoría fiscal ni legal externa.",
    }
