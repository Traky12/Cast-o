# -*- coding: utf-8 -*-
"""
Prueba del flujo completo de misión transfronteriza: propuesta, aceptación, inicio y completado.
Ejecutar desde la raíz: python scripts/test_cross_border_mission.py
"""
from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta
from messaging.european_drone_coordinator import EuropeanDroneCoordinator
from messaging.european_drone_network import EuropeanDroneNetwork
from blockchain.gaia_chain import GaiaChainClient


def test_cross_border_mission():
    drone_network = EuropeanDroneNetwork(gaiachain_client=GaiaChainClient())
    coordinator = EuropeanDroneCoordinator(drone_network, GaiaChainClient())

    # 1. Proponer misión España -> Portugal
    print("Proponiendo mision Espana -> Portugal...")
    proposal = coordinator.propose_mission(
        origin_operator_id="ES-CASTUO-001",
        destination_country="Portugal",
        purpose="Fumigacion de vinedos con bioestimulantes (certificacion ecologica)",
        payload={
            "required_drone_type": "PrecisionSprayer X1",
            "payload_capacity_kg": 10,
            "required_certifications": ["ISO 9001", "EcoCert"],
            "bioestimulant_type": "Aminoacidos + Algas",
            "area_ha": 50,
        },
        start_location={"lat": 39.4769, "lon": -6.3706},
        end_location={"lat": 37.0222, "lon": -7.9289},
    )
    print("  ID:", proposal["mission_id"])
    print("  Operador destino:", proposal["destination_operator"])
    print("  Smart Contract:", proposal["smart_contract"])

    mission_id = proposal["mission_id"]

    # 2. Aceptar (operador portugues)
    print("\nAceptando mision (operador portugues)...")
    acceptance = coordinator.accept_mission(
        mission_id=mission_id,
        destination_operator_id="PT-ALG-001",
        terms={
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat(),
            "end_time": (datetime.now() + timedelta(hours=5)).isoformat(),
            "price_eur": 1200,
            "additional_payload": {"drone_id": "PT-SPRAYER-003", "pilot": "Antonio Silva"},
        },
    )
    print("  Estado:", acceptance["new_status"], "| GaiaChain TX:", acceptance["gaiachain_tx"])

    # 3. Iniciar (operador espanol)
    print("\nIniciando mision (operador espanol)...")
    start_result = coordinator.start_mission(mission_id=mission_id, operator_id="ES-CASTUO-001")
    print("  Estado:", start_result["new_status"], "| Mision local:", start_result.get("local_mission_id"))

    # 4. Telemetria y completar (operador portugues)
    telemetry_data = {
        "route": [
            {"lat": 39.4769, "lon": -6.3706},
            {"lat": 38.5, "lon": -7.0},
            {"lat": 37.8, "lon": -7.5},
            {"lat": 37.0222, "lon": -7.9289},
        ],
        "total_distance": 425000,
        "max_altitude": 110,
        "avg_speed": 15,
        "payload_deployed": True,
        "weather_conditions": {"temperature": 22, "humidity": 65, "wind_speed": 12},
    }
    print("\nCompletando mision (operador portugues)...")
    completion = coordinator.complete_mission(
        mission_id=mission_id,
        operator_id="PT-ALG-001",
        telemetry_data=telemetry_data,
    )
    print("  Estado:", completion["new_status"])
    print("  Duracion (min):", completion["telemetry_summary"]["duration_min"])
    print("  Cumplimiento ruta:", completion["telemetry_summary"]["compliance"]["compliant"])
    print("  GaiaChain TX:", completion["gaiachain_tx"])

    # 5. Estado final
    print("\nEstado final de la mision:")
    status = coordinator.get_mission_status(mission_id)
    print("  ID:", status["mission"]["mission_id"])
    print("  Estado:", status["mission"]["status"])
    print("  Duracion:", status["mission"].get("duration_min"))
    print("  Cumplimiento:", status.get("compliance_status", {}).get("compliant"))

    # 6. Estadísticas
    stats = coordinator.get_network_stats()
    print("\nEstadisticas red:")
    print("  Misiones totales:", stats["total_missions"])
    print("  Tasa de exito:", stats["success_rate"], "%")
    print("  Operadores involucrados:", stats["total_operators_involved"])

    print("\nOK: Flujo transfronterizo completado.")


if __name__ == "__main__":
    test_cross_border_mission()
