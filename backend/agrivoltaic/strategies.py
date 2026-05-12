"""Strategy: cálculo demo vs UNE 216701 (extensible para fórmulas CTAEX)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .geothermal_synergy import enrich_envelope_with_geothermal_solar
from .models import DemoMetricsModel, FederatedMetricsEnvelope, SensorNormalized, UNEMetricsModel


@runtime_checkable
class AgrivoltaicStrategy(Protocol):
    def compute(self, sensors: SensorNormalized) -> FederatedMetricsEnvelope: ...


class DemoAgrivoltaicStrategy:
    """Estrategia actual: métricas orientativas hasta validación normativa."""

    def compute(self, sensors: SensorNormalized) -> FederatedMetricsEnvelope:
        s = sensors.solar_ghi_kwh_m2
        h = sensors.humidity_pct
        t = sensors.temp_celsius
        kwh_ha = round(s * 0.00506, 1)
        eur_ha = float(round(12.4 * (t / 18.0) + (h / 10.0), 0))
        water_kg = max(0.0, 1000.0 - (s * 0.02) - (h * 2.0))
        base = FederatedMetricsEnvelope(
            kwh_ha=float(kwh_ha),
            eur_ha_extra=eur_ha,
            water_savings_kg_ha=round(water_kg, 2),
            source="stub",
            certifiable=False,
            land_use_efficiency=None,
            normative_ref=None,
        )
        return enrich_envelope_with_geothermal_solar(base, sensors)

    def demo_dict(self, sensors: SensorNormalized) -> dict[str, int | float | bool | dict]:
        env = self.compute(sensors)
        out: dict[str, int | float | bool | dict] = {
            "kwh_ha": env.kwh_ha,
            "eur_ha_extra": int(round(env.eur_ha_extra)),
            "water_savings_pct": 20,
            "predicted_yield_pct": 35,
        }
        if env.solar_surplus_kw_est is not None:
            out["solar_surplus_kw_est"] = env.solar_surplus_kw_est
        if env.cop_geothermal is not None:
            out["cop_geothermal"] = env.cop_geothermal
        if env.thermal_exchange_w_m2 is not None:
            out["thermal_exchange_w_m2"] = env.thermal_exchange_w_m2
        if env.prioritize_geothermal_exchanger is True:
            out["prioritize_geothermal_exchanger"] = True
        if env.lue_land_use_efficiency is not None:
            out["lue_land_use_efficiency"] = env.lue_land_use_efficiency
        if env.osmosis_inlet_advisory:
            out["osmosis_inlet_advisory"] = env.osmosis_inlet_advisory
        return out


class UNE216701AgrivoltaicStrategy:
    """Anclaje para fórmulas oficiales CTAEX: reemplazar el cuerpo de `compute` cuando el anexo esté cerrado.

    Parámetros de entrada ya normalizados (SensorNormalized) incluyen GHI, viento, suelo e inclinación
    para que las ecuaciones normativas no dependan del formato del cliente.
    """

    def compute(self, sensors: SensorNormalized) -> FederatedMetricsEnvelope:
        _ = (
            sensors.wind_speed_m_s,
            sensors.irradiance_wm2,
            sensors.soil_moisture_pct,
            sensors.panel_tilt_deg,
            sensors.albedo,
        )
        une = self._une216701_official(sensors)
        base = FederatedMetricsEnvelope(
            kwh_ha=une.kwh_ha,
            eur_ha_extra=une.eur_ha_extra,
            water_savings_kg_ha=une.water_savings_kg_ha,
            source="une216701",
            certifiable=True,
            land_use_efficiency=une.land_use_efficiency,
            normative_ref=une.normative_ref,
        )
        return enrich_envelope_with_geothermal_solar(base, sensors)

    def _une216701_official(self, sensors: SensorNormalized) -> UNEMetricsModel:
        """Placeholder explícito: aquí se integran las fórmulas del documento CTAEX."""
        s, h, t = sensors.solar_ghi_kwh_m2, sensors.humidity_pct, sensors.temp_celsius
        kwh_ha = round(s * 0.00506, 2)
        eur_ha = round(12.4 * (t / 18.0) + (h / 10.0), 2)
        water = max(0.0, round(1000 - (s * 0.02) - (h * 2), 2))
        ler = None
        if sensors.panel_tilt_deg is not None and sensors.albedo is not None:
            ler = round(1.0 + (sensors.panel_tilt_deg / 90.0) * 0.15 * (1.0 - sensors.albedo), 3)
        return UNEMetricsModel(
            kwh_ha=kwh_ha,
            eur_ha_extra=eur_ha,
            water_savings_kg_ha=water,
            land_use_efficiency=ler,
            co2_avoided_kg_ha=round(s * 0.0004, 3) if ler else None,
            normative_ref="UNE-216701-CTAEX-STUB-v0",
        )


def get_active_strategy(*, une_implemented: bool) -> DemoAgrivoltaicStrategy | UNE216701AgrivoltaicStrategy:
    if une_implemented:
        return UNE216701AgrivoltaicStrategy()
    return DemoAgrivoltaicStrategy()
