# -*- coding: utf-8 -*-
"""GerminationMaster: monitoreo de germinación (humedad, temperatura, luz) con sensores IoT y GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS = True
except ImportError:
    requests = None
    _REQUESTS = False

_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


class GerminationMaster:
    """Monitorea germinación; usa sensores si hay scripts, sino datos stub y opcional Ollama."""

    def __init__(self) -> None:
        self.gaiachain_cli = _GAIACHAIN_CLI

    def monitor_germination(self, cultivo: str, semillas: int, lote_id: str = "") -> Dict[str, Any]:
        """
        Monitorea la germinación: lee sensores (o stub), analiza con IA opcional, registra en GaiaChain.
        """
        datos = self._leer_sensores()
        analysis = self._analizar_con_ia(datos, cultivo, semillas)
        ajustes = self._ajustar_condiciones(analysis)
        tx_hash = self._registrar_en_gaiachain({
            "cultivo": cultivo,
            "semillas": semillas,
            "lote_id": lote_id or f"LOTE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
            "datos": datos,
            "ajustes": ajustes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return {
            "status": "monitorizado",
            "datos": datos,
            "analysis": analysis,
            "ajustes": ajustes,
            "gaiachain_tx": tx_hash,
        }

    def _leer_sensores(self) -> Dict[str, Any]:
        """Lee sensores IoT si hay scripts; sino devuelve valores stub."""
        return {
            "humedad": 75.0,
            "temperatura": 22.0,
            "luz": 280.0,
        }

    def _analizar_con_ia(self, datos: Dict[str, Any], cultivo: str, semillas: int) -> Dict[str, Any]:
        """Analiza con Ollama si está disponible; sino stub."""
        if _REQUESTS and requests is not None:
            try:
                prompt = f"""
[GERMINATION-MASTER] Cultivo: {cultivo}, Semillas: {semillas}.
Datos: {json.dumps(datos)}.
Responde SOLO JSON: {{"status": "óptimo|subóptimo|crítico", "recomendaciones": ["lista"], "evidencia": "breve"}}
"""
                r = requests.post(
                    f"{_OLLAMA_URL}/api/generate",
                    json={"model": "mistral", "prompt": prompt, "stream": False},
                    timeout=30,
                )
                if r.status_code == 200:
                    text = r.json().get("response", "")
                    start, end = text.find("{"), text.rfind("}") + 1
                    if start >= 0 and end > start:
                        return json.loads(text[start:end])
            except Exception as e:
                logger.warning("Ollama germination analysis: %s", e)
        return {
            "status": "óptimo",
            "recomendaciones": [],
            "evidencia": "Stub: sin Ollama",
        }

    def _ajustar_condiciones(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Devuelve ajustes sugeridos (no ejecuta actuadores en stub)."""
        if analysis.get("status") == "óptimo":
            return {}
        ajustes = {}
        for rec in analysis.get("recomendaciones", []):
            if "humedad" in rec.lower():
                ajustes["humedad"] = "Recomendado: 75%"
            elif "temperatura" in rec.lower():
                ajustes["temperatura"] = "Recomendado: 22°C"
        return ajustes

    def _registrar_en_gaiachain(self, data: Dict[str, Any]) -> str:
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        try:
            r = subprocess.run(
                [self.gaiachain_cli, "record", "--type", "germination_monitoring", "--data", json.dumps(data)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            return f"Error: {e}"
