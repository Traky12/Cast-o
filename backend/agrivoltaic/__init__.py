"""Núcleo agrivoltaico Castúo: normalización, estrategias demo/UNE, salidas tipadas."""
from __future__ import annotations

from .exceptions import AgrivoltaicPayloadError
from .models import DemoMetricsModel, FederatedMetricsEnvelope, SensorNormalized, UNEMetricsModel
from .payload_adapter import normalize_agrivoltaic_payload
from .service import (
    build_storefront_analysis,
    compute_demo_metrics,
    compute_federated_envelope,
    envelope_to_audit_dict,
    une216701_enabled,
)
from .strategies import DemoAgrivoltaicStrategy, UNE216701AgrivoltaicStrategy, get_active_strategy

__all__ = [
    "AgrivoltaicPayloadError",
    "DemoAgrivoltaicStrategy",
    "DemoMetricsModel",
    "FederatedMetricsEnvelope",
    "SensorNormalized",
    "UNEMetricsModel",
    "UNE216701AgrivoltaicStrategy",
    "build_storefront_analysis",
    "compute_demo_metrics",
    "compute_federated_envelope",
    "envelope_to_audit_dict",
    "get_active_strategy",
    "normalize_agrivoltaic_payload",
    "une216701_enabled",
]
