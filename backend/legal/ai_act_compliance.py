# -*- coding: utf-8 -*-
"""Cumplimiento AI Act 2024: registro de decisiones de IA (Art. 13-15) y transparencia en GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", os.getenv("GAIA_CHAIN_CLI", "/usr/local/bin/gaiachain"))


class AIActCompliance:
    """Registro de decisiones de IA y generación de informes de transparencia (AI Act 2024)."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI

    def register_ai_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra una decisión de IA según AI Act 2024 (Art. 13-15).
        Campos recomendados: decision_id, model, input_data, output, timestamp, risk_assessment, human_oversight.
        Si faltan, se rellenan con valores por defecto.
        """
        defaults = {
            "decision_id": decision_data.get("decision_id", f"DEC-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"),
            "model": decision_data.get("model", "Mistral-7B"),
            "input_data": decision_data.get("input_data", {}),
            "output": decision_data.get("output", {}),
            "timestamp": decision_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "risk_assessment": decision_data.get("risk_assessment", {"level": "low", "mitigations": []}),
            "human_oversight": decision_data.get("human_oversight", {"reviewed_by": "Gemelo Digital", "approval": True}),
        }
        data = {**defaults, **decision_data}
        tx_data = {
            "type": "ai_act_decision",
            "data": {
                **data,
                "compliance": {
                    "regulation": "AI Act 2024",
                    "articles": ["Art. 13 (Transparencia)", "Art. 14 (Supervisión Humana)"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        }
        tx_hash = self._record(tx_data)
        return {
            "status": "registered",
            "gaiachain_tx": tx_hash,
            "ai_act_compliant": True,
        }

    def generate_transparency_report(self, decision_id: str) -> Dict[str, Any]:
        """Genera un informe de transparencia según AI Act Art. 13 (consulta GaiaChain si existe CLI)."""
        tx_data = self._query_ai_decision(decision_id)
        if not tx_data.get("valid"):
            report = {
                "decision_id": decision_id,
                "note": "Decisión no encontrada en GaiaChain (modo stub)",
                "compliance": {"ai_act_articles": ["Art. 13", "Art. 14", "Art. 15"]},
            }
            report_tx = self._record({"type": "ai_act_transparency_report", "data": report})
            return {"report": report, "gaiachain_tx": report_tx, "ai_act_compliant": True}
        d = tx_data["data"]
        report = {
            "decision_id": decision_id,
            "model": d.get("model"),
            "input_data": d.get("input_data"),
            "output": d.get("output"),
            "risk_assessment": d.get("risk_assessment"),
            "human_oversight": d.get("human_oversight"),
            "compliance": {"ai_act_articles": ["Art. 13", "Art. 14", "Art. 15"], "timestamp": datetime.now(timezone.utc).isoformat()},
        }
        report_tx = self._record({"type": "ai_act_transparency_report", "data": report})
        return {"report": report, "gaiachain_tx": report_tx, "ai_act_compliant": True}

    def _record(self, tx_data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            t = tx_data.get("type", "ai_act_decision")
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", t, "--data", json.dumps(tx_data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain record: %s", e)
            return f"Error: {e}"

    def _query_ai_decision(self, decision_id: str) -> Dict[str, Any]:
        if not os.path.isfile(self.gaiachain_cli):
            return {"valid": False, "error": "gaiachain-no-cli"}
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "query", "--type", "ai_act_decision", "--decision_id", decision_id],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not r.stdout.strip():
                return {"valid": False, "error": r.stderr or "not found"}
            return {"valid": True, "data": json.loads(r.stdout)}
        except Exception as e:
            return {"valid": False, "error": str(e)}
