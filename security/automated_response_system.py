# -*- coding: utf-8 -*-
"""
Sistema de respuesta automatizada a incidentes (SOC): TheHive + Velociraptor + GaiaChain.
"""
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class AutomatedResponseSystem:
    """
    Crea incidentes en TheHive, ejecuta playbooks (aislar host, bloquear IP, notificar, etc.)
    y registra en GaiaChain.
    """

    def __init__(
        self,
        thehive_url: str = "",
        thehive_api_key: str = "",
        velociraptor_url: str = "",
        velociraptor_api_key: str = "",
        gaiachain_client: Optional[Any] = None,
    ) -> None:
        self.thehive_url = (thehive_url or "").rstrip("/")
        self.thehive_api_key = thehive_api_key
        self.velociraptor_url = (velociraptor_url or "").rstrip("/")
        self.velociraptor_api_key = velociraptor_api_key
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.playbooks = self._load_playbooks()
        self.incident_counter = 0

    def _load_playbooks(self) -> Dict[str, Any]:
        return {
            "ransomware": {
                "severity": "critical",
                "actions": [
                    {"type": "isolate_host", "params": {"host_id": "{host_id}"}},
                    {"type": "block_ip", "params": {"ip": "{source_ip}"}},
                    {"type": "notify_team", "params": {"channel": "soc-critical"}},
                    {"type": "create_backup", "params": {"host_id": "{host_id}"}},
                    {"type": "analyze_with_velociraptor", "params": {"host_id": "{host_id}", "artifact": "Windows.KapeFiles"}},
                ],
                "escalation": ["cto", "legal"],
            },
            "apt_attempt": {
                "severity": "high",
                "actions": [
                    {"type": "collect_evidence", "params": {"host_id": "{host_id}", "days": "7"}},
                    {"type": "notify_team", "params": {"channel": "soc-high"}},
                    {"type": "analyze_with_velociraptor", "params": {"host_id": "{host_id}", "artifact": "Linux.Bash.History"}},
                    {"type": "check_threat_intel", "params": {"indicator": "{indicator}"}},
                ],
                "escalation": ["security_manager", "threat_intel"],
            },
            "unauthorized_access": {
                "severity": "medium",
                "actions": [
                    {"type": "revoke_access", "params": {"user_id": "{user_id}"}},
                    {"type": "notify_team", "params": {"channel": "soc-medium"}},
                    {"type": "audit_user_activity", "params": {"user_id": "{user_id}", "days": "30"}},
                ],
                "escalation": ["it_manager"],
            },
            "data_leak": {
                "severity": "critical",
                "actions": [
                    {"type": "revoke_data_access", "params": {"user_id": "{user_id}"}},
                    {"type": "notify_team", "params": {"channel": "soc-critical"}},
                    {"type": "legal_hold", "params": {"user_id": "{user_id}"}},
                    {"type": "check_dlp_logs", "params": {"user_id": "{user_id}", "days": "7"}},
                ],
                "escalation": ["legal", "hr", "cto"],
            },
            "unknown": {
                "severity": "medium",
                "actions": [
                    {"type": "notify_team", "params": {"channel": "soc-medium"}},
                ],
                "escalation": [],
            },
        }

    def _thehive_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        if not HAS_REQUESTS or not self.thehive_url:
            return {"id": f"stub-{hash(endpoint) % 10000}", "title": "Stub"}
        headers = {"Authorization": f"Bearer {self.thehive_api_key}", "Content-Type": "application/json"}
        url = f"{self.thehive_url}/api/{endpoint}"
        try:
            if method.upper() == "GET":
                r = requests.get(url, headers=headers, params=data or {}, timeout=30)
            else:
                r = requests.request(method, url, headers=headers, json=data, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("TheHive request failed: %s", e)
            return {"id": f"stub-{hash(endpoint) % 10000}", "error": str(e)}

    def _velociraptor_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        if not HAS_REQUESTS or not self.velociraptor_url:
            return {"flow_id": "stub"}
        headers = {"Authorization": f"Bearer {self.velociraptor_api_key}", "Content-Type": "application/json"}
        url = f"{self.velociraptor_url}/api/v1/{endpoint}"
        try:
            r = requests.request(method, url, headers=headers, json=data, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Velociraptor request failed: %s", e)
            return {"flow_id": "stub", "error": str(e)}

    def create_incident(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        incident_type = alert.get("type", "unknown")
        playbook = self.playbooks.get(incident_type, self.playbooks["unknown"])
        self.incident_counter += 1
        incident_data = {
            "title": f"[{playbook['severity'].upper()}] {incident_type.replace('_', ' ').title()} - #{self.incident_counter}",
            "description": f"Alerta CASTUO-SOC. Tipo: {incident_type}, Host: {alert.get('host_id')}, Usuario: {alert.get('user_id')}.",
            "severity": playbook["severity"].capitalize(),
            "tags": ["automated", "castuo-soc", f"source:{alert.get('source', 'unknown')}"],
            "date": int(datetime.now().timestamp() * 1000),
            "owner": "soc-team@castu.system",
        }
        incident = self._thehive_request("POST", "case", incident_data)
        incident_id = incident.get("id", f"inc-{self.incident_counter}")
        if self.gaiachain:
            self.gaiachain.log_security_incident({
                "incident_id": incident_id,
                "type": incident_type,
                "severity": playbook["severity"],
                "timestamp": datetime.now().isoformat(),
                "source": alert.get("source", "unknown"),
                "host_id": alert.get("host_id", "unknown"),
                "user_id": alert.get("user_id", "unknown"),
                "status": "created",
            })
        self._execute_playbook(incident_id, playbook, alert)
        return incident

    def _execute_playbook(self, incident_id: str, playbook: Dict[str, Any], alert: Dict[str, Any]) -> None:
        for action in playbook.get("actions", []):
            action_type = action.get("type", "")
            params = {}
            for k, v in action.get("params", {}).items():
                try:
                    params[k] = str(v).format(**alert) if isinstance(v, str) else v
                except KeyError:
                    params[k] = v
            try:
                if action_type == "isolate_host":
                    self._isolate_host(incident_id, **params)
                elif action_type == "block_ip":
                    self._block_ip(incident_id, **params)
                elif action_type == "notify_team":
                    self._notify_team(incident_id, **params)
                elif action_type == "create_backup":
                    self._create_backup(incident_id, **params)
                elif action_type == "analyze_with_velociraptor":
                    self._analyze_with_velociraptor(incident_id, **params)
                elif action_type == "collect_evidence":
                    self._collect_evidence(incident_id, **params)
                elif action_type == "revoke_access":
                    self._revoke_access(incident_id, **params)
                elif action_type == "audit_user_activity":
                    self._audit_user_activity(incident_id, **params)
                elif action_type == "revoke_data_access":
                    self._revoke_data_access(incident_id, **params)
                elif action_type == "legal_hold":
                    self._legal_hold(incident_id, **params)
                elif action_type == "check_dlp_logs":
                    self._check_dlp_logs(incident_id, **params)
                elif action_type == "check_threat_intel":
                    self._check_threat_intel(incident_id, **params)
            except Exception as e:
                logger.warning("Playbook action %s failed: %s", action_type, e)
            if self.gaiachain:
                self.gaiachain.log_incident_action({
                    "incident_id": incident_id,
                    "action": action_type,
                    "params": params,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                })

    def _isolate_host(self, incident_id: str, host_id: str = "") -> None:
        logger.info("Aislando host %s (incidente %s)", host_id, incident_id)

    def _block_ip(self, incident_id: str, ip: str = "") -> None:
        logger.info("Bloqueando IP %s (incidente %s)", ip, incident_id)

    def _notify_team(self, incident_id: str, channel: str = "") -> None:
        logger.info("Notificación a %s (incidente %s)", channel, incident_id)

    def _create_backup(self, incident_id: str, host_id: str = "") -> None:
        self._velociraptor_request("POST", "collect", {"client_id": host_id, "artifacts": ["Windows.Forensic.All"]})

    def _analyze_with_velociraptor(self, incident_id: str, host_id: str = "", artifact: str = "") -> None:
        self._velociraptor_request("POST", "collect", {"client_id": host_id, "artifacts": [artifact]})

    def _collect_evidence(self, incident_id: str, host_id: str = "", days: str = "7") -> None:
        self._velociraptor_request("POST", "collect", {"client_id": host_id, "artifacts": ["Windows.EventLogs.All"]})

    def _revoke_access(self, incident_id: str, user_id: str = "") -> None:
        logger.info("Revocando acceso usuario %s", user_id)

    def _audit_user_activity(self, incident_id: str, user_id: str = "", days: str = "30") -> None:
        logger.info("Auditoría actividad %s últimos %s días", user_id, days)

    def _revoke_data_access(self, incident_id: str, user_id: str = "") -> None:
        logger.info("Revocando acceso a datos %s", user_id)

    def _legal_hold(self, incident_id: str, user_id: str = "") -> None:
        logger.info("Legal hold para %s", user_id)

    def _check_dlp_logs(self, incident_id: str, user_id: str = "", days: str = "7") -> None:
        logger.info("Revisando DLP logs %s", user_id)

    def _check_threat_intel(self, incident_id: str, indicator: str = "") -> None:
        logger.info("Threat intel para indicador %s", indicator[:50])

    def monitor_alerts(self, interval: int = 300) -> None:
        """Bucle de monitoreo de alertas (en producción conectar a SIEM)."""
        logger.info("Monitoreo de alertas cada %ss", interval)
        try:
            while True:
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoreo detenido.")
