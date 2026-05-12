# -*- coding: utf-8 -*-
"""CannabisLab: análisis de cannabinoides (THC/CBD) y validación AEMPS (RD 903/2025)."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


class CannabisLab:
    """Analiza perfil de cannabinoides y valida contra límites AEMPS; registro en GaiaChain opcional."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI

    def analyze_cannabinoids(self, lote_id: str, muestra: str = "") -> Dict[str, Any]:
        """
        Analiza cannabinoides del lote; si hay script/espectrómetro lo usa, sino datos stub.
        Valida con límites AEMPS (RD 903/2025) y registra en GaiaChain.
        """
        cannabinoids = self._leer_espectrometro()
        compliance = self._validar_aemps(cannabinoids)
        tx_hash = self._registrar_en_gaiachain({
            "lote_id": lote_id,
            "muestra": muestra or f"MUE-{lote_id}",
            "cannabinoids": cannabinoids,
            "compliance": compliance,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "lote_id": lote_id,
            "muestra": muestra or f"MUE-{lote_id}",
            "cannabinoids": cannabinoids,
            "compliance": compliance,
            "gaiachain_tx": tx_hash,
        }

    def _leer_espectrometro(self) -> Dict[str, float]:
        """Stub: devuelve valores de ejemplo. En producción conectar a espectrómetro."""
        return {
            "THC": 18.5,
            "CBD": 8.2,
            "CBG": 0.5,
        }

    def _validar_aemps(self, cannabinoids: Dict[str, float]) -> Dict[str, Any]:
        """Valida contra límites tipo AEMPS (RD 903/2025)."""
        limits = {
            "THC": {"min": 15.0, "max": 25.0},
            "CBD": {"min": 5.0, "max": 15.0},
            "CBG": {"max": 1.0},
        }
        issues: List[Dict[str, Any]] = []
        for name, value in cannabinoids.items():
            if name in limits:
                L = limits[name]
                if "min" in L and value < L["min"]:
                    issues.append({"cannabinoid": name, "valor": value, "límite": L, "normativa": "RD 903/2025 Art. 12"})
                if "max" in L and value > L["max"]:
                    issues.append({"cannabinoid": name, "valor": value, "límite": L, "normativa": "RD 903/2025 Art. 12"})
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "normativa": "RD 903/2025 (Cannabis Medicinal)",
        }

    def _registrar_en_gaiachain(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "cannabis_analysis", "--data", json.dumps(data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"
