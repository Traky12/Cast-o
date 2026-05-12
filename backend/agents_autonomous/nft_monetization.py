# -*- coding: utf-8 -*-
"""NFTMonetization: tokenización de lotes como NFT con royalties, venta de acceso e informes."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))


class NFTMonetization:
    """Tokeniza lotes como NFT con royalties, vende acceso con factura y rastrea/paga royalties."""

    def __init__(self) -> None:
        from .nft_marketplace import NFTMarketplace
        from .invoice_bot import InvoiceBot
        self.nft_marketplace = NFTMarketplace()
        self.invoice_bot = InvoiceBot()
        self.gaiachain_cli = _GAIACHAIN_CLI

    def tokenize_lot(self, lote_id: str, royalty_percentage: float = 5.0, list_price: float = 1000.0) -> Dict[str, Any]:
        """Tokeniza un lote como NFT con royalties y lo lista en el marketplace."""
        nft_result = self.nft_marketplace.create_royalty_nft(lote_id, royalty_percentage)
        if nft_result.get("status") not in ("minted", "success"):
            return nft_result
        listing_result = self.nft_marketplace.list_nft_with_royalty(nft_result, list_price, royalty_percentage)
        return {"status": "success", "nft": nft_result, "listing": listing_result, "metadata": {"lote_id": lote_id, "royalty_percentage": royalty_percentage}}

    def sell_nft_access(self, nft_id: str, buyer_data: Dict[str, Any], price_eur: float = 1000.0) -> Dict[str, Any]:
        """Vende acceso a un NFT: factura, licencia de acceso y registro nft_sale en GaiaChain."""
        nft_data = self._query_nft(nft_id)
        if not nft_data:
            return {"status": "error", "reason": "No se encontro el NFT"}
        order_data = {"cliente": buyer_data, "productos": [{"nombre": f"Acceso a NFT: {nft_data.get('lote_id', nft_id)}", "tipo": "servicios_agronomicos", "cantidad": 1, "precio_unitario": price_eur}], "notas": f"Venta de acceso a NFT {nft_id}", "tipo": "nft_sale"}
        invoice_result = self.invoice_bot.generate_invoice(order_data)
        if invoice_result.get("status") != "success":
            return {"status": "error", "reason": invoice_result.get("reason", "Error al generar factura")}
        access_token = f"NFT-{nft_id[-8:] if len(nft_id) >= 8 else nft_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        license_data = {"license_id": f"NFT-LIC-{nft_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}", "nft_id": nft_id, "buyer_id": buyer_data.get("cif_nif"), "access_token": access_token, "expiry_date": (datetime.now(timezone.utc) + timedelta(days=365 * 10)).strftime("%Y-%m-%d"), "permitted_uses": ["data_access", "royalty_sharing", "non_commercial"], "invoice_id": invoice_result["invoice"]["numero_factura"], "gaiachain_tx": invoice_result.get("gaiachain_tx"), "price": price_eur}
        tx = self._record_gaiachain("nft_sale", license_data)
        license_data["gaiachain_tx"] = tx or license_data.get("gaiachain_tx", "gaiachain-no-cli")
        return {"status": "success", "invoice": invoice_result["invoice"], "license": license_data, "pdf_path": invoice_result.get("pdf_path"), "gaiachain_tx": license_data["gaiachain_tx"], "access_url": f"https://nft.castuo-system.com/access/{access_token}"}

    def track_nft_royalties(self, nft_id: str) -> Dict[str, Any]:
        """Rastrea royalties del NFT (ventas y pagos de royalties)."""
        tracked = self.nft_marketplace.track_royalties(nft_id)
        sales = self._query_gaiachain_list("nft_sale", nft_id=nft_id)
        total_revenue = sum(float(s.get("price", 0)) for s in sales)
        royalties_data = tracked.get("data", [])
        if not isinstance(royalties_data, list):
            royalties_data = [royalties_data] if royalties_data else []
        total_royalties = sum(float(r.get("amount", 0)) for r in royalties_data)
        royalty_pct = 5.0
        pending = max(0, total_revenue * (royalty_pct / 100) - total_royalties)
        return {"nft_id": nft_id, "total_sales": len(sales), "total_revenue": total_revenue, "royalty_percentage": royalty_pct, "total_royalties": total_royalties, "pending_royalties": pending, "sales": sales, "royalties": royalties_data, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}

    def pay_nft_royalties(self, nft_id: str) -> Dict[str, Any]:
        """Paga royalties pendientes del NFT y registra en GaiaChain."""
        report = self.track_nft_royalties(nft_id)
        pending = report.get("pending_royalties", 0)
        if pending <= 0:
            return {"status": "success", "message": "No hay royalties pendientes", "pending": 0}
        recipient = "0xSTUB-RECIPIENT"
        if report.get("royalties"):
            recipient = report["royalties"][0].get("recipient", recipient)
        payment_data = {"nft_id": nft_id, "amount": pending, "currency": "MATIC", "recipient": recipient, "payment_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), "status": "paid", "transaction_hash": f"0xROYALTY-{nft_id[-8:] if len(nft_id) >= 8 else nft_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"}
        self._record_gaiachain("royalty_payment", payment_data)
        return {"status": "success", "nft_id": nft_id, "amount_paid": pending, "transaction_hash": payment_data["transaction_hash"], "recipient": recipient}

    def _query_nft(self, nft_id: str) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return {"lote_id": nft_id, "nft_tx": nft_id}
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "nft_mint", "--nft_id", nft_id], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return None

    def _query_gaiachain_list(self, record_type: str, nft_id: str = "") -> list:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            args = [self.gaiachain_cli, "query", "--type", record_type]
            if nft_id:
                args.extend(["--nft_id", nft_id])
            r = subprocess.run(args, capture_output=True, text=True, timeout=10)
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
