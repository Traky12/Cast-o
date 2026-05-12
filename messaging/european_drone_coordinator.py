# -*- coding: utf-8 -*-
"""
Coordinador de misiones transfronterizas entre operadores europeos.
Negociación, cumplimiento normativo, smart contracts y trazabilidad GaiaChain.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from dataclasses import dataclass, field

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient
from messaging.european_drone_network import EuropeanDroneNetwork, EuropeanDroneOperator, DroneMission


@dataclass
class CrossBorderMission:
    """Misión transfronteriza entre operadores de diferentes países."""

    mission_id: str
    origin_operator: str
    origin_country: str
    destination_operator: str
    destination_country: str
    purpose: str
    payload: Dict[str, Any]
    start_location: Dict[str, float]
    end_location: Dict[str, float]
    waypoints: List[Dict[str, float]]
    start_time: str
    end_time: str
    status: str
    regulations_compliance: Dict[str, List[str]]
    gaiachain_tx: Optional[str] = None
    smart_contract: Optional[str] = None
    actual_start_time: Optional[str] = None
    actual_end_time: Optional[str] = None
    telemetry_data: Optional[Dict[str, Any]] = None
    issues: Optional[List[str]] = field(default_factory=list)
    origin_local_mission_id: Optional[str] = None
    destination_local_mission_id: Optional[str] = None


class EuropeanDroneCoordinator:
    """
    Coordinador de misiones transfronterizas entre operadores europeos.
    Negociación automática, cumplimiento normativo, smart contracts, trazabilidad GaiaChain.
    """

    def __init__(
        self,
        drone_network: EuropeanDroneNetwork,
        gaiachain_client: Optional[GaiaChainClient] = None,
    ) -> None:
        self.drone_network = drone_network
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.active_missions: Dict[str, CrossBorderMission] = {}
        self.smart_contract_templates = self._load_smart_contract_templates()

    def _load_smart_contract_templates(self) -> Dict[str, Dict]:
        """Carga plantillas de smart contracts para misiones transfronterizas."""
        return {
            "cross_border_mission": {
                "description": "Contrato para misiones entre operadores de diferentes países",
                "parameters": [
                    {"name": "origin_operator", "type": "string"},
                    {"name": "destination_operator", "type": "string"},
                    {"name": "mission_purpose", "type": "string"},
                    {"name": "payment_amount", "type": "uint256"},
                    {"name": "payment_currency", "type": "string", "default": "EUR"},
                    {"name": "mission_deadline", "type": "uint256"},
                ],
                "functions": [
                    {"name": "initiateMission", "inputs": ["string", "string", "string", "uint256", "string[]"]},
                    {"name": "confirmMission", "inputs": []},
                    {"name": "completeMission", "inputs": ["string"]},
                    {"name": "cancelMission", "inputs": ["string"]},
                ],
            },
            "payment_escrow": {
                "description": "Contrato de depósito en garantía para pagos",
                "parameters": [
                    {"name": "amount", "type": "uint256"},
                    {"name": "currency", "type": "string", "default": "EUR"},
                    {"name": "beneficiary", "type": "address"},
                    {"name": "expiration_date", "type": "uint256"},
                ],
                "functions": [
                    {"name": "depositFunds", "inputs": []},
                    {"name": "releaseFunds", "inputs": ["string"]},
                    {"name": "refundFunds", "inputs": ["string"]},
                ],
            },
        }

    def _operator_can_handle_payload(self, operator: EuropeanDroneOperator, payload: Dict[str, Any]) -> bool:
        """Verifica si un operador puede manejar una carga útil específica."""
        required_drone_type = payload.get("required_drone_type")
        if required_drone_type and required_drone_type not in operator.drone_types:
            return False
        required_certs = payload.get("required_certifications", [])
        missing = [c for c in required_certs if c not in operator.certifications]
        if missing:
            return False
        return True

    def _generate_waypoints(self, start: Dict[str, float], end: Dict[str, float]) -> List[Dict[str, float]]:
        """Genera waypoints intermedios para una ruta (simplificado)."""
        lat_diff = end["lat"] - start["lat"]
        lon_diff = end["lon"] - start["lon"]
        return [
            {"lat": start["lat"] + lat_diff * 0.33, "lon": start["lon"] + lon_diff * 0.33},
            {"lat": start["lat"] + lat_diff * 0.66, "lon": start["lon"] + lon_diff * 0.66},
        ]

    def _calculate_path_distance(self, path: List[Dict[str, float]]) -> float:
        """Calcula la distancia total de una ruta en metros."""
        return self.drone_network._calculate_path_distance(path)

    def _create_mission_smart_contract(
        self,
        mission_id: str,
        origin_operator: str,
        destination_operator: str,
        purpose: str,
        payload: Dict[str, Any],
        compliance_requirements: List[str],
    ) -> str:
        """Crea un smart contract en GaiaChain para la misión (simulado)."""
        contract_address = "0x" + hashlib.sha256(
            f"{mission_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:40]
        self.gaiachain.log_smart_contract({
            "contract_address": contract_address,
            "mission_id": mission_id,
            "type": "cross_border_mission",
            "parties": [origin_operator, destination_operator],
            "purpose": purpose,
            "payload": payload,
            "compliance_requirements": compliance_requirements,
            "status": "deployed",
            "timestamp": datetime.now().isoformat(),
        })
        return contract_address

    def propose_mission(
        self,
        origin_operator_id: str,
        destination_country: str,
        purpose: str,
        payload: Dict[str, Any],
        start_location: Dict[str, float],
        end_location: Dict[str, float],
    ) -> Dict[str, Any]:
        """Propone una misión transfronteriza a operadores en otro país."""
        origin_operator = self.drone_network.operators.get(origin_operator_id)
        if not origin_operator:
            return {"status": "error", "message": f"Operador {origin_operator_id} no encontrado"}

        destination_operators = [
            op for op in self.drone_network.operators.values()
            if op.country == destination_country and self._operator_can_handle_payload(op, payload)
        ]
        if not destination_operators:
            return {
                "status": "error",
                "message": f"No se encontraron operadores en {destination_country} con capacidades para {purpose}",
            }

        destination_operator = max(destination_operators, key=lambda op: op.fleet_size)
        waypoints = self._generate_waypoints(start_location, end_location)
        path = [start_location] + waypoints + [end_location]
        airspace_ok, violations = self.drone_network._check_airspace_restrictions(destination_country, path)
        if not airspace_ok:
            return {"status": "error", "message": "Ruta violaría restricciones de espacio aéreo", "violations": violations}

        origin_compliance = self.drone_network._get_required_compliance(origin_operator.country, purpose)
        dest_compliance = self.drone_network._get_required_compliance(destination_country, purpose)

        mission_id = f"XBORDER-{origin_operator.country}-{destination_country}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        proposed_mission = CrossBorderMission(
            mission_id=mission_id,
            origin_operator=origin_operator_id,
            origin_country=origin_operator.country,
            destination_operator=destination_operator.operator_id,
            destination_country=destination_country,
            purpose=purpose,
            payload=payload,
            start_location=start_location,
            end_location=end_location,
            waypoints=waypoints,
            start_time=(datetime.now() + timedelta(hours=2)).isoformat(),
            end_time=(datetime.now() + timedelta(hours=6)).isoformat(),
            status="proposed",
            regulations_compliance={
                origin_operator.country: origin_compliance,
                destination_country: dest_compliance,
            },
        )

        tx_id = self.gaiachain.log_cross_border_proposal({
            "mission_id": mission_id,
            "origin_operator": origin_operator_id,
            "destination_operator": destination_operator.operator_id,
            "purpose": purpose,
            "payload": payload,
            "route": path,
            "regulations_compliance": proposed_mission.regulations_compliance,
            "status": "proposed",
            "timestamp": datetime.now().isoformat(),
        })
        proposed_mission.gaiachain_tx = tx_id
        contract_address = self._create_mission_smart_contract(
            mission_id, origin_operator_id, destination_operator.operator_id,
            purpose, payload, list(set(origin_compliance + dest_compliance)),
        )
        proposed_mission.smart_contract = contract_address
        self.active_missions[mission_id] = proposed_mission

        return {
            "status": "success",
            "mission_id": mission_id,
            "origin_operator": origin_operator.name,
            "destination_operator": destination_operator.name,
            "destination_country": destination_country,
            "purpose": purpose,
            "gaiachain_tx": tx_id,
            "smart_contract": contract_address,
            "route_summary": {
                "start": start_location,
                "end": end_location,
                "waypoints": len(waypoints),
                "distance_km": self._calculate_path_distance(path) / 1000,
            },
            "compliance": proposed_mission.regulations_compliance,
            "next_steps": [
                f"Esperar respuesta de {destination_operator.name} (plazo: 24h)",
                f"Monitorear estado en GaiaChain: {tx_id}",
                "Firmar smart contract una vez aceptada",
            ],
            "destination_operator_contact": destination_operator.contact,
            "simulated_response": {"status": "pending", "operator_response": "Propuesta recibida, en revisión"},
        }

    def _update_mission_contract(
        self,
        contract_address: str,
        mission_id: str,
        status: str,
        terms: Dict[str, Any],
    ) -> bool:
        """Actualiza un smart contract de misión (simulado)."""
        self.gaiachain.log_smart_contract_update({
            "contract_address": contract_address,
            "mission_id": mission_id,
            "status": status,
            "updates": terms,
            "timestamp": datetime.now().isoformat(),
        })
        return True

    def accept_mission(
        self,
        mission_id: str,
        destination_operator_id: str,
        terms: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Acepta una misión propuesta por un operador origen."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        if mission.destination_operator != destination_operator_id:
            return {"status": "error", "message": "Operador destino no coincide con la propuesta"}
        if mission.status != "proposed":
            return {"status": "error", "message": f"Misión ya está en estado {mission.status}"}

        mission.status = "accepted"
        mission.start_time = terms.get("start_time", mission.start_time)
        mission.end_time = terms.get("end_time", mission.end_time)
        mission.payload.update(terms.get("additional_payload", {}))

        self._update_mission_contract(
            contract_address=mission.smart_contract or "",
            mission_id=mission_id,
            status="accepted",
            terms=terms,
        )
        tx_id = self.gaiachain.log_cross_border_acceptance({
            "mission_id": mission_id,
            "destination_operator": destination_operator_id,
            "status": "accepted",
            "terms": terms,
            "timestamp": datetime.now().isoformat(),
            "smart_contract": mission.smart_contract,
        })
        return {
            "status": "success",
            "mission_id": mission_id,
            "new_status": "accepted",
            "gaiachain_tx": tx_id,
            "smart_contract": mission.smart_contract,
            "next_steps": [
                "Coordinar detalles operativos con el operador origen",
                "Preparar drones y equipos para la misión",
                f"Iniciar misión antes de {mission.start_time}",
            ],
        }

    def start_mission(self, mission_id: str, operator_id: str) -> Dict[str, Any]:
        """Inicia una misión transfronteriza aceptada."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        if mission.status != "accepted":
            return {"status": "error", "message": f"Misión no está aceptada (estado: {mission.status})"}
        if operator_id not in (mission.origin_operator, mission.destination_operator):
            return {"status": "error", "message": "Operador no autorizado para iniciar esta misión"}

        mission.status = "in_progress"
        mission.actual_start_time = datetime.now().isoformat()
        self._update_mission_contract(
            contract_address=mission.smart_contract or "",
            mission_id=mission_id,
            status="in_progress",
            terms={"actual_start_time": mission.actual_start_time},
        )
        tx_id = self.gaiachain.log_cross_border_start({
            "mission_id": mission_id,
            "operator": operator_id,
            "status": "in_progress",
            "start_time": mission.actual_start_time,
            "timestamp": datetime.now().isoformat(),
            "smart_contract": mission.smart_contract,
        })

        drone_id = mission.payload.get("drone_id", "DRONE-001")
        if operator_id == mission.origin_operator:
            res = self.drone_network.plan_mission(
                operator_id=operator_id,
                drone_id=drone_id,
                start_location=mission.start_location,
                waypoints=mission.waypoints,
                purpose=f"Cross-border mission to {mission.destination_country}: {mission.purpose}",
                payload=mission.payload,
            )
            if res.get("status") == "success" and "mission" in res:
                mission.origin_local_mission_id = res["mission"].get("mission_id")
        else:
            start_loc = mission.waypoints[-1] if mission.waypoints else mission.start_location
            res = self.drone_network.plan_mission(
                operator_id=operator_id,
                drone_id=drone_id,
                start_location=start_loc,
                waypoints=[mission.end_location],
                purpose=f"Cross-border mission from {mission.origin_country}: {mission.purpose}",
                payload=mission.payload,
            )
            if res.get("status") == "success" and "mission" in res:
                mission.destination_local_mission_id = res["mission"].get("mission_id")

        local_mission_id = mission.origin_local_mission_id if operator_id == mission.origin_operator else mission.destination_local_mission_id
        return {
            "status": "success",
            "mission_id": mission_id,
            "new_status": "in_progress",
            "gaiachain_tx": tx_id,
            "local_mission_id": local_mission_id,
            "next_steps": [
                "Monitorear progreso de la misión en tiempo real",
                "Reportar cualquier incidencia al SOC",
                f"Completar misión antes de {mission.end_time}",
            ],
        }

    def _verify_route_compliance(self, mission: CrossBorderMission, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica si la ruta seguida cumple con la planificada."""
        planned_route = [mission.start_location] + mission.waypoints + [mission.end_location]
        actual_route = telemetry_data.get("route", [])
        issues: List[str] = []
        if not actual_route:
            return {"compliant": False, "issues": ["No se proporcionó datos de ruta"], "planned_route": planned_route, "actual_route": []}
        for i, waypoint in enumerate(planned_route):
            if i >= len(actual_route):
                issues.append(f"Ruta incompleta: faltan waypoints a partir del {i}")
                break
            distance = self.drone_network._haversine(
                waypoint["lat"], waypoint["lon"],
                actual_route[i]["lat"], actual_route[i]["lon"],
            )
            if distance > 500:
                issues.append(f"Desvío en waypoint {i}: {distance:.1f}m (límite: 500m)")
        max_allowed = {"Spain": 120, "Portugal": 120, "France": 150, "Italy": 120}.get(mission.origin_country, 120)
        if telemetry_data.get("max_altitude", 0) > max_allowed:
            issues.append(f"Altitud máxima excedida: {telemetry_data['max_altitude']}m (límite: {max_allowed}m)")
        return {"compliant": len(issues) == 0, "issues": issues, "planned_route": planned_route, "actual_route": actual_route}

    def _release_contract_funds(self, contract_address: str) -> bool:
        """Libera los fondos del smart contract al completar la misión (simulado)."""
        self.gaiachain.log_smart_contract_action({
            "contract_address": contract_address,
            "action": "release_funds",
            "status": "success",
            "timestamp": datetime.now().isoformat(),
        })
        return True

    def complete_mission(
        self,
        mission_id: str,
        operator_id: str,
        telemetry_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Completa una misión transfronteriza en progreso."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        if mission.status != "in_progress":
            return {"status": "error", "message": f"Misión no está en progreso (estado: {mission.status})"}
        if operator_id not in (mission.origin_operator, mission.destination_operator):
            return {"status": "error", "message": "Operador no autorizado para completar esta misión"}

        mission.status = "completed"
        mission.actual_end_time = datetime.now().isoformat()
        mission.telemetry_data = telemetry_data
        route_compliance = self._verify_route_compliance(mission, telemetry_data)
        if not route_compliance["compliant"]:
            mission.status = "completed_with_issues"
            mission.issues = route_compliance.get("issues", [])

        self._update_mission_contract(
            contract_address=mission.smart_contract or "",
            mission_id=mission_id,
            status=mission.status,
            terms={
                "status": mission.status,
                "actual_end_time": mission.actual_end_time,
                "telemetry_data": telemetry_data,
                "compliance_issues": mission.issues,
            },
        )
        tx_id = self.gaiachain.log_cross_border_completion({
            "mission_id": mission_id,
            "operator": operator_id,
            "status": mission.status,
            "end_time": mission.actual_end_time,
            "telemetry": telemetry_data,
            "compliance": route_compliance,
            "timestamp": datetime.now().isoformat(),
            "smart_contract": mission.smart_contract,
        })
        if mission.smart_contract:
            self._release_contract_funds(mission.smart_contract)

        duration_sec = 0.0
        if mission.actual_start_time and mission.actual_end_time:
            duration_sec = (datetime.fromisoformat(mission.actual_end_time) - datetime.fromisoformat(mission.actual_start_time)).total_seconds()
        return {
            "status": "success",
            "mission_id": mission_id,
            "new_status": mission.status,
            "gaiachain_tx": tx_id,
            "telemetry_summary": {
                "distance_km": telemetry_data.get("total_distance", 0) / 1000,
                "duration_min": duration_sec / 60,
                "max_altitude": telemetry_data.get("max_altitude", 0),
                "compliance": route_compliance,
            },
            "next_steps": [
                "Generar informe final de la misión",
                "Archivar datos en GaiaChain para trazabilidad",
                "Evaluar desempeño para futuras misiones",
            ],
        }

    def get_mission_status(self, mission_id: str) -> Dict[str, Any]:
        """Obtiene el estado completo de una misión transfronteriza."""
        mission = self.active_missions.get(mission_id)
        if not mission:
            return {"status": "error", "message": f"Misión {mission_id} no encontrada"}
        gaiachain_data = self.gaiachain.get_cross_border_mission(mission_id)
        origin_local_status = None
        if mission.origin_local_mission_id:
            origin_local_status = self.drone_network.get_mission_status(mission.origin_local_mission_id)
        destination_local_status = None
        if mission.destination_local_mission_id:
            destination_local_status = self.drone_network.get_mission_status(mission.destination_local_mission_id)

        duration_min = None
        if mission.actual_start_time and mission.actual_end_time:
            duration_min = (datetime.fromisoformat(mission.actual_end_time) - datetime.fromisoformat(mission.actual_start_time)).total_seconds() / 60

        mission_dict: Dict[str, Any] = {
            "mission_id": mission.mission_id,
            "origin_operator": mission.origin_operator,
            "destination_operator": mission.destination_operator,
            "purpose": mission.purpose,
            "status": mission.status,
            "start_time": mission.start_time,
            "end_time": mission.end_time,
            "actual_start_time": mission.actual_start_time,
            "actual_end_time": mission.actual_end_time,
            "duration_min": duration_min,
        }
        contract_data = self.gaiachain.get_smart_contract(mission.smart_contract or "")
        return {
            "status": "success",
            "mission": mission_dict,
            "gaiachain_data": gaiachain_data,
            "smart_contract": contract_data or {"contract_address": mission.smart_contract, "status": mission.status},
            "origin_local_mission": origin_local_status,
            "destination_local_mission": destination_local_status,
            "compliance_status": self._verify_route_compliance(mission, mission.telemetry_data or {}) if mission.status == "completed" or mission.status == "completed_with_issues" else None,
        }

    def get_operator_missions(self, operator_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene todas las misiones de un operador (origen o destino)."""
        missions = [
            m for m in self.active_missions.values()
            if (m.origin_operator == operator_id or m.destination_operator == operator_id)
            and (status_filter is None or m.status == status_filter)
        ]
        result = []
        for m in missions:
            op_origin = self.drone_network.operators.get(m.origin_operator)
            op_dest = self.drone_network.operators.get(m.destination_operator)
            result.append({
                "mission_id": m.mission_id,
                "origin_operator": m.origin_operator,
                "destination_operator": m.destination_operator,
                "purpose": m.purpose,
                "status": m.status,
                "role": "origin" if m.origin_operator == operator_id else "destination",
                "counterpart": (op_dest.name if op_dest else "Unknown") if m.origin_operator == operator_id else (op_origin.name if op_origin else "Unknown"),
            })
        return result

    def get_network_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la red de misiones transfronterizas."""
        by_status: Dict[str, int] = defaultdict(int)
        for m in self.active_missions.values():
            by_status[m.status] += 1
        by_pair: Dict[str, int] = defaultdict(int)
        for m in self.active_missions.values():
            by_pair[f"{m.origin_country}->{m.destination_country}"] += 1
        total_distance = sum(
            self._calculate_path_distance([m.start_location] + m.waypoints + [m.end_location]) / 1000
            for m in self.active_missions.values()
        )
        all_operators = set()
        for m in self.active_missions.values():
            all_operators.add(m.origin_operator)
            all_operators.add(m.destination_operator)
        completed = len([m for m in self.active_missions.values() if m.status == "completed"])
        return {
            "total_missions": len(self.active_missions),
            "missions_by_status": dict(by_status),
            "missions_by_country_pair": dict(by_pair),
            "total_distance_km": round(total_distance, 2),
            "total_operators_involved": len(all_operators),
            "success_rate": (completed / len(self.active_missions) * 100) if self.active_missions else 0.0,
        }


if __name__ == "__main__":
    from blockchain.gaia_chain import GaiaChainClient
    drone_network = EuropeanDroneNetwork(gaiachain_client=GaiaChainClient())
    coordinator = EuropeanDroneCoordinator(drone_network, GaiaChainClient())
    proposal = coordinator.propose_mission(
        origin_operator_id="ES-CASTUO-001",
        destination_country="Portugal",
        purpose="Fumigación de viñedos con bioestimulantes",
        payload={"required_drone_type": "PrecisionSprayer X1", "payload_capacity_kg": 10, "required_certifications": ["ISO 9001"]},
        start_location={"lat": 39.4769, "lon": -6.3706},
        end_location={"lat": 37.0222, "lon": -7.9289},
    )
    print("Propuesta:", proposal.get("status"), proposal.get("mission_id"))
    if proposal.get("status") == "success":
        mid = proposal["mission_id"]
        dest_id = coordinator.active_missions[mid].destination_operator
        acc = coordinator.accept_mission(mid, dest_id, {"start_time": (datetime.now() + timedelta(hours=3)).isoformat(), "end_time": (datetime.now() + timedelta(hours=7)).isoformat()})
        print("Aceptación:", acc.get("new_status"))
        dest_op = coordinator.active_missions[proposal["mission_id"]].destination_operator
        start_res = coordinator.start_mission(proposal["mission_id"], "ES-CASTUO-001")
        print("Inicio:", start_res.get("new_status"))
        comp = coordinator.complete_mission(proposal["mission_id"], dest_op, {"route": [{"lat": 39.47, "lon": -6.37}, {"lat": 37.02, "lon": -7.92}], "total_distance": 425000, "max_altitude": 110})
        print("Completado:", comp.get("new_status"), "compliance:", comp["telemetry_summary"]["compliance"].get("compliant"))
