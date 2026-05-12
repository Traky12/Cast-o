"""
BioGrid 2.0 / CASTUO 5.PRO — energía disponible: Perovskita + Biogás (Chlorella, purines).

Chlorella PRO captura CO2; exceso de N de purines alimenta biogás. Límite superior del
optimizador cuántico: x_ro + x_geo + x_o3 <= perovskita + biogás.
"""
from __future__ import annotations

from typing import Any


def get_bionergy_budget_kw(
    irradiance_wm2: float | None,
    *,
    chlorella_reactor_active: bool = True,
    biogas_tank_level_pct: float = 65.0,
    perovskite_array_m2: float = 42.0,
) -> dict[str, Any]:
    """Potencia eléctrica equivalente disponible para RO, bomba geotérmica y ciclo O3."""
    ir = float(irradiance_wm2 or 350.0)
    eta_pv = 0.21
    perovskite_kw = min(28.0, (ir / 1000.0) * perovskite_array_m2 * eta_pv)
    base_biogas = 10.5 if chlorella_reactor_active else 7.0
    biogas_kw = base_biogas * (0.5 + 0.5 * min(1.0, biogas_tank_level_pct / 100.0))
    total = round(perovskite_kw + biogas_kw, 3)
    return {
        "perovskite_kw": round(perovskite_kw, 3),
        "biogas_kw": round(biogas_kw, 3),
        "total_available_kw": total,
        "source": "biogrid_5pro",
    }
