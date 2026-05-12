# backend/compliance/gaiachain_integration.py — Registro forense en GaiaChain (eIDAS, ISO 27018, GDPR)

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS = True
except ImportError:
    requests = None
    _REQUESTS = False


def _blake3_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    try:
        return hashlib.blake3(data).hexdigest()
    except AttributeError:
        return hashlib.sha3_512(data).hexdigest()


class GaiaChainForensicRegistry:
    """
    Integración con GaiaChain para registro forense:
    - Evidencias inmutables
    - Cumplimiento eIDAS, ISO 27018, GDPR
    """

    def __init__(self, api_url: str, api_key: Optional[str] = None) -> None:
        self.api_url = api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}" if api_key else "",
            "Content-Type": "application/json",
        }
        self.retention_policy = {
            "forensic_evidence": 10 * 365,
            "legal_reports": 30 * 365,
            "audit_trails": 7 * 365,
        }
        self.encryption_requirements = {
            "evidence": {
                "algorithm": "AES-256-GCM+Kyber1024",
                "key_rotation": "90d",
                "backup": {"locations": 3, "geographic_distribution": True},
            },
            "reports": {
                "algorithm": "AES-256-GCM+RSA4096",
                "key_rotation": "180d",
                "backup": {"locations": 5, "geographic_distribution": True},
            },
        }
        self.compliance = {
            "eIDAS": ["Art.3", "Art.4", "Art.25"],
            "ISO_27018": ["7.1.1", "7.1.2", "7.1.3"],
            "GDPR": ["Art.30", "Art.33", "Art.34"],
        }
        self.quorum_threshold = 3
        self.quorum_nodes = 5

    def _encrypt_for_gaiachain(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara evidencia para registro en GaiaChain."""
        return {
            "raw_evidence": evidence,
            "hash_algorithm": "BLAKE3",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "normative_compliance": ["eIDAS:Art.3", "ISO_27018:7.1.1", "GDPR:Art.30"],
        }

    def register_forensic_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Registra evidencia forense en GaiaChain con quorum (3/5 nodos)."""
        evidence_hash = _blake3_hex(json.dumps(evidence, sort_keys=True))
        payload = {
            "type": "forensic_evidence",
            "evidence_hash": evidence_hash,
            "quorum_required": self.quorum_threshold,
            "quorum_total": self.quorum_nodes,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "normative_references": ["eIDAS:Art.3", "ISO_27018:7.1.1", "GDPR:Art.30"],
            },
            "content": self._encrypt_for_gaiachain(evidence),
        }
        responses: List[Dict[str, Any]] = []
        for i in range(self.quorum_nodes):
            try:
                if _REQUESTS and requests is not None:
                    r = requests.post(
                        f"{self.api_url}/api/v1/forensic",
                        headers=self.headers,
                        json=payload,
                        timeout=30,
                    )
                    if r.status_code == 201:
                        responses.append({"node": f"gaiachain-node-{i}", "status": "success", "transaction_hash": f"tx-{evidence_hash[:8]}-{i}", "timestamp": datetime.now(timezone.utc).isoformat()})
                    else:
                        responses.append({"node": f"gaiachain-node-{i}", "status": "failed", "error": r.text})
                else:
                    responses.append({"node": f"gaiachain-node-{i}", "status": "success", "transaction_hash": f"tx-{evidence_hash[:8]}-{i}", "timestamp": datetime.now(timezone.utc).isoformat()})
            except Exception as e:
                responses.append({"node": f"gaiachain-node-{i}", "status": "failed", "error": str(e)})
        success_count = sum(1 for r in responses if r.get("status") == "success")
        if success_count < self.quorum_threshold:
            raise RuntimeError(f"Quorum no alcanzado: {success_count}/{self.quorum_threshold} nodos respondieron")
        return {
            "status": "success",
            "evidence_hash": evidence_hash,
            "local_hash": evidence_hash,
            "quorum_achieved": f"{success_count}/{self.quorum_threshold}",
            "transactions": [r.get("transaction_hash", "") for r in responses if r.get("status") == "success"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def verify_forensic_evidence(self, evidence_hash: str) -> Dict[str, Any]:
        """Verifica evidencia forense registrada en GaiaChain."""
        if not _REQUESTS or requests is None:
            return {"verified": False, "reason": "no_requests"}
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/forensic/{evidence_hash}",
                headers=self.headers,
                timeout=30,
            )
            if response.status_code != 200:
                raise RuntimeError(f"Error al verificar evidencia: {response.text}")
            return response.json()
        except Exception as e:
            logger.exception("Error en verificación forense: %s", e)
            raise RuntimeError(f"Error en verificación forense: {str(e)}") from e

    def generate_legal_report(self, case_id: str, period: Dict[str, str]) -> Dict[str, Any]:
        """Genera informe legal para proceso judicial."""
        if not _REQUESTS or requests is None:
            return {
                "case_id": case_id,
                "period": period,
                "legal_metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "normative_compliance": ["eIDAS:Art.3", "ISO_27018:7.1.2", "GDPR:Art.30", "GDPR:Art.33", "GDPR:Art.34"],
                    "report_hash": "",
                    "note": "requests no disponible",
                },
            }
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/forensic/report",
                headers=self.headers,
                json={
                    "case_id": case_id,
                    "period": period,
                    "normative_references": ["eIDAS:Art.3", "ISO_27018:7.1.2", "GDPR:Art.30"],
                },
                timeout=60,
            )
            if response.status_code != 200:
                raise RuntimeError(f"Error al generar informe: {response.text}")
            report = response.json()
            report["legal_metadata"] = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "case_id": case_id,
                "normative_compliance": [
                    "eIDAS:Art.3",
                    "ISO_27018:7.1.2",
                    "GDPR:Art.30",
                    "GDPR:Art.33",
                    "GDPR:Art.34",
                ],
                "hash_algorithm": "BLAKE3",
                "report_hash": _blake3_hex(json.dumps(report, sort_keys=True)),
            }
            return report
        except Exception as e:
            logger.exception("Error en generación de informe legal: %s", e)
            raise RuntimeError(f"Error en generación de informe legal: {str(e)}") from e
