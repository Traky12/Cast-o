# -*- coding: utf-8 -*-
"""Informes de transparencia (GDPR Art. 13-14)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from backend.models.pro_account import ProAccount, ProUserProfile


class TransparencyReport:
    """Genera informes de transparencia para usuarios (GDPR)."""

    def generate_report(self, account: ProAccount, user: ProUserProfile) -> Dict[str, Any]:
        """Genera un informe de transparencia para un usuario."""
        ethics = user.ethics
        return {
            "user_id": user.user_id,
            "account_id": account.account_id,
            "generated_at": datetime.utcnow().isoformat(),
            "data_collected": [
                "Nombre y email (para autenticación)",
                "Historial de interacciones con agentes",
                "Preferencias de accesibilidad",
                "Feedback proporcionado",
            ],
            "data_purpose": [
                "Personalizar la experiencia del usuario",
                "Mejorar los agentes de IA",
                "Cumplir con normativas de accesibilidad",
                "Generar informes de cumplimiento",
            ],
            "data_retention": f"{getattr(ethics, 'data_retention_days', 90)} días",
            "data_sharing": [
                "No se comparte con terceros sin consentimiento",
                "Datos anonimizados para análisis agregados",
            ],
            "user_rights": [
                "Derecho a acceder a tus datos (GDPR Art. 15)",
                "Derecho a rectificar datos (GDPR Art. 16)",
                "Derecho a borrar datos (GDPR Art. 17)",
                "Derecho a oponerse al procesamiento (GDPR Art. 21)",
            ],
            "contact_for_privacy": getattr(
                account, "data_protection_officer", None
            ) or "dpo@ctaex.castu.system",
            "third_party_sharing": {
                "partners": ["GlobalGAP", "AEMPS"],
                "purpose": "Certificación y cumplimiento normativo",
                "data_types": ["cultivo", "rendimiento", "certificados"],
            },
            "ethics_commitment": {
                "equity": getattr(ethics, "equity", 1.0),
                "transparency": getattr(ethics, "transparency", 1.0),
                "privacy": getattr(ethics, "privacy", 1.0),
            },
            "compliance_standards": getattr(ethics, "compliance", []),
        }
