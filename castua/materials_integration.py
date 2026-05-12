# -*- coding: utf-8 -*-
"""
Integración CASTUA con CASTUO-SYSTEM™ 4.0: materiales compuestos y créditos de carbono.
Fabricación bio-compuestos, venta materiales, venta créditos (Verra/EU ETS — España/UE).
"""
from datetime import datetime
from typing import Any, Dict

import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    from carbon.verra_integration import VerraCarbon
except ImportError:
    VerraCarbon = None  # type: ignore


class CastuaMaterialsIntegration:
    """
    Producción de materiales compuestos desde biomasa CASTUA y venta de créditos de carbono.
    Mercados: España/UE (EU ETS, Verra, Gold Standard).
    """

    def __init__(self):
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self._material_production = None  # En producción: cliente Odoo/API CASTUO-SYSTEM
        self._carbon_market = None

    def produce_materials(self, biomass_kg: float) -> Dict[str, Any]:
        """Convierte biomasa en material compuesto (1 kg biomasa → 0.6 kg compuesto)."""
        composite_kg = biomass_kg * 0.6
        production_data = {
            "material_type": "hemp_composite",
            "kg_produced": composite_kg,
            "raw_material_kg": biomass_kg,
            "blockchain_tx": "",
        }
        if self.blockchain:
            production_data["blockchain_tx"] = self.blockchain.register_material_production({
                "material_type": "hemp_composite",
                "kg_produced": composite_kg,
                "raw_material_kg": biomass_kg,
                "timestamp": datetime.now().isoformat(),
                "production_data": production_data,
            })

        co2_saved = composite_kg * 3.0  # vs plástico convencional (kg CO₂)
        carbon_credits_kg = co2_saved
        if VerraCarbon:
            try:
                verra = VerraCarbon(api_key="", project_id="CASTUA-2026-001")
                credits = verra.calculate_credits({
                    "material_type": "hemp_composite",
                    "kg_produced": composite_kg,
                    "energy_kwh": composite_kg * 0.5,
                    "raw_material_kg": biomass_kg,
                })
                carbon_credits_kg = credits.get("carbon_credits_kg", co2_saved)
            except Exception:
                pass

        return {
            "composite_kg": composite_kg,
            "carbon_credits_kg": carbon_credits_kg,
            "blockchain_tx": production_data.get("blockchain_tx", ""),
        }

    def sell_materials(self, composite_kg: float, buyer_id: str) -> Dict[str, Any]:
        """Vende materiales compuestos; registra en GaiaChain."""
        sale_data = {
            "material_type": "hemp_composite",
            "kg": composite_kg,
            "buyer_id": buyer_id,
            "timestamp": datetime.now().isoformat(),
        }
        if self.blockchain:
            self.blockchain.register_material_sale(sale_data)
        return sale_data

    def sell_carbon_credits(self, credits_kg: float, buyer_id: str, price_per_ton: float = 70.0) -> Dict[str, Any]:
        """Vende créditos de carbono (mercados verificados UE/España)."""
        sale_data = {
            "credits_kg": credits_kg,
            "buyer_id": buyer_id,
            "price_per_ton": price_per_ton,
            "timestamp": datetime.now().isoformat(),
        }
        if self.blockchain:
            self.blockchain.register_carbon_sale(sale_data)
        return sale_data
