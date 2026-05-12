# -*- coding: utf-8 -*-
"""
Procesamiento de cáñamo industrial: biomasa → fibra, CBD, semillas, residuos.
Economía circular: residuos → biogás/compost. Créditos de carbono (Verra/UE).
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


class CannabisProcessor:
    """
    Procesador de cosecha de cáñamo: distribución en productos y residuos.
    Trazabilidad GaiaChain; créditos de carbono vía Verra (UE/España).
    """

    def __init__(self):
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self.inventory: Dict[str, float] = {
            "biomass": 0.0,
            "fiber": 0.0,
            "cbd": 0.0,
            "seeds": 0.0,
            "waste": 0.0,
        }

    def process_harvest(self, harvest_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa cosecha: biomasa → fibra 50%, CBD 5%, semillas 2%, residuos 43%."""
        biomass = harvest_data["yield_kg"]
        self.inventory["biomass"] += biomass
        self.inventory["fiber"] += biomass * 0.50
        self.inventory["cbd"] += biomass * 0.05
        self.inventory["seeds"] += biomass * 0.02
        self.inventory["waste"] += biomass * 0.43

        processing_data = {
            "input_kg": biomass,
            "outputs": {
                "fiber": biomass * 0.50,
                "cbd": biomass * 0.05,
                "seeds": biomass * 0.02,
                "waste": biomass * 0.43,
            },
            "timestamp": datetime.now().isoformat(),
            "greenhouse_id": harvest_data.get("greenhouse_id"),
            "tower_id": harvest_data.get("tower_id"),
        }
        if self.blockchain:
            self.blockchain.register_processing(processing_data)

        co2_saved = biomass * 1.85  # kg CO₂ vs convencional
        if VerraCarbon:
            try:
                verra = VerraCarbon(api_key="", project_id="CASTUA-2026-001")
                verra.calculate_credits({
                    "material_type": "hemp_composite",
                    "kg_produced": biomass,
                    "raw_material_kg": biomass,
                    "energy_kwh": biomass * 0.1,
                })
            except Exception:
                pass

        return processing_data

    def get_inventory(self) -> Dict[str, float]:
        """Devuelve inventario actual de productos procesados."""
        return dict(self.inventory)

    def process_waste(self, waste_kg: float) -> Dict[str, float]:
        """Convierte residuos en biogás (30%) y compost (70%). Registro GaiaChain + créditos."""
        biogas_kg = waste_kg * 0.3
        compost_kg = waste_kg * 0.7
        co2_avoided = waste_kg * 0.5  # evita metano

        waste_data = {
            "input_waste_kg": waste_kg,
            "output_biogas_kg": biogas_kg,
            "output_compost_kg": compost_kg,
            "timestamp": datetime.now().isoformat(),
            "co2_avoided_kg": co2_avoided,
        }
        if self.blockchain:
            self.blockchain.register_waste_processing(waste_data)
        self.inventory["waste"] -= waste_kg
        return {"biogas_kg": biogas_kg, "compost_kg": compost_kg, "co2_avoided_kg": co2_avoided}

    def sell_product(self, product_type: str, kg: float, buyer_id: str) -> Dict[str, Any]:
        """Vende producto procesado; registra en GaiaChain."""
        if self.inventory.get(product_type, 0) < kg:
            raise ValueError(f"Stock insuficiente de {product_type}")
        self.inventory[product_type] = self.inventory.get(product_type, 0) - kg

        sale_data = {
            "product_type": product_type,
            "kg": kg,
            "buyer_id": buyer_id,
            "timestamp": datetime.now().isoformat(),
            "price_per_kg": self._get_price(product_type),
        }
        if self.blockchain:
            self.blockchain.register_sale(sale_data)
        return sale_data

    def _get_price(self, product_type: str) -> float:
        """Precio de mercado (€/kg) — referencia España/UE."""
        prices = {"fiber": 1.5, "cbd": 50.0, "seeds": 2.0, "biomass": 0.5}
        return prices.get(product_type, 0.0)
