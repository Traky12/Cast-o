# -*- coding: utf-8 -*-
"""PaymentGateway: Stripe, Bizum y cripto (PSD2) con registro en GaiaChain."""
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


class PaymentGateway:
    """Crea intents de pago (Stripe/Bizum/Crypto) y registra en GaiaChain."""

    def __init__(self) -> None:
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.gaiachain_cli = _GAIACHAIN_CLI
        if _STRIPE and self.stripe_api_key:
            stripe.api_key = self.stripe_api_key

    def create_payment_intent(self, invoice_data: Dict[str, Any], method: str = "stripe") -> Dict[str, Any]:
        """Crea intento de pago según method: stripe, bizum, crypto."""
        amount_eur = float(invoice_data.get("total", 0))
        if method == "stripe":
            return self._create_stripe_payment(invoice_data, amount_eur)
        if method == "bizum":
            return self._create_bizum_payment(invoice_data, amount_eur)
        if method == "crypto":
            return self._create_crypto_payment(invoice_data, amount_eur)
        return {"status": "error", "reason": "Metodo de pago no soportado"}

    def _create_stripe_payment(self, invoice_data: Dict[str, Any], amount: float) -> Dict[str, Any]:
        if not _STRIPE or not self.stripe_api_key:
            return {"status": "error", "reason": "Stripe no configurado (STRIPE_API_KEY)"}
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency="eur",
                metadata={
                    "factura_id": invoice_data.get("numero_factura", ""),
                    "cliente": (invoice_data.get("cliente") or {}).get("cif_nif", ""),
                },
                description=f"Factura {invoice_data.get('numero_factura', '')}",
            )
            tx_hash = self._register_payment_in_gaiachain({
                "factura_id": invoice_data.get("numero_factura"),
                "metodo": "stripe",
                "payment_intent_id": intent.id,
                "amount": amount,
                "status": "created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return {
                "status": "success",
                "payment_url": intent.client_secret,
                "payment_id": intent.id,
                "gaiachain_tx": tx_hash,
            }
        except Exception as e:
            logger.warning("Stripe PaymentIntent: %s", e)
            return {"status": "error", "reason": str(e)}

    def _create_bizum_payment(self, invoice_data: Dict[str, Any], amount: float) -> Dict[str, Any]:
        bizum_code = f"BZM-{invoice_data.get('numero_factura', '')[-6:]}"
        tx_hash = self._register_payment_in_gaiachain({
            "factura_id": invoice_data.get("numero_factura"),
            "metodo": "bizum",
            "bizum_code": bizum_code,
            "amount": amount,
            "status": "created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "success",
            "bizum_code": bizum_code,
            "instructions": "Envia el pago con Bizum al codigo: " + bizum_code,
            "gaiachain_tx": tx_hash,
        }

    def _create_crypto_payment(self, invoice_data: Dict[str, Any], amount: float) -> Dict[str, Any]:
        crypto_address = "0xCASTUO" + (invoice_data.get("numero_factura", "") or "00000000")[-8:]
        tx_hash = self._register_payment_in_gaiachain({
            "factura_id": invoice_data.get("numero_factura"),
            "metodo": "crypto",
            "crypto_address": crypto_address,
            "amount": amount,
            "currency": "BioCoin",
            "status": "created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "success",
            "crypto_address": crypto_address,
            "network": "GaiaChain",
            "amount": amount,
            "gaiachain_tx": tx_hash,
        }

    def _register_payment_in_gaiachain(self, payment_data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "payment", "--data", json.dumps(payment_data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def confirm_payment(self, payment_id: str, method: str) -> Dict[str, Any]:
        """Confirma un pago y registra en GaiaChain."""
        status = "succeeded"
        if method == "stripe" and _STRIPE and self.stripe_api_key:
            try:
                intent = stripe.PaymentIntent.retrieve(payment_id)
                status = getattr(intent, "status", "succeeded")
            except Exception as e:
                status = "unknown"
                logger.warning("Stripe retrieve: %s", e)
        tx_hash = self._register_payment_in_gaiachain({
            "payment_id": payment_id,
            "method": method,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {"status": status, "gaiachain_tx": tx_hash}
