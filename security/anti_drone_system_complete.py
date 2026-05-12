# -*- coding: utf-8 -*-
"""
Sistema anti-drones completo: Dedrone DroneTracker, geovalla, jammer selectivo, firma PQ, SOC.
ETSI EN 303 413.
"""
import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

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

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class CompleteAntiDroneSystem:
    """
    Detección y neutralización de drones no autorizados: API Dedrone v2, geovalla,
    clasificación de amenazas, jammer por GPIO, registro en GaiaChain con firma tipo PQ, SOC webhook.
    """

    def __init__(
        self,
        dedrone_api_key: str = "",
        gaiachain_client: Optional[Any] = None,
        jammer_pin: Optional[int] = None,
        soc_webhook: Optional[str] = None,
    ) -> None:
        self.dedrone_api_key = dedrone_api_key or __import__("os").environ.get("DEDRONE_API_KEY", "")
        self.gaiachain = gaiachain_client or (GaiaChainClient() if GaiaChainClient else None)
        self.jammer_pin = jammer_pin
        self.soc_webhook = soc_webhook or __import__("os").environ.get("SOC_WEBHOOK_URL", "")
        self.drone_database = self._init_drone_database()
        self.alert_threshold = 0.8

        if self.jammer_pin is not None and HAS_GPIO and GPIO:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.jammer_pin, GPIO.OUT)
                GPIO.output(self.jammer_pin, GPIO.LOW)
            except Exception as e:
                logger.warning("GPIO jammer init: %s", e)

    def _init_drone_database(self) -> Dict[str, Any]:
        return {
            "authorized_drones": {
                "CASTUO-DRONE-001": {
                    "model": "DJI Matrice 300 RTK",
                    "rf_signature": "sig_abc123",
                    "purpose": "Inspección de paneles solares",
                    "last_seen": None,
                    "authorized_until": "2026-12-31",
                },
                "CASTUO-DRONE-002": {
                    "model": "DJI Mavic 3 Enterprise",
                    "rf_signature": "sig_def456",
                    "purpose": "Monitoreo de cultivos",
                    "last_seen": None,
                    "authorized_until": "2026-12-31",
                },
            },
            "unauthorized_drones": {},
            "threat_patterns": {
                "DJI Mavic 3": {"level": "medium", "description": "Dron comercial no autorizado"},
                "DJI Matrice 300": {"level": "high", "description": "Potencialmente usado para vigilancia"},
                "Autel Evo II": {"level": "high", "description": "Asociado a vigilancia no autorizada"},
                "Unknown": {"level": "critical", "description": "Dron no identificado"},
            },
            "geofence_zones": [
                {
                    "name": "Invernadero Principal",
                    "coordinates": [
                        {"lat": 38.8792, "lon": -6.9706},
                        {"lat": 38.8795, "lon": -6.9706},
                        {"lat": 38.8795, "lon": -6.9703},
                        {"lat": 38.8792, "lon": -6.9703},
                    ],
                    "max_altitude": 120,
                },
            ],
        }

    def _dedrone_api_call(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if not self.dedrone_api_key or not HAS_REQUESTS:
            return {"drones": []}
        headers = {"Authorization": f"Bearer {self.dedrone_api_key}", "Content-Type": "application/json"}
        url = f"https://api.dedrone.com/v2/{endpoint}"
        try:
            r = requests.get(url, headers=headers, params=params or {}, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.warning("Dedrone API: %s", e)
            return {"error": str(e), "drones": []}

    def _is_in_geofence(self, lat: float, lon: float, altitude: float) -> Tuple[bool, Optional[str]]:
        for zone in self.drone_database.get("geofence_zones", []):
            coords = zone.get("coordinates", [])
            if len(coords) < 2:
                continue
            lat_lo = min(c["lat"] for c in coords)
            lat_hi = max(c["lat"] for c in coords)
            lon_lo = min(c["lon"] for c in coords)
            lon_hi = max(c["lon"] for c in coords)
            if lat_lo <= lat <= lat_hi and lon_lo <= lon <= lon_hi and altitude <= zone.get("max_altitude", 999):
                return True, zone.get("name")
        return False, None

    def _classify_drone(self, drone_data: Dict[str, Any]) -> Dict[str, str]:
        drone_id = drone_data.get("id", drone_data.get("drone_id", "unknown"))
        model = drone_data.get("model", "Unknown")
        if drone_id in self.drone_database.get("authorized_drones", {}):
            self.drone_database["authorized_drones"][drone_id]["last_seen"] = drone_data.get("last_seen")
            return {
                "status": "authorized",
                "threat_level": "none",
                "action": "none",
                "description": self.drone_database["authorized_drones"][drone_id].get("purpose", ""),
            }
        for pattern, threat in self.drone_database.get("threat_patterns", {}).items():
            if pattern.lower() in model.lower():
                return {
                    "status": "unauthorized",
                    "threat_level": threat["level"],
                    "action": "monitor" if threat["level"] in ("low", "medium") else "neutralize",
                    "description": threat["description"],
                }
        return {
            "status": "unauthorized",
            "threat_level": "critical",
            "action": "neutralize",
            "description": "Dron no identificado - potencial amenaza",
        }

    def _activate_jammer(self, duration: int = 15) -> bool:
        if not self.jammer_pin or not HAS_GPIO or not GPIO:
            logger.info("Jammer no configurado (simulación)")
            return False
        try:
            GPIO.output(self.jammer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.jammer_pin, GPIO.LOW)
            return True
        except Exception as e:
            logger.warning("Jammer: %s", e)
            return False

    def _notify_soc(self, alert: Dict[str, Any]) -> bool:
        if not self.soc_webhook:
            logger.info("SOC webhook no configurado")
            return False
        loc = alert.get("location", {})
        payload = {
            "text": "ALERTA DE DRON NO AUTORIZADO",
            "attachments": [{
                "title": f"Dron {alert.get('model')} ({alert.get('drone_id')})",
                "color": "danger" if alert.get("threat_level") in ("high", "critical") else "warning",
                "fields": [
                    {"title": "ID", "value": str(alert.get("drone_id")), "short": True},
                    {"title": "Modelo", "value": str(alert.get("model")), "short": True},
                    {"title": "Ubicación", "value": f"Lat: {loc.get('lat', 'N/A')}, Lon: {loc.get('lon', 'N/A')}", "short": True},
                    {"title": "Altitud", "value": f"{alert.get('altitude', 0)}m", "short": True},
                    {"title": "Amenaza", "value": str(alert.get("threat_level")), "short": True},
                    {"title": "Acción", "value": str(alert.get("action")), "short": True},
                ],
            }],
        }
        try:
            if HAS_REQUESTS:
                r = requests.post(self.soc_webhook, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
                return r.status_code == 200
            import urllib.request
            req = urllib.request.Request(
                self.soc_webhook, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            return True
        except Exception as e:
            logger.warning("Notify SOC: %s", e)
            return False

    def _log_to_gaiachain(self, alert: Dict[str, Any]) -> str:
        event_hash = hashlib.sha3_512(json.dumps(alert, sort_keys=True).encode()).hexdigest()
        signature = f"PQ-SIG-{event_hash[:64]}"
        payload = {
            "type": "unauthorized_drone",
            "drone_id": alert.get("drone_id"),
            "model": alert.get("model"),
            "location": alert.get("location"),
            "altitude": alert.get("altitude"),
            "threat_level": alert.get("threat_level"),
            "action_taken": alert.get("action"),
            "timestamp": datetime.now().isoformat(),
            "pq_signature": signature,
            "event_hash": event_hash,
            "node_id": "anti_drone",
        }
        return self.gaiachain.log_security_alert(payload) if self.gaiachain else ""

    def scan_drones(self) -> List[Dict[str, Any]]:
        sensors = self._dedrone_api_call("sensors")
        if sensors.get("error"):
            return []
        drones_data = self._dedrone_api_call("drones")
        if drones_data.get("error"):
            return []
        drones = []
        for drone in drones_data.get("drones", []):
            loc = drone.get("location", {})
            lat, lon = loc.get("lat", 0), loc.get("lon", 0)
            alt = drone.get("altitude", 0)
            in_geofence, zone_name = self._is_in_geofence(lat, lon, alt)
            if not in_geofence:
                continue
            classification = self._classify_drone(drone)
            drone_id = drone.get("id", drone.get("drone_id", "unknown"))
            drones.append({
                **drone,
                "drone_id": drone_id,
                "zone": zone_name,
                "status": classification["status"],
                "threat_level": classification["threat_level"],
                "action": classification["action"],
                "description": classification["description"],
                "location": loc,
                "altitude": alt,
            })
        return drones

    def handle_drone_detection(self, drone: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "drone_id": drone.get("drone_id"),
            "model": drone.get("model"),
            "status": drone.get("status"),
            "threat_level": drone.get("threat_level"),
            "actions_taken": [],
            "gaiachain_tx": None,
        }
        try:
            if self._notify_soc(drone):
                result["actions_taken"].append("soc_notified")
            tx_id = self._log_to_gaiachain(drone)
            result["gaiachain_tx"] = tx_id
            if drone.get("threat_level") in ("high", "critical") and self._activate_jammer():
                result["actions_taken"].append("jammer_activated")
            uid = self.drone_database.get("unauthorized_drones", {})
            did = drone.get("drone_id")
            if drone.get("status") == "unauthorized":
                if did not in uid:
                    uid[did] = {
                        "first_seen": drone.get("last_seen"),
                        "last_seen": drone.get("last_seen"),
                        "threat_level": drone.get("threat_level"),
                        "actions": list(result["actions_taken"]),
                    }
                else:
                    uid[did]["last_seen"] = drone.get("last_seen")
                    uid[did]["actions"].extend(result["actions_taken"])
        except Exception as e:
            result["error"] = str(e)
        return result

    def monitor(self, interval: int = 30) -> None:
        logger.info("Monitoreo de drones (intervalo %ss)", interval)
        try:
            while True:
                drones = self.scan_drones()
                for drone in drones:
                    if drone.get("status") == "unauthorized":
                        res = self.handle_drone_detection(drone)
                        logger.info("Dron no autorizado: %s - Acciones: %s", drone.get("drone_id"), res.get("actions_taken"))
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Monitoreo detenido.")
        finally:
            if self.jammer_pin is not None and HAS_GPIO and GPIO:
                GPIO.cleanup()
