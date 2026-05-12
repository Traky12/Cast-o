# backend/compliance/automated_audit.py — Auditoría automatizada (ISO 27001:A.18.1.4)

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AutomatedAuditSystem:
    """Auditoría automatizada con registro opcional en blockchain/IPFS."""

    def __init__(self) -> None:
        self.audit_trails: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    def start_audit(self, audit_type: str, period: str = "last_30_days") -> str:
        audit_id = f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        self.audit_trails[audit_id] = {
            "type": audit_type,
            "period": period,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "events": [],
            "status": "running",
        }
        return audit_id

    def add_audit_event(self, audit_id: str, event: Dict[str, Any]) -> None:
        if audit_id not in self.audit_trails:
            return
        self.audit_trails[audit_id]["events"].append({
            **event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def finalize_audit(self, audit_id: str) -> Dict[str, Any]:
        if audit_id not in self.audit_trails:
            raise ValueError("Auditoría no encontrada")
        audit = self.audit_trails[audit_id]
        audit["end_time"] = datetime.now(timezone.utc).isoformat()
        audit["status"] = "completed"
        report = self._generate_report(audit_id, audit)
        self._register_in_blockchain(audit_id, report)
        return report

    def _generate_report(self, audit_id: str, audit: Dict[str, Any]) -> Dict[str, Any]:
        events = audit.get("events", [])
        return {
            "metadata": {
                "audit_id": audit_id,
                "type": audit["type"],
                "period": audit["period"],
                "start_time": audit["start_time"],
                "end_time": audit.get("end_time", ""),
            },
            "summary": {
                "total_events": len(events),
                "compliance_issues": sum(1 for e in events if e.get("compliant", True) is False),
                "severity_distribution": self._calculate_severity_distribution(events),
            },
            "events": events,
            "recommendations": self._generate_recommendations(events),
        }

    def _calculate_severity_distribution(self, events: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for e in events:
            s = e.get("severity", "low")
            counts[s] = counts.get(s, 0) + 1
        return counts

    def _generate_recommendations(self, events: List[Dict]) -> List[str]:
        recs = []
        for e in events:
            if e.get("compliant", True) is False:
                recs.append(
                    f"Corregir incumplimiento en {e.get('type', 'event')}: "
                    f"{e.get('description', 'Sin descripción')}. "
                    f"Normativa: {e.get('normative', 'Desconocida')}"
                )
        return recs

    def _register_in_blockchain(self, audit_id: str, report: Dict[str, Any]) -> None:
        try:
            script = os.path.join(
                os.path.dirname(__file__), "..", "scripts", "register_gaiachain_event.py"
            )
            if not os.path.isfile(script):
                self.logger.debug("Script register_gaiachain_event no encontrado")
                return
            details = json.dumps({"audit_id": audit_id, "summary": report.get("summary", {})})
            subprocess.run(
                [
                    os.environ.get("PYTHON", "python"),
                    script,
                    "--event_type", "audit_report",
                    "--details", details,
                    "--norms", "ISO_27001:A.18.1.4,GDPR:Art.30",
                ],
                capture_output=True,
                timeout=30,
                check=False,
            )
        except Exception as e:
            self.logger.debug("Registro GaiaChain omitido: %s", e)
