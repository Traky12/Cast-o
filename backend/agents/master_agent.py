# backend/agents/master_agent.py
# Agente maestro orquestación CASTÚO-SYSTEM™ v2.0 — Mistral AI, Prometheus, normativas UE

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from backend.agents.selfhealing_agent import SelfHealingAgent
    from backend.agents.ecommerce_agent import ECommerceAgent
    from backend.agents.logistics_agent import LogisticsAgent
    from backend.agents.compliance_agent import ComplianceAgent
    from backend.agents.ai_agent import TunedAIAgent

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
    from prometheus_api_client import PrometheusConnect
    _PROMETHEUS = True
except ImportError:
    PrometheusConnect = None
    _PROMETHEUS = False


class MasterAgent:
    """
    Agente maestro para orquestación de CASTÚO-SYSTEM™.
    Usa Mistral AI para decisiones autónomas. Cumple ISO 27001:2022, NIS2, EU AI Act.
    Acepta dependencias inyectadas (selfhealing, ecommerce, logistics, compliance, ai) o las resuelve del inyector.
    """

    def __init__(
        self,
        selfhealing_agent: Optional["SelfHealingAgent"] = None,
        ecommerce_agent: Optional["ECommerceAgent"] = None,
        logistics_agent: Optional["LogisticsAgent"] = None,
        compliance_agent: Optional["ComplianceAgent"] = None,
        ai_agent: Optional["TunedAIAgent"] = None,
        opa_client: Any = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.mistral = None
        self.prometheus = None
        if _MISTRAL:
            try:
                self.mistral = MistralClient(api_key=__import__("os").getenv("MISTRAL_API_KEY_EU", ""))
            except Exception as e:
                self.logger.warning("Mistral no disponible: %s", e)
        if _PROMETHEUS:
            try:
                self.prometheus = PrometheusConnect(url=__import__("os").getenv("PROMETHEUS_URL", "http://localhost:9090"), disable_ssl=True)
            except Exception as e:
                self.logger.warning("Prometheus no disponible: %s", e)

        try:
            from backend.core.dependency_injector import injector
            self.agent_registry = {
                "deployment": None,
                "selfhealing": selfhealing_agent if selfhealing_agent is not None else injector.resolve("SelfHealingAgent"),
                "ecommerce": ecommerce_agent if ecommerce_agent is not None else injector.resolve("ECommerceAgent"),
                "logistics": logistics_agent if logistics_agent is not None else injector.resolve("LogisticsAgent"),
                "compliance": compliance_agent if compliance_agent is not None else injector.resolve("ComplianceAgent"),
                "ai": ai_agent if ai_agent is not None else injector.resolve("TunedAIAgent"),
            }
        except (ImportError, ValueError):
            self.agent_registry = {
                "deployment": None,
                "selfhealing": selfhealing_agent,
                "ecommerce": ecommerce_agent,
                "logistics": logistics_agent,
                "compliance": compliance_agent,
                "ai": ai_agent,
            }
        try:
            self.opa_client = opa_client or __import__("backend.compliance.opa_client", fromlist=["OPAClient"]).OPAClient()
        except Exception:
            self.opa_client = None
        try:
            from backend.compliance.automated_audit import AutomatedAuditSystem
            self.audit_system = AutomatedAuditSystem()
        except Exception:
            self.audit_system = None
        self.current_audit_id: Optional[str] = None

        self.encryption = None
        self.traceability = None
        self._private_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        try:
            from backend.security.end_to_end_encryption import EndToEndEncryption
            from backend.compliance.immutable_traceability import ImmutableTraceability
            self.encryption = EndToEndEncryption()
            self.traceability = ImmutableTraceability(self.encryption)
            self._private_key, self._public_key = self.encryption.generate_key_pair()
            if self.traceability:
                import hashlib
                self.traceability.register_event({
                    "type": "agent_start",
                    "agent_name": "master_agent",
                    "public_key_hash": hashlib.blake3(self._public_key).hexdigest() if hasattr(hashlib, "blake3") else hashlib.sha3_512(self._public_key).hexdigest(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "normative_references": ["ISO_27001:A.12.4.1", "GDPR:Art.30"],
                })
        except Exception as e:
            self.logger.debug("Cifrado/trazabilidad E2E no disponibles: %s", e)

        self.forensic_analyzer = None
        self.defense_system = None
        self.fl_coordinator = None
        self.gaiachain = None
        if self.encryption and self.traceability:
            try:
                from backend.security.forensic_analyzer import ForensicAnalyzer
                from backend.ai.secure_federated_learning import SecureFederatedLearningCoordinator
                from backend.ai.federated_defense import FederatedDefenseSystem
                self.forensic_analyzer = ForensicAnalyzer(self.encryption, self.traceability)
                self.fl_coordinator = SecureFederatedLearningCoordinator(self.encryption, self.traceability)
                self.defense_system = FederatedDefenseSystem(
                    self.encryption, self.traceability, self.fl_coordinator
                )
                self.fl_coordinator.enable_defense_system(self.defense_system)
                gaia_url = __import__("os").environ.get("GAIA_CHAIN_URL", "http://gaiachain-service.gaiachain:8080")
                gaia_key = __import__("os").environ.get("GAIA_CHAIN_API_KEY", "")
                from backend.compliance.gaiachain_integration import GaiaChainForensicRegistry
                self.gaiachain = GaiaChainForensicRegistry(gaia_url, gaia_key)
            except Exception as ex:
                self.logger.debug("Sistema de defensa forense no disponible: %s", ex)

    def _collect_network_metrics(self) -> List[Dict[str, Any]]:
        """Recolecta métricas de red (stub; en producción integrar con Prometheus/SNMP)."""
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bytes_in": 1024,
                "bytes_out": 512,
                "packets": 10,
            }
        ]

    def _collect_behavior_metrics(self) -> List[Dict[str, Any]]:
        """Recolecta métricas de comportamiento (stub; en producción integrar con logs/APM)."""
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "api_calls": 5,
                "db_queries": 3,
                "login_attempts": 0,
            }
        ]

    def _notify_security_team(self, payload: Dict[str, Any]) -> None:
        """Notifica al equipo de seguridad (stub; en producción enviar a Slack/PagerDuty)."""
        self.logger.warning("Security incident notification: %s", list(payload.keys()))

    async def _handle_security_incident(self, evidence: Dict[str, Any]) -> None:
        """Maneja incidentes de seguridad: GaiaChain, defensa, informe forense, notificación."""
        if not self.defense_system or not self.traceability:
            return
        try:
            if self.gaiachain:
                try:
                    gaia_resp = self.gaiachain.register_forensic_evidence(evidence)
                    evidence["gaiachain_tx"] = gaia_resp.get("transaction_hash") or gaia_resp.get("local_hash")
                except Exception as e:
                    self.logger.debug("GaiaChain register: %s", e)
            response = await self.defense_system.detect_and_respond((True, evidence))
            if self.encryption and self.traceability and self._public_key:
                from backend.compliance.forensic_audit import ForensicAuditGenerator
                gen = ForensicAuditGenerator(self.encryption, self.traceability, self._private_key)
                ts = evidence.get("timestamps", [datetime.now(timezone.utc).isoformat()])
                start = ts[0] if ts else datetime.now(timezone.utc).isoformat()
                audit_report = gen.generate_audit_report(start, datetime.now(timezone.utc).isoformat())
                report_path = "/var/traceability/incident_report.json"
                gen.export_audit_report(audit_report, report_path, self._public_key)
            self._notify_security_team({
                "type": "security_incident",
                "evidence_hash": evidence.get("evidence_hash"),
                "response": response,
                "gaiachain_tx": evidence.get("gaiachain_tx"),
            })
        except Exception as e:
            self.logger.exception("Error handling security incident: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "security_incident_handling_error",
                    "error": str(e),
                    "severity": "critical",
                    "evidence_hash": evidence.get("evidence_hash", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            raise

    async def _execute_action(self, action: Dict[str, Any]) -> None:
        """Ejecuta una acción con cifrado y trazabilidad cuando están disponibles."""
        if not self.encryption or not self.traceability or not self._public_key or not self._private_key:
            cmd = action.get("command", "")
            if cmd and action.get("type") == "command":
                try:
                    subprocess.run(cmd, shell=True, check=True, timeout=30)
                except subprocess.CalledProcessError as e:
                    self.logger.error("Fallo comando: %s", e)
            return
        try:
            action_envelope = self.encryption.create_encrypted_envelope(
                action,
                self._public_key,
                metadata={"action_type": action.get("type", "unknown"), "agent": "master_agent"},
            )
            self.traceability.register_event({
                "type": "action_execution",
                "action_hash": action_envelope["integrity"]["hash"],
                "metadata": action_envelope["metadata"],
                "normative_references": ["ISO_27001:A.16.1.1", "GDPR:Art.32"],
            })
            decrypted_action, valid = self.encryption.verify_and_decrypt_envelope(
                action_envelope,
                self._private_key,
            )
            if not valid:
                raise ValueError("Acción inválida (falló verificación de integridad)")
            if decrypted_action.get("type") == "command":
                cmd = decrypted_action.get("command", "")
                if cmd:
                    subprocess.run(cmd, shell=True, check=True, timeout=30)
            self.traceability.register_event({
                "type": "action_completed",
                "action_hash": action_envelope["integrity"]["hash"],
                "status": "success",
                "normative_references": ["ISO_27001:A.16.1.4"],
            })
        except Exception as e:
            self.logger.error("Error en _execute_action: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "action_error",
                    "error": str(e),
                    "severity": "critical",
                    "normative_references": ["ISO_27001:A.16.1.1"],
                })
            raise

    async def _validate_action_with_opa(self, action: Dict[str, Any]) -> bool:
        """Valida la acción con OPA (o DynamicOPAValidator si está disponible)."""
        if not self.opa_client:
            self.logger.warning("OPA no disponible. Validación omitida.")
            return True
        try:
            try:
                from backend.compliance.dynamic_opa import DynamicOPAValidator
                validator = DynamicOPAValidator()
                result = await validator.validate_action(
                    {**action, "type": action.get("type", "command")},
                    context={"agent_name": "master_agent", "system": "CASTÚO-SYSTEM"},
                )
                return result.get("compliant", False)
            except ImportError:
                pass
            opa_input = {
                "action": {**action, "type": action.get("type", "command")},
                "metadata": {
                    "normative": action.get("normative_reference", "ISO_27001:A.12.6.1"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "agent": getattr(self, "agent_name", "master_agent"),
                },
            }
            result = await asyncio.to_thread(self.opa_client.evaluate_and_register, opa_input)
            return result.get("compliant", False)
        except Exception as e:
            self.logger.error("Error en OPA: %s", e)
            return False

    async def _consult_mistral(self, prompt: str, model: str = "mistral-large-latest") -> Dict[str, Any]:
        """Consulta a Mistral AI para toma de decisiones."""
        if not self.mistral:
            return {"actions": [], "overall_status": "normal", "recommendations": ["Mistral no configurado"]}
        try:
            messages = [
                ChatMessage(
                    role="system",
                    content="Eres el Agente Maestro de CASTÚO-SYSTEM™. Responde en JSON. Normativas: ISO 27001, GDPR, NIS2, EU AI Act.",
                ),
                ChatMessage(role="user", content=prompt),
            ]
            response = self.mistral.chat(model=model, messages=messages, temperature=0.1)
            text = response.choices[0].message.content
            return json.loads(text)
        except Exception as e:
            self.logger.error("Error Mistral: %s", e)
            return {"error": str(e), "actions": []}

    async def monitor_system(self) -> None:
        """Monitorea el sistema y toma decisiones autónomas."""
        if self.audit_system and self.current_audit_id is None:
            self.current_audit_id = self.audit_system.start_audit("system_monitoring", "rolling")
        while True:
            try:
                if self.forensic_analyzer and self.defense_system:
                    network_data = self._collect_network_metrics()
                    behavior_data = self._collect_behavior_metrics()
                    net_anomaly, net_evidence = self.forensic_analyzer.analyze_network_traffic(network_data)
                    if net_anomaly:
                        await self._handle_security_incident(net_evidence)
                    beh_anomaly, beh_evidence = self.forensic_analyzer.analyze_behavior(behavior_data)
                    if beh_anomaly:
                        await self._handle_security_incident(beh_evidence)
                metrics: Dict[str, float] = {}
                if self.prometheus:
                    try:
                        q = self.prometheus.custom_query('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)')
                        if q:
                            metrics["cpu_usage"] = float(q[0]["value"][1])
                        else:
                            metrics["cpu_usage"] = 0.0
                    except Exception:
                        metrics["cpu_usage"] = 0.0
                else:
                    metrics["cpu_usage"] = 0.0
                    metrics["memory_usage"] = 0.0
                    metrics["error_rate"] = 0.0

                prompt = f"""
                Métricas: {json.dumps(metrics)}.
                Normativas: ISO 27001:2022, NIS2, EU AI Act.
                Responde JSON: {{ "actions": [ {{ "command": "...", "priority": "low|medium|high", "justification": "..." }} ], "overall_status": "normal|warning|critical", "recommendations": [] }}
                """
                decision = await self._consult_mistral(prompt)
                self.logger.info("Decisión Mistral: %s", json.dumps(decision)[:500])

                for action in decision.get("actions") or []:
                    if not await self._validate_action_with_opa(action):
                        self.logger.warning("Acción bloqueada por OPA: %s", action.get("type", action.get("command", ""))[:80])
                        if self.audit_system and self.current_audit_id:
                            self.audit_system.add_audit_event(self.current_audit_id, {
                                "type": "agent_decision",
                                "action": action.get("command", ""),
                                "compliant": False,
                                "normative": "OPA",
                                "severity": "high",
                            })
                        continue
                    if self.audit_system and self.current_audit_id:
                        self.audit_system.add_audit_event(self.current_audit_id, {
                            "type": "agent_decision",
                            "action": action.get("command", ""),
                            "compliant": True,
                            "severity": "low",
                        })
                    action_with_type = {**action, "type": action.get("type", "command")}
                    if action.get("command"):
                        if self.encryption and self.traceability:
                            await self._execute_action(action_with_type)
                        else:
                            cmd = action.get("command", "")
                            if cmd.startswith("docker ") and "restart" in cmd:
                                try:
                                    subprocess.run(cmd, shell=True, check=True, timeout=30)
                                except subprocess.CalledProcessError as e:
                                    self.logger.error("Fallo comando: %s", e)

                try:
                    from backend.security.pq_crypto import PostQuantumCrypto
                    crypto = PostQuantumCrypto()
                    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "metrics": metrics, "decision": decision, "agent": "master_agent"}
                    crypto.kyber_encrypt(json.dumps(record))
                except Exception as e:
                    self.logger.debug("Registro GaiaChain omitido: %s", e)

            except Exception as e:
                self.logger.error("Error en monitor: %s", e)
                if self.audit_system and self.current_audit_id:
                    self.audit_system.add_audit_event(self.current_audit_id, {
                        "type": "error",
                        "description": str(e),
                        "severity": "critical",
                        "normative": "ISO_27001:A.16.1.1",
                    })
                await self._trigger_self_healing()

            await asyncio.sleep(60)

    async def _trigger_self_healing(self) -> None:
        """Activa el agente de auto-reparación."""
        if self.agent_registry.get("selfhealing") is None:
            try:
                from backend.agents.selfhealing_agent import SelfHealingAgent
                self.agent_registry["selfhealing"] = SelfHealingAgent()
            except Exception as e:
                self.logger.warning("SelfHealing no disponible: %s", e)
                return
        agent = self.agent_registry["selfhealing"]
        if hasattr(agent, "trigger_self_healing"):
            await agent.trigger_self_healing()

    async def run(self) -> None:
        """Ejecuta el agente maestro."""
        self.logger.info("Iniciando Agente Maestro CASTÚO-SYSTEM™")
        await self.monitor_system()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    try:
        from backend.core.dependency_injector import injector
        from backend.agents.selfhealing_agent import SelfHealingAgent
        from backend.agents.ecommerce_agent import ECommerceAgent
        from backend.agents.logistics_agent import LogisticsAgent
        from backend.agents.compliance_agent import ComplianceAgent
        from backend.agents.ai_agent import TunedAIAgent
        injector.register("SelfHealingAgent", SelfHealingAgent())
        injector.register("ECommerceAgent", ECommerceAgent())
        injector.register("LogisticsAgent", LogisticsAgent())
        injector.register("ComplianceAgent", ComplianceAgent())
        injector.register("TunedAIAgent", TunedAIAgent())
        agent = injector.inject(MasterAgent)
    except (ImportError, ValueError):
        agent = MasterAgent()
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
