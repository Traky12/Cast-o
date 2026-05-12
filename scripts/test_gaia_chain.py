# -*- coding: utf-8 -*-
"""
Script de prueba para GaiaChain (cliente stub).
Valida log_cross_border_proposal, get_cross_border_mission, log_smart_contract,
get_smart_contract, log_cross_border_acceptance y métodos IoT.
Ejecutar desde la raíz del proyecto: python scripts/test_gaia_chain.py
"""
from __future__ import print_function

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime
import json

from blockchain.gaia_chain import GaiaChainClient


def test_gaia_chain():
    gaia = GaiaChainClient()

    # 1. log_cross_border_proposal
    print("Probando log_cross_border_proposal...")
    proposal_tx = gaia.log_cross_border_proposal({
        "mission_id": "TEST-MISSION-001",
        "origin_operator": "ES-CASTUO-001",
        "destination_operator": "PT-ALG-001",
        "purpose": "Prueba de fumigacion",
        "payload": {"drone_type": "PrecisionSprayer X1", "capacity_kg": 5},
        "route": [
            {"lat": 39.4769, "lon": -6.3706},
            {"lat": 38.5, "lon": -7.0},
            {"lat": 37.0222, "lon": -7.9289},
        ],
        "regulations_compliance": {
            "Spain": ["ISO 9001", "RD 903/2025"],
            "Portugal": ["EcoCert", "ISO 14001"],
        },
    })
    print("  Propuesta registrada:", proposal_tx)

    # 2. get_cross_border_mission
    print("\nProbando get_cross_border_mission...")
    mission = gaia.get_cross_border_mission("TEST-MISSION-001")
    print("  Mision recuperada:", json.dumps(mission, indent=2) if mission else "None")

    # 3. log_smart_contract
    print("\nProbando log_smart_contract...")
    contract_tx = gaia.log_smart_contract({
        "contract_address": "0x123abc",
        "mission_id": "TEST-MISSION-001",
        "type": "cross_border_mission",
        "parties": ["ES-CASTUO-001", "PT-ALG-001"],
        "status": "deployed",
    })
    print("  Contrato registrado:", contract_tx)

    # 4. get_smart_contract
    print("\nProbando get_smart_contract...")
    contract = gaia.get_smart_contract("0x123abc")
    print("  Contrato recuperado:", json.dumps(contract, indent=2) if contract else "None")

    # 5. log_cross_border_acceptance
    print("\nProbando log_cross_border_acceptance...")
    acceptance_tx = gaia.log_cross_border_acceptance({
        "mission_id": "TEST-MISSION-001",
        "destination_operator": "PT-ALG-001",
        "status": "accepted",
        "terms": {"price_eur": 1200, "start_time": datetime.now().isoformat()},
    })
    print("  Aceptacion registrada:", acceptance_tx)

    # 6. log_iot_data / log_iot_auth
    print("\nProbando log_iot_data y log_iot_auth...")
    tx_iot = gaia.log_iot_data({
        "tray_id": "CASTUO-TRAY-001",
        "timestamp": datetime.now().isoformat(),
        "sensors": {"temperature": 22.5, "humidity": 65},
        "session_id": "test-session",
    })
    tx_auth = gaia.log_iot_auth({
        "tray_id": "CASTUO-TRAY-001",
        "session_id": "sess-123",
        "device_type": "raspberry_pi",
        "location": "Caceres",
    })
    print("  IoT data:", tx_iot, "| IoT auth:", tx_auth)

    print("\nOK: Todas las pruebas de GaiaChain pasaron.")


if __name__ == "__main__":
    test_gaia_chain()
