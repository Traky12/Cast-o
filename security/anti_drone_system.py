# -*- coding: utf-8 -*-
"""
Sistema anti-drones: detección RF (Dedrone) y jammer selectivo. ETSI EN 303 413.
"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    GPIO = None  # type: ignore


class AntiDroneSystem:
    """
    Detección y neutralización de drones no autorizados (Dedrone API + jammer opcional).
    Registro en GaiaChain y notificación a seguridad.
    """

    def __init__(
        self,
        dedrone_api_key: str = "",
        gaiachain_client: Optional[Any] = None,
        jammer_pin: Optional[int] = None,
    ) -> None:
        self.dedrone_api = dedrone_api_key or os.environ.get("DEDRONE_API_KEY", "")
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.jammer_pin = jammer_pin
        self.drone_database = self._load_drone_database()
        self.alert_threshold = 0.85
        if self.jammer_pin is not None and HAS_GPIO and GPIO:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.jammer_pin, GPIO.OUT)
                GPIO.output(self.jammer_pin, GPIO.LOW)
            except Exception as e:
                logger.warning("GPIO jammer init failed: %s", e)

    def _load_drone_database(self) -> Dict[str, Any]:
        return {
            "authorized": {
                "DJI_Mavic_3_CASTUO_01": {"rf_signature": "sig123", "last_seen": None},
                "DJI_Mavic_3_CASTUO_02": {"rf_signature": "sig456", "last_seen": None},
            },
            "unauthorized_patterns": {
                "DJI_Mavic_3": {"threat_level": "medium"},
                "DJI_Matric_300": {"threat_level": "high"},
                "Autel_Evo_II": {"threat_level": "high"},
                "Unknown": {"threat_level": "critical"},
            },
        }

    def _dedrone_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Llamada a API Dedrone (stub si no hay key)."""
        if not self.dedrone_api:
            return {"drones": []}
        try:
            import urllib.request
            import urllib.parse
            url = f"https://api.dedrone.com/v1/{endpoint}"
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.dedrone_api}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            logger.warning("Dedrone API error: %s", e)
            return {"drones": []}

    def scan_for_drones(self) -> List[Dict[str, Any]]:
        """Escanea presencia de drones (Dedrone)."""
        try:
            data = self._dedrone_api_request("sensors/drones")
            drones = []
            for drone in data.get("drones", []):
                drone_info = {
                    "drone_id": drone.get("id", "unknown"),
                    "model": drone.get("model", "Unknown"),
                    "rf_signature": drone.get("rf_signature"),
                    "gps_location": drone.get("location", {}),
                    "altitude": drone.get("altitude", 0),
                    "velocity": drone.get("velocity", 0),
                    "confidence": drone.get("confidence", 0),
                    "last_seen": drone.get("timestamp"),
                    "status": "unknown",
                }
                drone_info["status"] = self._classify_drone(drone_info)
                drones.append(drone_info)
            return drones
        except Exception as e:
            logger.warning("scan_for_drones error: %s", e)
            return []

    def _classify_drone(self, drone: Dict[str, Any]) -> str:
        if drone["drone_id"] in self.drone_database.get("authorized", {}):
            self.drone_database["authorized"][drone["drone_id"]]["last_seen"] = drone.get("last_seen")
            return "authorized"
        for pattern, info in self.drone_database.get("unauthorized_patterns", {}).items():
            if pattern in (drone.get("model") or ""):
                drone["threat_level"] = info["threat_level"]
                return "unauthorized"
        drone["threat_level"] = "critical"
        return "unauthorized"

    def _activate_jammer(self, duration: int = 10) -> None:
        if self.jammer_pin is None or not HAS_GPIO or not GPIO:
            logger.info("Jammer no configurado (modo simulación)")
            return
        try:
            GPIO.output(self.jammer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.jammer_pin, GPIO.LOW)
        except Exception as e:
            logger.warning("Jammer error: %s", e)

    def _notify_security_team(self, drone: Dict[str, Any]) -> None:
        alert = {
            "type": "unauthorized_drone",
            "drone_id": drone.get("drone_id"),
            "model": drone.get("model"),
            "location": drone.get("gps_location"),
            "threat_level": drone.get("threat_level", "critical"),
            "timestamp": datetime.now().isoformat(),
            "action": "jamming_activated" if drone.get("threat_level") in ("high", "critical") else "monitoring",
            "node_id": "anti_drone",
        }
        if self.gaiachain:
            self.gaiachain.log_security_alert(alert)
        webhook = os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("CASTUO_SLACK_WEBHOOK", "")
        if webhook:
            try:
                import urllib.request
                payload = json.dumps({
                    "text": "ALERTA: DRON NO AUTORIZADO DETECTADO",
                    "attachments": [{
                        "title": f"Dron {drone.get('model')} ({drone.get('drone_id')})",
                        "color": "danger",
                        "fields": [
                            {"title": "Ubicación", "value": str(drone.get("gps_location")), "short": True},
                            {"title": "Amenaza", "value": drone.get("threat_level", "critical"), "short": True},
                        ],
                    }],
                }).encode()
                req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=5) as r:
                    r.read()
            except Exception as e:
                logger.warning("Notify security: %s", e)

    def monitor(self, interval: int = 60) -> None:
        """Bucle de monitoreo de drones."""
        logger.info("Monitoreo de drones (intervalo %ss)", interval)
        try:
            while True:
                drones = self.scan_for_drones()
                for drone in drones:
                    if drone["status"] == "unauthorized":
                        self._notify_security_team(drone)
                        if drone.get("threat_level") in ("high", "critical"):
                            self._activate_jammer()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoreo de drones detenido.")
        finally:
            if self.jammer_pin is not None and HAS_GPIO and GPIO:
                GPIO.cleanup()
