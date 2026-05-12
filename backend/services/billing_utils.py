# -*- coding: utf-8 -*-
"""Email de facturación (SMTP + plantilla Jinja2). Sin WeasyPrint por defecto."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.services.water_ctaex_plans import PUBLIC_PLANS

logger = logging.getLogger(__name__)

_TEMPLATES = Path(__file__).resolve().parents[1] / "templates" / "billing"


def _smtp_config() -> dict[str, str | int] | None:
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USERNAME", "").strip()
    pwd = os.getenv("SMTP_PASSWORD", "").strip()
    if not host or not user:
        return None
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": user,
        "password": pwd,
        "from_email": os.getenv("SMTP_FROM_EMAIL", user),
    }


def _normalize_invoice(inv: dict[str, object]) -> dict[str, object]:
    out = dict(inv)
    pid = out.get("plan_id")
    if isinstance(pid, str) and pid and "plan_name" not in out and pid in PUBLIC_PLANS:
        out["plan_name"] = PUBLIC_PLANS[pid].get("name", pid)
    ac = out.get("amount_cents")
    tc = out.get("total_cents")
    if "amount_eur" not in out and isinstance(ac, int):
        out["amount_eur"] = ac / 100.0
    if "total_eur" not in out and isinstance(tc, int):
        out["total_eur"] = tc / 100.0
    tr = float(out.get("tax_rate", 0.21))
    if "tax_eur" not in out:
        if isinstance(ac, int):
            out["tax_eur"] = (ac / 100.0) * tr
        elif isinstance(out.get("amount_eur"), (int, float)):
            out["tax_eur"] = float(out["amount_eur"]) * tr
    return out


def render_invoice_email_html(invoice: dict[str, object]) -> str:
    if not _TEMPLATES.is_dir():
        return f"<p>Factura {invoice.get('invoice_number')} — configure templates en backend/templates/billing/</p>"
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("invoice_email.html")
    inv = _normalize_invoice(dict(invoice))
    return tpl.render(invoice=inv)


def send_invoice_email(
    invoice: dict[str, object],
    smtp_config: dict[str, str | int] | None = None,
) -> bool:
    """Envía HTML al customer_email de la factura. `smtp_config` opcional (host, port, username, password, from_email)."""
    cfg = smtp_config if smtp_config else _smtp_config()
    if not cfg:
        logger.warning("SMTP no configurado (SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD)")
        return False
    to_email = str(invoice.get("customer_email") or "").strip()
    if not to_email:
        return False
    try:
        inv = _normalize_invoice(dict(invoice))
        html = render_invoice_email_html(inv)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Factura {invoice.get('invoice_number', '')} — CASTÚO-SYSTEM"
        msg["From"] = str(cfg["from_email"])
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(str(cfg["host"]), int(cfg["port"])) as server:
            server.starttls()
            server.login(str(cfg["username"]), str(cfg["password"]))
            server.sendmail(str(cfg["from_email"]), [to_email], msg.as_string())
        return True
    except Exception as e:
        logger.warning("Envío factura fallido: %s", e)
        return False
