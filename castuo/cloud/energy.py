# -*- coding: utf-8 -*-
"""Gestión energética — Microred, agrovoltaica, excedentes a mercado P2P (España/UE)."""
from typing import Any, Dict


class EnergyManager:
    """
    Gestor de energía: batería, solar, red, venta de excedentes.
    Mercado eléctrico español / UE (P2P, excedentes).
    """

    def __init__(self, greenhouse_id: str):
        self.greenhouse_id = greenhouse_id
        self._battery_level = 80.0
        self._solar_generation = 0.0
        self._consumption = 0.0

    def get_status(self) -> Dict[str, Any]:
        """Estado actual: batería, generación solar, consumo."""
        return {
            "greenhouse_id": self.greenhouse_id,
            "battery_level": self._battery_level,
            "solar_generation": self._solar_generation,
            "consumption": self._consumption,
        }

    def switch_to_grid(self) -> None:
        """Conmutar a red cuando batería < 20%."""
        self._battery_level = max(0, self._battery_level)

    def sell_excess(self, excess_kwh: float) -> None:
        """Vender excedentes al mercado (España: mercados P2P / excedentes)."""
        pass
