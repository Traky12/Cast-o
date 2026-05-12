# -*- coding: utf-8 -*-
"""Modelo predictivo de alertas (stub; opcional: Prophet + Mistral)."""
from typing import Any, Dict, List, Optional


def predict_stock_shortage(
    material_id: int,
    current_stock: float,
    daily_consumption_avg: float,
    days_ahead: int = 3,
) -> Optional[Dict[str, Any]]:
    """Predice si habrá falta de stock en los próximos días."""
    if daily_consumption_avg <= 0:
        return None
    days_until_shortage = current_stock / daily_consumption_avg
    if days_until_shortage > days_ahead:
        return None
    return {
        "material_id": material_id,
        "current_stock": current_stock,
        "daily_consumption": daily_consumption_avg,
        "days_until_shortage": days_until_shortage,
        "severity": "high" if days_until_shortage <= 1 else "medium",
    }


def generate_alert_message(alert_data: Dict[str, Any], material_name: str = "") -> str:
    """Genera mensaje de alerta (sin Mistral)."""
    return (
        f"Stock bajo: {material_name}. Actual: {alert_data.get('current_stock', 0):.1f} kg, "
        f"consumo diario: {alert_data.get('daily_consumption', 0):.1f} kg/día, "
        f"días hasta agotarse: {alert_data.get('days_until_shortage', 0):.1f}. "
        "Se recomienda ordenar materia prima."
    )
