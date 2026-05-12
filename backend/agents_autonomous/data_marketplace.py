# -*- coding: utf-8 -*-
"""DataMarketplace: publicación y venta de productos de datos agronómicos con factura y sello eIDAS."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))

DATA_PRODUCTS = {
    "yield_data": {"name": "Dataset de Yield Optimizado", "description": "Datos de humedad, temperatura, luz y recomendaciones de IA.", "price": 199.99, "sample_data": {"metrics": ["humedad", "temperatura", "luz_par", "co2"], "frequency": "cada 5 min", "ai_analysis": True}},
    "cannabinoid_data": {"name": "Perfil Completo de Cannabinoides", "description": "THC, CBD, CBG y terpenos HPLC; trazabilidad AEMPS.", "price": 299.99, "sample_data": {"compounds": ["THC", "CBD", "CBG"], "method": "HPLC", "compliance": "RD 903/2025"}},
    "climate_data": {"name": "Dataset Climatico para Modelos Predictivos", "description": "Datos historicos clima para entrenar modelos de IA.", "price": 99.99, "sample_data": {"metrics": ["temperatura", "humedad", "presion"], "frequency": "cada 10 min"}},
}


class DataMarketplace:
    """Publica productos de datos, vende acceso con factura y licencia, listado e informe de royalties."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI
        from .invoice_bot import InvoiceBot
        try:
            from backend.legal.gaiachain_seal import GaiaChainSeal
            self.gaiachain_seal = GaiaChainSeal()
        except Exception:
            self.gaiachain_seal = None
        self.invoice_bot = InvoiceBot()

    def publish_data_product(self, lote_id: str, product_type: str) -> Dict[str, Any]:
        """Publica producto de datos: obtiene lote (GaiaChain o stub), registra y sella eIDAS."""
        if product_type not in DATA_PRODUCTS:
            return {"status": "error", "reason": "Tipo no valido (yield_data, cannabinoid_data, climate_data)"}
        harvest_data = self._query_harvest(lote_id)
        pt = DATA_PRODUCTS[product_type]
        product_id = f"DATA-{lote_id}-{product_type.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        product_data = {
            **pt,
            "lote_id": lote_id,
            "product_id": product_id,
            "creation_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status": "available",
            "sample_data": {**pt.get("sample_data", {}), "lote_details": {"producto": harvest_data.get("producto", "N/A"), "fecha_cosecha": harvest_data.get("fecha_cosecha", "N/A"), "peso_neto": harvest_data.get("peso_neto", "N/A")}},
        }
        tx = self._record_gaiachain("data_product", product_data)
        product_data["gaiachain_tx"] = tx or "gaiachain-no-cli"
        eidas_seal = ""
        if self.gaiachain_seal:
            try:
                seal_result = self.gaiachain_seal.generate_qualified_seal({"product_id": product_id, "lote_id": lote_id, "product_type": product_type, "creation_date": product_data["creation_date"]})
                eidas_seal = seal_result.get("seal", {}).get("hash", "")
            except Exception as e:
                logger.warning("Sello eIDAS data product: %s", e)
        return {"status": "success", "product": product_data, "gaiachain_tx": product_data["gaiachain_tx"], "eidas_seal": eidas_seal, "marketplace_url": f"https://data.castuo-system.com/products/{product_id}"}

    def sell_data_access(self, product_id: str, buyer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Vende acceso: consulta producto, genera factura, licencia de acceso y registra data_sale."""
        product = self._query_product(product_id)
        if not product:
            return {"status": "error", "reason": "No se encontro el producto"}
        price = product.get("price", 199.99)
        name = product.get("name", "Acceso datos")
        order_data = {"cliente": buyer_data, "productos": [{"nombre": name, "tipo": "servicios_agronomicos", "cantidad": 1, "precio_unitario": price}], "notas": f"Venta de acceso a datos: {product_id}", "tipo": "data_sale"}
        invoice_result = self.invoice_bot.generate_invoice(order_data)
        if invoice_result.get("status") != "success":
            return {"status": "error", "reason": invoice_result.get("reason", "Error al generar factura")}
        access_token = f"DATA-{product_id[-8:] if len(product_id) >= 8 else product_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        license_data = {"license_id": f"LIC-{product_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}", "product_id": product_id, "buyer_id": buyer_data.get("cif_nif"), "access_token": access_token, "expiry_date": (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d"), "permitted_uses": ["analysis", "research", "non_commercial"], "invoice_id": invoice_result["invoice"]["numero_factura"], "gaiachain_tx": invoice_result.get("gaiachain_tx"), "price": price}
        tx = self._record_gaiachain("data_sale", license_data)
        license_data["gaiachain_tx"] = tx or license_data.get("gaiachain_tx", "gaiachain-no-cli")
        return {"status": "success", "invoice": invoice_result["invoice"], "license": license_data, "pdf_path": invoice_result.get("pdf_path"), "gaiachain_tx": license_data["gaiachain_tx"], "access_url": f"https://data.castuo-system.com/access/{access_token}"}

    def list_data_products(self, status: str = "available") -> List[Dict[str, Any]]:
        """Lista productos de datos desde GaiaChain (o lista vacía)."""
        result = self._query_gaiachain("data_product", status=status)
        if not result:
            return []
        data = result.get("data", result)
        return data if isinstance(data, list) else [data]

    def generate_royalty_report(self, product_id: str, royalty_pct: float = 5.0) -> Dict[str, Any]:
        """Genera informe de royalties para un producto (ventas y 5% por venta)."""
        sales = self._query_sales(product_id)
        total_revenue = sum(float(s.get("price", 0)) for s in sales)
        royalties = total_revenue * (royalty_pct / 100)
        report = {"product_id": product_id, "total_sales": len(sales), "total_revenue": total_revenue, "royalties": royalties, "royalty_pct": royalty_pct, "sales": sales, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
        self._record_gaiachain("royalty_report", report)
        return report

    def _query_harvest(self, lote_id: str) -> Dict[str, Any]:
        if not os.path.isfile(self.gaiachain_cli):
            return {"producto": "Cultivo", "fecha_cosecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "peso_neto": "N/A"}
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "harvest", "--lote_id", lote_id], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return {"producto": "Cultivo", "fecha_cosecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "peso_neto": "N/A"}

    def _query_product(self, product_id: str) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return {"name": "Datos de yield", "price": 199.99, "product_id": product_id}
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "data_product", "--product_id", product_id], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return None

    def _query_sales(self, product_id: str) -> List[Dict[str, Any]]:
        if not os.path.isfile(self.gaiachain_cli):
            return []
        try:
            r = subprocess.run([self.gaiachain_cli, "query", "--type", "data_sale", "--product_id", product_id], capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                data = out.get("data", out)
                return data if isinstance(data, list) else [data]
        except Exception:
            pass
        return []

    def _query_gaiachain(self, record_type: str, **kwargs: Any) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return None
        try:
            args = [self.gaiachain_cli, "query", "--type", record_type]
            for k, v in kwargs.items():
                if v is not None:
                    args.extend([f"--{k}", str(v)])
            r = subprocess.run(args, capture_output=True, text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout)
        except Exception as e:
            logger.warning("GaiaChain query: %s", e)
        return None

    def _record_gaiachain(self, record_type: str, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run([self.gaiachain_cli, "record", "--type", record_type, "--data", json.dumps(data)], capture_output=True, text=True, timeout=10)
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain record: %s", e)
            return "gaiachain-no-cli"
