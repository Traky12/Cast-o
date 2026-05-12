# -*- coding: utf-8 -*-
"""
Detección de APT (Advanced Persistent Threats): integración con Velociraptor y threat intel.
Registro de alertas en GaiaChain y notificación al SOC.
"""
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

VELOCIRAPTOR_CLIENT = "/opt/velociraptor/client"
THREAT_INTEL_FEEDS = [
    "https://otx.alienvault.com/api/v1/indicators/export",
    "https://rules.emergingthreats.net/open/suricata/rules/",
]
APT_INDICATORS = [
    "mimikatz", "cobaltstrike", "powershell -ep bypass",
    "wmic process", "schtasks /create", "reg add",
    "certutil -decode", "bitsadmin /transfer",
    "rundll32.exe", "mshta.exe", "wscript.exe",
]


class APTDetector:
    """
    Actualización de threat intel, escaneo con Velociraptor (windows.apt.hunt),
    análisis de indicadores y registro de alertas en GaiaChain.
    """

    def __init__(self) -> None:
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self.velociraptor_path = Path(VELOCIRAPTOR_CLIENT)
        self.last_scan: Optional[str] = None

    def update_threat_intel(self) -> None:
        """Descarga feeds de threat intel (stub: en producción usar requests)."""
        logger.info("Actualizando inteligencia de amenazas...")
        for feed in THREAT_INTEL_FEEDS:
            try:
                name = feed.rstrip("/").split("/")[-2] if "/" in feed else "feed"
                subprocess.run(
                    ["curl", "-s", "-o", f"/tmp/threat_intel_{name}.json", feed],
                    check=False,
                    timeout=30,
                    capture_output=True,
                )
                logger.info("Feed actualizado: %s", feed)
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning("Error actualizando feed %s: %s", feed, e)

    def scan_system(self) -> bool:
        """Ejecuta colección Velociraptor (si existe el binario) y analiza resultados."""
        self.update_threat_intel()
        self.last_scan = datetime.now().isoformat()
        if not self.velociraptor_path.exists():
            logger.warning("Velociraptor client no encontrado en %s", self.velociraptor_path)
            return False
        try:
            result = subprocess.run(
                [str(self.velociraptor_path), "collect", "windows.apt.hunt", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                logger.warning("Error en escaneo Velociraptor: %s", result.stderr)
                return False
            findings = json.loads(result.stdout) if result.stdout else {}
            if findings.get("stats", {}).get("collected_files", 0) > 0:
                self._analyze_findings(findings)
            return True
        except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
            logger.warning("Error en escaneo: %s", e)
            return False

    def _analyze_findings(self, findings: Dict[str, Any]) -> None:
        """Busca indicadores de APT en archivos recolectados."""
        collected = findings.get("collected", []) or findings.get("results", [])
        alerts: List[Dict[str, Any]] = []
        for file_entry in collected:
            content = (file_entry.get("content") or file_entry.get("Content") or "").lower()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore").lower()
            path = file_entry.get("path") or file_entry.get("FullPath") or "desconocido"
            for indicator in APT_INDICATORS:
                if indicator in content:
                    alerts.append({
                        "indicator": indicator,
                        "file": path,
                        "content": content[:200],
                        "severity": "high",
                        "type": "apt_indicator",
                    })
        for alert in alerts:
            self._handle_apt_alert(alert)
        if not alerts:
            logger.info("No se detectaron indicadores de APT en este escaneo.")

    def _handle_apt_alert(self, alert: Dict[str, Any]) -> None:
        """Registra alerta en GaiaChain y notifica; simula aislamiento de host."""
        logger.warning("ALERTA APT: %s en %s", alert["indicator"], alert["file"])
        if self.blockchain:
            self.blockchain.log_security_alert({
                "type": "apt_indicator",
                "indicator": alert["indicator"],
                "file": alert["file"],
                "content_sample": alert["content"],
                "severity": alert["severity"],
                "timestamp": datetime.now().isoformat(),
                "action": "isolate_host",
                "node_id": "apt_detector",
            })
        host = alert["file"].split("/")[0] if "/" in alert["file"] else alert["file"]
        logger.info("Host afectado aislado (simulado): %s", host)

    def monitor_continuously(self, interval_seconds: int = 3600) -> None:
        """Bucle de monitoreo periódico."""
        logger.info("Monitoreo continuo de APT (intervalo: %s s)", interval_seconds)
        try:
            while True:
                logger.info("Escaneo programado a las %s", datetime.now().strftime("%H:%M:%S"))
                self.scan_system()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Monitoreo de APT detenido.")
