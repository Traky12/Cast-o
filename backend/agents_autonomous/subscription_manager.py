# -*- coding: utf-8 -*-
"""SubscriptionManager: suscripciones recurrentes con factura, sello eIDAS y GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))


class SubscriptionManager:
    """Gestiona suscripciones recurrentes: crear, consumir análisis, renovar, listar y cancelar."""

    PLANS = {
        "basic": {"price": 99.99, "analyses": 5, "frequency": "monthly", "description": "5 análisis de yield/cannabinoides al mes"},
        "premium": {"price": 299.99, "analyses": 20, "frequency": "monthly", "description": "20 análisis al mes + soporte prioritario"},
        "enterprise": {"price": 999.99, "analyses": "unlimited", "frequency": "monthly", "description": "Análisis ilimitados + datos históricos"},
    }

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI
        from .invoice_bot import InvoiceBot
        try:
            from backend.legal.gaiachain_seal import GaiaChainSeal
            self.gaiachain_seal = GaiaChainSeal()
        except Exception:
            self.gaiachain_seal = None
        self.invoice_bot = InvoiceBot()

    def create_subscription(self, client_data: Dict[str, Any], plan: str) -> Dict[str, Any]:
        """Crea suscripción recurrente: factura proforma, registro en GaiaChain y sello eIDAS."""
        if plan not in self.PLANS:
            return {"status": "error", "reason": "Plan no valido (basic, premium, enterprise)"}
        p = self.PLANS[plan]
        order_data = {
            "cliente": client_data,
            "productos": [{
                "nombre": f"Suscripcion {plan.capitalize()} - CASTUO-SYSTEM",
                "tipo": "servicios_agronomicos",
                "cantidad": 1,
                "precio_unitario": p["price"],
            }],
            "notas": f"Suscripcion automatica renovable {p['frequency']}",
            "tipo": "subscription",
        }
        invoice_result = self.invoice_bot.generate_invoice(order_data)
        if invoice_result.get("status") != "success":
            return invoice_result
        subscription_id = f"SUB-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{client_data.get('cif_nif', '')[-4:]}"
        end_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        remaining = p["analyses"] if p["analyses"] != "unlimited" else 9999
        subscription_data = {
            "subscription_id": subscription_id,
            "client_id": client_data.get("cif_nif"),
            "client_name": client_data.get("nombre"),
            "client_address": client_data.get("direccion", "N/A"),
            "client_email": client_data.get("email", ""),
            "plan": plan,
            "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "end_date": end_date,
            "status": "active",
            "invoice_id": invoice_result["invoice"]["numero_factura"],
            "remaining_analyses": remaining,
            "gaiachain_tx": invoice_result.get("gaiachain_tx", "gaiachain-no-cli"),
            "autorenew": True,
        }
        tx_sub = self._record_gaiachain("subscription", subscription_data)
        subscription_data["gaiachain_tx"] = tx_sub or subscription_data.get("gaiachain_tx")
        eidas_seal = ""
        if self.gaiachain_seal:
            try:
                seal_result = self.gaiachain_seal.generate_qualified_seal({
                    "subscription_id": subscription_id,
                    "client_id": client_data.get("cif_nif"),
                    "plan": plan,
                    "start_date": subscription_data["start_date"],
                    "invoice_id": invoice_result["invoice"]["numero_factura"],
                })
                eidas_seal = seal_result.get("seal", {}).get("hash", "")
            except Exception as e:
                logger.warning("Sello eIDAS suscripcion: %s", e)
        return {
            "status": "success",
            "subscription": subscription_data,
            "invoice": invoice_result["invoice"],
            "pdf_path": invoice_result.get("pdf_path"),
            "gaiachain_tx": subscription_data["gaiachain_tx"],
            "eidas_seal": eidas_seal,
        }

    def consume_analysis(self, subscription_id: str, analysis_type: str = "yield") -> Dict[str, Any]:
        """Consume un análisis de la suscripción (reduce contador; enterprise no reduce)."""
        subscription = self._query_gaiachain("subscription", subscription_id=subscription_id)
        if not subscription:
            return {"status": "error", "reason": "No se encontro la suscripcion"}
        data = subscription.get("data", subscription) if isinstance(subscription, dict) else subscription
        remaining = data.get("remaining_analyses", 0)
        plan = data.get("plan", "basic")
        if plan != "enterprise" and remaining == 0:
            return {"status": "error", "reason": "No quedan analisis disponibles en este plan"}
        if plan != "enterprise":
            remaining = max(0, (remaining if isinstance(remaining, int) else 5) - 1)
        consumption_data = {
            "subscription_id": subscription_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "remaining_analyses": remaining,
        }
        tx = self._record_gaiachain("analysis_consumption", consumption_data)
        return {"status": "success", "subscription_id": subscription_id, "remaining_analyses": remaining, "analysis_type": analysis_type, "gaiachain_tx": tx or "gaiachain-no-cli"}

    def renew_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Renueva suscripción: genera nueva factura y actualiza end_date y remaining."""
        subscription = self._query_gaiachain("subscription", subscription_id=subscription_id)
        if not subscription:
            return {"status": "error", "reason": "No se encontro la suscripcion"}
        data = subscription.get("data", subscription) if isinstance(subscription, dict) else subscription
        client_data = {
            "nombre": data.get("client_name", "Cliente"),
            "cif_nif": data.get("client_id", "N/A"),
            "direccion": data.get("client_address", "N/A"),
            "email": data.get("client_email", "email@desconocido.com"),
        }
        plan = data.get("plan", "basic")
        p = self.PLANS.get(plan, self.PLANS["basic"])
        order_data = {
            "cliente": client_data,
            "productos": [{"nombre": f"Renovacion Suscripcion {plan.capitalize()} - CASTUO-SYSTEM", "tipo": "servicios_agronomicos", "cantidad": 1, "precio_unitario": p["price"]}],
            "notas": f"Renovacion automatica de suscripcion {subscription_id}",
            "tipo": "subscription_renewal",
        }
        invoice_result = self.invoice_bot.generate_invoice(order_data)
        if invoice_result.get("status") != "success":
            return invoice_result
        end_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        remaining = p["analyses"] if p["analyses"] != "unlimited" else 9999
        updated = {**data, "end_date": end_date, "status": "active", "last_renewal_invoice": invoice_result["invoice"]["numero_factura"], "remaining_analyses": remaining, "gaiachain_tx": invoice_result.get("gaiachain_tx")}
        tx = self._record_gaiachain("subscription", updated)
        return {"status": "success", "subscription": updated, "invoice": invoice_result["invoice"], "pdf_path": invoice_result.get("pdf_path"), "gaiachain_tx": tx or invoice_result.get("gaiachain_tx")}

    def list_active_subscriptions(self) -> List[Dict[str, Any]]:
        """Lista suscripciones activas desde GaiaChain (o lista vacía si no hay CLI)."""
        out = self._query_gaiachain_list("subscription", status="active")
        return out if isinstance(out, list) else []

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancela una suscripción (marca status canceled y end_date hoy)."""
        subscription = self._query_gaiachain("subscription", subscription_id=subscription_id)
        if not subscription:
            return {"status": "error", "reason": "No se encontro la suscripcion"}
        data = subscription.get("data", subscription) if isinstance(subscription, dict) else subscription
        data["status"] = "canceled"
        data["end_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        tx = self._record_gaiachain("subscription", data)
        return {"status": "success", "subscription_id": subscription_id, "new_status": "canceled", "gaiachain_tx": tx or "gaiachain-no-cli"}

    def _record_gaiachain(self, record_type: str, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", record_type, "--data", json.dumps(data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain record: %s", e)
            return "gaiachain-no-cli"

    def _query_gaiachain(self, record_type: str, subscription_id: str = "", **kwargs: Any) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return None
        try:
            args = [self.gaiachain_cli, "query", "--type", record_type]
            if subscription_id:
                args.extend(["--subscription_id", subscription_id])
            for k, v in kwargs.items():
                if v is not None:
                    args.extend([f"--{k}", str(v)])
            r = subprocess.run(args, capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception as e:
            logger.warning("GaiaChain query: %s", e)
        return None

    def _query_gaiachain_list(self, record_type: str, status: str = "") -> List[Dict[str, Any]]:
        result = self._query_gaiachain(record_type, **({"status": status} if status else {}))
        if not result:
            return []
        data = result.get("data", result)
        return data if isinstance(data, list) else [data]
