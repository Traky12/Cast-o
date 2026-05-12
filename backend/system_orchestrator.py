"""
Núcleo de Gestión de Alta Precisión (AGRI-SENSE-CORE).

Bucle de control por retroalimentación negativa: no solo lee datos, predice desviaciones y actúa.
Comunicación asíncrona y atómica con geothermal_engine y capa de negocio (shopware).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from backend.agri_sense.constants import (
    CONFIDENCE_ACTION_THRESHOLD,
    CONFIDENCE_OZONE_FAULT_THRESHOLD,
    CONDUCTIVITY_OPTIMAL_RO_MS_CM_HIGH,
    CONDUCTIVITY_OPTIMAL_RO_MS_CM_LOW,
    FAIL_SAFE_NPK_VALVE_CLOSED_ON_OZONE_FAULT,
    GEOTHERMAL_SETPOINT_DEVIATION_C,
    OZONE_PH_SYNC_MAX_PH_FOR_INJECTION,
)
from backend.agri_sense.schemas import UltraPrecisionSchema, ValueWithPrecision
from backend.agri_sense.quantum_optimizer import optimize_bionergy_allocation
from backend.agri_sense.sensor_filters import NPKFilter
from backend.geothermal_engine import (
    calculate_thermal_exchange,
    estimate_heat_pump_cop,
    solar_surplus_kw_estimate,
)

_LOGGER = logging.getLogger("castuo.system_orchestrator")
_CONTROL_LOCK = asyncio.Lock()
_AUDIT_BUFFER: list[dict[str, Any]] = []
_AUDIT_MAX = 500
_GEOTHERMAL_SETPOINT_C = 18.0


@dataclass
class OrchestratorState:
    """Estado atómico leído por API/telemetría."""

    npk_valve_closed: bool = False
    heat_pump_flow_factor: float = 1.0
    ozone_injection_enabled: bool = False
    cop_geothermal: float | None = None
    last_ground_temp_c: float | None = None
    last_conductivity_ms_cm: float | None = None
    irrigation_demand_factor: float = 1.0
    last_cycle_ts: float = 0.0
    root_cause_last: str = ""
    last_irradiance_wm2: float | None = None
    quantum_confidence_score: float = 0.0
    energy_alloc_ro_kw: float = 0.0
    energy_alloc_geo_kw: float = 0.0
    energy_alloc_o3_kw: float = 0.0
    quantum_backend_last: str = ""


_state = OrchestratorState()
_npk_filter = NPKFilter(alpha=0.25)


def _audit(event: str, severity: str, root_cause: str, meta: dict[str, Any] | None = None) -> str:
    """Log de auditoría de alta resolución: evento + causa raíz."""
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "event": event,
        "severity": severity,
        "root_cause": root_cause,
        "timestamp": ts,
        "meta": meta or {},
    }
    h = hashlib.sha256(f"{ts}{event}{root_cause}".encode()).hexdigest()[:12]
    audit_id = f"AUD-{h}"
    payload["audit_id"] = audit_id
    _AUDIT_BUFFER.append(payload)
    if len(_AUDIT_BUFFER) > _AUDIT_MAX:
        _AUDIT_BUFFER.pop(0)
    _LOGGER.info("audit %s %s | %s", audit_id, event, root_cause)
    return audit_id


def _feedback_geothermal_osmosis(conductivity_ms_cm: float | None, ground_temp_c: float | None) -> None:
    """Ajustar flujo bomba de calor según CE para optimizar permeabilidad membranas RO."""
    if conductivity_ms_cm is None:
        return
    global _state
    if conductivity_ms_cm < CONDUCTIVITY_OPTIMAL_RO_MS_CM_LOW:
        _state.heat_pump_flow_factor = 1.15
        _audit(
            "heat_pump_flow_adjusted",
            "info",
            "CE por debajo de banda óptima RO; aumento de flujo para mejorar permeabilidad de membranas.",
            {"conductivity_ms_cm": conductivity_ms_cm, "factor": _state.heat_pump_flow_factor},
        )
    elif conductivity_ms_cm > CONDUCTIVITY_OPTIMAL_RO_MS_CM_HIGH:
        _state.heat_pump_flow_factor = 0.88
        _audit(
            "heat_pump_flow_adjusted",
            "info",
            "CE por encima de banda óptima RO; reducción de flujo para proteger membranas.",
            {"conductivity_ms_cm": conductivity_ms_cm, "factor": _state.heat_pump_flow_factor},
        )
    else:
        _state.heat_pump_flow_factor = 1.0

    if ground_temp_c is not None and _state.last_ground_temp_c is not None:
        dev = abs(ground_temp_c - _GEOTHERMAL_SETPOINT_C)
        if dev >= GEOTHERMAL_SETPOINT_DEVIATION_C:
            cop = estimate_heat_pump_cop(ground_temp_c)
            _state.cop_geothermal = cop
            _audit(
                "cop_recalculated",
                "info",
                f"T_suelo se desvió {dev:.2f}°C del setpoint; COP híbrido recalculado.",
                {"ground_temp_c": ground_temp_c, "setpoint_c": _GEOTHERMAL_SETPOINT_C, "cop": cop},
            )
    if ground_temp_c is not None:
        _state.last_ground_temp_c = ground_temp_c
    _state.last_conductivity_ms_cm = conductivity_ms_cm


def _feedback_ozone_ph(ph: ValueWithPrecision | None, ozone_ok: bool) -> None:
    """Sincronizar inyección O3 con pH para evitar oxidación de Nitrato/Potasio."""
    global _state
    if not ozone_ok and FAIL_SAFE_NPK_VALVE_CLOSED_ON_OZONE_FAULT:
        _state.npk_valve_closed = True
        _state.ozone_injection_enabled = False
        _audit(
            "fail_safe_npk_valve_closed",
            "critical",
            "Sensor de Ozono fallido o sin confianza; válvula NPK cerrada para evitar reacciones químicas no deseadas.",
            {},
        )
        return
    if ph is None or not ph.is_actionable(CONFIDENCE_ACTION_THRESHOLD):
        return
    if ph.value > OZONE_PH_SYNC_MAX_PH_FOR_INJECTION:
        _state.ozone_injection_enabled = False
        _state.root_cause_last = "pH por encima de umbral seguro para O3; inyección desactivada para proteger Nitrato/Potasio."
        _audit("ozone_injection_held", "warning", _state.root_cause_last, {"ph": ph.value})
    else:
        _state.ozone_injection_enabled = True
        _state.npk_valve_closed = False
        _state.root_cause_last = "pH en banda segura; O3 sincronizado con sensor."


def _feedback_solar_irrigation(
    irradiance_wm2: float | None,
    solar_ghi_kwh_m2: float,
    shadow_factor: float,
    evapotranspiration_mm: float | None,
) -> None:
    """Cruzar predicción sombras (UNE) con evapotranspiración: regar cuando la planta lo necesita."""
    surplus = solar_surplus_kw_estimate(irradiance_wm2, solar_ghi_kwh_m2)
    if evapotranspiration_mm is not None and evapotranspiration_mm > 0:
        demand = evapotranspiration_mm * (1.0 - 0.3 * (1.0 - shadow_factor))
        _state.irrigation_demand_factor = min(1.5, max(0.2, demand / max(0.1, evapotranspiration_mm)))
        _state.root_cause_last = (
            f"Riego ajustado por ET y sombra UNE; factor demanda {_state.irrigation_demand_factor:.2f}."
        )
    else:
        _state.irrigation_demand_factor = 1.0


async def _run_geothermal_async(depth_m: float, ground_temp: float, fluid_velocity: float) -> dict[str, Any]:
    """Llamada atómica al motor geotérmico (ejecutor para no bloquear el loop)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: calculate_thermal_exchange(depth_m, ground_temp, fluid_velocity),
    )


