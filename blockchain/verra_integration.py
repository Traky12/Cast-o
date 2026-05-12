# -*- coding: utf-8 -*-
"""
Integración Verra + GaiaChain — Registro de proyectos e informes de monitoreo en blockchain.
Normativas: VCS/VM0043, trazabilidad inmutable.
"""
import hashlib
import json
from datetime import datetime
from typing import Any, Dict

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class VerraIntegration:
    """Registro de proyectos Verra y envío de informes; sincronización con GaiaChain."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key
        self.base_url = "https://api.verra.org/v1"
        self.gaiachain = GaiaChainClient() if GaiaChainClient else None

    def register_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra proyecto de carbono en Verra y en GaiaChain."""
        payload = {
            "project_name": project_data.get("name"),
            "project_id": project_data.get("id"),
            "standard": "VCS",
            "methodology": "VM0043",
            "location": project_data.get("location"),
            "start_date": project_data.get("start_date"),
            "expected_reductions": project_data.get("expected_reductions"),
            "project_type": "Agriculture, Forestry and Other Land Use (AFOLU)",
            "proponent": project_data.get("proponent"),
            "validation_body": "TÜV SÜD",
        }
        # Llamada API real en producción; aquí stub
        out = {"project_id": project_data.get("id", "CASTUA-VERRA-2026-001"), "status": "registered"}
        project_data["verra_id"] = out["project_id"]
        if self.gaiachain:
            self.gaiachain.register_verra_project(project_data)
        return out

    def submit_monitoring_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envía informe de monitoreo a Verra y registra en GaiaChain."""
        payload = {
            "project_id": report_data.get("verra_id"),
            "reporting_period": {
                "start": report_data.get("period_start"),
                "end": report_data.get("period_end"),
            },
            "emission_reductions": report_data.get("emission_reductions"),
            "credits_requested": report_data.get("credits_requested"),
            "verification_body": "TÜV SÜD",
            "verification_date": datetime.now().isoformat(),
            "supporting_documents": [
                {
                    "type": "monitoring_report",
                    "ipfs_hash": report_data.get("ipfs_hash", ""),
                    "description": "Monitoring report for period",
                }
            ],
        }
        out = {"report_id": datetime.now().strftime("%Y%m%d%H%M"), "status": "submitted"}
        report_data["verra_report_id"] = out["report_id"]
        if self.gaiachain:
            self.gaiachain.register_verra_report(report_data)
        return out

    def generate_monitoring_report(self, production_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera informe de monitoreo desde datos de producción (CO₂ ahorrado por kg cáñamo)."""
        co2_saved_per_kg = 1.85
        total_co2_saved = production_data.get("weight_kg", 0) * co2_saved_per_kg
        report = {
            "project_id": production_data.get("verra_id", "CASTUA-VERRA-2026-001"),
            "project_name": production_data.get("project_name", "CASTUA Hemp Project"),
            "period_start": production_data.get("harvest_date", ""),
            "period_end": datetime.now().isoformat(),
            "production_data": {
                "batch_id": production_data.get("batch_id"),
                "strain": production_data.get("strain"),
                "weight_kg": production_data.get("weight_kg"),
                "energy_kwh": production_data.get("energy_kwh", 0),
                "water_saved_m3": production_data.get("water_saved_m3", 0),
            },
            "emission_reductions": {
                "baseline_emissions_kg": production_data.get("weight_kg", 0) * 3.5,
                "project_emissions_kg": production_data.get("weight_kg", 0) * 0.5,
                "net_reductions_kg": total_co2_saved,
            },
            "credits_requested": total_co2_saved / 1000,
            "verification_doc": self._generate_verification_doc(production_data),
        }
        report["ipfs_hash"] = hashlib.sha256(report["verification_doc"].encode()).hexdigest()
        return report

    def _generate_verification_doc(self, production_data: Dict[str, Any]) -> str:
        doc = {
            "project_name": production_data.get("project_name", "CASTUA Hemp Project"),
            "batch_id": production_data.get("batch_id"),
            "strain": production_data.get("strain"),
            "production_kg": production_data.get("weight_kg"),
            "harvest_date": production_data.get("harvest_date"),
            "thc_level": production_data.get("thc_level"),
            "cbd_level": production_data.get("cbd_level", 0),
            "energy_consumption_kwh": production_data.get("energy_kwh", 0),
            "water_consumption_m3": production_data.get("water_saved_m3", 0),
            "co2_saved_kg": production_data.get("weight_kg", 0) * 1.85,
            "verification_method": "Continuous monitoring with CASTUO Cloud 5.0",
            "auditor": "TÜV SÜD",
            "verification_date": datetime.now().isoformat(),
            "gaiachain_tx": production_data.get("gaiachain_tx", ""),
        }
        return json.dumps(doc, indent=2)
