# -*- coding: utf-8 -*-
"""Red europea de mensajería para gestión coordinada de drones agrícolas (ES, PT, FR, IT)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient


@dataclass
class EuropeanDroneOperator:
    """Información de un operador de drones en la red europea."""
    operator_id: str
    name: str
    country: str
    base_location: Dict[str, float]
    fleet_size: int
    drone_types: List[str]
    certifications: List[str]
    contact: Dict[str, str]
    api_endpoint: str
    last_seen: str


@dataclass
class DroneMission:
    """Definición de una misión para drones en la red europea."""
    mission_id: str
    operator_id: str
    drone_id: str
    start_location: Dict[str, float]
    end_location: Optional[Dict[str, float]]
    waypoints: List[Dict[str, float]]
    purpose: str
    start_time: str
    end_time: str
    status: str
    payload: Dict
    regulations_compliance: List[str]
    gaiachain_tx: Optional[str] = None
    telemetry: Optional[Dict] = None


class EuropeanDroneNetwork:
    """
    Red europea de mensajería para gestión coordinada de drones agrícolas.
    Conexión con operadores en España, Portugal, Francia e Italia;
    misiones transfronterizas; cumplimiento normativo; GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.operators = self._initialize_operators()
        self.active_missions: Dict[str, DroneMission] = {}
        self.country_regulations = self._load_country_regulations()
        self.airspace_restrictions = self._load_airspace_restrictions()

    def _initialize_operators(self) -> Dict[str, EuropeanDroneOperator]:
        """Inicializa la lista de operadores europeos conectados."""
        return {
            "ES-CASTUO-001": EuropeanDroneOperator(
                operator_id="ES-CASTUO-001",
                name="CASTUO-SYSTEM Extremadura",
                country="Spain",
                base_location={"lat": 39.4769, "lon": -6.3706},
                fleet_size=150,
                drone_types=[
                    "PrecisionSprayer X1",
                    "AgroSense Elite",
                    "SmartSeeder Pro",
                    "BioStim Pro",
                    "TerraMapper 3D",
                ],
                certifications=[
                    "ISO 9001",
                    "ISO 14001",
                    "AEMPS (cannabis medicinal)",
                    "EN 9100 (aeroespacial)",
                    "Certificación de economía circular",
                    "Real Decreto 1036/2017 (operación de drones)",
                    "Ley 18/2014 (seguridad privada)",
                    "Reglamento (UE) 2019/947 (drones)",
                    "RD 903/2025 (cannabis medicinal)",
                    "Ley 43/2003 (montes)",
                    "Normativa de uso de productos fitosanitarios",
                ],
                contact={
                    "email": "operaciones@castu.system",
                    "phone": "+34 927 123 456",
                    "emergency": "+34 600 123 456",
                },
                api_endpoint="https://api.castu.system/drones",
                last_seen=datetime.now().isoformat(),
            ),
            "ES-AND-001": EuropeanDroneOperator(
                operator_id="ES-AND-001",
                name="AgroDrones Andalucía",
                country="Spain",
                base_location={"lat": 37.3891, "lon": -5.9845},
                fleet_size=80,
                drone_types=["Multispectral Scout", "Sprayer Drone Pro"],
                certifications=["ISO 9001", "Certificación ecológica UE"],
                contact={"email": "contacto@agrodrones-and.es", "phone": "+34 954 123 789"},
                api_endpoint="https://api.agrodrones-and.es/v1",
                last_seen=datetime.now().isoformat(),
            ),
            "PT-ALG-001": EuropeanDroneOperator(
                operator_id="PT-ALG-001",
                name="Algarve AgriDrones",
                country="Portugal",
                base_location={"lat": 37.0222, "lon": -7.9289},
                fleet_size=60,
                drone_types=["Precision Agriculture Drone", "Soil Analysis Drone", "PrecisionSprayer X1"],
                certifications=["ISO 9001", "Certificación PRR", "EcoCert"],
                contact={"email": "info@agridrones-algarve.pt", "phone": "+351 289 123 456"},
                api_endpoint="https://api.agridrones.pt/v2",
                last_seen=datetime.now().isoformat(),
            ),
            "PT-LIS-001": EuropeanDroneOperator(
                operator_id="PT-LIS-001",
                name="Lisbon AgroTech Drones",
                country="Portugal",
                base_location={"lat": 38.7223, "lon": -9.1393},
                fleet_size=120,
                drone_types=["Multispectral Drone X", "Cargo Drone 50"],
                certifications=["ISO 9001", "ISO 14001", "Certificación PRR"],
                contact={"email": "support@agrotech-drones.pt", "phone": "+351 21 123 4567"},
                api_endpoint="https://api.agrotech.pt/drones",
                last_seen=datetime.now().isoformat(),
            ),
            "FR-PAC-001": EuropeanDroneOperator(
                operator_id="FR-PAC-001",
                name="Provence AgriDrones",
                country="France",
                base_location={"lat": 43.6119, "lon": 3.8772},
                fleet_size=200,
                drone_types=[
                    "Vineyard Monitoring Drone",
                    "Olive Tree Sprayer",
                    "Lavender Harvest Drone",
                ],
                certifications=[
                    "ISO 9001",
                    "HACCP",
                    "Certificación agrícola francesa",
                    "EcoCert (agricultura ecológica)",
                ],
                contact={
                    "email": "contact@agridrones-provence.fr",
                    "phone": "+33 4 12 34 56 78",
                },
                api_endpoint="https://api.agridrones.fr/v1",
                last_seen=datetime.now().isoformat(),
            ),
            "IT-TOS-001": EuropeanDroneOperator(
                operator_id="IT-TOS-001",
                name="Tuscany AgroDrones",
                country="Italy",
                base_location={"lat": 43.7696, "lon": 11.2558},
                fleet_size=180,
                drone_types=[
                    "Vineyard Precision Drone",
                    "Olive Grove Monitor",
                    "Truffle Detection Drone",
                ],
                certifications=[
                    "ISO 9001",
                    "ISO 22000",
                    "Certificación agrícola italiana",
                    "DOP/IGP para productos agrícolas",
                ],
                contact={"email": "info@agrodrones-tuscany.it", "phone": "+39 055 123456"},
                api_endpoint="https://api.agrodrones-tuscany.it/api",
                last_seen=datetime.now().isoformat(),
            ),
        }

    def _load_country_regulations(self) -> Dict[str, Dict]:
        """Carga las normativas por país para operación de drones."""
        return {
            "Spain": {
                "general": [
                    "Real Decreto 1036/2017 (operación de drones)",
                    "Ley 18/2014 (seguridad privada)",
                    "Reglamento (UE) 2019/947 (drones)",
                ],
                "agricultural": [
                    "RD 903/2025 (cannabis medicinal)",
                    "Ley 43/2003 (montes)",
                    "Normativa de uso de productos fitosanitarios",
                ],
                "airspace": {
                    "max_altitude": 120,
                    "flight_permit_required": True,
                },
                "certifications": ["ISO 9001", "ISO 14001", "AEMPS para cannabis"],
            },
            "Portugal": {
                "general": [
                    "Decreto-Lei n.º 10/2018 (operación de drones)",
                    "Regulamento (UE) 2019/947",
                    "Ley n.º 17/2009 (seguridad privada)",
                ],
                "agricultural": [
                    "Decreto-Lei n.º 30/2021 (uso de drones en agricultura)",
                    "Normas de aplicación de productos fitosanitarios",
                    "Certificación PRR",
                ],
                "airspace": {"max_altitude": 120, "flight_permit_required": True},
                "certifications": ["ISO 9001", "Certificación PRR"],
            },
            "France": {
                "general": [
                    "Arrêté du 17 décembre 2015 (drones)",
                    "Règlement (UE) 2019/947",
                    "Code de l'aviation civile (Art. L6211-1 et suivants)",
                ],
                "agricultural": [
                    "Arrêté du 27 décembre 2019 (épandage par drones)",
                    "Normes pour l'utilisation des produits phytopharmaceutiques",
                    "Certification EcoCert pour l'agriculture biologique",
                ],
                "airspace": {"max_altitude": 120, "flight_permit_required": True},
                "certifications": ["ISO 9001", "HACCP", "EcoCert"],
            },
            "Italy": {
                "general": [
                    "Regolamento ENAC (droni)",
                    "Regolamento (UE) 2019/947",
                    "Decreto Legislativo 61/2018 (sicurezza dei droni)",
                ],
                "agricultural": [
                    "Decreto 22 gennaio 2021 (uso di droni in agricoltura)",
                    "Normative sull'uso dei prodotti fitosanitari",
                    "Certificazioni DOP/IGP per prodotti agricoli",
                ],
                "airspace": {"max_altitude": 120, "flight_permit_required": True},
                "certifications": ["ISO 9001", "ISO 22000", "DOP/IGP"],
            },
        }

    def _load_airspace_restrictions(self) -> Dict[str, List[Dict]]:
        """Carga las restricciones del espacio aéreo por país."""
        return {
            "Spain": [
                {
                    "name": "Espacio aéreo controlado Madrid",
                    "type": "CTR",
                    "coordinates": [
                        {"lat": 40.4168, "lon": -3.7038},
                        {"lat": 40.5, "lon": -3.5},
                        {"lat": 40.3, "lon": -3.5},
                        {"lat": 40.3, "lon": -3.9},
                    ],
                    "max_altitude": 0,
                    "restriction": "Prohibido sin permiso ATC",
                },
            ],
            "Portugal": [],
            "France": [],
            "Italy": [],
        }

    def _point_in_polygon(self, point: Dict[str, float], polygon: List[Dict[str, float]]) -> bool:
        """Verifica si un punto está dentro de un polígono (ray-casting simplificado)."""
        if len(polygon) < 3:
            return False
        lat, lon = point.get("lat", 0), point.get("lon", 0)
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i].get("lat", 0), polygon[i].get("lon", 0)
            xj, yj = polygon[j].get("lat", 0), polygon[j].get("lon", 0)
            if ((yi > lon) != (yj > lon)) and (lat < (xj - xi) * (lon - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    def _check_airspace_restrictions(
        self, country: str, path: List[Dict[str, float]]
    ) -> Tuple[bool, List[Dict]]:
        """Verifica si una ruta de vuelo violaría restricciones del espacio aéreo."""
        violations: List[Dict] = []
        for zone in self.airspace_restrictions.get(country, []):
            for point in path:
                if self._point_in_polygon(point, zone.get("coordinates", [])):
                    violations.append({
                        "zone": zone["name"],
                        "type": zone["type"],
                        "restriction": zone["restriction"],
                        "violated_point": point,
                    })
        return len(violations) == 0, violations

    def _get_required_compliance(self, country: str, purpose: str) -> List[str]:
        """Obtiene los requisitos de cumplimiento para una misión."""
        regs = self.country_regulations.get(country, {})
        base = list(regs.get("general", []))
        if "agricultural" in purpose.lower() or "agricola" in purpose.lower():
            base.extend(regs.get("agricultural", []))
        return list(set(base))

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula la distancia entre dos puntos en metros (fórmula Haversine)."""
        R = 6371000  # Radio de la Tierra en metros
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        delta_phi = radians(lat2 - lat1)
        delta_lambda = radians(lon2 - lon1)
        a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _calculate_path_distance(self, path: List[Dict[str, float]]) -> float:
        """Calcula la distancia total de una ruta en metros."""
        distance = 0.0
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i + 1]
            distance += self._haversine(
                p1["lat"], p1["lon"],
                p2["lat"], p2["lon"],
            )
        return distance

    def _estimate_flight_time(self, distance: float, drone_type: str) -> int:
        """Estima el tiempo de vuelo en minutos."""
        speeds = {"Multirrotor": 10, "Ala fija": 15, "Hexacóptero": 8}
        speed = speeds.get(drone_type, 10)  # m/s
        return int((distance / speed) * 1.2 / 60) if speed else 0

    def plan_mission(
        self,
        operator_id: str,
        drone_id: str,
        start_location: Dict[str, float],
        waypoints: List[Dict[str, float]],
        purpose: str,
        payload: Dict,
    ) -> Dict:
        """Planifica una nueva misión para un dron en la red europea."""
        operator = self.operators.get(operator_id)
        if not operator:
            return {"status": "error", "message": f"Operador {operator_id} no encontrado"}

        country = operator.country
        mission_id = (
            f"MISSION-{country}-{datetime.now().strftime('%Y%m%d%H%M%S')}-"
            f"{len(self.active_missions) + 1:04d}"
        )

        path = [start_location] + waypoints
        is_valid, violations = self._check_airspace_restrictions(country, path)
        if not is_valid:
            return {
                "status": "error",
                "message": "Ruta violaría restricciones del espacio aéreo",
                "violations": violations,
            }

        required_compliance = self._get_required_compliance(country, purpose)
        operator_certs = set(operator.certifications)
        missing = [r for r in required_compliance if r not in operator_certs]
        if missing:
            return {
                "status": "error",
                "message": "Faltan certificaciones requeridas",
                "missing_certifications": missing,
            }

        total_distance = self._calculate_path_distance(path)
        drone_type = payload.get("drone_type", "Multirrotor")
        estimated_time = self._estimate_flight_time(total_distance, drone_type)
        if estimated_time <= 0:
            estimated_time = 30  # default 30 min

        end_time_dt = datetime.now() + timedelta(minutes=estimated_time)
        mission = DroneMission(
            mission_id=mission_id,
            operator_id=operator_id,
            drone_id=drone_id,
            start_location=start_location,
            end_location=waypoints[-1] if waypoints else None,
            waypoints=waypoints,
            purpose=purpose,
            start_time=datetime.now().isoformat(),
            end_time=end_time_dt.isoformat(),
            status="planned",
            payload=payload,
            regulations_compliance=required_compliance,
        )

        tx_id = self.gaiachain.log_drone_mission({
            "mission_id": mission_id,
            "operator_id": operator_id,
            "drone_id": drone_id,
            "country": country,
            "purpose": purpose,
            "start_location": start_location,
            "waypoints": waypoints,
            "start_time": mission.start_time,
            "estimated_end": mission.end_time,
            "regulations_compliance": required_compliance,
            "status": "planned",
            "payload": payload,
        })
        mission.gaiachain_tx = tx_id
        self.active_missions[mission_id] = mission

        return {
            "status": "success",
            "mission": {
                "mission_id": mission.mission_id,
                "operator_id": mission.operator_id,
                "drone_id": mission.drone_id,
                "start_location": mission.start_location,
                "waypoints": mission.waypoints,
                "purpose": mission.purpose,
                "start_time": mission.start_time,
                "end_time": mission.end_time,
                "status": mission.status,
                "payload": mission.payload,
                "regulations_compliance": mission.regulations_compliance,
            },
            "gaiachain_tx": tx_id,
            "estimated_flight_time": estimated_time,
            "total_distance_km": total_distance / 1000,
            "compliance_status": "fully_compliant",
        }

    def start_mission(self, mission_id: str) -> Dict:
        """Inicia una misión planificada."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        if mission.status != "planned":
            return {"status": "error", "message": f"Misión ya está en estado {mission.status}"}

        mission.status = "in_progress"
        mission.start_time = datetime.now().isoformat()
        self.gaiachain.log_drone_mission({
            "mission_id": mission_id,
            "status": "in_progress",
            "actual_start_time": mission.start_time,
            "timestamp": datetime.now().isoformat(),
        })
        return {
            "status": "success",
            "mission_id": mission_id,
            "new_status": "in_progress",
            "start_time": mission.start_time,
        }

    def complete_mission(self, mission_id: str, telemetry_data: Dict) -> Dict:
        """Completa una misión en progreso."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        if mission.status != "in_progress":
            return {"status": "error", "message": f"Misión no está en progreso (estado: {mission.status})"}

        mission.status = "completed"
        mission.end_time = datetime.now().isoformat()
        mission.telemetry = telemetry_data

        tx_id = self.gaiachain.log_drone_mission({
            "mission_id": mission_id,
            "status": "completed",
            "actual_end_time": mission.end_time,
            "telemetry": {
                "distance_km": telemetry_data.get("distance", 0) / 1000,
                "max_altitude": telemetry_data.get("max_altitude", 0),
                "battery_usage": telemetry_data.get("battery_usage", 0),
                "payload_deployed": telemetry_data.get("payload_deployed", False),
            },
            "timestamp": datetime.now().isoformat(),
        })
        duration_sec = (
            datetime.fromisoformat(mission.end_time) - datetime.fromisoformat(mission.start_time)
        ).total_seconds()
        return {
            "status": "success",
            "mission_id": mission_id,
            "new_status": "completed",
            "end_time": mission.end_time,
            "gaiachain_tx": tx_id,
            "telemetry_summary": {
                "distance_km": telemetry_data.get("distance", 0) / 1000,
                "duration_min": duration_sec / 60,
            },
        }

    def get_mission_status(self, mission_id: str) -> Dict:
        """Obtiene el estado de una misión."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        gaiachain_data = self.gaiachain.get_drone_mission(mission_id)
        op = self.operators.get(mission.operator_id)
        return {
            "status": "success",
            "mission": {
                "mission_id": mission.mission_id,
                "operator_id": mission.operator_id,
                "drone_id": mission.drone_id,
                "start_location": mission.start_location,
                "waypoints": mission.waypoints,
                "purpose": mission.purpose,
                "start_time": mission.start_time,
                "end_time": mission.end_time,
                "status": mission.status,
                "payload": mission.payload,
                "telemetry": mission.telemetry,
            },
            "gaiachain_data": gaiachain_data,
            "current_status": mission.status,
            "operator": op.name if op else "Desconocido",
        }

    def get_operator_missions(
        self, operator_id: str, status_filter: Optional[str] = None
    ) -> List[Dict]:
        """Obtiene las misiones de un operador."""
        missions = [
            m
            for m in self.active_missions.values()
            if m.operator_id == operator_id
            and (status_filter is None or m.status == status_filter)
        ]
        result = []
        for m in missions:
            op = self.operators.get(m.operator_id)
            result.append({
                "mission_id": m.mission_id,
                "operator_id": m.operator_id,
                "drone_id": m.drone_id,
                "purpose": m.purpose,
                "start_time": m.start_time,
                "end_time": m.end_time,
                "status": m.status,
                "operator_name": op.name if op else "Desconocido",
                "country": op.country if op else "Desconocido",
            })
        return result

    def get_cross_border_missions(self) -> List[Dict]:
        """Obtiene misiones que cruzan fronteras entre países (placeholder)."""
        return []

    def get_network_stats(self) -> Dict:
        """Obtiene estadísticas de la red europea."""
        missions_by_status: Dict[str, int] = {}
        for m in self.active_missions.values():
            missions_by_status[m.status] = missions_by_status.get(m.status, 0) + 1

        total_flight_hours = 0.0
        total_distance_km = 0.0
        for m in self.active_missions.values():
            if m.status == "completed" and m.start_time and m.end_time:
                delta = datetime.fromisoformat(m.end_time) - datetime.fromisoformat(m.start_time)
                total_flight_hours += delta.total_seconds() / 3600
            if m.status == "completed" and m.telemetry:
                total_distance_km += m.telemetry.get("distance", 0) / 1000

        operators_by_country: Dict[str, int] = {}
        for op in self.operators.values():
            operators_by_country[op.country] = operators_by_country.get(op.country, 0) + 1

        missions_by_country: Dict[str, int] = {}
        for m in self.active_missions.values():
            op = self.operators.get(m.operator_id)
            c = op.country if op else "Unknown"
            missions_by_country[c] = missions_by_country.get(c, 0) + 1

        return {
            "total_operators": len(self.operators),
            "operators_by_country": operators_by_country,
            "total_missions": len(self.active_missions),
            "missions_by_status": missions_by_status,
            "missions_by_country": missions_by_country,
            "total_flight_hours": round(total_flight_hours, 2),
            "total_distance_km": round(total_distance_km, 2),
        }

    def send_cross_border_request(
        self,
        origin_operator_id: str,
        destination_country: str,
        mission_purpose: str,
        payload_requirements: Dict,
    ) -> Dict:
        """Envía una solicitud de misión transfronteriza."""
        origin_operator = self.operators.get(origin_operator_id)
        if not origin_operator:
            return {"status": "error", "message": f"Operador {origin_operator_id} no encontrado"}

        def _operator_meets_requirements(op: EuropeanDroneOperator, req: Dict) -> bool:
            if "drone_type" in req and req["drone_type"] not in op.drone_types:
                return False
            if "required_certifications" in req:
                missing = [c for c in req["required_certifications"] if c not in op.certifications]
                if missing:
                    return False
            return True

        destination_operators = [
            op
            for op in self.operators.values()
            if op.country == destination_country
            and _operator_meets_requirements(op, payload_requirements)
        ]
        if not destination_operators:
            return {
                "status": "error",
                "message": f"No se encontraron operadores en {destination_country} con las capacidades requeridas",
            }

        selected = destination_operators[0]
        request_id = (
            f"XBORDER-{origin_operator.country}-{destination_country}-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        tx_id = self.gaiachain.log_cross_border_request({
            "request_id": request_id,
            "origin_operator": origin_operator_id,
            "origin_country": origin_operator.country,
            "destination_operator": selected.operator_id,
            "destination_country": destination_country,
            "purpose": mission_purpose,
            "payload_requirements": payload_requirements,
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
        })
        return {
            "status": "success",
            "request_id": request_id,
            "origin_operator": origin_operator.name,
            "destination_operator": selected.name,
            "destination_country": destination_country,
            "gaiachain_tx": tx_id,
            "next_steps": [
                f"Contactar a {selected.name} via {selected.contact.get('email', '')}",
                "Negociar términos de la misión transfronteriza",
                "Firmar acuerdo de colaboración (usando smart contracts en GaiaChain)",
            ],
        }

    def get_regulatory_compliance_report(self, country: str, mission_type: str) -> Dict:
        """Genera un informe de cumplimiento normativo para un tipo de misión en un país."""
        regulations = self.country_regulations.get(country, {})
        required = self._get_required_compliance(country, mission_type)
        certs = set()
        for key in ("general", "agricultural"):
            for r in regulations.get(key, []):
                if "ISO" in r or "Certificación" in r or "Certification" in r:
                    certs.add(r)
        return {
            "country": country,
            "mission_type": mission_type,
            "required_compliance": required,
            "detailed_regulations": {
                "general": regulations.get("general", []),
                "agricultural": regulations.get("agricultural", []),
                "airspace": regulations.get("airspace", {}),
            },
            "certification_requirements": list(certs),
            "recommended_actions": [
                "Obtener certificaciones faltantes",
                "Solicitar permisos de vuelo a autoridades locales",
                "Realizar evaluación de riesgo específica para la misión",
                "Registrar la misión en GaiaChain para trazabilidad",
            ],
        }


if __name__ == "__main__":
    drone_network = EuropeanDroneNetwork(gaiachain_client=GaiaChainClient())
    stats = drone_network.get_network_stats()
    print("Estadísticas de la Red Europea de Drones:")
    print(f"  Operadores totales: {stats['total_operators']}")
    for country, count in stats["operators_by_country"].items():
        print(f"  - {country}: {count}")
    res = drone_network.plan_mission(
        "ES-CASTUO-001",
        "DRONE-001",
        {"lat": 39.47, "lon": -6.37},
        [{"lat": 39.48, "lon": -6.35}],
        "agricultural spraying",
        {"drone_type": "Multirrotor"},
    )
    print("\nPlanificación misión:", res.get("status"), "- GaiaChain tx:", (res.get("gaiachain_tx") or "")[:24] + "...")
