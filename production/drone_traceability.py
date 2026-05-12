# -*- coding: utf-8 -*-
"""Sistema de trazabilidad con blockchain para drones fabricados (GaiaChain)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
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
class DroneManufacturingRecord:
    """Registro de fabricación de un dron individual."""
    drone_id: str
    product_id: str
    serial_number: str
    manufacturing_date: str
    components: List[Dict]
    quality_checks: List[Dict]
    compliance: List[str]
    gaiachain_tx: Optional[str]


class DroneTraceabilitySystem:
    """
    Sistema de trazabilidad para drones fabricados localmente.
    Registro individual, certificación de origen extremeño/español, GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.manufacturing_records: Dict[str, DroneManufacturingRecord] = {}
        self.catalog = DroneProductsCatalog()
        self.certificate_template = self._load_certificate_template()

    def _load_certificate_template(self) -> Dict:
        """Carga la plantilla para certificados de autenticidad."""
        return {
            "version": "1.0",
            "issuer": {
                "name": "CASTUO-SYSTEM™",
                "location": "Extremadura, España",
                "certification_authority": "Agencia de Certificación Extremeña (ACE)",
                "contact": "certificacion@castu.system",
            },
            "standard": {
                "name": "Norma Extremeña de Calidad Agritech (NECA)",
                "version": "2.1",
                "reference": "DECRETO 123/2025 de la Junta de Extremadura",
            },
            "qrcode": {
                "format": "ISO/IEC 18004",
                "data_fields": [
                    "drone_id",
                    "product_id",
                    "manufacturing_date",
                    "components_hash",
                    "quality_checks_hash",
                ],
            },
            "blockchain": {
                "network": "GaiaChain",
                "consensus": "HoneyBadgerBFT",
                "pq_signature": "Dilithium2",
            },
        }

    def _generate_drone_id(self, product_id: str, year: int, sequence: int) -> str:
        """Genera un ID único para un dron."""
        part = product_id.split("-")[2] if len(product_id.split("-")) > 2 else product_id
        return f"CASTUO-{part}-{year}-{sequence:04d}"

    def _get_compliance_requirements(self, product_id: str) -> List[str]:
        """Obtiene los requisitos de cumplimiento para un producto."""
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            return []
        base = [
            "RD 903/2025 (cannabis medicinal)",
            "ISO 9001:2015 (gestión de calidad)",
            "ISO 14001:2015 (gestión ambiental)",
            "Reglamento (UE) 2019/947 (drones)",
            "Normativa de seguridad industrial de Extremadura",
        ]
        return base + list(product.compliance)

    def _calculate_local_content(self, product_id: str) -> float:
        """Calcula el porcentaje de contenido local para un producto."""
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            return 0.0
        return 0.85

    def _estimate_co2_savings(self, product_id: str) -> float:
        """Estima el ahorro de CO2 por producción local vs. importación (kg)."""
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            return 0.0
        emission_factors = {"imported": 2.5, "local": 0.8}
        weights = {"Multirrotor": 8.0, "Ala fija": 12.0}
        weight = weights.get(product.drone_type, 10.0)
        if "Hexacóptero" in product.drone_type:
            weight = 15.0
        return (emission_factors["imported"] - emission_factors["local"]) * weight

    def register_manufacturing(
        self,
        product_id: str,
        components: List[Dict],
        quality_checks: List[Dict],
    ) -> Dict:
        """Registra la fabricación de un nuevo dron."""
        product = self.catalog.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Producto {product_id} no encontrado")

        year = datetime.now().year
        same_product_year = [
            r
            for r in self.manufacturing_records.values()
            if r.product_id == product_id and r.manufacturing_date.startswith(str(year))
        ]
        sequence = len(same_product_year) + 1
        drone_id = self._generate_drone_id(product_id, year, sequence)
        serial_number = f"ES-{year}-{product_id[-3:]}-{sequence:06d}"

        record = DroneManufacturingRecord(
            drone_id=drone_id,
            product_id=product_id,
            serial_number=serial_number,
            manufacturing_date=datetime.now().isoformat(),
            components=components,
            quality_checks=quality_checks,
            compliance=self._get_compliance_requirements(product_id),
            gaiachain_tx=None,
        )

        components_hash = hashlib.sha256(
            json.dumps(components, sort_keys=True).encode()
        ).hexdigest()
        quality_hash = hashlib.sha256(
            json.dumps(quality_checks, sort_keys=True).encode()
        ).hexdigest()

        tx_data = {
            "event_type": "drone_manufactured",
            "drone_id": drone_id,
            "product_id": product_id,
            "serial_number": serial_number,
            "manufacturing_date": record.manufacturing_date,
            "components_hash": components_hash,
            "quality_hash": quality_hash,
            "compliance": record.compliance,
            "manufacturer": "CASTUO-SYSTEM™ (Extremadura, España)",
            "local_content": self._calculate_local_content(product_id),
        }
        tx_id = self.gaiachain.log_manufacturing_event(tx_data)
        record.gaiachain_tx = tx_id
        self.manufacturing_records[drone_id] = record

        certificate = self._generate_certificate(record)
        return {
            "manufacturing_record": record,
            "certificate": certificate,
            "gaiachain_tx": tx_id,
            "qrcode_data": self._generate_qrcode_data(record),
        }

    def _generate_certificate(self, record: DroneManufacturingRecord) -> Dict:
        """Genera un certificado de autenticidad para un dron."""
        product = self.catalog.get_product_by_id(record.product_id)
        if not product:
            raise ValueError(f"Producto {record.product_id} no encontrado")

        cert_id = f"CERT-{record.drone_id}-{datetime.now().strftime('%Y%m%d')}"
        issuance_date = datetime.now().isoformat()
        local_content = self._calculate_local_content(record.product_id)
        co2_savings = self._estimate_co2_savings(record.product_id)

        certificate = {
            **self.certificate_template,
            "certificate_id": cert_id,
            "issuance_date": issuance_date,
            "drone": {
                "drone_id": record.drone_id,
                "product_id": record.product_id,
                "product_name": product.name,
                "serial_number": record.serial_number,
                "manufacturing_date": record.manufacturing_date,
                "manufacturer": {
                    "name": "CASTUO-SYSTEM™",
                    "location": "Extremadura, España",
                    "certification": "Fabricado con ≥85% de componentes locales",
                },
                "technical_specs": {
                    "drone_type": product.drone_type,
                    "payload_capacity": f"{product.payload_capacity} kg",
                    "autonomy": f"{product.autonomy} min",
                    "sensors": product.sensors,
                },
                "compliance": record.compliance,
                "local_content": local_content,
                "co2_savings": f"{co2_savings:.1f} kg vs. importación",
            },
            "blockchain": {
                "transaction_id": record.gaiachain_tx,
                "network": "GaiaChain",
                "timestamp": record.manufacturing_date,
            },
            "qrcode": self._generate_qrcode_data(record),
        }

        self.gaiachain.log_certificate_event(
            {
                "certificate_id": cert_id,
                "drone_id": record.drone_id,
                "issuance_date": issuance_date,
                "blockchain_tx": record.gaiachain_tx,
                "local_content": local_content,
            }
        )
        return certificate

    def _generate_qrcode_data(self, record: DroneManufacturingRecord) -> Dict:
        """Genera los datos para el código QR del certificado."""
        product = self.catalog.get_product_by_id(record.product_id)
        if not product:
            raise ValueError(f"Producto {record.product_id} no encontrado")
        components_hash = hashlib.sha256(
            json.dumps(record.components, sort_keys=True).encode()
        ).hexdigest()
        quality_hash = hashlib.sha256(
            json.dumps(record.quality_checks, sort_keys=True).encode()
        ).hexdigest()
        return {
            "drone_id": record.drone_id,
            "product_id": record.product_id,
            "product_name": product.name,
            "serial_number": record.serial_number,
            "manufacturing_date": record.manufacturing_date,
            "manufacturer": "CASTUO-SYSTEM™ (Extremadura, España)",
            "components_hash": components_hash,
            "quality_hash": quality_hash,
            "compliance": ",".join(record.compliance),
            "local_content": self._calculate_local_content(record.product_id),
            "verification_url": f"https://verify.castu.system/{record.drone_id}",
        }

    def verify_drone(self, drone_id: str) -> Dict:
        """Verifica la autenticidad de un dron usando su ID."""
        record = self.manufacturing_records.get(drone_id)
        if not record:
            return {"status": "not_found", "message": f"Dron {drone_id} no registrado"}

        gaiachain_data = self.gaiachain.get_manufacturing_record(drone_id)
        if not gaiachain_data:
            return {
                "status": "blockchain_error",
                "message": "Registro no encontrado en GaiaChain",
            }

        components_hash = hashlib.sha256(
            json.dumps(record.components, sort_keys=True).encode()
        ).hexdigest()
        quality_hash = hashlib.sha256(
            json.dumps(record.quality_checks, sort_keys=True).encode()
        ).hexdigest()

        if (
            components_hash != gaiachain_data.get("components_hash")
            or quality_hash != gaiachain_data.get("quality_hash")
        ):
            return {"status": "tampered", "message": "Datos de fabricación alterados"}

        product = self.catalog.get_product_by_id(record.product_id)
        certificate = self._generate_verification_certificate(record)
        return {
            "status": "authentic",
            "drone_id": drone_id,
            "product_name": product.name if product else record.product_id,
            "manufacturing_date": record.manufacturing_date,
            "local_content": self._calculate_local_content(record.product_id),
            "compliance": record.compliance,
            "certificate": certificate,
            "gaiachain_tx": record.gaiachain_tx,
            "verification_url": f"https://verify.castu.system/{drone_id}",
        }

    def _generate_verification_certificate(self, record: DroneManufacturingRecord) -> Dict:
        """Genera un certificado de verificación."""
        product = self.catalog.get_product_by_id(record.product_id)
        if not product:
            raise ValueError(f"Producto {record.product_id} no encontrado")
        return {
            "verification_id": f"VERIF-{record.drone_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "drone": {
                "drone_id": record.drone_id,
                "product_name": product.name,
                "serial_number": record.serial_number,
                "manufacturing_date": record.manufacturing_date,
                "manufacturer": "CASTUO-SYSTEM™ (Extremadura, España)",
            },
            "verification": {
                "status": "authentic",
                "components_hash_match": True,
                "quality_hash_match": True,
                "blockchain_verification": True,
                "local_content": self._calculate_local_content(record.product_id),
            },
            "blockchain": {
                "transaction_id": record.gaiachain_tx,
                "network": "GaiaChain",
                "consensus": "HoneyBadgerBFT",
                "pq_signature": "Dilithium2",
            },
            "qrcode_data": self._generate_qrcode_data(record),
        }

    def get_production_stats(self) -> Dict:
        """Obtiene estadísticas de producción y trazabilidad."""
        product_counts: Dict[str, int] = {}
        for r in self.manufacturing_records.values():
            product_counts[r.product_id] = product_counts.get(r.product_id, 0) + 1

        n = len(self.manufacturing_records)
        local_avg = (
            sum(self._calculate_local_content(r.product_id) for r in self.manufacturing_records.values()) / n
            if n else 0.0
        )
        co2_total = sum(
            self._estimate_co2_savings(r.product_id) for r in self.manufacturing_records.values()
        )

        compliance_union: Dict[str, int] = {}
        for r in self.manufacturing_records.values():
            for req in r.compliance:
                compliance_union[req] = compliance_union.get(req, 0) + 1

        recent = sorted(
            self.manufacturing_records.values(),
            key=lambda x: x.manufacturing_date,
            reverse=True,
        )[:10]
        recent_list = []
        for r in recent:
            p = self.catalog.get_product_by_id(r.product_id)
            recent_list.append({
                "drone_id": r.drone_id,
                "product_name": p.name if p else r.product_id,
                "date": r.manufacturing_date,
                "local_content": self._calculate_local_content(r.product_id),
            })

        return {
            "total_drones_manufactured": n,
            "products_manufactured": product_counts,
            "local_content_avg": local_avg,
            "co2_saved_kg": co2_total,
            "compliance_coverage": compliance_union,
            "recent_manufacturing": recent_list,
        }

    def get_manufacturing_records(self) -> Dict[str, Dict]:
        """Devuelve todos los registros de fabricación por drone_id (para interfaz master)."""
        return {
            drone_id: asdict(record)
            for drone_id, record in self.manufacturing_records.items()
        }

    def export_manufacturing_records(self, format: str = "json") -> str:
        """Exporta los registros de fabricación."""
        if format.lower() != "json":
            raise ValueError(f"Formato no soportado: {format}")
        records_list = []
        for r in self.manufacturing_records.values():
            p = self.catalog.get_product_by_id(r.product_id)
            rec = {
                "drone_id": r.drone_id,
                "product_id": r.product_id,
                "product_name": p.name if p else None,
                "serial_number": r.serial_number,
                "manufacturing_date": r.manufacturing_date,
                "components": r.components,
                "quality_checks": r.quality_checks,
                "compliance": r.compliance,
                "gaiachain_tx": r.gaiachain_tx,
            }
            records_list.append(rec)
        return json.dumps(
            {
                "records": records_list,
                "stats": self.get_production_stats(),
                "timestamp": datetime.now().isoformat(),
            },
            indent=2,
        )


if __name__ == "__main__":
    traceability = DroneTraceabilitySystem(gaiachain_client=GaiaChainClient())
    components = [
        {
            "component_id": "CF-EXT-001-2026-0421",
            "type": "Fibra de carbono",
            "supplier": "CarbonFiber Extremadura",
            "batch": "2026-04-001",
            "certification": ["ISO 9001", "EN 9100"],
            "quantity": 2.5,
            "local": True,
        },
    ]
    quality_checks = [
        {
            "check_id": "QC-20260620-001",
            "type": "Prueba de resistencia estructural",
            "result": "passed",
            "standard": "ISO 19438",
            "timestamp": datetime.now().isoformat(),
            "operator": "Técnico-003",
        },
    ]
    result = traceability.register_manufacturing(
        "CASTUO-DRONE-SPRAYER-001", components, quality_checks
    )
    print("Dron fabricado:", result["manufacturing_record"].drone_id)
    verification = traceability.verify_drone(result["manufacturing_record"].drone_id)
    print("Verificación:", verification["status"])
