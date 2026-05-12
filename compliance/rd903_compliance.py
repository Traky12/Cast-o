# -*- coding: utf-8 -*-
"""
Cumplimiento RD 903/2025 — Cannabis medicinal (España).
Requisitos seguridad, trazabilidad, control de calidad e informes.
Integración GaiaChain para trazabilidad inmutable.
"""
import json
from datetime import datetime
from typing import Any, Dict, List

import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class RD903Compliance:
    """
    Verificación de cumplimiento del Real Decreto 903/2025.
    Seguridad física/digital, trazabilidad a nivel planta/lote, control de calidad (THC < 0,2%), informes.
    """

    def __init__(self) -> None:
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self.requirements = {
            "security": {
                "physical": [
                    "Cercado perimetral con sensores",
                    "Cámaras de vigilancia 24/7",
                    "Control de acceso biométrico",
                    "Sistema de alarma conectado a FCS",
                ],
                "digital": [
                    "Trazabilidad blockchain (GaiaChain)",
                    "Almacenamiento de datos cifrado",
                    "Auditorías de seguridad periódicas",
                    "Software conforme AEMPS",
                ],
            },
            "traceability": {
                "plant_level": True,
                "batch_tracking": True,
                "immutable_records": True,
                "third_party_audit": "trimestral",
            },
            "quality_control": {
                "thc_limits": "<0,2%",
                "pesticide_testing": "Conforme normativa UE",
                "heavy_metal_testing": "Límites UE",
                "microbiological_testing": "ISO 11737",
            },
            "reporting": {
                "monthly": ["inventario", "producción", "residuos"],
                "quarterly": ["auditoría_seguridad", "control_calidad"],
                "annual": ["impacto_ambiental", "informe_financiero"],
            },
        }

    def check_security_compliance(self, facility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprueba si la instalación cumple requisitos de seguridad RD 903/2025."""
        missing: List[str] = []
        for req in self.requirements["security"]["physical"]:
            if req not in facility_data.get("physical_security", []):
                missing.append(req)
        for req in self.requirements["security"]["digital"]:
            if req not in facility_data.get("digital_security", []):
                missing.append(req)
        return {
            "compliant": len(missing) == 0,
            "missing_requirements": missing,
            "blockchain_verification": self._verify_blockchain_integration(facility_data),
        }

    def _verify_blockchain_integration(self, facility_data: Dict[str, Any]) -> bool:
        """Verifica que la instalación use GaiaChain para trazabilidad."""
        if facility_data.get("blockchain_system") != "GaiaChain":
            return False
        if not self.blockchain:
            return True  # stub
        recent = self.blockchain.get_recent_transactions(
            facility_id=facility_data.get("id"), limit=5
        )
        return len(recent) > 0

    def generate_compliance_report(
        self, facility_data: Dict[str, Any], production_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera informe de cumplimiento RD 903/2025 y lo registra en GaiaChain."""
        security_check = self.check_security_compliance(facility_data)
        traceability_ok = all([
            production_data.get("plant_level_tracking"),
            production_data.get("batch_tracking"),
            production_data.get("immutable_records"),
        ])
        quality_ok = all([
            (production_data.get("thc_level") or 0) < 0.2,
            production_data.get("pesticide_test") == "Conforme normativa UE",
            production_data.get("heavy_metal_test") == "Límites UE",
        ])
        report = {
            "facility_id": facility_data.get("id", ""),
            "timestamp": datetime.now().isoformat(),
            "security_compliance": security_check["compliant"],
            "missing_security": security_check["missing_requirements"],
            "traceability_compliance": traceability_ok,
            "quality_compliance": quality_ok,
            "overall_compliance": security_check["compliant"] and traceability_ok and quality_ok,
            "recommendations": [],
        }
        if not security_check["compliant"]:
            report["recommendations"].append({"area": "security", "actions": security_check["missing_requirements"]})
        if not traceability_ok:
            report["recommendations"].append({
                "area": "traceability",
                "actions": ["Implementar trazabilidad a nivel planta con GaiaChain", "Registro de todos los lotes", "Auditoría tercera parte"],
            })
        if not quality_ok:
            report["recommendations"].append({
                "area": "quality_control",
                "actions": ["Reanalizar THC", "Revisar uso de fitosanitarios", "Análisis de metales pesados"],
            })
        if self.blockchain:
            self.blockchain.register_compliance_report(report)
        return report

    def register_production_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra lote de producción conforme a RD 903/2025 (THC < 0,2%)."""
        required = ["batch_id", "strain", "planting_date", "harvest_date", "thc_level", "cbd_level", "weight_kg", "destination"]
        if not all(f in batch_data for f in required):
            raise ValueError("Faltan campos obligatorios para el registro del lote")
        if batch_data["thc_level"] >= 0.2:
            raise ValueError("Nivel de THC supera el límite legal (0,2%)")
        tx_hash = ""
        if self.blockchain:
            tx_hash = self.blockchain.register_cannabis_batch(batch_data)
        return {
            "status": "registered",
            "batch_id": batch_data["batch_id"],
            "blockchain_tx": tx_hash,
            "compliance": self._check_batch_compliance(batch_data),
        }

    def _check_batch_compliance(self, batch_data: Dict[str, Any]) -> bool:
        """Comprueba cumplimiento del lote (THC, documentación, destino)."""
        checks = {
            "thc_level": batch_data.get("thc_level", 1) < 0.2,
            "documentation": all(
                d in batch_data.get("documents", [])
                for d in ["quality_certificate", "security_log"]
            ),
            "destination": batch_data.get("destination") in ["research", "medical", "industrial"],
        }
        return all(checks.values())
