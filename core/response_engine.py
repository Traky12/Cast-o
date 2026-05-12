# -*- coding: utf-8 -*-
"""
Motor de respuestas adaptativas SABIONDA.
Genera respuestas personalizadas según perfil, tono y contexto.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.profile_engine import ProfileManager


class AdaptiveResponseEngine:
    """Motor para generar respuestas adaptadas al perfil del usuario."""

    def __init__(self, profile_manager: ProfileManager) -> None:
        self.profile_manager = profile_manager
        self.response_templates = self._load_response_templates()

    def _load_response_templates(self) -> Dict[str, Dict[str, str]]:
        """Carga plantillas de respuesta por perfil y tono."""
        return {
            "SABIONDA_MASTER_LANDUM": {
                "greeting": (
                    "🌍 **SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO** activado.\n"
                    "🔐 **Acceso total** a CASTUO-SYSTEM v5.0 | **Modo: Gestión Avanzada**\n"
                    "📌 **Contexto:** {context}\n"
                    "💡 **¿En qué área necesitas profundizar hoy?** (seguridad/blockchain/producción/red_europea)"
                ),
                "security_alert": (
                    "🚨 **ALERTA DE SEGURIDAD NIVEL {level}** 🚨\n"
                    "📍 **Ubicación:** {location}\n"
                    "🕒 **Hora:** {time}\n"
                    "📄 **Detalles:** {details}\n"
                    "⚡ **Acciones recomendadas:**\n{actions}\n"
                    "🔗 **Transacción GaiaChain:** [Ver en blockchain]({gaiachain_tx})"
                ),
                "production_report": (
                    "📊 **REPORTE DE PRODUCCIÓN (Lote: {batch_id})**\n"
                    "🌱 **Cultivo:** {crop}\n"
                    "📅 **Fecha:** {date}\n"
                    "📦 **Cantidad:** {quantity} kg\n"
                    "💰 **Valor:** €{value}\n"
                    "🔒 **Trazabilidad:** [GaiaChain TX]({gaiachain_tx})\n"
                    "📈 **Rendimiento vs. objetivo:** {yield_vs_target}%\n"
                    "🚀 **Próximos pasos:** {next_steps}"
                ),
                "error": (
                    "❌ **ERROR CRÍTICO DETECTADO** ❌\n"
                    "📌 **Código:** {error_code}\n"
                    "🔧 **Detalles técnicos:** {details}\n"
                    "🛠 **Solución propuesta:** {solution}\n"
                    "📞 **Contacto de soporte:** {support_contact}"
                ),
            },
            "LANDUM_PRO": {
                "greeting": (
                    "👩‍💼 **Modo LANDUM_PRO activado** | **CASTUO-SYSTEM v5.0**\n"
                    "🔹 **Perfil:** Gestión Avanzada (Nivel 90/100)\n"
                    "🔹 **Módulos disponibles:** seguridad, producción, blockchain, cumplimiento\n"
                    "💡 **¿Qué necesitas analizar hoy?** (Ej: 'estado del lote CASTUA-2026-001')"
                ),
                "security_alert": (
                    "⚠️ **ALERTA DE SEGURIDAD (Nivel {level})** ⚠️\n"
                    "📍 **Ubicación:** {location}\n"
                    "🕒 **Hora:** {time}\n"
                    "📄 **Detalles:** {details}\n"
                    "🔗 **Acciones automáticas aplicadas:** {auto_actions}\n"
                    "📌 **Recomendación:** {recommendation}"
                ),
                "compliance_report": (
                    "📋 **INFORME DE CUMPLIMIENTO (AEMPS/ISO 27001)**\n"
                    "📅 **Fecha:** {date}\n"
                    "🏢 **Operador:** {operator}\n"
                    "✅ **Normativas cumplidas:** {compliant_count}/{total}\n"
                    "⚠️ **Incidencias:** {issues}\n"
                    "🔗 **Evidencia en GaiaChain:** {gaiachain_tx}\n"
                    "📌 **Próxima auditoría:** {next_audit}"
                ),
            },
            "FARMER": {
                "greeting": (
                    "🌱 ¡Ey crack! **Sabionda** por aquí, ¿qué tal va esa finca? 😎\n"
                    "🔹 **Hoy tenemos:**\n"
                    "   - 🌧️ **Riego:** {irrigation_status}\n"
                    "   - 🚜 **Tareas pendientes:** {pending_tasks}\n"
                    "   - 📊 **Rendimiento:** {yield_status}\n"
                    "💬 **Dime, ¿en qué te ayudo?** (ej: '¿Cómo está el lote 3?')"
                ),
                "alert": (
                    "🚨 **¡Ojo con el lote {batch_id}, {farmer_name}!** 🚨\n"
                    "📌 **Problema:** {issue}\n"
                    "💡 **Mi recomendación:** {recommendation}\n"
                    "🔧 **¿Quieres que active el protocolo automático?** (Sí/No)"
                ),
                "harvest_report": (
                    "🌾 **¡Buenas noticias, {farmer_name}!** 🎉\n"
                    "📊 **Cosecha del lote {batch_id} completada:**\n"
                    "   - 🌱 **Cultivo:** {crop}\n"
                    "   - 📦 **Cantidad:** {quantity} kg\n"
                    "   - 💰 **Valor estimado:** €{value}\n"
                    "   - 🌟 **Calidad:** {quality} (THC: {thc}%, CBD: {cbd}%)\n"
                    "🔗 **Certificado:** [Ver en GaiaChain]({gaiachain_tx})\n"
                    "💡 **Próximo paso:** {next_step}"
                ),
                "error": (
                    "❌ **Ups, {farmer_name}, tenemos un problemilla...** 😅\n"
                    "📌 **Error:** {error}\n"
                    "🔧 **Solución rápida:** {quick_fix}\n"
                    "📞 **Si no se soluciona, llama a:** {support_phone}"
                ),
            },
            "STUDENT": {
                "greeting": (
                    "🎓 **¡Hola, futuro experto en agritech!** 🌱\n"
                    "📚 **Hoy aprenderemos sobre:** {topic}\n"
                    "🔹 **Nivel:** {level}\n"
                    "💡 **Objetivo de la sesión:** {objective}\n"
                    "📌 **¿Por dónde empezamos?** (teoría/práctica/ejemplos)"
                ),
                "lesson": (
                    "📖 **LECCIÓN: {lesson_title}**\n"
                    "🎯 **Objetivos:**\n{objectives}\n"
                    "📚 **Contenido:**\n{content}\n"
                    "💡 **Ejemplo práctico:**\n{example}\n"
                    "📝 **Ejercicio:** {exercise}\n"
                    "❓ **¿Alguna duda?** (Escribe 'siguiente' para continuar)"
                ),
                "quiz_result": (
                    "📊 **RESULTADO DEL QUIZ: {score}%**\n"
                    "🎉 **¡{feedback}!**\n"
                    "🔹 **Temas dominados:** {strong_areas}\n"
                    "📚 **Para mejorar:** {weak_areas}\n"
                    "💡 **Recomendación:** {recommendation}\n"
                    "📌 **Próximo tema:** {next_topic}"
                ),
            },
            "GUEST": {
                "greeting": "👋 **Modo demo** | CASTUO-SYSTEM v5.0\n💡 Explora las opciones disponibles.",
                "alert": "⚠️ **Alerta:** {issue}\n💡 {recommendation}",
                "error": "❌ **Error:** {error}",
            },
        }

    def generate_response(
        self,
        session_id: str,
        template_key: str,
        context: Dict[str, str],
    ) -> str:
        """Genera una respuesta adaptada al perfil del usuario."""
        session = self.profile_manager.get_session_info(session_id)
        if not session:
            return "❌ Error: Sesión no válida. Inicia sesión nuevamente."

        profile_id = session["profile"].get("profile_type", "GUEST")
        templates = self.response_templates.get(profile_id, self.response_templates["GUEST"])
        template = templates.get(template_key)

        if not template:
            template = self.response_templates["GUEST"].get(template_key, "❌ Plantilla no encontrada.")

        try:
            return template.format(**context)
        except KeyError:
            return template

    def get_available_templates(self, session_id: str) -> List[str]:
        """Obtiene las plantillas disponibles para una sesión."""
        session = self.profile_manager.get_session_info(session_id)
        if not session:
            return []
        profile_id = session["profile"].get("profile_type", "GUEST")
        return list(self.response_templates.get(profile_id, {}).keys())


if __name__ == "__main__":
    from blockchain.gaia_chain import GaiaChainClient
    from core.profile_engine import ProfileManager

    pm = ProfileManager(gaiachain_client=GaiaChainClient())
    engine = AdaptiveResponseEngine(pm)
    farmer_session = pm.create_session("juan_perez@finca.es", "FARMER")
    alert_response = engine.generate_response(
        farmer_session,
        "alert",
        {
            "batch_id": "CASTUA-2026-001",
            "farmer_name": "Juan",
            "issue": "el nivel de humedad está por debajo del 30% (óptimo: 60-70%)",
            "recommendation": "activa el riego automático con el comando: `/riego 1234 15ml`",
        },
    )
    safe = alert_response.encode("ascii", "replace").decode("ascii")
    print("Respuesta FARMER (longitud %d):" % len(alert_response), safe[:100] + "...")
    pm.close_session(farmer_session)
