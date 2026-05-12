"""
Contexto energetico publico (ENTSO-E, REE): URLs y esquemas reales cambian; este modulo
prioriza fallos controlados y datos de referencia documentados frente a llamadas rotas en CI.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    import requests
except ImportError:
    requests = None


class EnergyOSINT:
    def __init__(self) -> None:
        self.sources = {
            "entsoe_docs": "https://transparency.entsoe.eu/",
            "ree_portal": "https://www.ree.es/",
        }

    def get_energy_prices(self, country_code: str = "ES") -> Dict[str, Any]:
        token = os.environ.get("ENTSOE_API_TOKEN", "").strip()
        if not token or requests is None:
            return {
                "country": country_code,
                "prices": [],
                "note": "Sin ENTSOE_API_TOKEN: registrar token y cliente XML oficial.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": self.sources["entsoe_docs"],
            }
        # La API ENTSO-E es XML y requiere documentType/period; placeholder de integracion.
        return {
            "country": country_code,
            "prices": [],
            "note": "Implementar query Day-ahead segun manual ENTSO-E.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_energy_policies(self, region: str = "EU") -> Dict[str, Any]:
        policies: Dict[str, List[Dict[str, Any]]] = {
            "EU": [
                {
                    "name": "Fit for 55",
                    "description": "Hoja de ruta climatica UE (referencia publica).",
                    "year": 2021,
                    "link": "https://commission.europa.eu/strategy-and-policy/priorities-2019-2024/european-green-deal/delivering-european-green-deal/fit-55_en",
                },
                {
                    "name": "REPowerEU",
                    "description": "Soberania energetica y transicion (referencia publica).",
                    "year": 2022,
                    "link": "https://commission.europa.eu/strategy-and-policy/priorities-2019-2024/european-green-deal/repowereurope_en",
                },
            ],
            "ES": [
                {
                    "name": "PNIEC 2021-2030",
                    "description": "Plan Nacional Integrado de Energia y Clima (referencia MITECO).",
                    "year": 2020,
                    "link": "https://www.miteco.gob.es/",
                }
            ],
        }
        return {
            "region": region,
            "policies": policies.get(region, policies["EU"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_carbon_intensity(self, country_code: str = "ES") -> Dict[str, Any]:
        carbon_data = {
            "ES": {"intensity": 180, "units": "gCO2/kWh", "source": "referencia ilustrativa"},
            "FR": {"intensity": 50, "units": "gCO2/kWh", "source": "referencia ilustrativa"},
            "DE": {"intensity": 250, "units": "gCO2/kWh", "source": "referencia ilustrativa"},
        }
        return {
            "country": country_code,
            "carbon_intensity": carbon_data.get(
                country_code, {"intensity": None, "units": "gCO2/kWh"}
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
