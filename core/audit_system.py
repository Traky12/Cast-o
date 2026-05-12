# -*- coding: utf-8 -*-
"""
Sistema de logs y auditoría SABIONDA.
Registro inmutable de interacciones para trazabilidad y cumplimiento legal.
"""
from __future__ import annotations

import hashlib
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient


class AuditSystem:
    """Sistema de auditoría para registrar todas las interacciones con trazabilidad blockchain."""

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.local_logs: List[Dict] = []

    def log_interaction(
        self,
        session_id: str,
        user_id: str,
        profile_id: str,
        action: str,
        module: str,
        context: Dict,
        response: str,
        status: str = "success",
    ) -> str:
        """Registra una interacción en el sistema."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_id": user_id,
            "profile_id": profile_id,
            "action": action,
            "module": module,
            "context": context,
            "response_hash": hashlib.sha256(response.encode()).hexdigest(),
            "status": status,
        }
        if self.gaiachain:
            tx_id = self.gaiachain.log_system_interaction(log_entry)
        else:
            tx_id = hashlib.sha256(json.dumps(log_entry, sort_keys=True).encode()).hexdigest()[:24]
        self.local_logs.append({**log_entry, "gaiachain_tx": tx_id})
        return tx_id

    def get_interaction_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Obtiene el historial de interacciones de un usuario."""
        return [log for log in self.local_logs if log["user_id"] == user_id][-limit:]

    def get_security_alerts(self, days: int = 7) -> List[Dict]:
        """Obtiene alertas de seguridad recientes."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            log
            for log in self.local_logs
            if log.get("module") == "security"
            and log.get("action") == "alert"
            and datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]

    def export_audit_report(
        self,
        start_date: str,
        end_date: str,
        format: str = "json",
    ) -> Union[str, Dict]:
        """Exporta un informe de auditoría para un período."""
        try:
            start = datetime.fromisoformat(start_date + "T00:00:00")
        except ValueError:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        try:
            end = datetime.fromisoformat(end_date + "T23:59:59")
        except ValueError:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        filtered_logs = [
            log
            for log in self.local_logs
            if start <= datetime.fromisoformat(log["timestamp"]) <= end
        ]

        if format.lower() == "json":
            return json.dumps(filtered_logs, indent=2)
        if format.lower() == "csv":
            out = io.StringIO()
            if filtered_logs:
                writer = csv.DictWriter(
                    out,
                    fieldnames=[
                        "timestamp",
                        "session_id",
                        "user_id",
                        "profile_id",
                        "action",
                        "module",
                        "status",
                        "gaiachain_tx",
                    ],
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerows(filtered_logs)
            return out.getvalue()
        raise ValueError(f"Formato no soportado: {format}")

    def detect_anomalies(self) -> List[Dict]:
        """Detecta patrones anómalos en los logs."""
        anomalies: List[Dict] = []
        for log in self.local_logs:
            if log.get("action") == "access_denied":
                anomalies.append(
                    {
                        **log,
                        "anomaly_type": "unauthorized_access",
                        "severity": "high",
                    }
                )
        failed_attempts: Dict[str, int] = {}
        for log in self.local_logs:
            if log.get("status") == "failed":
                key = f"{log['user_id']}_{log.get('module', '')}"
                failed_attempts[key] = failed_attempts.get(key, 0) + 1
        for key, count in failed_attempts.items():
            if count >= 3:
                parts = key.rsplit("_", 1)
                user_id = parts[0] if len(parts) == 2 else key
                module = parts[1] if len(parts) == 2 else "unknown"
                anomalies.append(
                    {
                        "user_id": user_id,
                        "module": module,
                        "anomaly_type": "brute_force_attempt",
                        "count": count,
                        "severity": "critical",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        return anomalies


if __name__ == "__main__":
    audit = AuditSystem(gaiachain_client=GaiaChainClient())
    audit.log_interaction(
        "abc123",
        "juan_perez@finca.es",
        "FARMER",
        "query",
        "production",
        {"batch_id": "CASTUA-2026-001"},
        "El lote CASTUA-2026-001 tiene un rendimiento del 99.2%.",
    )
    audit.log_interaction(
        "ghi789",
        "auditor@aemps.es",
        "AUDITOR",
        "access_denied",
        "production",
        {"attempt": "write_to_blockchain"},
        "Acceso denegado.",
        status="failed",
    )
    print("Historial juan_perez:", len(audit.get_interaction_history("juan_perez@finca.es")))
    print("Anomalías:", audit.detect_anomalies())
    print("Export JSON:", audit.export_audit_report(
        (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        datetime.now().strftime("%Y-%m-%d"),
    )[:300] + "...")
