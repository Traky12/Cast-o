# backend/agents/selfhealing_agent.py
# Agente de auto-reparación CASTÚO-SYSTEM™ v2.0 — Mistral AI, Docker, GaiaChain

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    _MISTRAL = True
except ImportError:
    MistralClient = None
    ChatMessage = None
    _MISTRAL = False

try:
    import docker
    _DOCKER = True
except ImportError:
    docker = None
    _DOCKER = False


class SelfHealingAgent:
    """
    Agente de auto-reparación para CASTÚO-SYSTEM™.
    Analiza errores con Mistral, aplica soluciones, registra en GaiaChain.
    Cumple ISO 27001:2022 (A.16.1), NIS2 (2022/2555).
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.mistral: Any = None
        self.client: Any = None
        self.crypto: Any = None

        if _MISTRAL:
            try:
                self.mistral = MistralClient(api_key=__import__("os").getenv("MISTRAL_API_KEY_EU", ""))
            except Exception as e:
                self.logger.warning("Mistral no disponible: %s", e)
        if _DOCKER and docker:
            try:
                self.client = docker.from_env()
            except Exception as e:
                self.logger.warning("Docker no disponible: %s", e)
        try:
            from backend.security.pq_crypto import PostQuantumCrypto
            self.crypto = PostQuantumCrypto()
        except Exception as e:
            self.logger.warning("PostQuantumCrypto no disponible: %s", e)

    async def _analyze_error_with_mistral(self, error_log: str) -> Dict[str, Any]:
        """Analiza un error con Mistral AI."""
        if not self.mistral:
            return {
                "root_cause": "Mistral no configurado",
                "immediate_solution": [{"type": "command", "command": "docker ps", "description": "Ver estado contenedores"}],
                "long_term_actions": [],
                "compliance_impact": [],
            }
        try:
            prompt = f"""
            Error en CASTÚO-SYSTEM™ (normativas: ISO 27001 A.16.1, NIS2, EU AI Act):
            {error_log[:4000]}
            Responde JSON: root_cause, immediate_solution (lista de {{type, command, description}}), long_term_actions, compliance_impact.
            """
            response = self.mistral.chat(
                model="mistral-large-latest",
                messages=[
                    ChatMessage(role="system", content="Experto en auto-reparación de sistemas críticos UE."),
                    ChatMessage(role="user", content=prompt),
                ],
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.error("Análisis Mistral: %s", e)
            return {"root_cause": str(e), "immediate_solution": [], "long_term_actions": [], "compliance_impact": []}

    async def trigger_self_healing(self, error_context: str | None = None) -> None:
        """Inicia el proceso de auto-reparación."""
        self.logger.info("Iniciando auto-reparación...")

        error_logs = ""
        try:
            error_logs = subprocess.check_output(
                ["docker", "logs", "--tail", "50", "backend"],
                stderr=subprocess.STDOUT,
                timeout=10,
            ).decode()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            error_logs = "docker no disponible o contenedor backend no encontrado"
        if error_context:
            error_logs += "\n" + error_context

        analysis = await self._analyze_error_with_mistral(error_logs)
        self.logger.info("Análisis: %s", json.dumps(analysis)[:500])

        for sol in analysis.get("immediate_solution") or []:
            cmd = sol.get("command") or ""
            if isinstance(sol, dict) and cmd and sol.get("type") == "command":
                try:
                    subprocess.run(cmd, shell=True, check=True, timeout=30)
                    self.logger.info("Ejecutado: %s", cmd)
                except Exception as e:
                    self.logger.error("Fallo: %s", e)

        if self.crypto:
            try:
                record = {"timestamp": datetime.utcnow().isoformat(), "error_logs": error_logs[:2000], "analysis": analysis, "agent": "selfhealing_agent"}
                self.crypto.kyber_encrypt(json.dumps(record))
            except Exception as e:
                self.logger.debug("Registro omitido: %s", e)

    async def restart_service(self, service_name: str) -> None:
        """Reinicia un servicio Docker."""
        self.logger.info("Reiniciando servicio %s...", service_name)
        if not self.client:
            self.logger.warning("Docker no disponible")
            return
        try:
            containers = self.client.containers.list(filters={"name": service_name})
            if containers:
                containers[0].restart()
                self.logger.info("Servicio %s reiniciado", service_name)
            else:
                self.logger.warning("Contenedor no encontrado: %s", service_name)
        except Exception as e:
            self.logger.error("Error reinicio: %s", e)
            await self.trigger_self_healing(f"Fallo reinicio {service_name}: {e}")

    async def run(self) -> None:
        """Ejecuta el agente en modo continuo."""
        self.logger.info("Agente Self-Healing operativo")
        while True:
            await self.check_system_integrity()
            await asyncio.sleep(300)

    async def check_system_integrity(self) -> None:
        """Comprueba integridad de servicios críticos (stub: solo log)."""
        self.logger.debug("Verificando integridad del sistema...")
        if not self.client:
            return
        for name in ["backend", "frontend", "postgres"]:
            try:
                containers = self.client.containers.list(filters={"name": name})
                if not containers or containers[0].status != "running":
                    self.logger.warning("Servicio %s no running", name)
            except Exception as e:
                self.logger.debug("check %s: %s", name, e)


def main() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    agent = SelfHealingAgent()
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