async def control_cycle(sensors: UltraPrecisionSchema) -> dict[str, Any]:
    """
    Un ciclo del bucle de retroalimentación negativa.
    Debe ser invocado bajo _CONTROL_LOCK para garantizar atomicidad con shopware/geothermal.
    """
    async with _CONTROL_LOCK:
        global _state
        t0 = time.monotonic()
        root_causes: list[str] = []

        conductivity = sensors.conductivity_ms_cm.value if sensors.conductivity_ms_cm else None
        ground_temp = sensors.ground_temp_10m_c.value if sensors.ground_temp_10m_c else None
        ph_val = sensors.ph
        ozone_ok = sensors.ozone_sensor_ok(CONFIDENCE_OZONE_FAULT_THRESHOLD)

        _feedback_geothermal_osmosis(conductivity, ground_temp)
        _feedback_ozone_ph(ph_val, ozone_ok)

        irrad = sensors.irradiance_wm2.value if sensors.irradiance_wm2 else None
        _feedback_solar_irrigation(irrad, 1500.0, 0.7, None)

        old_ir = _state.last_irradiance_wm2
        should_q = False
        if irrad is not None:
            if old_ir is None:
                should_q = True
            elif old_ir > 1e-6 and abs(float(irrad) - old_ir) / old_ir > 0.10:
                should_q = True
            _state.last_irradiance_wm2 = float(irrad)

        if should_q:
            ph_v = ph_val.value if ph_val else None
            loop = asyncio.get_event_loop()
            qres = await loop.run_in_executor(
                None,
                lambda: optimize_bionergy_allocation(
                    irradiance_wm2=irrad,
                    ph=ph_v,
                    conductivity_ms_cm=conductivity,
                    ground_temp_c=ground_temp,
                    ozone_injection_allowed=ozone_ok and (
                        ph_v is None or ph_v <= OZONE_PH_SYNC_MAX_PH_FOR_INJECTION
                    ),
                ),
            )
            _state.quantum_confidence_score = float(qres["quantum_confidence_score"])
            _state.energy_alloc_ro_kw = float(qres["x_ro_kw"])
            _state.energy_alloc_geo_kw = float(qres["x_geo_kw"])
            _state.energy_alloc_o3_kw = float(qres["x_o3_kw"])
            _state.quantum_backend_last = str(qres.get("quantum_backend", ""))
            _audit(
                "quantum_bio_grid_optimization",
                "info",
                qres.get("root_cause_summary", "QAOA/BioGrid"),
                {
                    "quantum_confidence_score": _state.quantum_confidence_score,
                    "backend": _state.quantum_backend_last,
                    "x_ro_kw": _state.energy_alloc_ro_kw,
                    "x_geo_kw": _state.energy_alloc_geo_kw,
                    "x_o3_kw": _state.energy_alloc_o3_kw,
                },
            )
            root_causes.append(
                f"Optimizador 5.PRO+: Quantum Confidence {_state.quantum_confidence_score:.1f}% "
                f"({_state.quantum_backend_last})."
            )

        if sensors.nitrate_ppm and sensors.potassium_ppm and _npk_filter.is_ready_for_actuation():
            n = _npk_filter.nitrate_filtered()
            k = _npk_filter.potassium_filtered()
            root_causes.append(f"N/K filtrados (EWMA): N={n} ppm, K={k} ppm.")
        elif sensors.nitrate_ppm and sensors.potassium_ppm:
            _npk_filter.update_nitrate(sensors.nitrate_ppm.value)
            _npk_filter.update_potassium(sensors.potassium_ppm.value)
            root_causes.append("Acumulando muestras N/K para filtro; sin actuación aún.")

        _state.last_cycle_ts = t0
        if root_causes:
            _state.root_cause_last = " ".join(root_causes)

        audit_id = _audit(
            "control_cycle",
            "info",
            _state.root_cause_last or "Ciclo de control ejecutado.",
            {
                "npk_valve_closed": _state.npk_valve_closed,
                "cop_geothermal": _state.cop_geothermal,
                "heat_pump_flow_factor": _state.heat_pump_flow_factor,
                "irrigation_demand_factor": _state.irrigation_demand_factor,
                "quantum_confidence_score": _state.quantum_confidence_score,
            },
        )
        return {
            "audit_id": audit_id,
            "state": {
                "npk_valve_closed": _state.npk_valve_closed,
                "heat_pump_flow_factor": _state.heat_pump_flow_factor,
                "ozone_injection_enabled": _state.ozone_injection_enabled,
                "cop_geothermal": _state.cop_geothermal,
                "irrigation_demand_factor": _state.irrigation_demand_factor,
                "quantum_confidence_score": _state.quantum_confidence_score,
                "energy_alloc_ro_kw": _state.energy_alloc_ro_kw,
                "energy_alloc_geo_kw": _state.energy_alloc_geo_kw,
                "energy_alloc_o3_kw": _state.energy_alloc_o3_kw,
                "quantum_backend_last": _state.quantum_backend_last,
            },
            "cycle_duration_s": round(time.monotonic() - t0, 4),
        }


