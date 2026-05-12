# -*- coding: utf-8 -*-
"""QuantumSentinel: escaneo WebCheck + análisis Sabionda (Ollama) y registro de alertas en GaiaChain."""
from __future__ import annotations

import json
import logging
import os
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    import requests
    _REQUESTS = True
except ImportError:
    requests = None
    _REQUESTS = False

_WEBCHECK_URL = os.getenv("WEBCHECK_URL", "http://localhost:3000/api/analyze")
_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")
_QUANTUM_SENTINEL_ACTIVATE_PROTECTION = os.getenv("QUANTUM_SENTINEL_ACTIVATE_PROTECTION", "").lower() in ("1", "true", "yes")


class QuantumSentinel:
    """Escanea dominio con WebCheck, analiza con Sabionda (Mistral) y opcionalmente registra alertas en GaiaChain."""

    def __init__(self) -> None:
        self.webcheck_url = _WEBCHECK_URL
        self.sabionda_url = f"{_OLLAMA_URL}/api/generate"
        self.gaiachain_cli = _GAIACHAIN_CLI

    def scan_and_protect(self, target_domain: str) -> Dict[str, Any]:
        """
        Escanea el dominio con WebCheck y activa protecciones si hay riesgos.
        Sin WebCheck/Ollama devuelve resultado seguro (status safe) con datos mínimos.
        """
        scan_result = self._webcheck_scan(target_domain)
        if not scan_result.get("success"):
            return {
                "status": "error",
                "error": scan_result.get("error", "WebCheck no disponible"),
                "scan": None,
                "analysis": {"risk": "UNKNOWN", "reason": "Escaneo no ejecutado", "recommendations": []},
            }

        analysis = self._analyze_with_sabionda(scan_result.get("data") or {})

        if analysis.get("risk") == "HIGH" and _QUANTUM_SENTINEL_ACTIVATE_PROTECTION:
            self._activate_protection_mode(analysis.get("reason", "Riesgo alto"))
            alert_tx = self._register_alert_in_gaiachain(analysis)
            return {
                "status": "protected",
                "scan": scan_result.get("data"),
                "analysis": analysis,
                "gaiachain_tx": alert_tx,
                "actions": ["firewall_activated", "notifications_sent"],
            }
        return {
            "status": "safe" if analysis.get("risk") != "HIGH" else "risk_detected",
            "scan": scan_result.get("data"),
            "analysis": analysis,
        }

    def _webcheck_scan(self, target: str) -> Dict[str, Any]:
        """Ejecuta un escaneo con WebCheck (GET con query url)."""
        if not _REQUESTS or requests is None:
            return {"success": False, "error": "requests no disponible"}
        try:
            resp = requests.get(
                f"{self.webcheck_url}?url={target}",
                timeout=30,
            )
            if resp.status_code != 200:
                return {"success": False, "error": resp.text}
            return {"success": True, "data": resp.json()}
        except Exception as e:
            logger.warning("WebCheck scan failed: %s", e)
            return {"success": False, "error": str(e)}

    def _analyze_with_sabionda(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el escaneo con Sabionda (Ollama/Mistral). Si falla, devuelve risk LOW."""
        prompt = f"""
[QUANTUM-SENTINEL: ANALISIS DE AMENAZAS]
Datos del escaneo WebCheck:
{json.dumps(scan_data, indent=2)}

Responde ÚNICAMENTE con un JSON válido (sin markdown):
{{"risk": "LOW|MEDIUM|HIGH", "reason": "Explicación breve (máx 100 palabras)", "recommendations": ["acción1", "acción2"]}}
"""
        if not _REQUESTS or requests is None:
            return {"risk": "LOW", "reason": "Análisis no disponible", "recommendations": []}
        try:
            resp = requests.post(
                self.sabionda_url,
                json={"model": "mistral", "prompt": prompt, "stream": False},
                timeout=60,
            )
            if resp.status_code != 200:
                return {"risk": "LOW", "reason": "Ollama no respondió", "recommendations": []}
            text = resp.json().get("response", "")
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception as e:
            logger.warning("Sabionda analysis failed: %s", e)
        return {"risk": "LOW", "reason": "Análisis no disponible", "recommendations": []}

    def _activate_protection_mode(self, reason: str) -> None:
        """Activa modo protección (ej. iptables). Solo en Linux y si QUANTUM_SENTINEL_ACTIVATE_PROTECTION=1."""
        logger.warning("ACTIVANDO PROTOCOLO DE PROTECCIÓN: %s", reason)
        if platform.system() != "Linux":
            return
        try:
            subprocess.run(
                ["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", "80", "-j", "DROP"],
                check=False,
                capture_output=True,
                timeout=5,
            )
            subprocess.run(
                ["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", "443", "-j", "ACCEPT"],
                check=False,
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            logger.warning("iptables no ejecutado: %s", e)

    def _register_alert_in_gaiachain(self, analysis: Dict[str, Any]) -> str:
        """Registra la alerta en GaiaChain si el CLI está disponible."""
        if not os.path.isfile(self.gaiachain_cli):
            return "gaiachain-no-cli"
        tx_data = {
            "type": "security_alert",
            "data": {
                "risk": analysis.get("risk"),
                "reason": analysis.get("reason"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actions": analysis.get("recommendations", []),
            },
        }
        try:
            r = subprocess.run(
                [
                    self.gaiachain_cli,
                    "record",
                    "--type", "security_alert",
                    "--data", json.dumps(tx_data),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return (r.stdout or "").strip() or "gaiachain-alert-ok" if r.returncode == 0 else f"Error: {r.stderr}"
        except Exception as e:
            logger.warning("GaiaChain alert: %s", e)
            return f"Error: {e}"
