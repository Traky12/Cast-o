# Integración robótica / señales — laboratorio Castúo (no sustituye ROS2 en campo).

from backend.integrations.robotics.evolution_engine import EvolutionEngine, evolve_simple_genetic
from backend.integrations.robotics.neuromorphic_edge import (
    HydroponicsSNN,
    MemristorSynapse,
    hydro_infer_dict,
)
from backend.integrations.robotics.robot_traceability import build_robot_evolution_audit_payload
from backend.integrations.robotics.security_layer import RobotSecurityLayer
from backend.integrations.robotics.signal_manager import SignalManager, SignalSnapshot

__all__ = [
    "EvolutionEngine",
    "HydroponicsSNN",
    "MemristorSynapse",
    "SignalManager",
    "SignalSnapshot",
    "RobotSecurityLayer",
    "build_robot_evolution_audit_payload",
    "evolve_simple_genetic",
    "hydro_infer_dict",
]
