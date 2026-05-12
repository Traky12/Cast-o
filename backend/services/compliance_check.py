# -*- coding: utf-8 -*-
"""Análisis de cumplimiento normativo UE (checklist automático)."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class ComplianceCheck(BaseModel):
    """Checklist automático para validar conformidad con regulaciones UE."""

    gdpr: bool = False
    ai_act: bool = False
    pac_2026: bool = False
    globalgap: bool = False
    aemps: bool = False
    issues: List[str] = []

    def check_all(self, system_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida el cumplimiento con todas las normativas UE relevantes."""
        self.issues = []

        # GDPR (RGPD)
        self.gdpr = (
            system_data.get("data_protection", {}).get("gdpr_compliant", False)
        )
        if not self.gdpr:
            self.issues.append(
                "Falta cumplimiento con GDPR (Art. 25: privacidad por diseño)"
            )

        # AI Act (UE 2024/1689)
        ai = system_data.get("ai_models", {})
        self.ai_act = bool(
            ai.get("transparency_report", False)
            and ai.get("bias_test", {}).get("passed", False)
        )
        if not self.ai_act:
            self.issues.append(
                "Modelos de IA no cumplen con AI Act (Art. 13: transparencia)"
            )

        # PAC 2026
        self.pac_2026 = (
            system_data.get("agrovoltaic", {}).get("pac_compliant", False)
        )
        if not self.pac_2026:
            self.issues.append(
                "Superficies agrovoltaicas no cumplen con PAC 2026"
            )

        # GlobalGAP
        self.globalgap = (
            system_data.get("certifications", {})
            .get("globalgap", {})
            .get("valid", False)
        )
        if not self.globalgap:
            self.issues.append(
                "Falta certificación GlobalGAP para exportación"
            )

        # AEMPS
        self.aemps = (
            system_data.get("cannabis", {}).get("aemps_certified", False)
        )
        if not self.aemps:
            self.issues.append(
                "Lotes de cannabis no certificados por AEMPS (RD 903/2025)"
            )

        return {
            "compliant": all([
                self.gdpr,
                self.ai_act,
                self.pac_2026,
                self.globalgap,
                self.aemps,
            ]),
            "checks": {
                "gdpr": self.gdpr,
                "ai_act": self.ai_act,
                "pac_2026": self.pac_2026,
                "globalgap": self.globalgap,
                "aemps": self.aemps,
            },
            "issues": self.issues,
        }
