# -*- coding: utf-8 -*-
"""Sistema de producción local para fabricación de drones (Extremadura/España)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dataclasses import dataclass, asdict

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient
from .drone_products_catalog import DroneProductsCatalog, DroneProduct


@dataclass
class LocalSupplier:
    """Información de un proveedor local (Extremadura/España)."""
    supplier_id: str
    name: str
    location: str
    materials: List[str]
    capacity: Dict[str, float]
    lead_time: int
    quality_certifications: List[str]
    contact: Dict[str, str]


@dataclass
class ProductionOrder:
    """Orden de producción para un producto."""
    order_id: str
    product_id: str
    quantity: int
    start_date: str
    end_date: str
    status: str
    materials_required: Dict[str, float]
    suppliers: Dict[str, List[str]]
    production_cost: float
    sale_value: float
    gaiachain_tx: Optional[str] = None


class LocalProductionSystem:
    """
    Sistema de producción local para fabricación de drones en Extremadura/España.
    Gestiona proveedores locales, órdenes de producción, trazabilidad y GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.catalog = DroneProductsCatalog()
        self.suppliers = self._initialize_suppliers()
        self.production_orders: List[ProductionOrder] = []
        self.inventory = self._initialize_inventory()
        self.local_production_stats = {
            "jobs_created": 0,
            "local_content": 0.85,
            "co2_saved": 0.0,
            "economic_impact": 0.0,
        }

    def _name_to_supplier_id(self, catalog_supplier_name: str) -> Optional[str]:
        """Mapea nombre de proveedor del catálogo a supplier_id."""
        for sid, s in self.suppliers.items():
            if s.name in catalog_supplier_name or catalog_supplier_name.startswith(s.name):
                return sid
        return None

    def _initialize_suppliers(self) -> Dict[str, LocalSupplier]:
        """Inicializa la base de datos de proveedores locales."""
        return {
            "CF-EXT-001": LocalSupplier(
                supplier_id="CF-EXT-001",
                name="CarbonFiber Extremadura",
                location="Cáceres, Extremadura",
                materials=["Fibra de carbono", "Compuestos de fibra de vidrio"],
                capacity={"Fibra de carbono": 5000.0, "Compuestos de fibra de vidrio": 3000.0},
                lead_time=7,
                quality_certifications=["ISO 9001", "EN 9100 (aeroespacial)"],
                contact={"email": "ventas@carbonfiber-ext.com", "phone": "+34 927 123 456"},
            ),
            "AL-TAJO-001": LocalSupplier(
                supplier_id="AL-TAJO-001",
                name="Aleaciones del Tajo",
                location="Talavera de la Reina, Castilla-La Mancha",
                materials=["Aleación de aluminio", "Aleación de magnesio"],
                capacity={"Aleación de aluminio": 10000.0, "Aleación de magnesio": 2000.0},
                lead_time=5,
                quality_certifications=["ISO 9001", "EN 15085 (soldadura)"],
                contact={"email": "comercial@aleacionestajo.es", "phone": "+34 925 654 321"},
            ),
            "PL-BAD-001": LocalSupplier(
                supplier_id="PL-BAD-001",
                name="Plásticos Agrícolas Sáenz",
                location="Badajoz, Extremadura",
                materials=["PLA biodegradable", "ABS reciclado", "Polipropileno"],
                capacity={"PLA biodegradable": 8000.0, "ABS reciclado": 12000.0, "Polipropileno": 15000.0},
                lead_time=3,
                quality_certifications=["ISO 9001", "OK Compost (biodegradable)"],
                contact={"email": "info@plasticos-saenz.com", "phone": "+34 924 321 654"},
            ),
            "EL-MER-001": LocalSupplier(
                supplier_id="EL-MER-001",
                name="Electrónica Avanzada Mérida",
                location="Mérida, Extremadura",
                materials=["Placas de circuito", "Sensores IoT", "Módulos GPS"],
                capacity={"Placas de circuito": 5000.0, "Sensores IoT": 10000.0, "Módulos GPS": 3000.0},
                lead_time=10,
                quality_certifications=["ISO 9001", "IATF 16949 (automotriz)"],
                contact={"email": "ventas@electronica-merida.es", "phone": "+34 924 654 987"},
            ),
            "OP-EXT-001": LocalSupplier(
                supplier_id="OP-EXT-001",
                name="Óptica de Precisión Extremadura",
                location="Cáceres, Extremadura",
                materials=["Lentes ópticas", "Filtros multiespectrales", "Cámaras térmicas"],
                capacity={"Lentes ópticas": 2000.0, "Filtros multiespectrales": 1500.0, "Cámaras térmicas": 500.0},
                lead_time=14,
                quality_certifications=["ISO 9001", "ISO 10110 (óptica)"],
                contact={"email": "info@optica-ext.com", "phone": "+34 927 987 654"},
            ),
            "AC-INOX-001": LocalSupplier(
                supplier_id="AC-INOX-001",
                name="Aceros Inoxidables del Guadiana",
                location="Badajoz, Extremadura",
                materials=["Acero inoxidable", "Acero templado"],
                capacity={"Acero inoxidable": 20000.0, "Acero templado": 5000.0},
                lead_time=7,
                quality_certifications=["ISO 9001", "EN 10088 (aceros inoxidables)"],
                contact={"email": "comercial@aceros-guadiana.es", "phone": "+34 924 123 789"},
            ),
            "RE-EXT-001": LocalSupplier(
                supplier_id="RE-EXT-001",
                name="Reciclados Extremadura",
                location="Plasencia, Extremadura",
                materials=["Plástico reciclado", "Metales reciclados", "Compuestos reciclados"],
                capacity={"Plástico reciclado": 15000.0, "Metales reciclados": 10000.0, "Compuestos reciclados": 8000.0},
                lead_time=5,
                quality_certifications=["ISO 14001", "Certificación de economía circular"],
                contact={"email": "info@reciclados-ext.com", "phone": "+34 927 321 987"},
            ),
        }

    def _initialize_inventory(self) -> Dict[str, float]:
        """Inicializa el inventario de materiales."""
        return {
            "Fibra de carbono": 2000.0,
            "Aleación de aluminio": 5000.0,
            "PLA biodegradable": 3000.0,
            "Acero inoxidable": 8000.0,
            "Cámaras multiespectrales": 200.0,
            "Módulos GPS": 500.0,
            "Sensores IoT": 1000.0,
            "Baterías LiPo": 800.0,
        }

    def _calculate_local_content(self, product_id: str) -> float:
        """Calcula el porcentaje de contenido local para un producto (0-1)."""
        product = self.catalog.get_product_by_id(product_id)
        if not product or not product.local_suppliers:
            return 0.0
        found = sum(1 for n in product.local_suppliers if self._name_to_supplier_id(n))
        return min(1.0, found / len(product.local_suppliers))

    def _calculate_co2_savings(self, product_id: str, quantity: int) -> float:
        """Estima el ahorro de CO2 por producción local vs. importación (kg)."""
        emission_factors = {"imported": 2.5, "local": 0.8}
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            return 0.0
        weight_kg = {"Multirrotor": 8.0, "Ala fija": 12.0, "Multirrotor (Hexacóptero)": 15.0}.get(
            product.drone_type, 10.0
        )
        if "Hexacóptero" in product.drone_type:
            weight_kg = 15.0
        savings_per_unit = (emission_factors["imported"] - emission_factors["local"]) * weight_kg
        return savings_per_unit * quantity

    def create_production_order(self, product_id: str, quantity: int) -> Dict:
        """Crea una orden de producción para un producto."""
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Producto {product_id} no encontrado")

        materials_needed = {mat: float(quantity) for mat in product.materials}
        suppliers_assigned: Dict[str, List[str]] = {}
        for material in product.materials:
            suppliers_assigned[material] = [
                sid for sid, sup in self.suppliers.items() if material in sup.materials
            ]

        order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{len(self.production_orders) + 1:04d}"
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=product.production_time * quantity)).strftime("%Y-%m-%d")

        order = ProductionOrder(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            materials_required=materials_needed,
            suppliers=suppliers_assigned,
            production_cost=product.production_cost * quantity,
            sale_value=product.sale_price * quantity,
            gaiachain_tx=None,
        )

        tx_id = self.gaiachain.log_production_event(
            {
                "event_type": "production_order_created",
                "order_id": order.order_id,
                "product_id": product_id,
                "quantity": quantity,
                "start_date": start_date,
                "end_date": end_date,
                "local_content": self._calculate_local_content(product_id),
                "co2_savings": self._calculate_co2_savings(product_id, quantity),
                "suppliers": list(suppliers_assigned.keys()),
                "timestamp": datetime.now().isoformat(),
            }
        )
        order.gaiachain_tx = tx_id
        self.production_orders.append(order)

        self.local_production_stats["jobs_created"] += quantity * product.production_time
        self.local_production_stats["economic_impact"] += order.sale_value * 0.85
        self.local_production_stats["co2_saved"] += self._calculate_co2_savings(product_id, quantity)

        order_dict = asdict(order)
        return {
            "order": order_dict,
            "local_impact": {
                "jobs_created": quantity * product.production_time,
                "economic_impact": order.sale_value * 0.85,
                "co2_saved": self._calculate_co2_savings(product_id, quantity),
                "local_content_percentage": self._calculate_local_content(product_id) * 100,
            },
            "gaiachain_tx": tx_id,
        }

    def process_order(self, order_id: str) -> Dict:
        """Procesa una orden de producción (simula el proceso)."""
        order = next((o for o in self.production_orders if o.order_id == order_id), None)
        if not order:
            raise ValueError(f"Orden {order_id} no encontrada")
        if order.status != "pending":
            return {"status": order.status, "message": f"Orden ya está en estado {order.status}"}

        product = self.catalog.get_product_by_id(order.product_id)
        if not product:
            raise ValueError(f"Producto {order.product_id} no encontrado")

        for material, qty in order.materials_required.items():
            if self.inventory.get(material, 0) < qty:
                for supplier_id in order.suppliers.get(material, []):
                    supplier = self.suppliers.get(supplier_id)
                    if supplier and material in supplier.capacity:
                        self.gaiachain.log_supply_chain_event(
                            {
                                "event_type": "material_order",
                                "order_id": order.order_id,
                                "supplier_id": supplier_id,
                                "material": material,
                                "quantity": qty,
                                "expected_delivery": (
                                    datetime.now() + timedelta(days=supplier.lead_time)
                                ).strftime("%Y-%m-%d"),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        break

        order.status = "in_progress"
        self.gaiachain.log_production_event(
            {
                "event_type": "production_started",
                "order_id": order.order_id,
                "product_id": order.product_id,
                "timestamp": datetime.now().isoformat(),
                "expected_completion": order.end_date,
            }
        )

        for material, qty in order.materials_required.items():
            self.inventory[material] = self.inventory.get(material, 0) - qty

        order.status = "completed"
        self.gaiachain.log_production_event(
            {
                "event_type": "production_completed",
                "order_id": order.order_id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "timestamp": datetime.now().isoformat(),
                "quality_check": "passed",
                "destination": "Almacén central",
            }
        )

        return {
            "status": "completed",
            "order": asdict(order),
            "products_manufactured": order.quantity,
            "economic_impact": order.sale_value * 0.85,
            "co2_saved": self._calculate_co2_savings(order.product_id, order.quantity),
        }

    def get_production_stats(self) -> Dict:
        """Obtiene estadísticas de producción local."""
        return {
            **self.local_production_stats,
            "current_orders": len(self.production_orders),
            "pending_orders": len([o for o in self.production_orders if o.status == "pending"]),
            "in_progress_orders": len([o for o in self.production_orders if o.status == "in_progress"]),
            "completed_orders": len([o for o in self.production_orders if o.status == "completed"]),
            "inventory_levels": self.inventory,
            "suppliers_count": len(self.suppliers),
        }

    def optimize_production_plan(
        self, product_id: str, quantity: int, months: int = 6
    ) -> Dict:
        """Optimiza un plan de producción para maximizar el impacto local."""
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Producto {product_id} no encontrado")

        monthly_target = quantity / months
        local_suppliers: Dict[str, str] = {}
        extremeña_cities = ["Cáceres", "Badajoz", "Mérida", "Plasencia"]
        for material in product.materials:
            candidates = [
                sid
                for sid, sup in self.suppliers.items()
                if material in sup.materials
                and any(c in sup.location for c in extremeña_cities)
            ]
            if candidates:
                best = min(candidates, key=lambda sid: self.suppliers[sid].lead_time)
                local_suppliers[material] = best

        local_content = len(local_suppliers) / max(1, len(product.materials))
        co2_saved = self._calculate_co2_savings(product_id, quantity)
        jobs_created = quantity * product.production_time
        economic_impact = quantity * product.sale_price * 0.85

        return {
            "product": product.name,
            "quantity": quantity,
            "monthly_target": monthly_target,
            "production_time": product.production_time * quantity,
            "local_suppliers": local_suppliers,
            "local_content_percentage": local_content * 100,
            "co2_saved_kg": co2_saved,
            "jobs_created": jobs_created,
            "economic_impact_eur": economic_impact,
            "materials_required": {mat: quantity for mat in product.materials},
            "recommended_actions": [
                f"Aumentar capacidad de producción de {mat} con {self.suppliers[sid].name}"
                for mat, sid in local_suppliers.items()
                if mat in ("Fibra de carbono", "Aleación de aluminio")
            ],
        }

    def export_production_plan(self, format: str = "json") -> str:
        """Exporta el plan de producción actual."""
        if format.lower() == "json":
            return json.dumps(
                {
                    "production_orders": [asdict(o) for o in self.production_orders],
                    "stats": self.get_production_stats(),
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )
        raise ValueError(f"Formato no soportado: {format}")


if __name__ == "__main__":
    production_system = LocalProductionSystem(gaiachain_client=GaiaChainClient())
    stats = production_system.get_production_stats()
    print("Estadísticas iniciales:", stats["suppliers_count"], "proveedores")
    order_result = production_system.create_production_order(
        "CASTUO-DRONE-SPRAYER-001", 20
    )
    print("Orden creada:", order_result["order"]["order_id"])
    process_result = production_system.process_order(order_result["order"]["order_id"])
    print("Procesamiento:", process_result["status"])
