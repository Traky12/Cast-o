# -*- coding: utf-8 -*-
"""Validador de cumplimiento normativo (AI Act, GDPR, ISO)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.models.pro_account import ProAccount


class ComplianceValidator:
    """Valida que una cuenta Pro cumpla con normativas éticas y legales."""

    def __init__(self) -> None:
        self.required_compliance = [
            "AI_Act_UE_2024_1689",
            "GDPR",
            "ISO_27001",
        ]
        self.min_ethics_thresholds = {
            "equity": 0.8,
            "transparency": 0.9,
            "privacy": 0.95,
            "sustainability": 0.7,
        }

    def validate_account(self, account: ProAccount) -> Tuple[bool, List[str]]:
        """Valida que una cuenta cumpla con los estándares éticos."""
        errors: List[str] = []
        owner = account.owner
        if not owner or not owner.ethics:
            return False, ["Cuenta sin propietario o directrices éticas"]

        for norm in self.required_compliance:
            if norm not in (owner.ethics.compliance or []):
                errors.append(f"Falta cumplimiento con {norm}")

        for ethic, threshold in self.min_ethics_thresholds.items():
            current = getattr(owner.ethics, ethic, 0.0)
            if current < threshold:
                errors.append(f"{ethic} ({current}) < umbral mínimo ({threshold})")

        last_audit = None
        for a in (account.activity_log or []):
            if a.action == "compliance_report_generated":
                if last_audit is None or a.timestamp > last_audit:
                    last_audit = a.timestamp
        if last_audit and owner.ethics:
            freq = getattr(owner.ethics, "audit_frequency", "monthly")
            days = (datetime.utcnow() - last_audit).days
            if freq == "monthly" and days > 30:
                errors.append("Auditoría mensual pendiente")
            elif freq == "quarterly" and days > 90:
                errors.append("Auditoría trimestral pendiente")

        # GDPR Art. 5: limitación del plazo de conservación
        if not self.validate_data_retention(account):
            errors.append("Datos de actividad retenidos más allá del plazo permitido (data_retention_days)")

        return (len(errors) == 0, errors)

    def validate_data_retention(self, account: ProAccount) -> bool:
        """Valida que los datos no se retengan más de lo permitido (GDPR Art. 5)."""
        owner = account.owner
        if not owner or not owner.ethics:
            return True
        max_days = getattr(owner.ethics, "data_retention_days", 90)
        now = datetime.utcnow()
        for activity in account.activity_log or []:
            delta = (now - activity.timestamp).days
            if delta > max_days:
                return False
        return True

    def generate_compliance_report(self, account: ProAccount) -> Dict[str, Any]:
        """Genera un informe de cumplimiento detallado."""
        owner = account.owner
        ethics = owner.ethics if owner else None
        is_valid, errors = self.validate_account(account)

        report: Dict[str, Any] = {
            "account_id": account.account_id,
            "generated_at": datetime.utcnow().isoformat(),
            "compliance_status": "compliant" if is_valid else "non_compliant",
            "checked_standards": self.required_compliance,
            "ethics_scores": {},
            "issues": errors,
            "recommendations": [],
        }
        if ethics:
            report["ethics_scores"] = {
                e: getattr(ethics, e, 0.0)
                for e in ["equity", "transparency", "privacy", "sustainability"]
            }
            for ethic, threshold in self.min_ethics_thresholds.items():
                current = getattr(ethics, ethic, 0.0)
                if current < threshold:
                    report["recommendations"].append(
                        f"Aumentar {ethic} de {current} a {threshold}"
                    )
        return report
