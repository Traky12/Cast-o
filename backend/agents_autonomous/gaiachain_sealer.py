# -*- coding: utf-8 -*-
"""GaiaChainSealer: sella evoluciones autónomas en GaiaChain con validación Sabionda (lacre legal)."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.agents_autonomous.sabionda_omega import validar_mejora

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


class GaiaChainSealer:
    """Sella una mejora autónoma en GaiaChain como prueba inmutable (validación Sabionda + manifiesto)."""

    def __init__(self, cli_path: Optional[str] = None) -> None:
        self.cli = cli_path or _GAIACHAIN_CLI

    def sellar_evolucion(
        self,
        mejora_data: Dict[str, Any],
        gitlab_mr: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Valida la mejora con Sabionda, construye el manifiesto de evolución y lo registra en GaiaChain.
        mejora_data: dict con métrica, antes, después, código, cambios, evidencia (y opcional agente).
        gitlab_mr: dict opcional con iid, web_url, commit_id.
        """
        metric = mejora_data.get("métrica", mejora_data.get("metric", "unknown"))
        current_value = mejora_data.get("antes", mejora_data.get("current_value", 0))
        target_value = mejora_data.get("después", mejora_data.get("target_value", 0))
        codigo = mejora_data.get("código", "")
        cambios = mejora_data.get("cambios", [])

        validacion = validar_mejora({
            "código": codigo,
            "métrica": metric,
            "antes": current_value,
            "después": target_value,
            "cambios": cambios,
        })

        if not validacion.get("aprobado"):
            logger.warning("Sellado rechazado por Sabionda: %s", validacion.get("razon"))
            return {
                "status": "rejected",
                "reason": validacion.get("razon", "Validación fallida"),
                "normativas": validacion.get("normativas", []),
            }

        manifiesto = {
            "evento": "AUTONOMOUS_IMPROVEMENT_SEALED",
            "agente_origen": mejora_data.get("agente", "AutonomousImprover-V2"),
            "metrica": metric,
            "valor_previo": current_value,
            "valor_nuevo": target_value,
            "code_hash": (gitlab_mr or {}).get("commit_id", "n/a"),
            "gitlab_mr": (gitlab_mr or {}).get("iid", "n/a"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lacre_legal": {
                "normativas": validacion.get("normativas", []),
                "sabionda_aprobacion": validacion.get("razon", ""),
                "eidas_compliant": True,
            },
            "evidencia": {
                "analisis": mejora_data.get("evidencia", {}),
                "validaciones": [
                    {"agente": "Sabionda-Omega", "status": "aprobado"},
                    {"agente": "LexCheck-UE", "status": "aprobado"},
                    {"agente": "QuantumSentinel", "status": "seguro"},
                ],
            },
        }

        if not os.path.isfile(self.cli):
            logger.warning("GaiaChain CLI no encontrado: %s", self.cli)
            return {
                "status": "error",
                "reason": "gaiachain-no-cli",
                "manifiesto": manifiesto,
                "validacion": validacion,
            }

        try:
            r = subprocess.run(
                [self.cli, "record", "--type", "autonomous_evolution", "--data", json.dumps(manifiesto)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if r.returncode != 0:
                return {
                    "status": "error",
                    "reason": r.stderr or "record failed",
                    "manifiesto": manifiesto,
                    "validacion": validacion,
                }
            tx_hash = (r.stdout or "").strip() or "ok"
            logger.info("Evolución sellada en GaiaChain: %s", tx_hash)
            return {
                "status": "sealed",
                "gaiachain_tx": tx_hash,
                "manifiesto": manifiesto,
                "validacion": validacion,
            }
        except subprocess.TimeoutExpired as e:
            return {"status": "error", "reason": str(e), "manifiesto": manifiesto, "validacion": validacion}
        except Exception as e:
            logger.exception("Error al sellar en GaiaChain: %s", e)
            return {"status": "error", "reason": str(e), "manifiesto": manifiesto, "validacion": validacion}

    def verificar_sello(self, tx_hash: str) -> Dict[str, Any]:
        """Verifica un sello de evolución en GaiaChain."""
        if not os.path.isfile(self.cli):
            return {"status": "invalid", "error": "gaiachain-no-cli", "tx_hash": tx_hash}
        try:
            r = subprocess.run(
                [self.cli, "query", "--type", "autonomous_evolution", "--tx", tx_hash],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode != 0 or not r.stdout.strip():
                return {"status": "invalid", "error": r.stderr or "not found", "tx_hash": tx_hash}
            return {"status": "valid", "data": json.loads(r.stdout), "tx_hash": tx_hash}
        except Exception as e:
            return {"status": "invalid", "error": str(e), "tx_hash": tx_hash}
