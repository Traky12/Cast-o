# -*- coding: utf-8 -*-
"""Integración Gold Standard (GS4GG) - stub para PDD y reportes XML."""
import xml.etree.ElementTree as ET
from typing import Any, Dict


class GoldStandard:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.goldstandard.org/v2"

    def register_project(self, project_data: Dict[str, Any]) -> bytes:
        """Registra proyecto (stub; devuelve XML)."""
        root = ET.Element("ProjectDesignDocument")
        ET.SubElement(root, "ProjectTitle").text = project_data.get("name", "")
        ET.SubElement(root, "ProjectId").text = project_data.get("id", "")
        ET.SubElement(root, "Standard").text = "GS4GG"
        return ET.tostring(root, encoding="unicode").encode("utf-8")

    def submit_monitoring_report(self, report_data: Dict) -> bytes:
        """Envía reporte de monitoreo (stub)."""
        root = ET.Element("MonitoringReport")
        ET.SubElement(root, "ProjectId").text = report_data.get("project_id", "")
        ET.SubElement(root, "CreditsIssued").text = str(report_data.get("credits_issued", 0))
        return ET.tostring(root, encoding="unicode").encode("utf-8")
