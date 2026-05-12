# -*- coding: utf-8 -*-
"""
Configuración del perfil SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO.
Acceso total y personalización avanzada.
"""
from __future__ import annotations

import json
from typing import Dict, List

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.profile_engine import ProfileConfig, ProfileType


def get_sabionda_master_config() -> ProfileConfig:
    """Configuración personalizada para SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO."""
    return ProfileConfig(
        profile_type=ProfileType.SABIONDA_MASTER_LANDUM,
        tone="professional_technical",
        allowed_modules=["*"],
        restrictions={},
        max_tokens=256000,
        response_style="detailed_structured",
        custom_settings={
            "version_management": True,
            "debug_mode": True,
            "ai_autonomy": 90,
            "multi_language": ["es", "en", "pt", "fr", "it"],
            "response_signature": True,
            "advanced_analytics": True,
            "blockchain_admin": True,
            "security_override": True,
            "custom_templates": {
                "system_status": (
                    "🌍 **SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO** | **Modo: Gestión Avanzada**\n"
                    "📌 **Estado del sistema:** {status}\n"
                    "🔧 **Módulos activos:** {active_modules}\n"
                    "📊 **Métricas clave:**\n{metrics}\n"
                    "💡 **Recomendaciones:** {recommendations}"
                ),
                "security_breach": (
                    "🚨 **ALERTA DE SEGURIDAD CRÍTICA** 🚨\n"
                    "📍 **Ubicación:** {location}\n"
                    "🕒 **Hora:** {time}\n"
                    "📄 **Detalles:** {details}\n"
                    "⚡ **Acciones automáticas:** {auto_actions}\n"
                    "🔗 **Transacción GaiaChain:** {gaiachain_tx}\n"
                    "🛡️ **Protocolos activados:** {protocols}\n"
                    "📞 **Equipo de seguridad notificado:** {security_team}"
                ),
                "production_optimization": (
                    "📈 **OPTIMIZACIÓN DE PRODUCCIÓN (Lote: {batch_id})**\n"
                    "🌱 **Cultivo:** {crop}\n"
                    "📅 **Fecha:** {date}\n"
                    "📊 **Métricas actuales:**\n{current_metrics}\n"
                    "💡 **Recomendaciones de IA:**\n{ai_recommendations}\n"
                    "🔧 **Acciones propuestas:**\n{proposed_actions}\n"
                    "📌 **Impacto estimado:** {estimated_impact}\n"
                    "🔗 **Evidencia en GaiaChain:** {gaiachain_tx}"
                ),
            },
        },
    )


def get_version_restrictions() -> Dict[str, Dict]:
    """Define las restricciones para versiones derivadas de SABIONDA_MASTER."""
    return {
        "LANDUM_PRO": {
            "allowed_modules": [
                "security",
                "production",
                "blockchain",
                "compliance",
                "analytics",
                "messaging",
                "iot",
            ],
            "restrictions": {
                "blockchain_write": False,
                "security_admin": False,
                "version_management": False,
                "debug_mode": False,
                "ai_autonomy": 70,
            },
            "tone": "technical_professional",
            "max_tokens": 128000,
        },
        "TECHNICIAN": {
            "allowed_modules": ["production", "iot", "maintenance"],
            "restrictions": {
                "blockchain_write": False,
                "security_admin": False,
                "compliance_edit": False,
                "version_management": False,
                "debug_mode": False,
                "ai_autonomy": 50,
            },
            "tone": "friendly_technical",
            "max_tokens": 64000,
        },
        "FARMER": {
            "allowed_modules": ["iot", "alerts", "basic_analytics"],
            "restrictions": {
                "blockchain_write": False,
                "security_admin": False,
                "compliance_edit": False,
                "version_management": False,
                "debug_mode": False,
                "advanced_analytics": False,
                "ai_autonomy": 30,
            },
            "tone": "extremeño_friendly",
            "max_tokens": 32000,
            "response_style": "simple_concise",
        },
        "AUDITOR": {
            "allowed_modules": ["compliance", "reports", "blockchain_read"],
            "restrictions": {
                "blockchain_write": False,
                "security_admin": False,
                "production_edit": False,
                "version_management": False,
                "debug_mode": False,
                "ai_autonomy": 20,
            },
            "tone": "formal_neutral",
            "max_tokens": 64000,
        },
        "STUDENT": {
            "allowed_modules": ["academy", "simulations", "basic_reports"],
            "restrictions": {
                "blockchain_write": False,
                "security_admin": False,
                "production_edit": False,
                "version_management": False,
                "debug_mode": False,
                "sensitive_data": False,
                "ai_autonomy": 10,
            },
            "tone": "educational_encouraging",
            "max_tokens": 16000,
            "response_style": "step_by_step",
        },
        "GUEST": {
            "allowed_modules": ["demo", "basic_info"],
            "restrictions": {
                "blockchain_write": False,
                "security_admin": False,
                "production_edit": False,
                "version_management": False,
                "debug_mode": False,
                "advanced_features": False,
                "sensitive_data": False,
                "ai_autonomy": 0,
            },
            "tone": "neutral_simple",
            "max_tokens": 8000,
            "response_style": "minimal",
        },
    }


if __name__ == "__main__":
    master_config = get_sabionda_master_config()
    print("Configuración SABIONDA_MASTER:", json.dumps(master_config.to_dict(), indent=2)[:500] + "...")
    version_restrictions = get_version_restrictions()
    for version, restrictions in version_restrictions.items():
        print(f"  {version}: {restrictions['tone']}, max_tokens={restrictions['max_tokens']}")
