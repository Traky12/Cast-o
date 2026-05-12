# -*- coding: utf-8 -*-
"""MarketBot: publicar servicios en Fiverr/Upwork y procesar pedidos con trazabilidad GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))

try:
    import requests
    _REQUESTS = True
except ImportError:
    requests = None
    _REQUESTS = False


class MarketBot:
    """Publica servicios en mercados (Fiverr/Upwork) y procesa pedidos con validación LexCheck."""

    def __init__(self) -> None:
        self.fiverr_api_key = os.getenv("FIVERR_API_KEY")
        self.gaiachain_cli = _GAIACHAIN_CLI
        self.base_url = os.getenv("FIVERR_API_URL", "https://api.fiverr.com/v1")

    def publish_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Publica un servicio; si hay API key llama a Fiverr, sino devuelve stub y registra en GaiaChain."""
        if not self._validate_service_legality(service_data):
            return {"status": "error", "reason": "Servicio no cumple normativas (campos o palabras prohibidas)"}
        if _REQUESTS and requests and self.fiverr_api_key:
            try:
                r = requests.post(
                    f"{self.base_url}/users/me/gigs",
                    headers={"Authorization": f"Bearer {self.fiverr_api_key}", "Content-Type": "application/json"},
                    json={
                        "title": service_data.get("nombre", ""),
                        "description": service_data.get("descripcion", ""),
                        "price": service_data.get("precio", 0),
                        "delivery_time": service_data.get("tiempo_entrega", 3),
                        "category": service_data.get("categoria", "programming_tech"),
                        "tags": service_data.get("etiquetas", ["ai", "blockchain", "agriculture"]),
                    },
                    timeout=30,
                )
                r.raise_for_status()
                gig_data = r.json()
                tx_hash = self._register_service_in_gaiachain({
                    "service_id": gig_data.get("id", ""),
                    "nombre": service_data.get("nombre"),
                    "precio": service_data.get("precio"),
                    "plataforma": "Fiverr",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                return {"status": "published", "service_url": gig_data.get("url", ""), "gaiachain_tx": tx_hash}
            except Exception as e:
                logger.warning("Fiverr publish: %s", e)
                return {"status": "error", "reason": str(e)}
        tx_hash = self._register_service_in_gaiachain({
            "service_id": "stub",
            "nombre": service_data.get("nombre"),
            "precio": service_data.get("precio"),
            "plataforma": "stub",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {"status": "stub", "message": "FIVERR_API_KEY no configurado; servicio registrado en GaiaChain", "gaiachain_tx": tx_hash}

    def _validate_service_legality(self, service_data: Dict[str, Any]) -> bool:
        required = ["nombre", "descripcion", "precio"]
        if not all(service_data.get(f) is not None for f in required):
            return False
        desc = (service_data.get("descripcion") or "").lower()
        if any(k in desc for k in ["cannabis", "drogas", "ilegal"]):
            return False
        return True

    def _register_service_in_gaiachain(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "market_service", "--data", json.dumps(data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def handle_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un pedido: analisis_yield o generar_contrato; registra entrega en GaiaChain."""
        if not all(order_data.get(f) for f in ["cliente", "servicio", "datos"]):
            return {"status": "error", "reason": "Pedido invalido: cliente, servicio, datos"}
        servicio = order_data.get("servicio", "")
        if servicio == "analisis_yield":
            from backend.agents_autonomous.yield_master import analizar_yield
            result = analizar_yield(order_data.get("datos", {}))
        elif servicio == "generar_contrato":
            from backend.agents_autonomous.contract_generator import generate_contract
            datos = order_data.get("datos", {})
            result = generate_contract(
                contract_type=datos.get("contract_type", "BioCoin_Supply"),
                parties=datos.get("parties", []),
                terms=datos.get("terms", []),
                jurisdiction=datos.get("jurisdiction", "EU"),
            )
        else:
            return {"status": "error", "reason": "Servicio no soportado (analisis_yield, generar_contrato)"}
        delivery = {"cliente": order_data["cliente"], "servicio": servicio, "resultados": result, "timestamp": datetime.now(timezone.utc).isoformat()}
        tx_hash = self._register_delivery_in_gaiachain(delivery)
        return {"status": "delivered", "resultados": result, "gaiachain_tx": tx_hash}

    def _register_delivery_in_gaiachain(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "service_delivery", "--data", json.dumps(data)],
                capture_output=True, text=True, timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"

    def _query_harvest(self, lote_id: str) -> Dict[str, Any]:
        if not os.path.isfile(self.gaiachain_cli):
            return {"producto": "Cultivo", "lote_id": lote_id}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "harvest", "--lote_id", lote_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return {"producto": "Cultivo", "lote_id": lote_id}

    def _query_data_product(self, product_id: str) -> Dict[str, Any] | None:
        if not os.path.isfile(self.gaiachain_cli):
            return {"name": "Datos de yield", "price": 199.99, "lote_id": product_id.replace("DATA-", "").split("-")[0] if "DATA-" in product_id else ""}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "data_product", "--product_id", product_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out.get("data", out)
        except Exception:
            pass
        return None

    PRODUCT_TYPES = {
        "yield_data": {"name": "Datos de Yield", "description": "Dataset analisis de yield (humedad, temperatura, luz).", "price": 199.99, "category": "agricultural_data", "tags": ["yield", "agrovoltaica", "AI"]},
        "cannabinoid_data": {"name": "Perfil Cannabinoides", "description": "Analisis THC/CBD/CBG y trazabilidad RD 903/2025.", "price": 299.99, "category": "cannabis_data", "tags": ["cannabinoids", "HPLC", "medical"]},
        "climate_data": {"name": "Datos Climaticos", "description": "Temperatura, humedad, CO2, luz PAR por ciclo.", "price": 99.99, "category": "climate_data", "tags": ["IoT", "sensors", "agriculture"]},
    }

    def publish_data_product(self, lote_id: str, product_type: str = "yield_data") -> Dict[str, Any]:
        """Publica producto de datos (yield_data, cannabinoid_data, climate_data) y registra en GaiaChain."""
        if product_type not in self.PRODUCT_TYPES:
            return {"status": "error", "reason": "Tipo no valido (yield_data, cannabinoid_data, climate_data)"}
        harvest_data = self._query_harvest(lote_id)
        pt = self.PRODUCT_TYPES[product_type]
        name = f"{pt['name']} - {harvest_data.get('producto', lote_id)} (Lote {lote_id})"
        payload = {"lote_id": lote_id, "product_type": product_type, "name": name, "description": pt["description"], "price": pt["price"], "category": pt["category"], "tags": pt["tags"], "timestamp": datetime.now(timezone.utc).isoformat()}
        gaia_tx = "gaiachain-no-cli"
        if os.path.isfile(self.gaiachain_cli):
            try:
                r = subprocess.run(
                    [self.gaiachain_cli, "record", "--type", "data_product", "--data", json.dumps(payload)],
                    capture_output=True, text=True, timeout=10,
                )
                gaia_tx = (r.stdout or "").strip() or "ok" if r.returncode == 0 else gaia_tx
            except Exception:
                pass
        return {"status": "success", "product_id": f"DATA-{lote_id}-{product_type.upper()}", "product_data": pt, "gaiachain_tx": gaia_tx, "marketplace_url": f"https://data.castuo-system.com/products/{(gaia_tx or '')[:16]}"}

    def sell_data_access(self, product_id: str, buyer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Vende acceso a producto de datos: factura + licencia y registro en GaiaChain."""
        from .invoice_bot import InvoiceBot
        product = self._query_data_product(product_id)
        if not product:
            return {"status": "error", "reason": "Producto no encontrado"}
        if not isinstance(product, dict):
            product = {"name": "Datos", "price": 99.99}
        invoice_bot = InvoiceBot()
        if not invoice_bot._validate_client_data(buyer_data):
            buyer_data["direccion"] = buyer_data.get("direccion", "N/A")
            buyer_data["email"] = buyer_data.get("email", "comprador@example.com")
        invoice_result = invoice_bot.generate_invoice({
            "cliente": buyer_data,
            "productos": [{"nombre": product.get("name", "Acceso datos"), "tipo": "servicios_agronomicos", "cantidad": 1, "precio_unitario": product.get("price", 99.99)}],
            "notas": f"Venta de acceso a datos: {product_id}",
        })
        if invoice_result.get("status") != "success":
            return {"status": "error", "reason": invoice_result.get("reason", "Error al generar factura")}
        access_token = f"DATA-{product_id[-8:] if len(product_id) >= 8 else product_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        license_data = {"product_id": product_id, "buyer_id": buyer_data.get("cif_nif"), "access_token": access_token, "expiry_date": (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d"), "permitted_uses": ["analysis", "research", "non_commercial"], "gaiachain_tx": invoice_result.get("gaiachain_tx")}
        gaia_tx = "gaiachain-no-cli"
        if os.path.isfile(self.gaiachain_cli):
            try:
                r = subprocess.run([self.gaiachain_cli, "record", "--type", "data_sale", "--data", json.dumps(license_data)], capture_output=True, text=True, timeout=10)
                gaia_tx = (r.stdout or "").strip() or "ok" if r.returncode == 0 else gaia_tx
            except Exception:
                pass
        return {"status": "success", "invoice": invoice_result.get("invoice"), "license": license_data, "gaiachain_tx": gaia_tx, "access_url": f"https://data.castuo-system.com/access/{access_token}"}

    def track_data_sales(self, product_id: str) -> Dict[str, Any]:
        """Consulta ventas de un producto de datos en GaiaChain."""
        if not os.path.isfile(self.gaiachain_cli):
            return {"status": "stub", "data": [], "product_id": product_id}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "data_sale", "--product_id", product_id],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                out = json.loads(r.stdout)
                return out if isinstance(out, dict) else {"data": out, "product_id": product_id}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
        return {"data": [], "product_id": product_id}
