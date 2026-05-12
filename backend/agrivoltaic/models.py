"""Modelos Pydantic: entrada normalizada y salidas tipadas (demo / UNE 216701)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SensorNormalized(BaseModel):
    """Entrada única al núcleo de cálculo tras adaptar legacy y federated."""

    model_config = ConfigDict(frozen=True)

    solar_ghi_kwh_m2: float = Field(..., ge=0, description="GHI kWh/m²·año o periodo coherente con CTAEX")
    humidity_pct: float = Field(default=42.0, ge=0, le=100)
    temp_celsius: float = Field(default=18.5, ge=-50, le=60)
    wind_speed_m_s: float | None = Field(default=None, ge=0, description="Opcional UNE / sombreado dinámico")
    irradiance_wm2: float | None = Field(default=None, ge=0, description="Irradiancia instantánea W/m²")
    soil_moisture_pct: float | None = Field(default=None, ge=0, le=100, description="Humedad suelo %")
    panel_tilt_deg: float | None = Field(default=None, ge=0, le=90)
    albedo: float | None = Field(default=None, ge=0, le=1)
    ground_temperature_10m: float | None = Field(default=None, ge=-5, le=45, description="T suelo 10 m (geotermia)")
    heat_pump_status: str | None = Field(default=None, description="idle|heating|cooling|off")
    delta_t_fluid: float | None = Field(default=None, description="ΔT circuito primario/secundario K")
    water_inlet_temp_c: float | None = Field(default=None, description="T agua entrada RO/LSS")


class DemoMetricsModel(BaseModel):
    """Salida demo (no certificable)."""

    model_config = ConfigDict(frozen=True)

    kwh_ha: float
    eur_ha_extra: int
    water_savings_pct: int = 20
    predicted_yield_pct: int = 35


class UNEMetricsModel(BaseModel):
    """Contrato preparado para fórmulas oficiales CTAEX / UNE 216701.

    Los campos numéricos se rellenan cuando `une216701_strategy` esté activo;
    `normative_ref` identifica versión del anexo aplicado.
    """

    model_config = ConfigDict(frozen=True)

    kwh_ha: float = Field(..., description="Energía específica según norma")
    eur_ha_extra: float = Field(..., description="Rendimiento económico agrivoltaico")
    water_savings_kg_ha: float = Field(..., description="Ahorro hídrico estimado kg/ha")
    land_use_efficiency: float | None = Field(default=None, description="LER u otro índice normativo")
    co2_avoided_kg_ha: float | None = None
    normative_ref: str = Field(default="UNE-216701-CTAEX-PENDING")
    certifiable: Literal[True] = True
    source: Literal["une216701"] = "une216701"


class FederatedMetricsEnvelope(BaseModel):
    """Unión demo + UNE + sinergia geotérmica (COP, intercambiador, ósmosis)."""

    model_config = ConfigDict(frozen=True)

    kwh_ha: float
    eur_ha_extra: float
    water_savings_kg_ha: float
    source: Literal["stub", "une216701"]
    certifiable: bool
    land_use_efficiency: float | None = None
    normative_ref: str | None = None
    cop_geothermal: float | None = None
    thermal_exchange_w_m2: float | None = None
    solar_surplus_kw_est: float | None = None
    prioritize_geothermal_exchanger: bool | None = None
    osmosis_inlet_advisory: dict[str, Any] | None = None
    lue_land_use_efficiency: float | None = Field(
        default=None, description="Alias LUE para tablero (sombra + uso suelo)"
    )
