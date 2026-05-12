# -*- coding: utf-8 -*-
"""AutomaticBilling: facturación recurrente, informes de ingresos y declaraciones AEAT automáticas."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))


class AutomaticBilling:
    """Procesa facturación recurrente, informes mensuales, declaraciones 303/390 y pagos pendientes."""

    def __init__(self) -> None:
        from .invoice_bot import InvoiceBot
        from .subscription_manager import SubscriptionManager
        from .aeat_bot import AEATBot
        self.invoice_bot = InvoiceBot()
        self.subscription_manager = SubscriptionManager()
        self.aeat_bot = AEATBot()
        self.gaiachain_cli = _GAIACHAIN_CLI

    def process_recurring_billing(self) -> Dict[str, Any]:
        """Renueva suscripciones activas cuya end_date ya pasó."""
        subscriptions = self.subscription_manager.list_active_subscriptions()
        processed = renewed = errors = 0
        for sub in subscriptions:
            try:
                data = sub.get("data", sub) if isinstance(sub, dict) else sub
                sub_id = data.get("subscription_id") or sub.get("subscription_id")
                if not sub_id:
                    continue
                end_date = data.get("end_date") or sub.get("end_date", "")
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except Exception:
                    end_dt = datetime.now(timezone.utc)
                if datetime.now(timezone.utc).date() >= end_dt.date():
                    self.subscription_manager.renew_subscription(sub_id)
                    renewed += 1
                processed += 1
            except Exception as e:
                logger.warning("Procesar suscripcion: %s", e)
                errors += 1
        return {"status": "success", "processed": processed, "renewed": renewed, "errors": errors, "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}

    def generate_monthly_revenue_report(self, month: int, year: int) -> Dict[str, Any]:
        """Informe de ingresos mensuales desde facturas en GaiaChain."""
        invoices = self._query_invoices(month, year)
        revenue_by_type: Dict[str, float] = {}
        total_revenue = 0.0
        for inv in invoices:
            data = inv.get("data", inv) if isinstance(inv, dict) else inv
            productos = data.get("productos", [])
            product_type = productos[0].get("tipo", "unknown") if productos else "unknown"
            amount = float(data.get("total", 0))
            revenue_by_type[product_type] = revenue_by_type.get(product_type, 0) + amount
            total_revenue += amount
        report = {"month": month, "year": year, "total_revenue": total_revenue, "revenue_by_type": revenue_by_type, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "invoices_count": len(invoices)}
        self._record_gaiachain("monthly_revenue_report", report)
        return report

    def generate_automatic_declarations(self) -> Dict[str, Any]:
        """Genera declaración 303 del mes y, si es diciembre, resumen anual 390; simula envío AEAT."""
        now = datetime.now(timezone.utc)
        month, year = now.month, now.year
        model_303 = self.aeat_bot.generate_iva_declaration(month, year)
        submission_303 = self.aeat_bot.submit_to_aeat(model_303.get("xml_path", ""))
        model_390 = None
        submission_390 = None
        if month == 12:
            model_390 = self.aeat_bot.generate_annual_summary(year)
            submission_390 = self.aeat_bot.submit_annual_summary(model_390.get("xml_path", ""))
        return {"status": "success", "model_303": {"generated": True, "xml_path": model_303.get("xml_path"), "gaiachain_tx": model_303.get("gaiachain_tx"), "submission": submission_303}, "model_390": {"generated": model_390 is not None, "xml_path": model_390.get("xml_path") if model_390 else None, "gaiachain_tx": model_390.get("gaiachain_tx") if model_390 else None, "submission": submission_390}, "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")}

    def process_pending_payments(self) -> Dict[str, Any]:
        """Consulta pagos pendientes en GaiaChain y simula confirmación (stub si no hay tipo payment)."""
        pending = self._query_payments("pending")
        processed = confirmed = 0
        for payment in pending:
            try:
                data = payment.get("data", payment) if isinstance(payment, dict) else payment
                if data.get("invoice_id") is None and data.get("amount"):
                    client = {"nombre": data.get("client_name", "Cliente"), "cif_nif": data.get("client_id", "N/A"), "direccion": data.get("client_address", "N/A"), "email": data.get("client_email", "noreply@castuo-system.com")}
                    self.invoice_bot.generate_invoice({"cliente": client, "productos": [{"nombre": data.get("product_name", "Pago"), "tipo": "servicios_agronomicos", "cantidad": 1, "precio_unitario": data.get("amount", 0)}], "notas": f"Pago confirmado (ID: {data.get('payment_id', '')})", "tipo": "payment_confirmation"})
                confirmed += 1
                processed += 1
            except Exception as e:
                logger.warning("Procesar pago: %s", e)
                processed += 1
        return {"status": "success", "processed": processed, "confirmed": confirmed, "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}

    def _query_invoices(self, month: int, year: int) -> list:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "invoice", "--start", f"{year}-{month:02d}-01", "--end", f"{year}-{month:02d}-31"], capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out if isinstance(out, list) else [out]
        except Exception:
            pass
        return []

    def _query_payments(self, status: str) -> list:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "payment", "--status", status], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                data = out.get("data", out)
                return data if isinstance(data, list) else [data]
        except Exception:
            pass
        return []

    def _record_gaiachain(self, record_type: str, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run([self.gaiachain_cli, "record", "--type", record_type, "--data", json.dumps(data)], capture_output=True, text=True, timeout=10)
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain record: %s", e)
            return "gaiachain-no-cli"
