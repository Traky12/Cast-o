# -*- coding: utf-8 -*-
"""Integración Verra (VCS) - metodología VM0043 (stub; producción con API real)."""
from datetime import datetime
from typing import Any, Dict


class VerraCarbon:
    def __init__(self, api_key: str = "", project_id: str = ""):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = "https://api.verra.org/v1"

    def register_project(self, project_data: Dict[str, Any]) -> Dict:
        """Registra proyecto en Verra (stub)."""
        return {"status": "ok", "project_id": self.project_id or project_data.get("id", "")}

    def submit_monitoring_report(self, report_data: Dict) -> Dict:
        """Envía reporte de monitoreo (stub)."""
        return {"status": "ok", "report_id": datetime.now().strftime("%Y%m%d%H%M")}

    def calculate_credits(self, production_data: Dict) -> Dict:
        """Calcula créditos según VM0043: proyecto vs línea base."""
        factors = {
            "hemp_composite": {"production": 0.5, "raw_material": 0.3, "energy": 0.4},
            "conventional_plastic": 3.5,
        }
        mt = production_data.get("material_type", "hemp_composite")
        project_emissions = (
            production_data.get("kg_produced", 0) * factors.get(mt, {}).get("production", 0.5)
            + production_data.get("raw_material_kg", 0) * factors.get(mt, {}).get("raw_material", 0.3)
            + production_data.get("energy_kwh", 0) * factors.get(mt, {}).get("energy", 0.4)
        )
        baseline = production_data.get("kg_produced", 0) * factors.get("conventional_plastic", 3.5)
        reduction = max(0, baseline - project_emissions)
        return {
            "project_emissions": project_emissions,
            "baseline_emissions": baseline,
            "carbon_credits_kg": reduction,
            "carbon_credits_tons": reduction / 1000,
        }

    def generate_verification_doc(self, production_data: Dict, credits: Dict) -> Dict:
        """Documento de verificación VCS (stub)."""
        return {
            "project_id": self.project_id,
            "report_date": datetime.now().isoformat(),
            "production_data": production_data,
            "emissions": credits,
            "credits_issued": credits.get("carbon_credits_tons", 0),
            "verification": {"methodology": "VM0043"},
        }
