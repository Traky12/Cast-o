"""Adapter: unifica payload legacy (sensores) y federated (sensors_data, solar_exposure)."""
from __future__ import annotations

from typing import Any

from .exceptions import AgrivoltaicPayloadError
from .models import SensorNormalized


def _float_key(d: dict[str, Any], *keys: str, default: float | None = None) -> float | None:
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except (TypeError, ValueError) as e:
                raise AgrivoltaicPayloadError(f"Valor no numérico en '{k}'", field=k) from e
    return default


def normalize_agrivoltaic_payload(
    raw: dict[str, Any],
    *,
    require_solar: bool = False,
    default_solar: float = 2450.0,
) -> SensorNormalized:
    """Fusiona claves españolas/inglesas y niveles anidados en un único SensorNormalized."""
    sensores: dict[str, Any] = {}
    if isinstance(raw.get("sensores"), dict):
        sensores.update(raw["sensores"])
    if isinstance(raw.get("sensors_data"), dict):
        sensores.update(raw["sensors_data"])

    solar_top = _float_key(raw, "solar_exposure", "solar", "ghi_kwh_m2")
    solar_sens = _float_key(
        sensores,
        "solar",
        "solar_exposure",
        "ghi_kwh_m2",
        "radiacion_solar",
    )
    solar = solar_top if solar_top is not None else solar_sens
    if solar is None:
        if require_solar:
            raise AgrivoltaicPayloadError(
                "solar_exposure o sensores.solar requerido para certificación federada",
                field="solar_exposure",
            )
        solar = default_solar
    if solar < 0:
        raise AgrivoltaicPayloadError("Radiación solar no puede ser negativa", field="solar_exposure")

    hum = _float_key(sensores, "humedad", "humidity", "rh", "relative_humidity", default=42.0)
    tmp = _float_key(sensores, "temperatura", "temperature", "temp", "t_c", default=18.5)
    assert hum is not None and tmp is not None

    wind = _float_key(sensores, "viento_m_s", "wind_speed", "wind_m_s")
    irr = _float_key(sensores, "irradiancia_wm2", "irradiance_wm2", "irradiance")
    soil = _float_key(sensores, "humedad_suelo", "soil_moisture", "soil_moisture_pct")
    tilt = _float_key(sensores, "inclinacion_deg", "panel_tilt_deg", "tilt_deg")
    albedo = _float_key(sensores, "albedo")

    if isinstance(raw.get("sensors_data"), list):
        lst = raw["sensors_data"]
        if not isinstance(lst, list):
            raise AgrivoltaicPayloadError("sensors_data lista inválida", field="sensors_data")
        try:
            if len(lst) >= 3:
                solar = float(lst[0]) if solar_top is None and solar_sens is None else solar
                hum = float(lst[1])
                tmp = float(lst[2])
            elif len(lst) == 2:
                hum, tmp = float(lst[0]), float(lst[1])
            elif len(lst) == 1 and solar_top is None and solar_sens is None:
                solar = float(lst[0])
        except (TypeError, ValueError, IndexError) as e:
            raise AgrivoltaicPayloadError(
                "sensors_data como lista: use [GHI,humedad,temp] o [humedad,temp] con solar_exposure",
                field="sensors_data",
            ) from e

    if hum < 0 or hum > 100:
        raise AgrivoltaicPayloadError("humedad fuera de rango 0-100", field="humedad")
    if tmp < -50 or tmp > 60:
        raise AgrivoltaicPayloadError("temperatura fuera de rango operativo", field="temperatura")

    gt = _float_key(raw, "ground_temperature_10m") or _float_key(
        sensores, "ground_temperature_10m", "temperatura_suelo_10m", "ground_temp_10m", "t_suelo_10m"
    )
    dt_fluid = _float_key(raw, "delta_t_fluid") or _float_key(
        sensores, "delta_t_fluid", "delta_t_primario", "dt_fluid"
    )
    hp_raw = raw.get("heat_pump_status") or sensores.get("heat_pump_status")
    heat_pump = str(hp_raw).strip() if hp_raw is not None else None
    if heat_pump == "":
        heat_pump = None
    water_in = _float_key(
        sensores,
        "temperatura_agua_entrada",
        "water_inlet_temp_c",
        "water_inlet_temp",
        "t_agua_entrada_ro",
    )

    return SensorNormalized(
        solar_ghi_kwh_m2=solar,
        humidity_pct=hum,
        temp_celsius=tmp,
        wind_speed_m_s=wind,
        irradiance_wm2=irr,
        soil_moisture_pct=soil,
        panel_tilt_deg=tilt,
        albedo=albedo,
        ground_temperature_10m=gt,
        heat_pump_status=heat_pump,
        delta_t_fluid=dt_fluid,
        water_inlet_temp_c=water_in,
    )


_SYNERGY_KEYS = frozenset(
    {
        "cop_geothermal",
        "thermal_exchange_w_m2",
        "solar_surplus_kw_est",
        "prioritize_geothermal_exchanger",
        "lue_land_use_efficiency",
        "osmosis_inlet_advisory",
    }
)


def legacy_dict_for_response(finca_id: str, normalized: SensorNormalized, demo: dict[str, Any]) -> dict[str, Any]:
    """Dict histórico storefront + capa sinergia (COP, excedente solar, ósmosis) si aplica."""
    base: dict[str, Any] = {
        "status": "success",
        "finca_id": finca_id,
        "message": "Análisis en vivo",
        "kwh_ha": demo["kwh_ha"],
        "kwh_ha_label": f"{demo['kwh_ha']}kWh/ha",
        "paneles_temp": normalized.temp_celsius,
        "eur_ha_extra": demo["eur_ha_extra"],
        "eur_ha_label": f"+€{demo['eur_ha_extra']}/ha",
        "predicted_yield_pct": demo["predicted_yield_pct"],
        "water_savings_pct": demo["water_savings_pct"],
    }
    for k in _SYNERGY_KEYS:
        if k in demo:
            base[k] = demo[k]
    return base
