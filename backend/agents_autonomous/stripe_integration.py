# -*- coding: utf-8 -*-
"""StripeIntegration: productos, enlaces de pago y webhooks con registro en GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))

try:
    import stripe
    _STRIPE = True
except ImportError:
    stripe = None
    _STRIPE = False


class StripeIntegration:
    """Crea productos y enlaces de pago en Stripe; registra en GaiaChain."""

    def __init__(self) -> None:
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.gaiachain_cli = _GAIACHAIN_CLI
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if _STRIPE and self.stripe_api_key:
            stripe.api_key = self.stripe_api_key

    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea producto y precio en Stripe; registra en GaiaChain."""
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado (STRIPE_API_KEY)"}
        try:
            product = stripe.Product.create(
                name=product_data.get("nombre", ""),
                description=product_data.get("descripcion", ""),
                metadata={"normativas": json.dumps(product_data.get("normativas", ["GDPR", "AI_Act_2024"]))},
            )
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(float(product_data.get("precio", 0)) * 100),
                currency="eur",
                metadata={"iva_type": product_data.get("iva_type", "standard"), "jurisdiction": product_data.get("jurisdiction", "ES")},
            )
            tx_hash = self._register_in_gaiachain("stripe_product", {
                "product_id": product.id, "price_id": price.id,
                "nombre": product_data.get("nombre"), "precio": product_data.get("precio"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            if tx_hash and not tx_hash.startswith("Error"):
                stripe.Product.modify(product.id, metadata={"gaiachain_tx": tx_hash})
            return {"status": "success", "product_id": product.id, "price_id": price.id, "gaiachain_tx": tx_hash or "gaiachain-no-cli"}
        except Exception as e:
            logger.warning("Stripe product: %s", e)
            return {"status": "error", "reason": str(e)}

    def create_payment_link(self, price_id: str, client_email: str = "") -> Dict[str, Any]:
        """Crea enlace de pago en Stripe; registra en GaiaChain."""
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado"}
        try:
            link = stripe.PaymentLink.create(
                line_items=[{"price": price_id, "quantity": 1}],
                payment_intent_data={"metadata": {"client_email": client_email, "timestamp": datetime.now(timezone.utc).isoformat()}},
            )
            tx_hash = self._register_in_gaiachain("stripe_payment_link", {
                "payment_link_id": link.id, "price_id": price_id, "client_email": client_email, "url": link.url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {"status": "success", "payment_url": link.url, "gaiachain_tx": tx_hash or "gaiachain-no-cli"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Procesa webhook de Stripe (pago completado/fallido)."""
        if not _STRIPE or not self.webhook_secret:
            return {"status": "error", "reason": "STRIPE_WEBHOOK_SECRET no configurado"}
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        except Exception as e:
            return {"status": "error", "reason": str(e)}
        if event.type == "payment_intent.succeeded":
            pi = event.data.object
            tx_hash = self._register_in_gaiachain("stripe_payment", {
                "payment_intent_id": pi.id, "amount": getattr(pi, "amount", 0) / 100, "status": "succeeded",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {"status": "success", "event_type": event.type, "gaiachain_tx": tx_hash}
        if event.type == "payment_intent.payment_failed":
            pi = event.data.object
            tx_hash = self._register_in_gaiachain("stripe_payment", {
                "payment_intent_id": pi.id, "status": "failed", "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {"status": "failed", "event_type": event.type, "gaiachain_tx": tx_hash}
        return {"status": "ignored", "event_type": event.type}

    def create_subscription_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea plan de suscripcion en Stripe (producto + precio recurrente) y registra en GaiaChain."""
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado"}
        try:
            product = stripe.Product.create(
                name=plan_data.get("name", ""),
                description=plan_data.get("description", ""),
                metadata={"type": "subscription_plan", "gaiachain_tx": "pendiente"},
            )
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(float(plan_data.get("price", 0)) * 100),
                currency="eur",
                recurring={"interval": plan_data.get("interval", "month"), "interval_count": plan_data.get("interval_count", 1)},
                metadata={"gaiachain_tx": "pendiente", "plan_type": plan_data.get("type", "standard")},
            )
            gaia_tx = self._register_subscription_plan({"plan_id": price.id, "product_id": product.id, "name": plan_data.get("name"), "price": plan_data.get("price"), "interval": plan_data.get("interval", "month"), "timestamp": datetime.now(timezone.utc).isoformat()})
            if gaia_tx and not gaia_tx.startswith("Error"):
                stripe.Product.modify(product.id, metadata={"gaiachain_tx": gaia_tx})
                stripe.Price.modify(price.id, metadata={"gaiachain_tx": gaia_tx})
            return {"status": "success", "plan_id": price.id, "product_id": product.id, "gaiachain_tx": gaia_tx or "gaiachain-no-cli"}
        except stripe.error.StripeError as e:
            return {"status": "error", "reason": str(e)}

    def create_customer_subscription(self, customer_email: str, price_id: str) -> Dict[str, Any]:
        """Crea suscripcion para un cliente en Stripe y registra en GaiaChain."""
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado"}
        try:
            customers = stripe.Customer.list(email=customer_email)
            customer = customers.data[0] if customers.data else stripe.Customer.create(email=customer_email, metadata={"gaiachain_tx": "pendiente"})
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price_id}],
                metadata={"gaiachain_tx": "pendiente", "customer_email": customer_email},
            )
            gaia_tx = self._register_customer_subscription({"subscription_id": subscription.id, "customer_id": customer.id, "price_id": price_id, "status": subscription.status, "current_period_end": subscription.current_period_end, "timestamp": datetime.now(timezone.utc).isoformat()})
            if gaia_tx and not gaia_tx.startswith("Error"):
                stripe.Subscription.modify(subscription.id, metadata={"gaiachain_tx": gaia_tx})
            invoice_url = getattr(subscription.latest_invoice, "invoice_pdf", None) or (subscription.latest_invoice if hasattr(subscription.latest_invoice, "invoice_pdf") else "")
            if hasattr(invoice_url, "invoice_pdf"):
                invoice_url = invoice_url.invoice_pdf if invoice_url else ""
            return {"status": "success", "subscription_id": subscription.id, "customer_id": customer.id, "gaiachain_tx": gaia_tx or "gaiachain-no-cli", "invoice_url": invoice_url or ""}
        except stripe.error.StripeError as e:
            return {"status": "error", "reason": str(e)}

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancela una suscripcion en Stripe y registra en GaiaChain."""
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado"}
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            original_tx = subscription.metadata.get("gaiachain_tx", "N/A")
            stripe.Subscription.delete(subscription_id)
            gaia_tx = self._register_subscription_cancelation({"subscription_id": subscription_id, "status": "canceled", "cancelation_date": datetime.now(timezone.utc).isoformat(), "original_gaiachain_tx": original_tx})
            return {"status": "success", "subscription_id": subscription_id, "gaiachain_tx": gaia_tx or "gaiachain-no-cli", "cancelation_date": datetime.now(timezone.utc).isoformat()}
        except stripe.error.StripeError as e:
            return {"status": "error", "reason": str(e)}

    def list_subscriptions(self, status: str = "active") -> Dict[str, Any]:
        """Lista suscripciones en Stripe (active, canceled, all)."""
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado"}
        try:
            kwargs = {} if status == "all" else {"status": status}
            subs = stripe.Subscription.list(**kwargs)
            items = [{"id": s.id, "customer": s.customer, "status": s.status, "current_period_end": s.current_period_end, "gaiachain_tx": s.metadata.get("gaiachain_tx", "N/A")} for s in subs.auto_paging_iter()]
            return {"status": "success", "subscriptions": items, "count": len(items)}
        except stripe.error.StripeError as e:
            return {"status": "error", "reason": str(e)}

    def _register_subscription_plan(self, plan_data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "stripe_subscription_plan", "--data", json.dumps(plan_data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def _register_customer_subscription(self, subscription_data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "stripe_customer_subscription", "--data", json.dumps(subscription_data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def _register_subscription_cancelation(self, cancelation_data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "stripe_subscription_cancelation", "--data", json.dumps(cancelation_data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def _register_in_gaiachain(self, record_type: str, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", record_type, "--data", json.dumps(data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"
