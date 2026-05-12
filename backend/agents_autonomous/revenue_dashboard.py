# -*- coding: utf-8 -*-
"""RevenueDashboard: ingresos en tiempo real, mensuales y proyección para el dashboard de monetización."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))


class RevenueDashboard:
    """Dashboard de ingresos: últimas 24h, mensual y proyección a N meses."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI

    def get_realtime_revenue(self) -> Dict[str, Any]:
        """Ingresos de las últimas 24h por tipo, facturas, suscripciones activas, ventas datos y NFTs."""
        start = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        invoices = self._query_invoices(start, end)
        revenue_by_type: Dict[str, float] = {}
        total_revenue = 0.0
        for inv in invoices:
            data = inv.get("data", inv) if isinstance(inv, dict) else inv
            productos = data.get("productos", [])
            pt = productos[0].get("tipo", "unknown") if productos else "unknown"
            amount = float(data.get("total", 0))
            revenue_by_type[pt] = revenue_by_type.get(pt, 0) + amount
            total_revenue += amount
        active_subs = len(self._query_list("subscription", status="active"))
        data_sales = len(self._query_list("data_sale", start=start, end=end))
        nft_sales = len(self._query_list("nft_sale", start=start, end=end))
        return {"status": "success", "period": "last_24h", "total_revenue": total_revenue, "revenue_by_type": revenue_by_type, "invoice_count": len(invoices), "active_subscriptions": active_subs, "data_sales": data_sales, "nft_sales": nft_sales, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}

    def get_monthly_revenue(self, month: int, year: int) -> Dict[str, Any]:
        """Ingresos del mes: total, por tipo, facturas, suscripciones y ventas datos/NFTs."""
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-31"
        invoices = self._query_invoices(start, end)
        revenue_by_type = {}
        total_revenue = 0.0
        for inv in invoices:
            data = inv.get("data", inv) if isinstance(inv, dict) else inv
            productos = data.get("productos", [])
            pt = productos[0].get("tipo", "unknown") if productos else "unknown"
            amount = float(data.get("total", 0))
            revenue_by_type[pt] = revenue_by_type.get(pt, 0) + amount
            total_revenue += amount
        subs = self._query_list("subscription", start=start, end=end)
        active_subs = len([s for s in subs if (s.get("data", s) or s).get("status") == "active"])
        new_subs = len([s for s in subs if (s.get("data", s) or s).get("start_date", "").startswith(f"{year}-{month:02d}")])
        data_sales = len(self._query_list("data_sale", start=start, end=end))
        nft_sales = len(self._query_list("nft_sale", start=start, end=end))
        return {"status": "success", "month": month, "year": year, "total_revenue": total_revenue, "revenue_by_type": revenue_by_type, "invoice_count": len(invoices), "active_subscriptions": active_subs, "new_subscriptions": new_subs, "data_sales": data_sales, "nft_sales": nft_sales, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}

    def get_revenue_projection(self, months: int = 6) -> Dict[str, Any]:
        """Proyección de ingresos para los próximos meses basada en informes mensuales históricos."""
        historical: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        for i in range(1, 7):
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            report = self._query_monthly_report(m, y)
            if report:
                historical.append({"month": m, "year": y, "revenue": report.get("total_revenue", 0), "invoices": report.get("invoices_count", 0)})
        avg_revenue = sum(h["revenue"] for h in historical) / len(historical) if historical else 0.0
        projection = []
        for i in range(1, months + 1):
            m = now.month + i
            y = now.year
            while m > 12:
                m -= 12
                y += 1
            projection.append({"month": m, "year": y, "projected_revenue": round(avg_revenue, 2)})
        return {"status": "success", "historical": historical, "average_monthly_revenue": round(avg_revenue, 2), "projection": projection, "generated_at": now.strftime("%Y-%m-%d %H:%M:%S")}

    def _query_invoices(self, start: str, end: str) -> list:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "invoice", "--start", start, "--end", end], capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out if isinstance(out, list) else [out]
        except Exception as e:
            logger.warning("GaiaChain query invoices: %s", e)
        return []

    def _query_list(self, record_type: str, status: str = "", start: str = "", end: str = "") -> list:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            args = [self.gaiachain_cli, "query", "--type", record_type]
            if status:
                args.extend(["--status", status])
            if start:
                args.extend(["--start", start])
            if end:
                args.extend(["--end", end])
            r = subprocess.run(args, capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                data = out.get("data", out)
                return data if isinstance(data, list) else [data]
        except Exception:
            pass
        return []

    def _query_monthly_report(self, month: int, year: int) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return None
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "monthly_revenue_report", "--month", str(month), "--year", str(year)], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return None
