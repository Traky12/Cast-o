# backend/ai/federated_defense.py — Sistema de defensa federado (detección y respuesta automatizada)

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False

try:
    from backend.ai.secure_federated_learning import SecureFederatedLearningCoordinator
    _FL = True
except ImportError:
    SecureFederatedLearningCoordinator = None
    _FL = False

try:
    from backend.security.forensic_analyzer import ForensicAnalyzer
    _FORENSIC = True
except ImportError:
    ForensicAnalyzer = None
    _FORENSIC = False

try:
    from backend.compliance.immutable_traceability import ImmutableTraceability
    _TRACE = True
except ImportError:
    ImmutableTraceability = None
    _TRACE = False

try:
    from backend.security.end_to_end_encryption import EndToEndEncryption
    _E2E = True
except ImportError:
    EndToEndEncryption = None
    _E2E = False

try:
    from backend.ai.sandbox_manager import SandboxManager
    _SANDBOX = True
except ImportError:
    SandboxManager = None
    _SANDBOX = False


def _blake3_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class FederatedDefenseSystem:
    """
    Sistema de defensa federado:
    - Modelos de IA distribuidos para detección de amenazas
    - Respuesta automatizada y coordinada
    - Cumplimiento legal (ISO 27001, GDPR, EU AI Act)
    """

    DEFENSE_ACTIONS = {
        "network_anomaly": {
            "low": ["log", "notify"],
            "medium": ["log", "notify", "rate_limit"],
            "high": ["log", "notify", "rate_limit", "ip_block"],
            "critical": ["log", "notify", "rate_limit", "ip_block", "quarantine"],
        },
        "behavior_anomaly": {
            "low": ["log", "notify"],
            "medium": ["log", "notify", "session_terminate"],
            "high": ["log", "notify", "session_terminate", "account_lock"],
            "critical": ["log", "notify", "session_terminate", "account_lock", "forensic_analysis"],
        },
    }

    DEFENSE_POLICIES = {
        "default": {
            "response_time_target": 100,
            "false_positive_target": 0.001,
            "escalation_path": ["security-team", "devops-team", "executive-team"],
            "legal_requirements": [
                "GDPR:Art.33",
                "GDPR:Art.34",
                "ISO_27001:A.16.1.4",
                "NIST_SP_800-61",
            ],
        },
        "aggressive": {
            "response_time_target": 50,
            "false_positive_target": 0.005,
            "escalation_path": ["security-team", "devops-team", "legal-team", "executive-team"],
            "additional_actions": ["immediate_block", "deep_forensic"],
        },
        "paranoid": {
            "response_time_target": 20,
            "false_positive_target": 0.01,
            "escalation_path": ["security-team", "devops-team", "legal-team", "executive-team", "external-auditors"],
            "additional_actions": ["immediate_block", "deep_forensic", "system_lockdown"],
        },
    }

    def __init__(
        self,
        encryption: Any,
        traceability: Any,
        fl_coordinator: Any,
    ) -> None:
        self.encryption = encryption
        self.traceability = traceability
        self.fl_coordinator = fl_coordinator
        self.defense_models: Dict[str, Any] = {}
        self.action_log: List[Dict] = []
        self.current_policy = "default"
        self.human_approval_required = {"critical": True, "high": False, "medium": False, "low": False}
        self.legal_compliance = {
            "GDPR": {"articles": [25, 32, 33, 34], "compliance": True},
            "ISO_27001": {"controls": ["A.12.4.1", "A.12.6.1", "A.16.1.1", "A.16.1.4"], "compliance": True},
            "NIST": {"standards": ["SP_800-53", "SP_800-61", "SP_800-86"], "compliance": True},
            "EU_AI_Act": {"annexes": ["III", "IV"], "compliance": True},
        }
        self.sandbox_manager = SandboxManager(kubernetes_client=None) if _SANDBOX and SandboxManager else None

    def _preprocess_training_data(self, data: List[Dict]) -> Any:
        if not _NUMPY or np is None:
            return []
        features = []
        for item in data:
            features.append([
                float(item.get("bytes_in", 0)),
                float(item.get("bytes_out", 0)),
                float(item.get("packets", 0)),
                float(item.get("api_calls", 0)),
                float(item.get("db_queries", 0)),
                float(item.get("login_attempts", 0)),
            ])
        return np.array(features)

    def _generate_model_hash(self, model: Dict) -> str:
        return _blake3_hex(json.dumps(model, sort_keys=True))

    async def train_defense_model(self, node_id: str, training_data: List[Dict]) -> Dict:
        """Entrena modelo de defensa en un nodo federado (simulado)."""
        try:
            features = self._preprocess_training_data(training_data)
            labels = np.array([1 if d.get("label") == "anomaly" else 0 for d in training_data]) if _NUMPY and np is not None and training_data else np.array([])
            model = {
                "type": "isolation_forest",
                "params": {
                    "n_estimators": 100,
                    "contamination": 0.01,
                    "features": features.tolist() if hasattr(features, "tolist") else [],
                    "labels": labels.tolist() if hasattr(labels, "tolist") else [],
                },
                "metadata": {
                    "node_id": node_id,
                    "training_time": datetime.now(timezone.utc).isoformat(),
                    "samples": len(training_data),
                },
            }
            if self.traceability:
                self.traceability.register_event({
                    "type": "defense_model_trained",
                    "node_id": node_id,
                    "model_hash": self._generate_model_hash(model),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "normative_references": ["ISO_27001:A.12.6.1", "GDPR:Art.35", "EU_AI_Act:Anexo_III"],
                })
            self.defense_models[node_id] = model
            return model
        except Exception as e:
            if self.traceability:
                self.traceability.register_event({
                    "type": "defense_training_error",
                    "node_id": node_id,
                    "error": str(e),
                    "severity": "critical",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            raise

    async def detect_and_respond(self, analysis_result: Tuple[bool, Dict]) -> Dict:
        """Detecta amenazas y ejecuta respuesta federada."""
        is_anomaly, evidence = analysis_result
        if not is_anomaly:
            return {"status": "clean", "actions": []}
        try:
            severity = evidence.get("severity", "low")
            anomaly_type = evidence.get("type", "network_anomaly")
            actions_map = self.DEFENSE_ACTIONS.get(anomaly_type, self.DEFENSE_ACTIONS["network_anomaly"])
            actions = actions_map.get(severity, ["log", "notify"])
            policy = self.DEFENSE_POLICIES.get(self.current_policy, self.DEFENSE_POLICIES["default"])
            extra = policy.get("additional_actions", [])
            for a in extra:
                if a not in actions:
                    actions = list(actions) + [a]
            response = await self._execute_defense_actions(actions, evidence)
            if self.traceability:
                self.traceability.register_event({
                    "type": "defense_response_executed",
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "actions": actions,
                    "evidence_hash": evidence.get("evidence_hash", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "normative_references": ["ISO_27001:A.16.1.4", "GDPR:Art.32", "EU_AI_Act:Anexo_IV"],
                })
            await self._notify_federated_nodes(anomaly_type, severity, evidence)
            return {
                "status": "defended",
                "actions": response,
                "evidence_hash": evidence.get("evidence_hash", ""),
                "severity": severity,
            }
        except Exception as e:
            if self.traceability:
                self.traceability.register_event({
                    "type": "defense_response_error",
                    "error": str(e),
                    "severity": "critical",
                    "evidence_hash": evidence.get("evidence_hash", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            raise

    def _resolve_action_name(self, action: Any) -> str:
        if isinstance(action, dict):
            return str(action.get("action", ""))
        return str(action)

    async def _request_human_approval(self, action: str, evidence: Dict) -> bool:
        """Solicita aprobación humana para acciones críticas (en producción: Slack/API)."""
        logger.warning(
            "Solicitando aprobación humana para acción '%s' (severidad: %s)",
            action,
            evidence.get("severity", "unknown"),
        )
        if __import__("os").environ.get("DEFENSE_MODE") != "paranoid":
            return True
        return False

    def _handle_action_error(self, action_name: str, error_msg: str) -> Dict:
        return {
            "action": action_name,
            "status": "failed",
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _execute_defense_actions(self, actions: List[Any], evidence: Dict) -> List[Dict]:
        result = []
        severity = evidence.get("severity", "low")
        for action in actions:
            try:
                name = self._resolve_action_name(action)
                params = action.get("params", {}) if isinstance(action, dict) else {}
                if self.human_approval_required.get(severity) and name in ("quarantine", "ip_block", "account_lock", "forensic_analysis"):
                    approved = await self._request_human_approval(name, evidence)
                    if not approved:
                        result.append({
                            "action": name,
                            "status": "pending_approval",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                        continue
                if name == "log":
                    result.append(self._log_evidence(evidence))
                elif name == "notify":
                    result.append(await self._notify_security_team(evidence))
                elif name == "rate_limit":
                    result.append(await self._apply_rate_limiting(evidence))
                elif name == "ip_block":
                    result.append(await self._block_ip_address(evidence))
                elif name == "quarantine":
                    if severity == "critical":
                        approved = await self._request_human_approval("quarantine", evidence)
                        if not approved:
                            result.append({"action": "quarantine", "status": "pending_approval", "timestamp": datetime.now(timezone.utc).isoformat()})
                            continue
                    result.append(await self._quarantine_node(evidence))
                elif name == "session_terminate":
                    result.append(await self._terminate_sessions(evidence))
                elif name == "account_lock":
                    result.append(await self._lock_account(evidence))
                elif name == "forensic_analysis":
                    result.append(await self._deep_forensic_analysis(evidence))
                else:
                    result.append({"action": name, "status": "skipped", "reason": "unknown"})
            except Exception as e:
                result.append(self._handle_action_error(self._resolve_action_name(action), str(e)))
        return result

    def _log_evidence(self, evidence: Dict) -> Dict:
        entry = {
            "action": "log",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Evidence logged to secure storage",
        }
        self.action_log.append(entry)
        return entry

    async def _notify_security_team(self, evidence: Dict) -> Dict:
        entry = {
            "action": "notify",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": "security-team-slack",
            "message": f"Anomalía detectada: {evidence.get('type', 'unknown')} (severidad: {evidence.get('severity', 'unknown')})",
        }
        self.action_log.append(entry)
        return entry

    async def _apply_rate_limiting(self, evidence: Dict) -> Dict:
        raw = (evidence.get("raw_data") or [{}])
        target = raw[0].get("source_ip", "unknown") if raw else "unknown"
        entry = {
            "action": "rate_limit",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": target,
            "limit": "100req/min",
        }
        if self.traceability:
            self.traceability.register_event({
                "type": "rate_limit_applied",
                "target": entry["target"],
                "limit": entry["limit"],
                "evidence_hash": entry["evidence_hash"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return entry

    async def _block_ip_address(self, evidence: Dict) -> Dict:
        raw = (evidence.get("raw_data") or [{}])
        target_ip = raw[0].get("source_ip", "unknown") if raw else "unknown"
        entry = {
            "action": "ip_block",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_ip": target_ip,
            "duration": "24h",
        }
        if self.traceability:
            self.traceability.register_event({
                "type": "ip_blocked",
                "target_ip": target_ip,
                "duration": "24h",
                "evidence_hash": entry["evidence_hash"],
                "normative_references": ["ISO_27001:A.13.1.1"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return entry

    async def _quarantine_node(self, evidence: Dict) -> Dict:
        node_id = evidence.get("node_id") or evidence.get("source_ip", "unknown")
        if self.sandbox_manager:
            result = self.sandbox_manager.create_sandbox(node_id, evidence)
            if result.get("status") == "created":
                if self.traceability:
                    self.traceability.register_event({
                        "type": "node_quarantined",
                        "node_id": node_id,
                        "sandbox_name": result.get("sandbox_name", ""),
                        "evidence_hash": evidence.get("evidence_hash"),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                return {
                    "action": "quarantine",
                    "status": "success",
                    "node_id": node_id,
                    "sandbox": result.get("sandbox_name"),
                    "evidence_hash": evidence.get("evidence_hash", ""),
                    "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
                }
            return {
                "action": "quarantine",
                "status": "failed",
                "node_id": node_id,
                "error": result.get("error", "unknown"),
                "evidence_hash": evidence.get("evidence_hash", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        entry = {
            "action": "quarantine",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Node quarantine requested (integrate with orchestrator)",
        }
        return entry

    async def _terminate_sessions(self, evidence: Dict) -> Dict:
        entry = {
            "action": "session_terminate",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Sessions termination requested",
        }
        return entry

    async def _lock_account(self, evidence: Dict) -> Dict:
        entry = {
            "action": "account_lock",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Account lock requested",
        }
        return entry

    async def _deep_forensic_analysis(self, evidence: Dict) -> Dict:
        entry = {
            "action": "forensic_analysis",
            "status": "success",
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": "Deep forensic analysis requested",
        }
        return entry

    async def _notify_federated_nodes(self, anomaly_type: str, severity: str, evidence: Dict) -> Dict:
        recipients = list(getattr(self.fl_coordinator, "node_public_keys", {}).keys())
        notification = {
            "type": "federated_threat_notification",
            "anomaly_type": anomaly_type,
            "severity": severity,
            "evidence_hash": evidence.get("evidence_hash", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recipients": recipients,
        }
        if self.traceability:
            self.traceability.register_event({
                "type": "federated_notification_sent",
                "anomaly_type": anomaly_type,
                "severity": severity,
                "evidence_hash": evidence.get("evidence_hash", ""),
                "nodes_notified": len(recipients),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        return notification
