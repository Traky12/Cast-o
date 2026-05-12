"""Fachada de servicio: estrategia activa + normalización."""
from __future__ import annotations

import os
from typing import Any

from .models import FederatedMetricsEnvelope, SensorNormalized
from .payload_adapter import legacy_dict_for_response, normalize_agrivoltaic_payload
from .strategies import DemoAgrivoltaicStrategy, get_active_strategy


def une216701_enabled() -> bool:
    return os.getenv("CASTUO_UNE216701_IMPLEMENTED", "").lower() in ("1", "true", "yes")


def compute_demo_metrics(solar: float, humidity: float, temp: float) -> dict[str, Any]:
    """Compatibilidad histórica con firmas (solar, humedad, temp)."""
    sn = SensorNormalized(
        solar_ghi_kwh_m2=solar,
        humidity_pct=humidity,
        temp_celsius=temp,
    )
    return DemoAgrivoltaicStrategy().demo_dict(sn)


def build_storefront_analysis(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_agrivoltaic_payload(raw, require_solar=False)
    demo = DemoAgrivoltaicStrategy().demo_dict(normalized)
    finca_id = str(raw.get("finca_id") or "CTAEX_001")
    return legacy_dict_for_response(finca_id, normalized, demo)


def compute_federated_envelope(
    raw: dict[str, Any],
    *,
    une_implemented: bool | None = None,
) -> tuple[SensorNormalized, FederatedMetricsEnvelope]:
    une = une216701_enabled() if une_implemented is None else une_implemented
    normalized = normalize_agrivoltaic_payload(raw, require_solar=False)
    strategy = get_active_strategy(une_implemented=une)
    return normalized, strategy.compute(normalized)


def envelope_to_audit_dict(env: FederatedMetricsEnvelope) -> dict[str, Any]:
    return env.model_dump()
