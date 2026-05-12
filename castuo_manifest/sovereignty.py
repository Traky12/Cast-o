"""Marco soberanía EU: trazabilidad E2E, RED III, DR, adaptación regulatoria, expansión."""
from __future__ import annotations

from typing import Any

REQUIRED_EU_KEYS = frozenset(
    {
        "traceability_encryption_mandatory",
        "eu_sovereignty_seal",
        "trazabilidad",
        "resilencia",
        "crecimiento",
        "expansion",
    }
)


def eu_sovereignty_framework() -> dict[str, Any]:
    return {
        "traceability_encryption_mandatory": True,
        "data_residency": "EU-first",
        "eu_sovereignty_seal": "V1.0-SOVEREIGNTY",
        "frameworks_reference": [
            "GDPR",
            "NIS2",
            "eIDAS2",
            "EU AI Act",
            "RED III",
        ],
        "agents_code_of_conduct": [
            "Sabionda",
            "Mistral",
            "Cursor",
        ],
        "trazabilidad": {
            "description": (
                "Trazabilidad E2E: encriptación obligatoria en tránsito y en reposo; cadena de identidad digital."
            ),
            "red_iii_binding": (
                "Registro inmutable acoplado a RED III: la certificación energética verde exige trazabilidad auditable."
            ),
            "sorghum_harvest_rule": (
                "No se emite crédito de bioetanol si la trazabilidad del sorgo de origen no está firmada por "
                "[TERRA-ARMOR-05] (Nexus) en el momento de la siega."
            ),
            "features": [
                "Encriptación obligatoria en tránsito y en reposo",
                "Registro inmutable vinculado a RED III",
                "Auditoría continua y automática",
            ],
        },
        "resilencia": {
            "description": (
                "Continuidad operativa, redundancia y Disaster Recovery (DR) alineado con NIS2."
            ),
            "disaster_recovery_explicit": True,
            "provisional_master_node": (
                "Si el nodo central de la Escuela Rural 4.0 queda inoperativo, cualquier nodo [OMEGA-LINK] "
                "(Aetheris) con cómputo suficiente puede asumir el rol de Nodo Maestro Provisional "
                "para mantener la red de energía y gobernanza local."
            ),
            "features": [
                "Redundancia de sistemas críticos",
                "Protocolos explícitos de Disaster Recovery (DR)",
                "Capacidad de operación autónoma y fail-over OMEGA-LINK",
            ],
        },
        "crecimiento": {
            "description": (
                "Modularidad plug&play y capa de adaptación regulatoria sin parar la producción territorial."
            ),
            "regulatory_adaptation_layer": (
                "Si la UE publica nueva normativa sobre IA (p. ej. evolución EU AI Act), el sistema puede "
                "actualizar pesos éticos y políticas sin detener la producción de [BIO-HUB-DIGITAL]."
            ),
            "features": [
                "Escalabilidad modular plug&play",
                "Capa de adaptación regulatoria (IA y sectorial)",
                "Integración con nuevos sistemas sin downtime productivo crítico",
            ],
        },
        "expansion": {
            "description": (
                "Expansión trans-territorial del modelo manteniendo estándares de soberanía y trazabilidad."
            ),
            "trans_territorial_protocol": (
                "Exportación del modelo Extremeño a regiones homólogas (Alentejo, Andalucía, etc.) "
                "con misma integridad criptográfica y marco EU."
            ),
            "features": [
                "Expansión a nuevos territorios con estándares sellados",
                "Adopción de tecnologías y estándares sin debilitar PQC/trazabilidad",
                "Colaboración estratégica bajo gobernanza multisig CIPHER-LEVEL-5",
            ],
        },
    }


def assert_eu_sovereignty_block_complete(eu: dict[str, Any]) -> None:
    from .exceptions import SovereigntyViolationError

    missing = REQUIRED_EU_KEYS - set(eu.keys())
    if missing:
        raise SovereigntyViolationError(
            f"eu_sovereignty incompleto; faltan claves: {sorted(missing)}"
        )
    tr = eu.get("trazabilidad") or {}
    if "sorghum_harvest_rule" not in tr:
        raise SovereigntyViolationError(
            "trazabilidad.sorghum_harvest_rule obligatorio (RED III / TERRA-ARMOR-05)."
        )
    res = eu.get("resilencia") or {}
    if not res.get("disaster_recovery_explicit"):
        raise SovereigntyViolationError("resilencia.disaster_recovery_explicit debe ser True.")
    cre = eu.get("crecimiento") or {}
    if "regulatory_adaptation_layer" not in cre:
        raise SovereigntyViolationError("crecimiento.regulatory_adaptation_layer obligatorio.")
