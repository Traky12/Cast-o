import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml
from zapv2 import ZAPv2


logger = logging.getLogger(__name__)


class ZAPUtils:
    def __init__(self, config_path: str = "security-tests/config/zap_config.yaml") -> None:
        self.config = self._load_config(config_path)
        self.zap: Optional[ZAPv2] = None
        self.gaiachain_url = os.getenv("GAIACHAIN_URL", "https://gaiachain.castuo-system.eu")
        self.gaiachain_token = os.getenv("GAIA_CHAIN_ADMIN_TOKEN") or os.getenv(
            "GAIACHAIN_ADMIN_TOKEN"
        )
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def initialize_zap(self) -> ZAPv2:
        if self.zap is None:
            proxy = self.config["zap"]["proxy"]
            host = os.getenv("ZAP_PROXY_HOST", proxy["host"])
            port = int(os.getenv("ZAP_PROXY_PORT", str(proxy["port"])))
            api_key = os.getenv("ZAP_API_KEY", proxy.get("api_key", ""))
            self.zap = ZAPv2(
                apikey=api_key,
                proxies={
                    "http": f"http://{host}:{port}",
                    "https": f"http://{host}:{port}",
                },
            )
            logger.info("Conectado a ZAP en %s:%s", host, port)
        return self.zap

    def get_scan_config(self, scan_type: str) -> Dict[str, Any]:
        return self.config["zap"]["scans"].get(scan_type, {})

    # GaiaChain integration -------------------------------------------------

    def register_vulnerability_in_gaiachain(self, vulnerability: Dict[str, Any]) -> Optional[str]:
        if not self.config["zap"]["gaiachain"].get("register_vulnerabilities", False):
            return None
        if not self.gaiachain_token:
            return None
        try:
            payload = {
                "token_id": 0,
                "action_type": "vulnerability_detected",
                "status": "open",
                "details": {
                    "vulnerability_id": vulnerability.get("id", "unknown"),
                    "name": vulnerability.get("name", "unknown"),
                    "severity": vulnerability.get("severity", "unknown"),
                    "cwe": vulnerability.get("cwe", "unknown"),
                    "url": vulnerability.get("url", ""),
                    "method": vulnerability.get("method", ""),
                    "parameter": vulnerability.get("parameter", ""),
                    "evidence": vulnerability.get("evidence", ""),
                    "compliance_impact": vulnerability.get("compliance_impact", []),
                    "mitigation": vulnerability.get("mitigation", []),
                },
                "norms": self._get_norms_for_vulnerability(vulnerability),
                "legal_basis": {
                    "description": f"Vulnerabilidad detectada: {vulnerability.get('name', 'unknown')}",
                    "severity": vulnerability.get("severity", "unknown"),
                    "scan_type": vulnerability.get("scan_type", "unknown"),
                },
            }
            headers = {
                "Authorization": f"Bearer {self.gaiachain_token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                f"{self.gaiachain_url}/api/v1/events", headers=headers, json=payload, timeout=15
            )
            if resp.status_code == 201:
                tx_hash = resp.json().get("tx_hash")
                logger.info("Vulnerabilidad registrada en GaiaChain: %s", tx_hash)
                return tx_hash
            logger.warning("Error registrando vulnerabilidad en GaiaChain: %s", resp.text)
        except Exception as exc:
            logger.error("Exception registrando vulnerabilidad: %s", exc)
        return None

    def register_scan_result_in_gaiachain(self, scan_result: Dict[str, Any]) -> Optional[str]:
        if not self.config["zap"]["gaiachain"].get("register_scan_results", False):
            return None
        if not self.gaiachain_token:
            return None
        try:
            payload = {
                "token_id": 0,
                "action_type": "security_scan_completed",
                "status": "completed",
                "details": {
                    "scan_type": scan_result.get("scan_type", "unknown"),
                    "target_url": scan_result.get("target_url", ""),
                    "start_time": scan_result.get("start_time", ""),
                    "end_time": scan_result.get("end_time", ""),
                    "vulnerabilities_found": scan_result.get("vulnerabilities_found", 0),
                    "vulnerabilities_by_severity": scan_result.get(
                        "vulnerabilities_by_severity", {}
                    ),
                    "compliance_status": scan_result.get("compliance_status", {}),
                    "scan_id": scan_result.get("scan_id", ""),
                },
                "norms": ["ISO_27001:A.12.6.1", "GDPR:Art.32"],
                "legal_basis": {
                    "description": f"Escaneo de seguridad: {scan_result.get('scan_type', 'unknown')}",
                    "target": scan_result.get("target_url", ""),
                },
            }
            headers = {
                "Authorization": f"Bearer {self.gaiachain_token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                f"{self.gaiachain_url}/api/v1/events", headers=headers, json=payload, timeout=15
            )
            if resp.status_code == 201:
                tx_hash = resp.json().get("tx_hash")
                logger.info("Resultado de escaneo registrado en GaiaChain: %s", tx_hash)
                return tx_hash
            logger.warning("Error registrando resultado de escaneo: %s", resp.text)
        except Exception as exc:
            logger.error("Exception registrando resultado de escaneo: %s", exc)
        return None

    def _get_norms_for_vulnerability(self, vulnerability: Dict[str, Any]) -> List[str]:
        norms: List[str] = ["ISO_27001:A.12.6.1", "GDPR:Art.32"]
        vid = (vulnerability.get("id") or "").lower()
        name = (vulnerability.get("name") or "").lower()
        if "sql" in vid or "injection" in name:
            norms += ["ISO_27001:A.14.2.5", "Ley_3_2023:Art.20"]
        if "xss" in name:
            norms += ["ISO_27001:A.14.2.1"]
        return norms

    # Slack alerts ----------------------------------------------------------

    def send_slack_alert(
        self, message: str, severity: str = "warning", context: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self.slack_webhook or not self.config["zap"]["alerts"]["slack"].get("enabled", False):
            return
        min_sev = self.config["zap"]["alerts"]["slack"].get("min_severity", "high").lower()
        sev = severity.lower()
        if min_sev == "high" and sev not in ("high", "critical"):
            return
        color = "#ff0000" if sev == "critical" else "#ff9900" if sev == "high" else "#3498db"
        payload = {
            "text": ":shield: *Alerta de Seguridad* :shield:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{severity.upper()}: {message}",
                    "fields": [
                        {"title": "Severidad", "value": severity, "short": True},
                        {
                            "title": "Fecha",
                            "value": datetime.utcnow().isoformat() + "Z",
                            "short": True,
                        },
                    ]
                    + [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in (context or {}).items()
                    ],
                    "footer": "CASTÚO-SYSTEM™ Security Monitoring",
                }
            ],
        }
        try:
            resp = requests.post(self.slack_webhook, json=payload, timeout=10)
            if resp.status_code != 200:
                logger.warning("Error enviando alerta a Slack: %s", resp.text)
        except Exception as exc:
            logger.error("Exception enviando alerta a Slack: %s", exc)

    # Vulnerability catalog -------------------------------------------------

    def load_vulnerability_catalog(self) -> Dict[str, Any]:
        catalog_path = Path(__file__).resolve().parents[1] / "config" / "vulnerabilities.yaml"
        with open(catalog_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def enrich_with_catalog(self, alerts: List[Dict[str, Any]], scan_type: str, scan_id: str) -> List[Dict[str, Any]]:
        catalog = self.load_vulnerability_catalog()
        vulns_cat = catalog.get("vulnerabilities", [])
        result: List[Dict[str, Any]] = []
        for alert in alerts:
            risk_code = str(alert.get("riskcode", "1"))
            sev_map = {"3": "critical", "2": "high", "1": "medium", "0": "low"}
            severity = sev_map.get(risk_code, "low")
            cwe = str(alert.get("cweid", "")) or ""
            name = (alert.get("name") or "").lower()
            cat_vuln = None
            for v in vulns_cat:
                if v["cwe"] == cwe or v["id"] in name:
                    cat_vuln = v
                    break
            v = {
                "id": alert.get("pluginId", "unknown"),
                "name": alert.get("name", "unknown"),
                "severity": severity,
                "cwe": cwe,
                "url": alert.get("url", ""),
                "method": alert.get("method", ""),
                "parameter": alert.get("param", ""),
                "evidence": alert.get("evidence", ""),
                "description": alert.get("description", ""),
                "solution": alert.get("solution", ""),
                "other_info": alert.get("other", ""),
                "compliance_impact": cat_vuln.get("compliance_impact", []) if cat_vuln else [],
                "mitigation": cat_vuln.get("mitigation", []) if cat_vuln else [],
                "zap_alert_id": alert.get("id", ""),
                "scan_type": scan_type,
                "scan_id": scan_id,
            }
            tx = self.register_vulnerability_in_gaiachain(v)
            if tx:
                v["gaiachain_tx"] = tx
            result.append(v)
        return result

    # Compliance thresholds -------------------------------------------------

    def check_compliance_thresholds(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        thresholds = self.config["zap"]["severity_thresholds"]
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in vulnerabilities:
            sev = v.get("severity", "low").lower()
            if sev in counts:
                counts[sev] += 1
        status = {"overall": True, "counts": counts, "thresholds": thresholds}
        if counts["critical"] > thresholds["critical"]:
            status["overall"] = False
            status["reason"] = (
                f"Se encontraron {counts['critical']} vulnerabilidades críticas "
                f"(máx {thresholds['critical']})"
            )
        elif counts["high"] > thresholds["high"]:
            status["overall"] = False
            status["reason"] = (
                f"Se encontraron {counts['high']} vulnerabilidades altas "
                f"(máx {thresholds['high']})"
            )
        status["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return status

    # Report generation -----------------------------------------------------

    def generate_report(self, scan_results: Dict[str, Any], fmt: str = "html") -> str:
        report_dir = Path(self.config["zap"]["reports"]["output_dir"])
        report_dir.mkdir(parents=True, exist_ok=True)
        scan_id = scan_results.get("scan_id", "unknown")
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = report_dir / f"security_scan_{scan_id}_{ts}.{fmt}"
        if fmt == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(scan_results, f, indent=2)
        else:
            # Para html/md delegamos a report_generator si se necesita más adelante
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(scan_results, indent=2))
        return str(path)