def get_state() -> OrchestratorState:
    """Estado actual del orquestador (lectura atómica para API/dashboard)."""
    return _state


def get_audit_tail(n: int = 10) -> list[dict[str, Any]]:
    """Últimos n eventos de auditoría con audit_id y gravedad."""
    return list(_AUDIT_BUFFER[-n:]) if _AUDIT_BUFFER else []


def set_geothermal_setpoint_c(value: float) -> None:
    """Punto de consigna T suelo para recálculo de COP."""
    global _GEOTHERMAL_SETPOINT_C
    _GEOTHERMAL_SETPOINT_C = float(value)


def manual_intervention(action: str, **kwargs: Any) -> dict[str, Any]:
    """Intervención manual: forzar ciclo ozono o ajustar COP/setpoint."""
    global _state
    if action == "force_ozone_cycle":
        _state.ozone_injection_enabled = True
        _state.npk_valve_closed = False
        aid = _audit("manual_ozone_cycle", "warning", "Ciclo de limpieza Ozono forzado por operador.", kwargs)
        return {"audit_id": aid, "action": action}
    if action == "set_cop_geothermal" and "cop" in kwargs:
        _state.cop_geothermal = float(kwargs["cop"])
        aid = _audit("manual_cop_set", "info", "COP geotérmico ajustado manualmente.", kwargs)
        return {"audit_id": aid, "action": action}
    if action == "set_geothermal_setpoint" and "temp_c" in kwargs:
        set_geothermal_setpoint_c(kwargs["temp_c"])
        aid = _audit("manual_setpoint", "info", "Setpoint geotérmico modificado por operador.", kwargs)
        return {"audit_id": aid, "action": action}
    return {"error": "unknown_action", "action": action}
