# -*- coding: utf-8 -*-
"""YieldMaster: optimización de métricas agrovoltaicas (yield, humedad, energía)."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_SCRIPT_ANALYZE_YIELD = os.getenv(
    "CASTUO_ANALYZE_YIELD_SCRIPT",
    str(Path(__file__).resolve().parents[2] / "scripts" / "analyze_yield.py"),
)


def analizar_yield(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza métricas de yield; usa script existente si está disponible, sino stub.
    Args:
        data: Dict con datos de sensores (humedad, temperatura, yield, etc.).
    Returns:
        Dict con current_yield, recomendaciones, simulacion, evidencia.
    """
    if Path(_SCRIPT_ANALYZE_YIELD).is_file():
        try:
            result = subprocess.run(
                [
                    "python",
                    _SCRIPT_ANALYZE_YIELD,
                    "--input", json.dumps(data),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).resolve().parents[2],
            )
            if result.returncode == 0 and result.stdout.strip():
                analysis = json.loads(result.stdout)
                recomendaciones: List[str] = []
                cy = analysis.get("current_yield", data.get("yield", 98.5))
                if cy < 99.0 and "optimal_humidity" in analysis:
                    recomendaciones.append(
                        f"Aumentar humedad a {analysis.get('optimal_humidity', 72)}% "
                        f"para alcanzar {analysis.get('optimal_yield', 99.0)}%"
                    )
                if analysis.get("temperature", 0) > 30:
                    recomendaciones.append("Activar sistema de enfriamiento por QKD")
                return {
                    "current_yield": cy,
                    "recomendaciones": recomendaciones or analysis.get("recomendaciones", []),
                    "simulacion": analysis.get("simulation", analysis.get("simulacion", {})),
                    "evidencia": analysis.get("evidence_file", "pix4d_analysis.json"),
                }
        except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
            logger.warning("analyze_yield script falló, usando stub: %s", e)

    return _stub_analizar_yield(data)


def _stub_analizar_yield(data: Dict[str, Any]) -> Dict[str, Any]:
    """Respuesta stub cuando no hay script de análisis."""
    cy = data.get("yield", 98.5)
    return {
        "current_yield": cy,
        "recomendaciones": [
            "Aumentar humedad en 2% para alcanzar 99.0%",
            "Optimizar algoritmo de riego con QKD",
        ],
        "simulacion": {
            "escenario_1": {"humedad": 72, "yield": 99.0},
            "escenario_2": {"humedad": 75, "yield": 99.2},
        },
        "evidencia": "stub_simulation.json",
    }
